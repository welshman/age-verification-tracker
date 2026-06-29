#!/usr/bin/env python3
"""
Age Verification Law Global Tracker - Scraper
Scrapes news, RSS feeds, and public government sources.
Outputs: data/laws.json
"""

import json
import os
import re
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import feedparser
import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

LAWS_FILE = DATA_DIR / "laws.json"
STATS_FILE = DATA_DIR / "stats.json"

# ── RSS / Atom Feeds ──────────────────────────────────────────────────────────
FEEDS = [
    {"url": "https://feeds.feedburner.com/eff/updates", "source": "EFF", "region": "Global"},
    {"url": "https://iapp.org/feed/", "source": "IAPP", "region": "Global"},
    {"url": "https://www.icmec.org/feed/", "source": "ICMEC", "region": "Global"},
    {"url": "https://edri.org/feed/", "source": "EDRi", "region": "Europe"},
    {"url": "https://www.out-law.com/rss", "source": "Pinsent Masons", "region": "Global"},
    {"url": "https://techcrunch.com/tag/age-verification/feed/", "source": "TechCrunch", "region": "Global"},
    {"url": "https://www.bbc.co.uk/news/technology/rss.xml", "source": "BBC Tech", "region": "UK"},
    {"url": "https://www.ofcom.org.uk/rss/news", "source": "Ofcom", "region": "UK"},
    {"url": "https://ico.org.uk/feed/", "source": "ICO UK", "region": "UK"},
    {"url": "https://www.acma.gov.au/rss.xml", "source": "ACMA", "region": "Australia"},
    {"url": "https://www.ftc.gov/feeds/press-release.xml", "source": "FTC", "region": "USA"},
    {"url": "https://epic.org/feed/", "source": "EPIC", "region": "USA"},
    {"url": "https://www.misbar.com/en/feed", "source": "Misbar", "region": "Global"},
    {"url": "https://www.consilium.europa.eu/en/rss/", "source": "EU Council", "region": "Europe"},
    {"url": "https://digital-strategy.ec.europa.eu/en/rss.xml", "source": "EU Digital Strategy", "region": "Europe"},
]

# ── Keywords to filter relevant items ─────────────────────────────────────────
KEYWORDS = [
    "age verification", "age check", "age gate", "online safety",
    "children online", "minor", "COPPA", "KOSA", "online safety act",
    "digital age", "age assurance", "pornography law", "adult content law",
    "children's privacy", "kids online", "AADC", "DSA age", "age appropriate",
    "parental consent", "child protection online"
]

