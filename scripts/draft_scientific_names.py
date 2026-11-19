#!/usr/bin/env python3
"""
Make sure data/wiki_custom.csv has one row per Poster Name, and draft a
Scientific Name for any row that lacks one using the iNaturalist taxa search.

wiki_custom.csv columns
-----------------------
name             Poster Name, as first written on an Original Poster
custom_name      Optional Wikipedia page to use instead of the Poster Name
scientific_name  The Species' identity (may be a genus where the poster was vague)
rank             iNaturalist rank of scientific_name (species, genus, ...)
checked          'y' once a human has confirmed scientific_name; drafts are blank

Rows whose name starts with '#' or 'ALT?' are notes and left alone.
Drafted rows are never overwritten on later runs; edit them by hand.

Usage:
    python scripts/draft_scientific_names.py            # draft missing names
    python scripts/draft_scientific_names.py --dry-run  # show what would be queried
"""

import argparse
import json
import re
import time
import urllib.parse
import urllib.request

from common import (POSTER_RECORDS_CSV, USER_AGENT, WIKI_CUSTOM_CSV, is_comment,
                    normalise, read_csv, write_csv)

FIELDNAMES = ["name", "custom_name", "scientific_name", "rank", "checked"]
TAXA_URL = "https://api.inaturalist.org/v1/taxa/autocomplete"
UK_PLACE_ID = 6857   # bias common-name matches towards British usage
DELAY = 1.0          # iNaturalist asks for <= 1 request/second


def search_taxon(query: str) -> dict | None:
    params = urllib.parse.urlencode({
        "q": query, "per_page": 1, "is_active": "true",
        "locale": "en-GB", "preferred_place_id": UK_PLACE_ID,
    })
    req = urllib.request.Request(f"{TAXA_URL}?{params}", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        results = json.load(resp).get("results", [])
    return results[0] if results else None


def query_for(row: dict) -> str:
    """Search term: the Wikipedia override if any, minus underscores and '(butterfly)'-style notes."""
    q = (row.get("custom_name") or row["name"]).replace("_", " ")
    return re.sub(r"\(.*?\)", "", q).strip()


def main() -> None:
    args_parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    args_parser.add_argument("--dry-run", action="store_true")
    args = args_parser.parse_args()

    rows = read_csv(WIKI_CUSTOM_CSV)
    known = {normalise(r["name"]) for r in rows if not is_comment(r["name"])}

    # Add a row for every Poster Name not yet listed (first-seen spelling).
    added = 0
    for rec in read_csv(POSTER_RECORDS_CSV):
        if rec["normalised"] not in known:
            known.add(rec["normalised"])
            rows.append({"name": rec["name"]})
            added += 1
    print(f"{added} new Poster Names added to {WIKI_CUSTOM_CSV.name}")

    todo = [r for r in rows if not is_comment(r["name"]) and not r.get("scientific_name")]
    print(f"{len(todo)} rows need a drafted Scientific Name")

    try:
        for i, row in enumerate(todo, 1):
            query = query_for(row)
            if args.dry_run:
                print(f"  would query {query!r}")
                continue
            taxon = search_taxon(query)
            if taxon:
                row["scientific_name"] = taxon["name"]
                row["rank"] = taxon.get("rank", "")
                common = taxon.get("preferred_common_name", "")
                print(f"  [{i}/{len(todo)}] {row['name']:40s} -> {taxon['name']} ({row['rank']}, {common})")
            else:
                print(f"  [{i}/{len(todo)}] {row['name']:40s} -> (no match)")
            time.sleep(DELAY)
    finally:
        if not args.dry_run:
            # Alphabetical; note rows sit just after the name they annotate.
            rows.sort(key=lambda r: (normalise(r["name"].lstrip("#").replace("ALT?", "")), is_comment(r["name"])))
            write_csv(WIKI_CUSTOM_CSV, rows, FIELDNAMES)
            print(f"Saved {WIKI_CUSTOM_CSV.name}. Review drafts (checked column blank) by hand.")


if __name__ == "__main__":
    main()
