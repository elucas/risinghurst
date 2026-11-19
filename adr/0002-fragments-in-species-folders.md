# Fragments are separate pages, grouped in a folder named after their species

Hand-written notes about a Species (Fragments) need their own Sense, When and Season tags. Zola taxonomies tag whole pages, so tags on the species page would apply to the species all year round. Each Fragment is therefore its own page in `content/fragments/<slug>/`, where `<slug>` is the species page's slug (`content/fragments/fox/breeding.md` belongs to `content/species/fox.md`). Species pages stay flat generated pages carrying the Poster Record taxonomies. The generators never touch `content/fragments/`.

## Considered Options

- **Species as a folder section with Fragments inside** (the first plan). Rejected because Zola sections (`_index.md`) can't have taxonomies, so species would lose their years/months/kingdom/categories/pdfs tags.
- **Fragments name their species with `extra.species = "<Scientific Name>"`.** More consistent with adr/0001, but more typing. We chose the folder name.
- **Overlay file merged by a script, or plain data files read with `load_data`.** Rejected because tags would stay per-species, or there would be no taxonomy pages at all.

## Consequences

- Species page slugs are permanent: they name Fragment folders. `data/species.json` records each Scientific Name's slug, and the generator reuses it. When Poster Names merge into one Species, the old URLs become `aliases`.
- Fragments render as small pages of their own: `render = false` pages are left out of taxonomy listings.
- Each Fragment folder needs a `_index.md` with `transparent = true` so all Fragments appear in the `fragments` section that templates scan. `scripts/new_fragment.py` and `make_species_pages.py` create it.
- Wikipedia content isn't copied into species pages. It's looked up at build time from `wiki.json` (keyed by Scientific Name) through the shared `species.card` component.
