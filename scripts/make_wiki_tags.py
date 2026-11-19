#!/usr/bin/env python3
"""
Read the Poster Names in data/posters/poster_records.csv and write
data/wiki_tags.csv with kingdom and category columns.

Output columns: name, normalised, kingdom, categories

Kingdom:    Plant | Animal | Fungi

Categories (pipe-separated, multiple where applicable):
  Tree | Flower | Grass
  Bird | Butterfly | Moth | Insect | Arachnid | Mammal | Reptile | Amphibian
  Vertebrate | Invertebrate

Vertebrate/Invertebrate are added automatically for all animals:
  Birds, Mammals, Reptiles, Amphibians → also Vertebrate
  Butterflies, Moths, Insects, Arachnids → also Invertebrate

RAW_TAGS is keyed by the exact 'normalised' Poster Name so it
can be amended directly for future runs without any normalisation logic.
"""

from common import POSTER_RECORDS_CSV, WIKI_TAGS_CSV, read_csv, write_csv

A = "Animal"
P = "Plant"
F = "Fungi"

# ── Classification dictionary ─────────────────────────────────────────────────
# Key   = exact 'normalised' Poster Name
# Value = (kingdom, [categories])   — categories are joined with '|' in output

RAW_TAGS: dict[str, tuple[str, list[str]]] = {

    # ── Butterflies (Animal | Butterfly | Invertebrate) ───────────────────────
    "brimstone":            (A, ["Butterfly", "Invertebrate"]),
    "cabbagewhite":         (A, ["Butterfly", "Invertebrate"]),
    "commabutterfly":       (A, ["Butterfly", "Invertebrate"]),
    "commonblue":           (A, ["Butterfly", "Invertebrate"]),
    "gatekeeper":           (A, ["Butterfly", "Invertebrate"]),
    "hollyblue":            (A, ["Butterfly", "Invertebrate"]),
    "largewhite":           (A, ["Butterfly", "Invertebrate"]),
    "meadowbrown":          (A, ["Butterfly", "Invertebrate"]),
    "orangetip":            (A, ["Butterfly", "Invertebrate"]),
    "paintedlady":          (A, ["Butterfly", "Invertebrate"]),
    "peacockbutterfly":     (A, ["Butterfly", "Invertebrate"]),
    "redadmiral":           (A, ["Butterfly", "Invertebrate"]),
    "ringlet":              (A, ["Butterfly", "Invertebrate"]),
    "smallblue":            (A, ["Butterfly", "Invertebrate"]),
    "smalltortoiseshell":   (A, ["Butterfly", "Invertebrate"]),
    "smallwhite":           (A, ["Butterfly", "Invertebrate"]),
    "speckledwood":         (A, ["Butterfly", "Invertebrate"]),

    # ── Moths (Animal | Moth | Invertebrate) ─────────────────────────────────
    "gardentigermoth":      (A, ["Moth", "Invertebrate"]),
    "sixspotburnet":        (A, ["Moth", "Invertebrate"]),

    # ── Insects (Animal | Insect | Invertebrate) ─────────────────────────────
    "blackandyellowlonghornbeetle": (A, ["Insect", "Invertebrate"]),
    "cardinalbeetle":       (A, ["Insect", "Invertebrate"]),

    # ── Arachnids (Animal | Arachnid | Invertebrate) ─────────────────────────
    "labyrinthspider":      (A, ["Arachnid", "Invertebrate"]),

    # ── Birds (Animal | Bird | Vertebrate) ───────────────────────────────────
    "blackbird":            (A, ["Bird", "Vertebrate"]),
    "blackheadedgull":      (A, ["Bird", "Vertebrate"]),
    "bluetit":              (A, ["Bird", "Vertebrate"]),
    "buzzard":              (A, ["Bird", "Vertebrate"]),
    "canadagoose":          (A, ["Bird", "Vertebrate"]),
    "chaffinch":            (A, ["Bird", "Vertebrate"]),
    "collareddove":         (A, ["Bird", "Vertebrate"]),
    "crow":                 (A, ["Bird", "Vertebrate"]),
    "dunnock":              (A, ["Bird", "Vertebrate"]),
    "goldfinch":            (A, ["Bird", "Vertebrate"]),
    "greatspottedwoodpecker": (A, ["Bird", "Vertebrate"]),
    "greattit":             (A, ["Bird", "Vertebrate"]),
    "greenfinch":           (A, ["Bird", "Vertebrate"]),
    "greenwoodpecker":      (A, ["Bird", "Vertebrate"]),
    "greyheron":            (A, ["Bird", "Vertebrate"]),
    "herringgull":          (A, ["Bird", "Vertebrate"]),
    "jackdaw":              (A, ["Bird", "Vertebrate"]),
    "longtailedtit":        (A, ["Bird", "Vertebrate"]),
    "magpie":               (A, ["Bird", "Vertebrate"]),
    "redkite":              (A, ["Bird", "Vertebrate"]),
    "robin":                (A, ["Bird", "Vertebrate"]),
    "songthrush":           (A, ["Bird", "Vertebrate"]),
    "sparrow":              (A, ["Bird", "Vertebrate"]),
    "starling":             (A, ["Bird", "Vertebrate"]),
    "woodpigeon":           (A, ["Bird", "Vertebrate"]),
    "wren":                 (A, ["Bird", "Vertebrate"]),

    # ── Mammals (Animal | Mammal | Vertebrate) ────────────────────────────────
    "badger":               (A, ["Mammal", "Vertebrate"]),
    "fox":                  (A, ["Mammal", "Vertebrate"]),
    "roedeer":              (A, ["Mammal", "Vertebrate"]),

    # ── Reptiles (Animal | Reptile | Vertebrate) ──────────────────────────────
    "slowworm":             (A, ["Reptile", "Vertebrate"]),

    # ── Amphibians (Animal | Amphibian | Vertebrate) ──────────────────────────
    "commonfrog":           (A, ["Amphibian", "Vertebrate"]),

    # ── Trees (Plant | Tree) ──────────────────────────────────────────────────
    "appletree":            (P, ["Tree"]),
    "ashtree":              (P, ["Tree"]),
    "beech":                (P, ["Tree"]),
    "blackthorn":           (P, ["Tree"]),
    "cherrytree":           (P, ["Tree"]),
    "crabappletree":        (P, ["Tree"]),
    "crackwillow":          (P, ["Tree"]),
    "eldertree":            (P, ["Tree"]),
    "englishoak":           (P, ["Tree"]),
    "hawthorn":             (P, ["Tree"]),
    "hazel":                (P, ["Tree"]),
    "horsechestnut":        (P, ["Tree"]),
    "limetree":             (P, ["Tree"]),
    "poplar":               (P, ["Tree"]),
    "privet":               (P, ["Tree"]),
    "pussywillow":          (P, ["Tree"]),
    "rowantree":            (P, ["Tree"]),
    "sycamore":             (P, ["Tree"]),
    "turkeyoak":            (P, ["Tree"]),
    "walnuttree":           (P, ["Tree"]),
    "willow":               (P, ["Tree"]),

    # ── Wildflowers (Plant | Flower) ──────────────────────────────────────────
    "bindweed":             (P, ["Flower"]),
    "birdsfoottrefoil":     (P, ["Flower"]),
    "blackberry":           (P, ["Flower"]),
    "blackmedic":           (P, ["Flower"]),
    "bluebell":             (P, ["Flower"]),
    "buttercup":            (P, ["Flower"]),
    "catkins":              (P, ["Flower"]),
    "celandine":            (P, ["Flower"]),
    "chickweed":            (P, ["Flower"]),
    "cleavers":             (P, ["Flower"]),
    "commonhogweed":        (P, ["Flower"]),
    "commonknapweed":       (P, ["Flower"]),
    "commonnettle":         (P, ["Flower"]),
    "commonspottedorchid":  (P, ["Flower"]),
    "cowparsley":           (P, ["Flower"]),
    "creepingcinquefoil":   (P, ["Flower"]),
    "cuckooflower":         (P, ["Flower"]),
    "cuckoopint":           (P, ["Flower"]),
    "cutleavedcranesbill":  (P, ["Flower"]),
    "daisy":                (P, ["Flower"]),
    "dandelion":            (P, ["Flower"]),
    "dock":                 (P, ["Flower"]),
    "dogrose":              (P, ["Flower"]),
    "fieldforgetmenot":     (P, ["Flower"]),
    "fleabane":             (P, ["Flower"]),
    "garlicmustard":        (P, ["Flower"]),
    "greaterplantain":      (P, ["Flower"]),
    "greaterstitchwort":    (P, ["Flower"]),
    "greatwillowherb":      (P, ["Flower"]),
    "groundivy":            (P, ["Flower"]),
    "groundsel":            (P, ["Flower"]),
    "hawkweed":             (P, ["Flower"]),
    "hedgewoundwort":       (P, ["Flower"]),
    "hellebore":            (P, ["Flower"]),
    "herbrobert":           (P, ["Flower"]),
    "honeysuckle":          (P, ["Flower"]),
    "ivy":                  (P, ["Flower"]),
    "lesserstitchwort":     (P, ["Flower"]),
    "lesseryellowtrefoil":  (P, ["Flower"]),
    "matricariadiscoidea":  (P, ["Flower"]),
    "meadowvetchling":      (P, ["Flower"]),
    "nettle":               (P, ["Flower"]),
    "oxeyedaisy":           (P, ["Flower"]),
    "purplewoodanemone":    (P, ["Flower"]),
    "redclover":            (P, ["Flower"]),
    "redcurrant":           (P, ["Flower"]),
    "ribwortplantain":      (P, ["Flower"]),
    "selfheal":             (P, ["Flower"]),
    "slenderspeedwell":     (P, ["Flower"]),
    "slendertare":          (P, ["Flower"]),
    "smoothsowthistle":     (P, ["Flower"]),
    "snowdrop":             (P, ["Flower"]),
    "sowthistle":           (P, ["Flower"]),
    "spanishbluebell":      (P, ["Flower"]),
    "speedwell":            (P, ["Flower"]),
    "thistle":              (P, ["Flower"]),
    "tuftedvetch":          (P, ["Flower"]),
    "violet":               (P, ["Flower"]),
    "whiteclover":          (P, ["Flower"]),
    "whitedeadnettle":      (P, ["Flower"]),
    "wildangelica":         (P, ["Flower"]),
    "wildclary":            (P, ["Flower"]),
    "woodavens":            (P, ["Flower"]),
    "woundworthedgenettle": (P, ["Flower"]),
    "yarrow":               (P, ["Flower"]),
    "yellowrattle":         (P, ["Flower"]),

    # ── Grasses (Plant | Grass) ───────────────────────────────────────────────
    "annualmeadowgrass":    (P, ["Grass"]),
    "cocksfoot":            (P, ["Grass"]),
    "commonbent":           (P, ["Grass"]),
    "creepingbent":         (P, ["Grass"]),
    "cresteddogstail":      (P, ["Grass"]),
    "falseoatgrass":        (P, ["Grass"]),
    "italianryegrass":      (P, ["Grass"]),
    "meadowfoxtail":        (P, ["Grass"]),
    "meadowgrass":          (P, ["Grass"]),
    "perennialryegrass":    (P, ["Grass"]),
    "redfescue":            (P, ["Grass"]),
    "roughmeadowgrass":     (P, ["Grass"]),
    "ryegrass":             (P, ["Grass"]),
    "smoothmeadowgrass":    (P, ["Grass"]),
    "timothygrass":         (P, ["Grass"]),
    "yorkshirefog":         (P, ["Grass"]),

    # ── Fungi ─────────────────────────────────────────────────────────────────
    "baypolypore":          (F, []),
    "bracketfungi":         (F, []),
    "coalfungus":           (F, []),
    "daedaleopsisconfragosa": (F, []),
    "dryadssaddle":         (F, []),
    "fieldmushroom":        (F, []),
    "inocyberimosa":        (F, []),
    "tornfibrecap":         (F, []),
    "troopingfunnel":       (F, []),
    "wolfsmilk":            (F, []),
}

# ── Process Poster Names ──────────────────────────────────────────────────────

rows = list({r["normalised"]: r for r in reversed(read_csv(POSTER_RECORDS_CSV))}.values())
rows.sort(key=lambda r: r["normalised"])

out_rows = []
unmatched = []

for row in rows:
    key = row["normalised"]
    if key in RAW_TAGS:
        kingdom, cats = RAW_TAGS[key]
        categories = "|".join(cats)
    else:
        kingdom = categories = ""
        unmatched.append(row["name"])

    out_rows.append({
        "name":       row["name"],
        "normalised": key,
        "kingdom":    kingdom,
        "categories": categories,
    })

write_csv(WIKI_TAGS_CSV, out_rows, ["name", "normalised", "kingdom", "categories"])

print(f"Wrote {len(out_rows)} rows to {WIKI_TAGS_CSV.name}")
print(f"RAW_TAGS entries : {len(RAW_TAGS)}")

if unmatched:
    print(f"\n{len(unmatched)} unmatched (add to RAW_TAGS):")
    for name in unmatched:
        print(f"  {name!r}")
else:
    print("\nAll rows matched.")
