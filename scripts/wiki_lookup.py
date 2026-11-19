#!/usr/bin/env python3
"""
Look up a Wikipedia summary for every Species and write:

  data/wiki.csv   – fetched summaries, one row per looked-up name (cache; incremental)
  data/wiki.json  – the same data keyed by Scientific Name, for templates

Species come from the Poster Name mapping (data/wiki_custom.csv) and from
every fetched month in data/observations/.

What gets queried
-----------------
* Poster species: wiki_custom.csv's custom_name if set, else the Poster Name.
* Observation-only species: the scientific name, falling back to the common name.

A cached row is re-queried when the query that produced it differs from the
current one (e.g. after editing custom_name in wiki_custom.csv), so fixing a
wrong match is: edit wiki_custom.csv, re-run this script.

Usage:
    python scripts/wiki_lookup.py              # query what's missing/changed, then write wiki.json
    python scripts/wiki_lookup.py --offline    # only rebuild wiki.json from wiki.csv
"""

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request

from common import (USER_AGENT, WIKI_CSV, WIKI_JSON, load_observation_months, normalise,
                    poster_names, read_csv, write_csv, write_json)

SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
# Wikimedia rate-limits unidentified clients hard; be gentle.
DELAY = 10.0
LICENSE = "CC BY-SA 4.0"

FIELDNAMES = [
    "name", "normalised",
    "wiki_status", "wiki_url", "wiki_title", "wiki_thumbnail",
    "wiki_desc", "wiki_timestamp", "wiki_extract", "wiki_json",
    "scientific_name", "wiki_query",
]


class RateLimited(Exception):
    pass


def lookup(query: str) -> dict | None:
    title = urllib.parse.quote(query.replace(" ", "_"), safe="")
    req = urllib.request.Request(SUMMARY_URL.format(title=title), headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode()
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            raise RateLimited(query) from exc
        if exc.code != 404:
            print(f"    HTTP {exc.code} for {query!r}")
        return None
    data = json.loads(raw)
    if data.get("type") == "disambiguation":
        return None
    return {
        "wiki_status": "200",
        "wiki_url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
        "wiki_title": data.get("title", ""),
        "wiki_thumbnail": data.get("thumbnail", {}).get("source", ""),
        "wiki_desc": data.get("description", ""),
        "wiki_timestamp": data.get("timestamp", ""),
        "wiki_extract": data.get("extract", ""),
        "wiki_json": raw,
    }


def wanted_species() -> dict[str, dict]:
    """Scientific Name -> {name, normalised, queries[], custom}."""
    species: dict[str, dict] = {}
    for key, row in poster_names().items():
        sci = row.get("scientific_name")
        if not sci or sci in species:
            continue
        custom = (row.get("custom_name") or "").strip()
        species[sci] = {"name": row["name"], "normalised": key,
                        "queries": [custom or row["name"]], "custom": bool(custom)}
    for month in load_observation_months():
        for sp in month["species"]:
            sci = sp["scientific_name"]
            if sci and sci not in species:
                common = sp.get("common_name") or sci
                species[sci] = {"name": common, "normalised": normalise(common),
                                "queries": list(dict.fromkeys([sci, common])), "custom": False}
    return species


def attach_scientific_names(rows: list[dict], species: dict[str, dict]) -> None:
    """Older wiki.csv rows have no scientific_name; infer it from their normalised name/title."""
    by_key: dict[str, str] = {}
    for sci, sp in species.items():
        for key in (sp["normalised"], normalise(sci)):
            by_key.setdefault(key, sci)
    for key, row in poster_names().items():
        if row.get("scientific_name"):
            by_key[key] = row["scientific_name"]
    for row in rows:
        if not row.get("scientific_name"):
            row["scientific_name"] = (by_key.get(row["normalised"])
                                      or by_key.get(normalise(row.get("wiki_title", ""))) or "")


def needs_query(row: dict | None, sp: dict) -> bool:
    if row is None or row.get("wiki_status") not in ("200", "404"):
        return True
    if row.get("wiki_query"):
        return row["wiki_query"] not in sp["queries"]
    # Legacy row with no recorded query: trust it unless a custom page was asked for
    # and the cached title doesn't match it (e.g. "Fox" cached, "Red fox" wanted).
    return sp["custom"] and normalise(row.get("wiki_title", "")) != normalise(sp["queries"][0].replace("_", " "))


def to_json_entry(row: dict) -> dict:
    try:
        extract_html = json.loads(row.get("wiki_json") or "{}").get("extract_html", "")
    except ValueError:
        extract_html = ""
    return {
        "title": row["wiki_title"],
        "url": row["wiki_url"],
        "description": row["wiki_desc"],
        "extract": row["wiki_extract"],
        "extract_html": extract_html or row["wiki_extract"],
        "thumbnail": row["wiki_thumbnail"],
        "timestamp": row["wiki_timestamp"],
        "license": LICENSE,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--offline", action="store_true", help="Don't query Wikipedia")
    args = parser.parse_args()

    species = wanted_species()
    rows = read_csv(WIKI_CSV)
    attach_scientific_names(rows, species)

    def row_for(sci: str) -> dict | None:
        matches = [r for r in rows if r.get("scientific_name") == sci]
        return next((r for r in matches if r.get("wiki_status") == "200"), matches[0] if matches else None)

    todo = [sci for sci, sp in species.items() if needs_query(row_for(sci), sp)]
    print(f"{len(species)} species; {len(species) - len(todo)} cached, {len(todo)} to query"
          + (" (skipped: --offline)" if args.offline else ""))

    if not args.offline:
        try:
            for i, sci in enumerate(todo, 1):
                sp = species[sci]
                result, used = None, ""
                for query in sp["queries"]:
                    if i > 1 or used:
                        time.sleep(DELAY)
                    used = query
                    result = lookup(query)
                    if result:
                        break
                old = row_for(sci)
                new = {"name": sp["name"], "normalised": sp["normalised"], "scientific_name": sci,
                       "wiki_query": used, **(result or {"wiki_status": "404"})}
                if old:
                    rows[rows.index(old)] = new
                else:
                    rows.append(new)
                write_csv(WIKI_CSV, rows, FIELDNAMES)
                print(f"  [{i}/{len(todo)}] {sci:35s} {used!r:35s} {(result or {}).get('wiki_url', '(not found)')}")
        except RateLimited as exc:
            print(f"\n429 Too Many Requests at {exc}. Progress saved; re-run later to continue.")

    write_csv(WIKI_CSV, rows, FIELDNAMES)

    out = {}
    for sci in species:
        row = row_for(sci)
        if row and row.get("wiki_status") == "200":
            out[sci] = to_json_entry(row)
    write_json(WIKI_JSON, out)
    missing = sorted(set(species) - set(out))
    print(f"Wrote {len(out)} entries to {WIKI_JSON.name}"
          + (f"; no Wikipedia page for: {', '.join(missing)}" if missing else ""))


if __name__ == "__main__":
    main()
