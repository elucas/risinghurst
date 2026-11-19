#!/usr/bin/env python3
"""
Generate a thin page in content/species/ for every Species found in a Poster
Record or an Observation, and the slug registry data/species.json.

A species page holds identity and Poster Record taxonomies only. Wikipedia
content is looked up at build time from data/wiki.json, and hand-written
Fragments live in content/fragments/<slug>/ (never touched by this script).

Slugs are permanent: fragment folders are named after them. Once a Scientific
Name has a slug in data/species.json it keeps it. When several Poster Names
map to one Scientific Name (e.g. Nettle / Common Nettle) they share a page, and
the other names' old URLs become aliases.

Usage:
    python scripts/make_species_pages.py
"""

import json
from collections import defaultdict

from common import (SPECIES_CONTENT, SPECIES_INDEX_JSON, WIKI_TAGS_CSV, POSTER_RECORDS_CSV,
                    load_observation_months, month_name, normalise, poster_names, read_csv,
                    write_json)

MONTH_ORDER = list(month_name(f"{i:02d}") for i in range(1, 13))
GENERATED_MARKER = "generated = true"

# iNaturalist iconic group -> (kingdom, categories), matching data/wiki_tags.csv vocabulary
ICONIC = {
    "Aves": ("Animal", ["Bird", "Vertebrate"]),
    "Mammalia": ("Animal", ["Mammal", "Vertebrate"]),
    "Reptilia": ("Animal", ["Reptile", "Vertebrate"]),
    "Amphibia": ("Animal", ["Amphibian", "Vertebrate"]),
    "Actinopterygii": ("Animal", ["Fish", "Vertebrate"]),
    "Insecta": ("Animal", ["Insect", "Invertebrate"]),
    "Arachnida": ("Animal", ["Arachnid", "Invertebrate"]),
    "Mollusca": ("Animal", ["Mollusc", "Invertebrate"]),
    "Animalia": ("Animal", ["Invertebrate"]),
    "Plantae": ("Plant", []),
    "Fungi": ("Fungi", []),
    "Protozoa": ("Protozoa", []),
    "Chromista": ("Chromista", []),
}


def toml_list(items) -> str:
    return "[" + ", ".join(json.dumps(v) for v in items) + "]"


