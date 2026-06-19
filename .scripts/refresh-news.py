"""
Daily refresh of the Anduril IPO Tracker data arrays.

Driven by .github/workflows/refresh-news.yml on a daily cron (and via
"Run workflow" in the GitHub UI). Idempotent: only writes when the
content actually changes; the workflow only commits if `git diff` is
non-empty.

Anduril is private and has NOT filed an S-1, so unlike the SpaceX tracker
this script has no registrant CIK to poll. It does two things:

  * ARTICLE_POOL  — fully replaced from Google News RSS (no API key needed)
  * "Updated" dates on live FILINGS links + sitemap <lastmod>  — bumped to today

It also runs a *best-effort* EDGAR full-text probe for an Anduril S-1 /
DRS. SEC's full-text endpoint frequently 403s GitHub Actions runner IPs,
so this is wrapped defensively and simply prints what it finds; it does
NOT mutate the file on a match (the first real filing is a high-stakes,
hand-curated event). When Anduril actually files, wire its CIK into the
SpaceX-style EDGAR poller — see that repo's refresh-news.py for the shape.

Run locally with:
    python .scripts/refresh-news.py
"""

import datetime as dt
import html as html_module
import json
import re
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

REPO = Path(__file__).resolve().parents[1]
INDEX = REPO / "index.html"
SITEMAP = REPO / "sitemap.xml"

# SEC requires a real UA; Google News doesn't care but we're polite either way.
UA = ("anduril-ipo-tracker contact@bookhockeys.com "
      "(anduril.bookhockeys.com)")


def fetch(url, accept="*/*", retries=2):
    """GET a URL with our UA. Retries on transient errors."""
    last_err = None
    for attempt in range(retries + 1):
        try:
            req = Request(url, headers={"User-Agent": UA, "Accept": accept})
            with urlopen(req, timeout=30) as r:
                return r.read()
        except Exception as e:
            last_err = e
            if attempt < retries:
                import time
                time.sleep(3 + attempt * 4)  # 3s, 7s
    raise last_err


# === Google News RSS =========================================================
GNEWS_URL = "https://news.google.com/rss/search?q=%22Anduril%22+IPO&hl=en-US&gl=US&ceid=US:en"

# Friendly source names so the UI doesn't show "Bloomberg.com" next to "Bloomberg".
SOURCE_NORMALIZE = {
    "Bloomberg.com": "Bloomberg",
    "The Wall Street Journal": "WSJ",
    "Wall Street Journal": "WSJ",
    "The Motley Fool": "Motley Fool",
    "Reuters": "Reuters",
    "Yahoo Finance": "Yahoo Finance",
    "Yahoo": "Yahoo Finance",
    "Seeking Alpha": "Seeking Alpha",
    "Bloomberg": "Bloomberg",
    "CNBC": "CNBC",
    "TechCrunch": "TechCrunch",
    "Forge Global": "Forge Global",
}


def parse_pubdate(s):
    """Parse RFC 2822 with or without timezone token."""
    for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S %z"):
        try:
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    try:
        return dt.datetime.strptime(s[:25].strip(), "%a, %d %b %Y %H:%M:%S").date()
    except ValueError:
        return None


def google_news_articles():
    body = fetch(GNEWS_URL, accept="application/rss+xml")
    root = ET.fromstring(body)
    out = []
    for item in root.iter("item"):
        title_raw = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        # Google News titles end with " - Source"
        m = re.match(r"^(.+?)\s+-\s+([^-]+)$", title_raw)
        if m:
            title, source = m.group(1).strip(), m.group(2).strip()
        else:
            title, source = title_raw, "Unknown"
        title = html_module.unescape(title)
        source = SOURCE_NORMALIZE.get(source, source)
        d = parse_pubdate(pub)
        if not d or not link or not title:
            continue
        out.append({
            "title": title,
            "source": source,
            "date": d.isoformat(),
            "url": link,
        })
    return out


