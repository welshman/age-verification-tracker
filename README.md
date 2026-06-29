# 🌍 Global Age Verification Law Tracker

> **Fully automated** — no human input required. Updates daily via GitHub Actions.

🔗 **Live site:** https://welshman.github.io/age-verification-tracker

## What it tracks
- Every major age verification law & regulation worldwide
- Regulatory fines and enforcement authorities
- Proposed, active, suspended & updated laws
- Real-time news from 15+ authoritative sources

## How it works

```
GitHub Actions (daily 06:00 UTC)
  └── scripts/scraper.py        → fetches RSS feeds & builds data/laws.json
  └── scripts/build_site.py     → renders templates/index.html → docs/index.html
  └── git commit & push          → GitHub Pages auto-publishes
```

## Sources
| Source | Type | Region |
|--------|------|--------|
| Ofcom | Official | UK |
| ICO UK | Official | UK |
| FTC | Official | USA |
| EU Digital Strategy | Official | Europe |
| EU Council | Official | Europe |
| ACMA | Official | Australia |
| EFF | NGO | Global |
| IAPP | Industry | Global |
| EDRi | NGO | Europe |
| EPIC | NGO | USA |
| Pinsent Masons (Out-Law) | Legal | Global |
| TechCrunch | News | Global |
| BBC Technology | News | UK |

## Running locally
```bash
pip install -r requirements.txt
python scripts/scraper.py
python scripts/build_site.py
# open docs/index.html
```

## License
MIT — free to use, fork, and adapt.