def main() -> None:
    names = poster_names()
    tags = {r["normalised"]: r for r in read_csv(WIKI_TAGS_CSV)}
    registry: dict[str, dict] = {}
    if SPECIES_INDEX_JSON.exists():
        registry = json.loads(SPECIES_INDEX_JSON.read_text(encoding="utf-8"))

    # ── Gather every Species, keyed by Scientific Name ──────────────────────
    species: dict[str, dict] = defaultdict(lambda: {
        "poster_keys": defaultdict(int), "poster_names": [], "years": set(), "months": set(),
        "pdfs": set(), "observed_months": set(), "common_name": "", "iconic_group": "", "rank": "",
    })

    for rec in read_csv(POSTER_RECORDS_CSV):
        key = rec["normalised"]
        mapping = names.get(key, {})
        sci = mapping.get("scientific_name") or f"poster:{key}"   # unmapped (e.g. Catkins)
        sp = species[sci]
        sp["poster_keys"][key] += 1
        if rec["name"] not in sp["poster_names"]:
            sp["poster_names"].append(rec["name"])
        sp["rank"] = mapping.get("rank", "")
        sp["years"].add(rec["year"])
        sp["months"].add(month_name(rec["month"]))
        sp["pdfs"].add(rec["filename"])

    for month in load_observation_months():
        for o in month["species"]:
            sp = species[o["scientific_name"]]
            sp["observed_months"].add(month["month"])
            sp["common_name"] = sp["common_name"] or o["common_name"]
            sp["iconic_group"] = sp["iconic_group"] or o["iconic_group"]

    # ── Assign permanent slugs ──────────────────────────────────────────────
    taken = {entry["slug"]: sci for sci, entry in registry.items()}
    for sci in sorted(species, key=lambda s: (not species[s]["poster_keys"], s)):
        sp = species[sci]
        if sci in registry:
            sp["slug"] = registry[sci]["slug"]
            continue
        if sp["poster_keys"]:
            # Prefer the most-used Poster Name, then alphabetical.
            candidates = sorted(sp["poster_keys"], key=lambda k: (-sp["poster_keys"][k], k))
        else:
            candidates = [normalise(sp["common_name"]), normalise(sci)]
        slug = next((c for c in candidates if c and c not in taken), normalise(sci))
        sp["slug"] = slug
        taken[slug] = sci

    # ── Write pages ─────────────────────────────────────────────────────────
    written = set()
    out_registry = {}
    for sci, sp in sorted(species.items(), key=lambda kv: kv[1]["slug"]):
        slug = sp["slug"]
        primary = slug if slug in sp["poster_keys"] else next(iter(sp["poster_keys"]), "")
        title = (names.get(primary, {}).get("name") if primary else "") or sp["common_name"] or sci
        title = title.split("(")[0].strip()
        title = title[:1].upper() + title[1:]          # iNaturalist names can be lower-case
        aliases = [f"species/{k}/" for k in sorted(sp["poster_keys"]) if k != slug]

        t = tags.get(primary, {})
        if t.get("kingdom"):
            kingdom, categories = t["kingdom"], [c for c in t.get("categories", "").split("|") if c]
        else:
            kingdom, categories = ICONIC.get(sp["iconic_group"], ("", []))

        real_sci = "" if sci.startswith("poster:") else sci
        lines = [
            "+++",
            f"# Generated by scripts/make_species_pages.py: edits here will be overwritten.",
            f"# Add your own notes as Fragments in content/fragments/{slug}/",
            f"title = {json.dumps(title)}",
            'template = "species.html"',
        ]
        if aliases:
            lines.append(f"aliases = {toml_list(aliases)}")
        lines += [
            "",
            "[taxonomies]",
            f"years = {toml_list(sorted(sp['years']))}",
            f"months = {toml_list(sorted(sp['months'], key=MONTH_ORDER.index))}",
            f"kingdom = {toml_list([kingdom] if kingdom else [])}",
            f"categories = {toml_list(categories)}",
            f"pdfs = {toml_list(sorted(sp['pdfs']))}",
            "",
            "[extra]",
            f"scientific_name = {json.dumps(real_sci)}",
            f"rank = {json.dumps(sp['rank'] or ('species' if real_sci else ''))}",
            f"poster_names = {toml_list(sp['poster_names'])}",
            f"observed_months = {toml_list(sorted(sp['observed_months']))}",
            GENERATED_MARKER,
            "+++",
            "",
        ]
        (SPECIES_CONTENT / f"{slug}.md").write_text("\n".join(lines), encoding="utf-8")
        written.add(f"{slug}.md")
        if real_sci:
            out_registry[real_sci] = {"slug": slug, "title": title}

    # ── Remove stale generated pages (merged Poster Names now redirect via aliases) ──
    removed = []
    for path in SPECIES_CONTENT.glob("*.md"):
        if path.name == "_index.md" or path.name in written:
            continue
        text = path.read_text(encoding="utf-8")
        if GENERATED_MARKER in text or "pdfs = [" in text:   # old generator had no marker
            path.unlink()
            removed.append(path.name)

    # ── Fragment folders: each needs a transparent _index.md and a matching species page ──
    fragments = SPECIES_CONTENT.parent / "fragments"
    for folder in sorted(p for p in fragments.glob("*") if p.is_dir()):
        if f"{folder.name}.md" not in written:
            print(f"WARNING: content/fragments/{folder.name}/ has no species page called {folder.name}")
            continue
        index = folder / "_index.md"
        if not index.exists():
            title = next((sp["title"] for sp in out_registry.values() if sp["slug"] == folder.name), folder.name)
            index.write_text(f'+++\ntitle = {json.dumps(title)}\ntransparent = true\n'
                             'page_template = "fragment.html"\n+++\n', encoding="utf-8")

    write_json(SPECIES_INDEX_JSON, out_registry)
    print(f"Wrote {len(written)} species pages; removed {len(removed)} stale"
          + (f" ({', '.join(sorted(removed))})" if removed else ""))
    unmapped = [s for s in species if s.startswith("poster:")]
    if unmapped:
        print(f"No Scientific Name yet (fill in data/wiki_custom.csv): {', '.join(unmapped)}")


if __name__ == "__main__":
    main()
