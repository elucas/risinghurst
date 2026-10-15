#!/usr/bin/env python3
"""
Fetch iNaturalist research-grade observations near a fixed location and
write them to a dated CSV file.

Usage:
    python fetch_observations.py              # defaults to previous calendar month
    python fetch_observations.py --month 2024-03
"""

import argparse
import csv
import sys
from datetime import date, datetime
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
API_URL = "https://api.inaturalist.org/v2/observations"
LATITUDE = 51.75858
LONGITUDE = -1.19039
RADIUS_KM = 0.6
QUALITY_GRADE = "research"
PER_PAGE = 100

# Request all fields from the v2 API; we cherry-pick what we need when flattening.
# (The v2 API's selective dot-notation field filtering returns 422 for nested resources.)
FIELDS = "all"

# Columns written to the CSV (order matters)
CSV_COLUMNS = [
    "id",
    "uuid",
    "observed_on",
    "time_observed_at",
    "quality_grade",
    "latitude",
    "longitude",
    "place_guess",
    "taxon_id",
    "taxon_scientific_name",
    "taxon_common_name",
    "taxon_rank",
    "taxon_iconic_group",
    "observer",
    "uri",
    "description",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def previous_month_range() -> tuple[date, date]:
    """Return (first_day, last_day) of the previous calendar month."""
    today = date.today()
    first_of_this_month = today.replace(day=1)
    last_of_prev = first_of_this_month - __import__("datetime").timedelta(days=1)
    first_of_prev = last_of_prev.replace(day=1)
    return first_of_prev, last_of_prev


def parse_month(month_str: str) -> tuple[date, date]:
    """Parse a 'yyyy-mm' string and return (first_day, last_day)."""
    try:
        dt = datetime.strptime(month_str, "%Y-%m")
    except ValueError:
        sys.exit(f"Error: --month must be in yyyy-mm format, got '{month_str}'")

    first = dt.date().replace(day=1)
    # Advance to first day of next month, then step back one day
    if first.month == 12:
        last = first.replace(year=first.year + 1, month=1, day=1)
    else:
        last = first.replace(month=first.month + 1, day=1)
    last = last - __import__("datetime").timedelta(days=1)
    return first, last


def flatten_observation(obs: dict) -> dict:
    """Extract a flat dict of CSV-ready values from one API result."""
    taxon = obs.get("taxon") or {}
    user = obs.get("user") or {}

    # 'location' in v2 is a "lat,lng" string
    location_str = obs.get("location", "")
    lat, lng = ("", "")
    if location_str and "," in location_str:
        parts = location_str.split(",", 1)
        lat, lng = parts[0].strip(), parts[1].strip()

    return {
        "id": obs.get("id", ""),
        "uuid": obs.get("uuid", ""),
        "observed_on": obs.get("observed_on", ""),
        "time_observed_at": obs.get("time_observed_at", ""),
        "quality_grade": obs.get("quality_grade", ""),
        "latitude": lat,
        "longitude": lng,
        "place_guess": obs.get("place_guess", ""),
        "taxon_id": taxon.get("id", ""),
        "taxon_scientific_name": taxon.get("name", ""),
        "taxon_common_name": taxon.get("preferred_common_name", ""),
        "taxon_rank": taxon.get("rank", ""),
        "taxon_iconic_group": taxon.get("iconic_taxon_name", ""),
        "observer": user.get("login", ""),
        "uri": obs.get("uri", ""),
        "description": (obs.get("description") or "").replace("\n", " ").strip(),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def fetch_observations(d1: date, d2: date) -> list[dict]:
    params = {
        "lat": LATITUDE,
        "lng": LONGITUDE,
        "radius": RADIUS_KM,
        "quality_grade": QUALITY_GRADE,
        "d1": d1.isoformat(),
        "d2": d2.isoformat(),
        "per_page": PER_PAGE,
        "order_by": "observed_on",
        "order": "asc",
        "fields": FIELDS,
    }

    print(f"Querying iNaturalist API for {d1} → {d2} …")
    try:
        response = requests.get(API_URL, params=params, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        sys.exit(f"API request failed: {exc}")

    data = response.json()
    total = data.get("total_results", 0)
    results = data.get("results", [])
    print(f"  Total matching observations on server: {total}")
    print(f"  Observations retrieved: {len(results)}")
    return results


def write_csv(rows: list[dict], d1: date, d2: date) -> Path:
    filename = Path(f"./inaturalist/observations_{d1}_{d2}.csv")
    with filename.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return filename


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch iNaturalist research-grade observations to CSV."
    )
    parser.add_argument(
        "--month",
        metavar="yyyy-mm",
        help="Month to query (defaults to the previous calendar month).",
    )
    args = parser.parse_args()

    if args.month:
        d1, d2 = parse_month(args.month)
    else:
        d1, d2 = previous_month_range()

    results = fetch_observations(d1, d2)

    if not results:
        print("No observations found for this period.")
        return

    flat_rows = [flatten_observation(obs) for obs in results]
    output_path = write_csv(flat_rows, d1, d2)  # rows already flattened; write_csv just serialises them
    print(f"  Written to: {output_path.resolve()}")


if __name__ == "__main__":
    main()
