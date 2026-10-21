# Anduril IPO Tracker

A single-page, no-backend tracker for the **Anduril Industries** IPO — built for
retail investors who don't want to miss the filing. Live at
**[anduril.bookhockeys.com](https://anduril.bookhockeys.com/)**.

It's a sibling of the SpaceX IPO Tracker
and shares its architecture, but it's tuned for a company at a much earlier
stage: **Anduril has not filed an S-1.** So rather than faking a confirmed date,
this tracker is honest about what's known and what isn't.

## What it shows

- **Estimated window** — `2026–27`, clearly labelled unconfirmed. Palmer Luckey
  has said Anduril will go public "in the next few years," after profitability
  and manufacturing scale; Forge Global puts ~60% odds on a 2026 listing.
- **Stat board** — latest valuation ($61B), 2025 revenue (~$2.2B), 2026 revenue
  estimate (~$4.3B), and total raised ($11B+). This replaces the SpaceX
  countdown, which makes no sense without a date.
- **Ticker ribbon** — `TBD`. No symbol or exchange is reserved until a public
  prospectus is filed.
- **Latest coverage** — the 5 newest news items, auto-refreshed daily.
- **Timeline** — full funding history (Seed → Series H) plus the three
  outstanding pre-IPO milestones (profitability, the S-1 filing, the listing),
  each shown as `DATE TBD` until it actually happens. The S-1 row is flagged
  **"→ Watch this."**
- **Filings & sources** — a prominent "No S-1 on file yet" banner, plus the
  fastest links to catch the real filing: EDGAR full-text search, Forge/Hiive
  secondaries, the Anduril newsroom, and the third-party SPV Form Ds that are
  the only Anduril mentions on EDGAR today.
- **Reminders** — pick a 1/3/6-month horizon and get a check-in via `.ics`
  (native phone/desktop alarm), Google Calendar, or a browser notification.
  No email, no SMS, no server.
- **Save-as-PNG** — hover any article or timeline card for a camera button that
  exports just that card (lazy-loads html2canvas only on first click).

## Architecture

Static `index.html` (one file, vanilla JS, no build step) on GitHub Pages.
Three data arrays — `ARTICLE_POOL`, `TIMELINE`, `FILINGS` — live inside the page
between `AUTO:*:START/END` markers.

### The "worker" is a free GitHub Action

There is **no Cloudflare Worker** and no server. A daily GitHub Actions cron
([`.github/workflows/refresh-news.yml`](.github/workflows/refresh-news.yml))
runs [`.scripts/refresh-news.py`](.scripts/refresh-news.py), which:

1. Replaces `ARTICLE_POOL` from Google News RSS (`"Anduril" IPO`, 90-day window).
2. Bumps the `Updated` dates on live links and `sitemap.xml`.
3. Runs a **best-effort EDGAR full-text probe** for an Anduril S-1/DRS and logs
   a loud notice if one appears — a signal to hand-curate the big timeline event.

It only commits when content actually changed. Because Anduril has no registrant
CIK yet, the script does *not* auto-poll EDGAR by CIK the way the SpaceX tracker
does. When Anduril files, copy the SpaceX `edgar_filings()` poller in and pin the
new CIK.

## Local development

```bash
# serve the folder (any static server works)
python -m http.server 8103
# -> http://localhost:8103

# regenerate the OG image + apple-touch-icon after a palette/content change
python .scripts/build-og-image.py

# dry-run the daily refresh locally
python .scripts/refresh-news.py
```

## Deployment

GitHub Pages from the repo root. The custom domain is set via the `CNAME`
file (`anduril.bookhockeys.com`); point the subdomain at GitHub's Pages
endpoint in DNS, then enable Pages in repo settings.

## Disclaimer

Not investment advice, and not affiliated with Anduril. Anduril is private and
has not filed for an IPO. All figures come from public reporting and management
commentary and are subject to change. There is no offer price, ticker, or
exchange until a public S-1 is filed.

## Changelog

### v0.2.0 — 2026-10-20 (four-month catch-up: $90B tender, Fury production, 2027+ window)
- **Hero window moved from "2026–27" to "2027+".** With no S-1 on EDGAR by late October, a 2026 listing is no longer possible, and CEO Brian Schimpf told CNBC in July the company is "not in a rush" and that a hype cycle is a bad time to debut. The page's whole point is honest framing, so the headline now says what the evidence says.
- **Valuation mark is now $90B**, from the October 13 employee tender offer ($94.80/share, ~$1.3B cap, closes Nov 9). Price block, stat board, caption, meta tags and OG image all explain that this is a secondary buyback, not a priced round; the $61B Series H remains the last primary round, and the July Reuters report of ~$100B round talks is noted as unconfirmed.
- **Four timeline events added** that the news bot caught but the hand-curated timeline did not: June 17 Air Force production award for the FQ-44A Fury, July 9 "not in a rush" interview, July 28 first Fury off the Arsenal-1 line (named "Fury" Sept 14), and the Oct 13 tender. The final future event is retitled "Public listing — 2027 or later".
- llms.txt and the footer disclaimer brought to the same dates. OG image regenerated.

### v0.1.1 — 2026-06-29 (refresh script: multi-query news)
- **Bot's news refresh now runs 7 queries** instead of the single hardcoded `"Anduril" IPO`. New queries: `"Anduril Industries" IPO`, `"Anduril" IPO`, `"Anduril" funding`, `"Anduril" valuation`, `"Anduril" contract`, `"Anduril" SEC`, `"Anduril" S-1`. Results merged + URL-deduped + freshest 25 kept after the 90-day cutoff. Smoke test today: 373 unique items across 7 queries vs. ~50 from the single old query. Catches material non-IPO news (defense contracts, funding rounds, valuation marks) that the narrow query was filtering out.
- **No content changes** — script-only release. The next daily cron tick will exercise the new behavior. The S-1 EDGAR probe is unchanged (still informational-only since Anduril hasn't filed).

### v0.1.0 — 2026-06-05
Initial release. Forked the SpaceX IPO Tracker's architecture and re-pointed it
at Anduril. The key design decision: because Anduril is far earlier in the IPO
process (no S-1, no ticker, no date), the page is built to be *honest about
uncertainty* rather than mimic a confirmed-IPO layout — the countdown became a
stat board, the date became an estimated window, the ticker reads `TBD`, future
timeline events show `DATE TBD`, and the filings section leads with a "nothing
filed yet" banner. The daily refresh Action carries over for news, with the
EDGAR step downgraded to a watch-and-notify probe until Anduril gets a CIK.
