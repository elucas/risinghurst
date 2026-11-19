#!/usr/bin/env bash
# OCR every Original Poster PDF (static/pdfs/) to text in data/posters/text/.
# The text files are then annotated BY HAND: prefix each Poster Name line with '@'
# (see scripts/build_poster_records.py). Re-running this overwrites those edits,
# so only run it for new PDFs.
#
# History: text was first extracted with ocrmypdf (v16.13), e.g.
#   parallel --tag -j 2 ocrmypdf '{}' 'output/{}' ::: *.pdf
set -euo pipefail
cd "$(dirname "$0")/.."
for f in static/pdfs/*.pdf; do
    uv run docling convert -vv --device=cpu --to=text --output=data/posters/text "$f"
done