# ── Known laws seed database (bootstraps first run) ───────────────────────────
SEED_LAWS = [
    {
        "id": "uk-osa-2023",
        "title": "Online Safety Act 2023",
        "country": "United Kingdom",
        "region": "Europe",
        "status": "Active",
        "effective_date": "2024-01-31",
        "summary": "Requires platforms to implement robust age verification to prevent children accessing harmful content. Enforced by Ofcom with fines up to £18m or 10% of global revenue.",
        "fines": "Up to £18 million or 10% of global annual revenue",
        "authority": "Ofcom",
        "url": "https://www.legislation.gov.uk/ukpga/2023/50/contents",
        "tags": ["pornography", "social media", "children", "platforms"],
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d")
    },
    {
        "id": "eu-dsa-2022",
        "title": "Digital Services Act (DSA)",
        "country": "European Union",
        "region": "Europe",
        "status": "Active",
        "effective_date": "2024-02-17",
        "summary": "Requires very large online platforms to implement age verification for minors and restrict targeted advertising to children. Non-compliance fines up to 6% of global turnover.",
        "fines": "Up to 6% of global annual turnover",
        "authority": "European Commission / National DSCs",
        "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32022R2065",
        "tags": ["platforms", "advertising", "children", "VLOP"],
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d")
    },
    {
        "id": "us-coppa-1998",
        "title": "Children's Online Privacy Protection Act (COPPA)",
        "country": "United States",
        "region": "Americas",
        "status": "Active",
        "effective_date": "2000-04-21",
        "summary": "Federal law requiring websites to obtain verifiable parental consent before collecting personal information from children under 13. FTC enforces with significant penalties.",
        "fines": "Up to $51,744 per violation",
        "authority": "FTC (Federal Trade Commission)",
        "url": "https://www.ftc.gov/legal-library/browse/rules/childrens-online-privacy-protection-rule-coppa",
        "tags": ["privacy", "children", "parental consent", "data"],
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d")
    },
    {
        "id": "us-kosa-2024",
        "title": "Kids Online Safety Act (KOSA)",
        "country": "United States",
        "region": "Americas",
        "status": "Active",
        "effective_date": "2024-07-30",
        "summary": "Signed into law July 2024. Requires platforms to implement default privacy settings for minors and provide parental controls. Platforms must minimize data collection and addictive design.",
        "fines": "Up to $50,000 per violation per day",
        "authority": "FTC",
        "url": "https://www.congress.gov/bill/118th-congress/senate-bill/1409",
        "tags": ["social media", "children", "privacy", "safety"],
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d")
    },
    {
        "id": "au-osa-2024",
        "title": "Online Safety Amendment (Social Media Minimum Age) Act 2024",
        "country": "Australia",
        "region": "Asia-Pacific",
        "status": "Active",
        "effective_date": "2025-07-01",
        "summary": "Bans children under 16 from using social media platforms. Platforms must take reasonable steps to verify ages. Fines for systematic non-compliance.",
        "fines": "Up to AUD $49.5 million for systemic breaches",
        "authority": "ACMA (Australian Communications and Media Authority)",
        "url": "https://www.legislation.gov.au/",
        "tags": ["social media", "under 16", "ban", "children"],
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d")
    },
    {
        "id": "fr-av-2023",
        "title": "French Age Verification Decree (Pornography)",
        "country": "France",
        "region": "Europe",
        "status": "Active",
        "effective_date": "2023-10-01",
        "summary": "Requires pornographic websites to implement robust age verification for French users. Arcom (formerly CSA) can order ISPs to block non-compliant sites.",
        "fines": "Site blocking by ISPs; criminal penalties",
        "authority": "Arcom",
        "url": "https://www.arcom.fr/",
        "tags": ["pornography", "blocking", "children"],
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d")
    },
    {
        "id": "de-juschg-2021",
        "title": "Youth Protection Act (JuSchG) 2021 Reform",
        "country": "Germany",
        "region": "Europe",
        "status": "Active",
        "effective_date": "2021-05-01",
        "summary": "Expanded German youth protection to online platforms. Requires age classification and appropriate access controls for harmful content online.",
        "fines": "Up to €50 million",
        "authority": "KJM (Commission for Youth Media Protection)",
        "url": "https://www.bmj.de/",
        "tags": ["youth protection", "platforms", "classification"],
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d")
    },
    {
        "id": "ca-bill-c63-2024",
        "title": "Online Harms Act (Bill C-63)",
        "country": "Canada",
        "region": "Americas",
        "status": "Proposed",
        "effective_date": "TBD",
        "summary": "Proposed Canadian legislation requiring age-appropriate design and verification for children. Creates a Digital Safety Commission. Currently progressing through Parliament.",
        "fines": "Up to CAD $10 million or 3% of global revenue",
        "authority": "Digital Safety Commission (proposed)",
        "url": "https://www.canada.ca/en/department-justice/news/2024/02/government-of-canada-introduces-online-harms-act.html",
        "tags": ["online harms", "children", "proposed", "social media"],
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d")
    },
    {
        "id": "sg-copa-2022",
        "title": "Code of Practice for Online Safety (Singapore)",
        "country": "Singapore",
        "region": "Asia-Pacific",
        "status": "Active",
        "effective_date": "2023-07-18",
        "summary": "Requires major social media services operating in Singapore to implement safety measures including age verification and child safety tools.",
        "fines": "Up to SGD $1 million per breach",
        "authority": "IMDA (Infocomm Media Development Authority)",
        "url": "https://www.imda.gov.sg/",
        "tags": ["social media", "children", "safety"],
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d")
    },
    {
        "id": "uk-aadc-2020",
        "title": "Age Appropriate Design Code (Children's Code)",
        "country": "United Kingdom",
        "region": "Europe",
        "status": "Active",
        "effective_date": "2021-09-02",
        "summary": "ICO code requiring services likely to be accessed by children to apply default privacy settings and restrict data profiling. Enforced via UK GDPR.",
        "fines": "Up to £17.5 million or 4% of global turnover under UK GDPR",
        "authority": "ICO (Information Commissioner's Office)",
        "url": "https://ico.org.uk/for-organisations/childrens-code-hub/",
        "tags": ["privacy", "children", "design", "data"],
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d")
    },
    {
        "id": "us-louisiana-hb142",
        "title": "Louisiana HB 142 (Age Verification for Pornography)",
        "country": "United States",
        "region": "Americas",
        "status": "Active",
        "effective_date": "2023-01-01",
        "summary": "First US state law requiring websites publishing pornographic content to verify users are over 18. Basis for similar laws in other US states.",
        "fines": "Civil liability; nominal damages",
        "authority": "Louisiana Attorney General",
        "url": "https://legis.la.gov/",
        "tags": ["pornography", "state law", "USA", "18+"],
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d")
    },
    {
        "id": "eu-gdpr-children",
        "title": "GDPR Article 8 (Children's Consent)",
        "country": "European Union",
        "region": "Europe",
        "status": "Active",
        "effective_date": "2018-05-25",
        "summary": "Sets the age of digital consent at 16 (or 13–15 depending on member state). Services must verify age and obtain parental consent for children below the threshold.",
        "fines": "Up to €20 million or 4% of global annual turnover",
        "authority": "National Data Protection Authorities",
        "url": "https://gdpr.eu/article-8-conditions-applicable-to-childs-consent/",
        "tags": ["GDPR", "privacy", "consent", "children"],
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d")
    }
]


