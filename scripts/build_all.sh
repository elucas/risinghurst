#!/usr/bin/env bash
# Rebuild all generated data and content. Run from anywhere.
#
#   scripts/build_all.sh            # offline: rebuild from data already on disk
#   scripts/build_all.sh --fetch    # also fetch last month's iNaturalist observations
#                                   # and look up any new species on Wikipedia
#
# Fresh checkout? Fetched data isn't in git (adr/0003). Fetch the months you want first:
#   uv run scripts/fetch_observations.py --month 2026-10 --month 2026-11
#   scripts/build_all.sh --fetch
set -euo pipefail
cd "$(dirname "$0")"

uv run build_poster_records.py           # OCR text  -> data/posters/poster_records.csv
uv run make_wiki_tags.py                 # Poster Names -> data/wiki_tags.csv (kingdom/categories)
if [[ "${1:-}" == "--fetch" ]]; then
    uv run fetch_observations.py         # previous month -> data/observations/YYYY-MM.json
    uv run draft_scientific_names.py     # new Poster Names -> drafted rows in data/wiki_custom.csv
    uv run wiki_lookup.py                # -> data/wiki.csv + data/wiki.json
else
    uv run wiki_lookup.py --offline      # data/wiki.csv -> data/wiki.json
fi
uv run make_species_pages.py             # -> content/species/*.md + data/species.json
uv run make_observation_pages.py         # -> content/observations/YYYY-MM.md
