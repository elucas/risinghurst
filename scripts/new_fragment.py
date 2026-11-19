#!/usr/bin/env python3
"""
Start a new Fragment for a species.

    python scripts/new_fragment.py fox breeding

creates content/fragments/fox/breeding.md (and the folder's _index.md if
needed). The folder name must be a species page slug, i.e. a file in
content/species/. Existing files are never overwritten.
"""

import sys

from common import CONTENT, SPECIES_CONTENT

FRAGMENTS = CONTENT / "fragments"

TEMPLATE = """+++
title = "{title}"
[taxonomies]
senses = []   # see / hear / smell / touch / taste
when = []     # day / night / dawn / dusk; leave empty for any time
season = []   # e.g. ["December", "January"]; leave empty for all year
# [extra]
# image = "https://..."        # optional; defaults to the Wikipedia photo
# image_credit = "Photo: ..."
+++
One or two sentences: this text is what appears on posters.
"""


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    slug, name = sys.argv[1], sys.argv[2].removesuffix(".md")
    species_page = SPECIES_CONTENT / f"{slug}.md"
    if not species_page.exists():
        sys.exit(f"No species page {species_page.relative_to(CONTENT.parent)}; "
                 "the folder name must match a species slug.")

    folder = FRAGMENTS / slug
    folder.mkdir(parents=True, exist_ok=True)
    index = folder / "_index.md"
    if not index.exists():
        title = next((line.split("=", 1)[1].strip().strip('"')
                      for line in species_page.read_text(encoding="utf-8").splitlines()
                      if line.startswith("title")), slug)
        index.write_text(f'+++\ntitle = "{title}"\ntransparent = true\n'
                         'page_template = "fragment.html"\n+++\n', encoding="utf-8")

    path = folder / f"{name}.md"
    if path.exists():
        sys.exit(f"{path.relative_to(CONTENT.parent)} already exists")
    path.write_text(TEMPLATE.format(title=name.replace("-", " ").capitalize()), encoding="utf-8")
    print(f"Created {path.relative_to(CONTENT.parent)}")


if __name__ == "__main__":
    main()
