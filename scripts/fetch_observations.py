#!/usr/bin/env python3
"""
Fetch research-grade iNaturalist Observations near Risinghurst for one calendar
month and save them to data/observations/YYYY-MM.json.

The file keeps one record per Observation ("observations") and also a
per-Species summary ("species") so templates don't need to group rows.

Usage:
    python scripts/fetch_observations.py                 # previous calendar month
    python scripts/fetch_observations.py --month 2026-10
    python scripts/fetch_observations.py --month 2025-05 --month 2025-06
"""

import argparse
import sys
import time
from datetime import date, datetime, timedelta, timezone

import requests

from common import OBSERVATIONS_DIR, USER_AGENT, write_json

API_URL = "https://api.inaturalist.org/v2/observations"
LATITUDE = 51.75858
LONGITUDE = -1.19039
RADIUS_KM = 0.6
QUALITY_GRADE = "research"
PER_PAGE = 100
# The v2 API's dot-notation field filtering 422s on nested resources, so ask for everything.
FIELDS = "all"


def month_range(month: str | None) -> tuple[date, date]:
    if month:
        try:
            first = datetime.strptime(month, "%Y-%m").date()
        except ValueError:
            sys.exit(f"--month must be yyyy-mm, got {month!r}")
    else:
        first = (date.today().replace(day=1) - timedelta(days=1)).replace(day=1)
    next_first = (first.replace(day=28) + timedelta(days=4)).replace(day=1)
    return first, next_first - timedelta(days=1)


def flatten(obs: dict) -> dict:
    taxon = obs.get("taxon") or {}
    user = obs.get("user") or {}
    return {
        "id": obs.get("id"),
        "uri": obs.get("uri", ""),
        "observed_on": obs.get("observed_on", ""),
        "time_observed_at": obs.get("time_observed_at") or "",
        "scientific_name": taxon.get("name", ""),
        "common_name": taxon.get("preferred_common_name", ""),
        "rank": taxon.get("rank", ""),
        "iconic_group": taxon.get("iconic_taxon_name", ""),
        "observer": user.get("login", ""),
        "license_code": obs.get("license_code") or "",
        "place_guess": obs.get("place_guess", ""),
        "description": (obs.get("description") or "").replace("\n", " ").strip(),
    }


def summarise(observations: list[dict]) -> list[dict]:
    """One entry per Species with a count, so repeat sightings collapse to one row."""
    species: dict[str, dict] = {}
    for o in observations:
        entry = species.setdefault(o["scientific_name"], {
            "scientific_name": o["scientific_name"],
            "common_name": o["common_name"] or o["scientific_name"],
            "iconic_group": o["iconic_group"],
            "count": 0,
            "first_observed": o["observed_on"],
            "observers": [],
            "observations": [],
        })
        entry["count"] += 1
        entry["first_observed"] = min(entry["first_observed"], o["observed_on"])
        if o["observer"] not in entry["observers"]:
            entry["observers"].append(o["observer"])
        entry["observations"].append({"uri": o["uri"], "observed_on": o["observed_on"],
                                      "observer": o["observer"]})
    return sorted(species.values(), key=lambda s: s["common_name"].lower())


def fetch(d1: date, d2: date) -> tuple[list[dict], int]:
    results, page, total = [], 1, 0
    while True:
        params = {
            "lat": LATITUDE, "lng": LONGITUDE, "radius": RADIUS_KM,
            "quality_grade": QUALITY_GRADE, "d1": d1.isoformat(), "d2": d2.isoformat(),
            "per_page": PER_PAGE, "page": page, "order_by": "observed_on", "order": "asc",
            "fields": FIELDS,
        }
        resp = requests.get(API_URL, params=params, timeout=30, headers={"User-Agent": USER_AGENT})
        resp.raise_for_status()
        data = resp.json()
        total = data.get("total_results", 0)
        batch = data.get("results", [])
        results.extend(batch)
        if not batch or len(results) >= total:
            return results, total
        page += 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--month", metavar="yyyy-mm", action="append",
                        help="Month to fetch (repeatable). Defaults to the previous calendar month.")
    args = parser.parse_args()

    for i, month in enumerate(args.month or [None]):
        if i:
            time.sleep(1)  # iNaturalist asks for <= 1 request/second
        d1, d2 = month_range(month)
        print(f"iNaturalist {d1} → {d2} …", end=" ", flush=True)
        try:
            raw, total = fetch(d1, d2)
        except requests.RequestException as exc:
            sys.exit(f"API request failed: {exc}")
        observations = [flatten(o) for o in raw]
        out = OBSERVATIONS_DIR / f"{d1:%Y-%m}.json"
        write_json(out, {
            "month": f"{d1:%Y-%m}",
            "start": d1.isoformat(),
            "end": d2.isoformat(),
            "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "source": "https://www.inaturalist.org",
            "query": {"lat": LATITUDE, "lng": LONGITUDE, "radius_km": RADIUS_KM,
                      "quality_grade": QUALITY_GRADE},
            "total_results": total,
            "observations": observations,
            "species": summarise(observations),
        })
        print(f"{len(observations)} observations → {out.relative_to(OBSERVATIONS_DIR.parent.parent)}")


if __name__ == "__main__":
    main()