def filter_articles(articles, days=90, cap=25):
    """Anduril IPO coverage is sparser than SpaceX, so use a 90-day window."""
    cutoff = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    seen = set()
    out = []
    for a in sorted(articles, key=lambda x: x["date"], reverse=True):
        if a["date"] < cutoff:
            continue
        key = (a["title"].lower()[:80], a["source"].lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(a)
        if len(out) >= cap:
            break
    return out


# === HTML / JS array surgery =================================================

def js_escape(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def render_articles_block(articles):
    """Render the contents BETWEEN the AUTO:ARTICLES:START/END markers."""
    lines = ["  const ARTICLE_POOL = ["]
    for a in articles:
        lines.append(
            f'    {{ title: "{js_escape(a["title"])}", '
            f'source: "{js_escape(a["source"])}", '
            f'date: "{a["date"]}", '
            f'url: "{js_escape(a["url"])}" }},'
        )
    if articles:
        lines[-1] = lines[-1].rstrip(",")
    lines.append("  ];")
    return "\n" + "\n".join(lines) + "\n"


def replace_articles(text, articles):
    pattern = re.compile(
        r"(// AUTO:ARTICLES:START[^\n]*\n)(.*?)(\s*// AUTO:ARTICLES:END)",
        re.DOTALL,
    )
    body = render_articles_block(articles)
    end_marker = "  // AUTO:ARTICLES:END"
    return pattern.sub(lambda m: m.group(1) + body + end_marker, text, count=1)


def bump_updated_dates(text, today_iso):
    """Bump every entry whose dateKind is 'Updated' to today's date."""
    return re.sub(
        r'date: "\d{4}-\d{2}-\d{2}", dateKind: "Updated"',
        f'date: "{today_iso}", dateKind: "Updated"',
        text,
    )


def update_sitemap(today_iso):
    s = SITEMAP.read_text(encoding="utf-8")
    s2 = re.sub(r"<lastmod>[^<]*</lastmod>",
                f"<lastmod>{today_iso}</lastmod>", s, count=1)
    if s2 != s:
        SITEMAP.write_text(s2, encoding="utf-8")
        return True
    return False


# === Best-effort S-1 watch (informational only) ==============================
EDGAR_FTS = ("https://efts.sec.gov/LATEST/search-index?"
             "q=%22Anduril+Industries%22&forms=S-1,DRS,F-1")


def probe_edgar_s1():
    """Print whether EDGAR full-text search now returns an Anduril
    registration statement. Does NOT mutate the page — alerts the
    operator (via the Actions log) that it's time to hand-curate the
    big event. Fully defensive; SEC often 403s runner IPs."""
    try:
        body = fetch(EDGAR_FTS, accept="application/json")
        data = json.loads(body)
        hits = data.get("hits", {}).get("hits", [])
        andu = [h for h in hits
                if "anduril" in json.dumps(h).lower()]
        if andu:
            print(f"  *** EDGAR: {len(andu)} possible Anduril registration "
                  f"filing(s) detected — HAND-CURATE the S-1 timeline event! ***")
            for h in andu[:5]:
                src = h.get("_source", {})
                print(f"      {src.get('file_date','?')}  "
                      f"{src.get('forms', src.get('root_forms','?'))}  "
                      f"{src.get('display_names','?')}")
        else:
            print("  EDGAR: no Anduril registration statement yet.")
    except Exception as e:
        print(f"  EDGAR probe skipped (non-fatal): {e}", file=sys.stderr)


# === main ===================================================================

def main():
    print(f"[refresh-news] starting {dt.datetime.now(dt.timezone.utc).isoformat()}")
    today = dt.date.today()
    today_iso = today.isoformat()

    text = INDEX.read_text(encoding="utf-8")
    orig = text

    # Step 1: articles
    try:
        articles_raw = google_news_articles()
        articles = filter_articles(articles_raw)
        print(f"  Google News: {len(articles_raw)} items -> {len(articles)} kept "
              f"after dedupe + 90-day cutoff")
        if articles:
            text = replace_articles(text, articles)
        else:
            print("  No fresh articles — leaving ARTICLE_POOL as-is")
    except Exception as e:
        print(f"  WARNING: Google News fetch failed: {e}", file=sys.stderr)

    # Step 2: bump 'Updated' dates on live links
    text = bump_updated_dates(text, today_iso)

    # Step 3: S-1 watch (informational only)
    probe_edgar_s1()

    # Step 4: write only if changed
    sitemap_changed = update_sitemap(today_iso)
    if text != orig:
        INDEX.write_text(text, encoding="utf-8")
        print("  Wrote index.html")
    else:
        print("  index.html unchanged")
    if sitemap_changed:
        print("  Wrote sitemap.xml")
    return 0


if __name__ == "__main__":
    sys.exit(main())
