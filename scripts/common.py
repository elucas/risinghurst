"""Shared paths and helpers for the data pipeline.

Every data source joins on a Species' Scientific Name (see GLOSSARY.md and
adr/0001-scientific-name-as-species-identity.md).
"""

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CONTENT = ROOT / "content"

# Hand-made (committed)
POSTER_TEXT_DIR = DATA / "posters" / "text"          # OCR text, @-annotated by hand
POSTER_RECORDS_CSV = DATA / "posters" / "poster_records.csv"
WIKI_CUSTOM_CSV = DATA / "wiki_custom.csv"            # Poster Name -> Scientific Name (+ wiki query)
WIKI_TAGS_CSV = DATA / "wiki_tags.csv"
SPECIES_INDEX_JSON = DATA / "species.json"            # Scientific Name -> species page slug/title

# Fetched from third parties (git-ignored; see adr/0003-fetched-data-not-committed.md)
WIKI_CSV = DATA / "wiki.csv"
WIKI_JSON = DATA / "wiki.json"
OBSERVATIONS_DIR = DATA / "observations"

SPECIES_CONTENT = CONTENT / "species"
OBSERVATIONS_CONTENT = CONTENT / "observations"

# Wikimedia asks for an identifying User-Agent; keep it generic.
USER_AGENT = "RisinghurstWildlife/1.0 (static community nature site)"

MONTH_NAMES = {
    "01": "January", "02": "February", "03": "March", "04": "April",
    "05": "May", "06": "June", "07": "July", "08": "August",
    "09": "September", "10": "October", "11": "November", "12": "December",
}


def normalise(name: str) -> str:
    """Squash a common name into a key: 'Cock's Foot (Dactylis)' -> 'cocksfoot'."""
    name = re.sub(r"\(.*?\)", "", name or "")
    name = name.lower().replace("-", " ")
    name = re.sub(r"[^a-z ]", "", name)
    return "".join(name.split())


def month_name(value: str) -> str:
    """'06' -> 'June'. Non-numeric values (e.g. 'autumn') are title-cased."""
    return MONTH_NAMES.get(value, value.capitalize())


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1, ensure_ascii=False, sort_keys=True)
        fh.write("\n")


def is_comment(name: str) -> bool:
    """wiki_custom.csv rows starting with '#' or 'ALT?' are notes, not mappings."""
    return name.startswith("#") or name.startswith("ALT?")


def poster_names() -> dict[str, dict]:
    """Hand-curated Poster Name mapping from wiki_custom.csv, keyed by normalised name."""
    out = {}
    for row in read_csv(WIKI_CUSTOM_CSV):
        if is_comment(row["name"]):
            continue
        out[normalise(row["name"])] = row
    return out


def load_observation_months() -> list[dict]:
    """Every data/observations/YYYY-MM.json, oldest first."""
    months = []
    for path in sorted(OBSERVATIONS_DIR.glob("*.json")):
        with path.open(encoding="utf-8") as fh:
            months.append(json.load(fh))
    return months
