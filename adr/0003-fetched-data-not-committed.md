# Fetched third-party data is not committed

Wikipedia data (`wiki.csv`, `wiki.json`) and iNaturalist observation data are fetched caches and are left out of git. Anyone checking out the repo fetches their own fresh copy. Hand-made data is committed: `wiki_custom.csv` / the Poster Name mapping, poster records, fragments and posters. Templates load fetched data with `load_data(..., required=false)`, so a fresh checkout still builds, just with empty cards. Pages credit Wikipedia (CC BY-SA 4.0) and iNaturalist observers, so the site stays compliant even if this decision is reversed later.

## Consequences

- The built site in `docs/` (GitHub Pages output) is still committed and contains content derived from the fetched data.
- Builds aren't reproducible from git alone. A new fetch can change the output when Wikipedia articles or observations change.