def load_existing() -> list:
    if LAWS_FILE.exists():
        with open(LAWS_FILE) as f:
            return json.load(f)
    return SEED_LAWS.copy()


def make_id(title: str, source: str) -> str:
    raw = f"{title}-{source}".lower()
    return hashlib.md5(raw.encode()).hexdigest()[:10]


def is_relevant(text: str) -> bool:
    t = text.lower()
    return any(kw.lower() in t for kw in KEYWORDS)


def classify_region(text: str) -> str:
    mappings = {
        "uk": "Europe", "united kingdom": "Europe", "britain": "Europe",
        "europe": "Europe", "eu ": "Europe", "france": "Europe",
        "germany": "Europe", "netherlands": "Europe", "italy": "Europe",
        "spain": "Europe", "ireland": "Europe", "sweden": "Europe",
        "usa": "Americas", "united states": "Americas", "america": "Americas",
        "canada": "Americas", "brazil": "Americas", "mexico": "Americas",
        "australia": "Asia-Pacific", "new zealand": "Asia-Pacific",
        "india": "Asia-Pacific", "singapore": "Asia-Pacific",
        "japan": "Asia-Pacific", "south korea": "Asia-Pacific",
        "china": "Asia-Pacific", "uae": "Middle East",
        "saudi": "Middle East", "africa": "Africa",
    }
    t = text.lower()
    for key, region in mappings.items():
        if key in t:
            return region
    return "Global"


def classify_status(text: str) -> str:
    t = text.lower()
    if any(w in t for w in ["proposed", "bill", "draft", "consultation", "planned"]):
        return "Proposed"
    if any(w in t for w in ["passed", "enacted", "signed", "effective", "active", "came into force"]):
        return "Active"
    if any(w in t for w in ["suspended", "blocked", "injunction", "halted"]):
        return "Suspended"
    if any(w in t for w in ["amended", "updated", "revised"]):
        return "Updated"
    return "Active"


def scrape_feeds(existing_ids: set) -> list:
    new_items = []
    headers = {"User-Agent": "AgeVerificationTracker/1.0 (github.com/welshman/age-verification-tracker)"}

    for feed_info in FEEDS:
        try:
            feed = feedparser.parse(feed_info["url"])
            for entry in feed.entries[:20]:
                title = entry.get("title", "")
                summary = entry.get("summary", entry.get("description", ""))
                link = entry.get("link", "")
                combined = f"{title} {summary}"

                if not is_relevant(combined):
                    continue

                entry_id = make_id(title, feed_info["source"])
                if entry_id in existing_ids:
                    continue

                # Parse date
                pub_date = entry.get("published", entry.get("updated", ""))
                try:
                    parsed_date = dateparser.parse(pub_date).strftime("%Y-%m-%d")
                except Exception:
                    parsed_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

                # Clean summary
                clean_summary = BeautifulSoup(summary, "lxml").get_text(separator=" ", strip=True)[:500]

                new_items.append({
                    "id": entry_id,
                    "title": title,
                    "country": feed_info["region"],
                    "region": classify_region(combined),
                    "status": classify_status(combined),
                    "effective_date": parsed_date,
                    "summary": clean_summary,
                    "fines": "See source for details",
                    "authority": feed_info["source"],
                    "url": link,
                    "tags": [kw for kw in KEYWORDS if kw.lower() in combined.lower()][:5],
                    "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d")
                })
        except Exception as e:
            print(f"[WARN] Feed {feed_info['url']}: {e}")

    return new_items


def update_stats(laws: list) -> dict:
    by_region = {}
    by_status = {}
    for law in laws:
        r = law.get("region", "Global")
        s = law.get("status", "Unknown")
        by_region[r] = by_region.get(r, 0) + 1
        by_status[s] = by_status.get(s, 0) + 1

    return {
        "total": len(laws),
        "by_region": by_region,
        "by_status": by_status,
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    }


def main():
    print("[INFO] Loading existing data...")
    laws = load_existing()
    existing_ids = {law["id"] for law in laws}

    print("[INFO] Scraping feeds...")
    new_items = scrape_feeds(existing_ids)
    print(f"[INFO] Found {len(new_items)} new relevant items")

    laws.extend(new_items)

    # Sort: seed laws first (by effective_date desc), then news items
    laws.sort(key=lambda x: x.get("last_updated", "2000-01-01"), reverse=True)

    with open(LAWS_FILE, "w") as f:
        json.dump(laws, f, indent=2, ensure_ascii=False)
    print(f"[INFO] Saved {len(laws)} laws to {LAWS_FILE}")

    stats = update_stats(laws)
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"[INFO] Stats: {stats}")


if __name__ == "__main__":
    main()
