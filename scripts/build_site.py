#!/usr/bin/env python3
"""
Build the static HTML site from data/laws.json
Outputs: docs/index.html (GitHub Pages serves from /docs)
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from jinja2 import Environment, FileSystemLoader

DATA_DIR = Path("data")
DOCS_DIR = Path("docs")
DOCS_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR = Path("templates")

with open(DATA_DIR / "laws.json") as f:
    laws = json.load(f)

with open(DATA_DIR / "stats.json") as f:
    stats = json.load(f)

env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
template = env.get_template("index.html")

html = template.render(
    laws=laws,
    stats=stats,
    generated_at=datetime.now(timezone.utc).strftime("%d %B %Y, %H:%M UTC"),
    regions=sorted(set(law["region"] for law in laws)),
    statuses=sorted(set(law["status"] for law in laws)),
)

output = DOCS_DIR / "index.html"
output.write_text(html, encoding="utf-8")
print(f"[INFO] Built {output} ({len(laws)} laws)")
