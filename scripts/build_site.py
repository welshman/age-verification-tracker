#!/usr/bin/env python3
"""
Build the static HTML site from data/laws.json
Outputs: docs/index.html
"""

import json
from collections import defaultdict
from pathlib import Path
from datetime import datetime, timezone
from jinja2 import Environment, FileSystemLoader

DATA_DIR  = Path("data")
DOCS_DIR  = Path("docs")
DOCS_DIR.mkdir(exist_ok=True)
TEMPLATES = Path("templates")

with open(DATA_DIR / "laws.json") as f:
    laws = json.load(f)

with open(DATA_DIR / "stats.json") as f:
    stats = json.load(f)

# Build countries_by_region dict for the country grid
countries_by_region = defaultdict(lambda: defaultdict(list))
for law in laws:
    region  = law.get("region", "Global")
    country = law.get("country", "Unknown")
    if country not in ("Global", "Unknown"):
        countries_by_region[region][country].append(law)

# Convert defaultdicts to plain dicts for Jinja2
countries_by_region = {r: dict(c) for r, c in countries_by_region.items()}

env = Environment(loader=FileSystemLoader(str(TEMPLATES)))
template = env.get_template("index.html")

html = template.render(
    laws=laws,
    laws_json=json.dumps(laws, ensure_ascii=False),
    stats=stats,
    generated_at=datetime.now(timezone.utc).strftime("%d %B %Y, %H:%M UTC"),
    regions=sorted(countries_by_region.keys()),
    statuses=sorted(set(law["status"] for law in laws)),
    countries_by_region=countries_by_region,
)

out = DOCS_DIR / "index.html"
out.write_text(html, encoding="utf-8")
print(f"[INFO] Built {out} ({len(laws)} laws, {sum(len(v) for v in countries_by_region.values())} countries)")
