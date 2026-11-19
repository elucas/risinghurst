#!/usr/bin/env python3
"""
Scan the OCR text of every Original Poster for @-annotated Poster Names and
write data/posters/poster_records.csv (one row per Poster Record).

Each annotated line looks like:  @Common Blue
or with a scientific name:       @Meadow foxtail (Alopecurus pratensis)

Output columns: filename, year, month, name, normalised
"""

import re

from common import POSTER_RECORDS_CSV, POSTER_TEXT_DIR, normalise, write_csv


def parse_year_month(filename: str) -> tuple[str, str]:
    m = re.match(r"(\d{4})[_-](\d{2})", filename) or re.match(r"(\d{4})[_-](\w+)", filename)
    return (m.group(1), m.group(2)) if m else ("", "")


def main() -> None:
    rows = []
    for path in sorted(POSTER_TEXT_DIR.glob("*.txt")):
        year, month = parse_year_month(path.name)
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("@"):
                name = line[1:].strip()
                rows.append({"filename": path.name, "year": year, "month": month,
                             "name": name, "normalised": normalise(name)})

    write_csv(POSTER_RECORDS_CSV, rows, ["filename", "year", "month", "name", "normalised"])
    print(f"Wrote {len(rows)} Poster Records to {POSTER_RECORDS_CSV.relative_to(POSTER_RECORDS_CSV.parents[2])}")


if __name__ == "__main__":
    main()
