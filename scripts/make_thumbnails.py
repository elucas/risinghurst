#!/usr/bin/env python3
"""
Convert every page of every Original Poster PDF (static/pdfs/) to a JPEG thumbnail.

Output
------
static/thumbnails/        one JPEG per page, named  {source.pdf}.{page}.jpg
content/thumbnails.json   metadata dict, pretty-printed (used by the homepage)

JSON structure
--------------
{
  "example.pdf": {
    "year":       "2019",
    "month":      "06",
    "topics":     ["birds"],
    "thumbnails": ["example.pdf.0.jpg", "example.pdf.1.jpg"]
  },
  ...
}
"""

import json
import os
import re

import fitz  # pymupdf

# ── Config ────────────────────────────────────────────────────────────────────

ROOT        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_DIR     = os.path.join(ROOT, "static", "pdfs")
THUMB_DIR   = os.path.join(ROOT, "static", "thumbnails")
JSON_OUT    = os.path.join(ROOT, "content", "thumbnails.json")
THUMB_WIDTH = 300   # pixels; height scales proportionally

# ── Filename parsing ──────────────────────────────────────────────────────────

# Listed most-specific first so a substring like "meadow" isn't matched before
# "meadow-wild-flowers" consumes it.
KNOWN_TOPICS = [
    "meadow-wild-flowers",
    "wild-flowers",
    "other-things",
    "spring-extra",
    "butterflies",
    "wildflowers",
    "grasses",
    "birds",
    "meadow",
    "trees",
    "other",
    "spring",
]

SEASONS = {"winter", "autumn", "spring", "summer"}


def parse_pdf_name(filename: str) -> dict:
    """Return {"year", "month", "topics"} parsed from a PDF filename."""
    stem = filename.removesuffix(".pdf")

    # Year – first four digits
    m = re.match(r"(\d{4})", stem)
    year = m.group(1) if m else None

    # Month – two-digit number takes priority, then season name
    m = re.search(r"[_-](\d{2})(?:[_-]|$)", stem)
    if m:
        month = m.group(1)
    else:
        m = re.search(r"[_-](winter|autumn|spring|summer)(?:[_-]|$)", stem, re.IGNORECASE)
        month = m.group(1).lower() if m else None

    # Topics – scan for known keywords left-to-right, consuming each match
    lower = stem.lower()
    topics = []
    for topic in KNOWN_TOPICS:
        if topic in lower:
            topics.append(topic)
            lower = lower.replace(topic, "", 1)

    return {"year": year, "month": month, "topics": topics or None}


# ── Thumbnail generation ──────────────────────────────────────────────────────

os.makedirs(THUMB_DIR, exist_ok=True)

pdfs = sorted(f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf"))
metadata = {}

for pdf_name in pdfs:
    pdf_path = os.path.join(PDF_DIR, pdf_name)
    info = parse_pdf_name(pdf_name)
    thumbnails = []

    doc = fitz.open(pdf_path)
    for page_num, page in enumerate(doc):
        scale = THUMB_WIDTH / page.rect.width
        pix   = page.get_pixmap(matrix=fitz.Matrix(scale, scale))

        thumb_name = f"{pdf_name}.{page_num}.jpg"
        pix.save(os.path.join(THUMB_DIR, thumb_name))
        thumbnails.append(thumb_name)

    doc.close()

    metadata[pdf_name] = {**info, "thumbnails": thumbnails}
    print(f"{pdf_name:55s} {len(thumbnails)} page(s)  topics={info['topics']}")

# ── Write JSON ────────────────────────────────────────────────────────────────

with open(JSON_OUT, "w", encoding="utf-8") as fh:
    json.dump(metadata, fh, indent=2)

print(f"\nWrote {JSON_OUT}")
