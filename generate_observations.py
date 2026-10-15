#!/usr/bin/env python3
"""
Read iNaturalist CSV exports from ./inaturalist/ and render a Zola-compatible
markdown page for each one in ./content/observations/.

Filename convention expected:
    observations_YYYY-MM-DD_YYYY-MM-DD.csv

Output:
    content/observations/YYYY-MM.md
"""

import csv
import re
import sys
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

# ---------------------------------------------------------------------------
# Paths (all relative to this script's location)
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
INATURALIST_DIR = BASE_DIR / "inaturalist"
OUTPUT_DIR = BASE_DIR / "content" / "observations"
TEMPLATE_DIR = INATURALIST_DIR
TEMPLATE_FILE = "observation.md.j2"

FILENAME_PATTERN = re.compile(
    r"observations_(?P<start>\d{4}-\d{2}-\d{2})_(?P<end>\d{4}-\d{2}-\d{2})\.csv"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_dates_from_filename(path: Path) -> tuple[datetime, datetime] | None:
    """Return (start_date, end_date) parsed from the CSV filename, or None."""
    m = FILENAME_PATTERN.match(path.name)
    if not m:
        return None
    start = datetime.strptime(m.group("start"), "%Y-%m-%d")
    end = datetime.strptime(m.group("end"), "%Y-%m-%d")
    return start, end


def format_time(raw: str) -> str:
    """
    Convert an ISO 8601 timestamp (e.g. '2026-09-06T12:30:29+01:00')
    to a compact display string: '06 Sep 12:30'.
    Falls back to the raw value if parsing fails.
    """
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
        try:
            dt = datetime.strptime(raw[:19], "%Y-%m-%dT%H:%M:%S")
            return dt.strftime("%d %b %H:%M")
        except ValueError:
            pass
    return raw


def read_rows(csv_path: Path) -> list[dict]:
    """Return a list of row dicts with a pre-formatted time_display field."""
    rows = []
    with csv_path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            row["time_display"] = format_time(row.get("time_observed_at", ""))
            rows.append(row)
    return rows


def output_path(start: datetime) -> Path:
    return OUTPUT_DIR / f"{start.strftime('%Y-%m')}.md"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape([]),  # plain markdown — no HTML escaping
        keep_trailing_newline=True,
    )
    template = env.get_template(TEMPLATE_FILE)

    csv_files = sorted(INATURALIST_DIR.glob("observations_*.csv"))
    if not csv_files:
        sys.exit(f"No CSV files found in {INATURALIST_DIR}")

    for csv_path in csv_files:
        dates = parse_dates_from_filename(csv_path)
        if dates is None:
            print(f"  Skipping (unexpected filename): {csv_path.name}")
            continue

        start, _end = dates
        rows = read_rows(csv_path)

        context = {
            "year": start.strftime("%Y"),
            "month_name": start.strftime("%B"),
            "month_str": start.strftime("%m"),
            # Zola TOML date — bare value, no quotes
            "date": start.strftime("%Y-%m-%d"),
            "title": start.strftime("%B %Y"),
            "count": len(rows),
            "rows": rows,
        }

        out = output_path(start)
        out.write_text(template.render(**context), encoding="utf-8")
        print(f"  Written {len(rows):>3} rows → {out.relative_to(BASE_DIR)}")

    print(f"\nDone. {len(csv_files)} file(s) processed.")


if __name__ == "__main__":
    main()
