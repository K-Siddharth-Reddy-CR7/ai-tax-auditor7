"""Product resolution benchmark (PRB) — v3 design, eight categories.

Category                     expected   label provenance
P1 exact catalogue names     ANSWER     catalogue record itself (identity)
P2 formatting variants       ANSWER     catalogue record (label-preserving case/space/punctuation edits)
P3 typos                     ANSWER     catalogue record (one seeded edit; collision-checked)
P4 shortened/initialisms     EITHER     catalogue record (rule: head noun / initialism; correct answer
                                        or abstention both acceptable; a wrong code is an error)
P5 confusable neighbours     ANSWER     catalogue record (typo/reorder applied to a base type that shares
                                        a word with a base type of a different HS code)
P6 ambiguous / underspecified ABSTAIN   pre-declared rules over the catalogue (shared words; category names)
P7 outside catalogue          ABSTAIN   Open Products Facts category names from pre-declared disjoint
   (informal names)                     top-level branches; look-alikes (sharing a catalogue word) flagged
P8 formal HS 2022 texts       ANSWER for the 43 catalogue codes (by definition), ABSTAIN otherwise;
                                        reported as a SEPARATE out-of-register category

"Catalogue record" labels are catalogue-asserted: they say which catalogue entry is meant, not that the
catalogue's HS assignment is legally correct.
"""
from lexitax_v2.normalize import canonical, singular, tokens
from lexitax_v2.reference import base_type, catalogue

from .build_common import finalize
from .perturb import PERTURBATIONS, rng_for
from .refdata import load_hs6, load_opf_categories

FIELDS = ["item_id", "subset", "text", "expected", "label_hs", "label_base_types", "abstain_reason",
          "label_source", "mapping_basis", "hs_exists", "in_catalogue_support", "transform", "look_alike",
          "parent", "group", "cluster", "split"]

OPF_DISJOINT_ROOTS = [  # pre-declared: top-level branches with no overlap with the 60 catalogue types
    "Apparel & Accessories", "Arts & Entertainment", "Baby & Toddler", "Furniture", "Luggage & Bags",
    "Media", "Musical Instruments", "Office Supplies", "Religious & Ceremonial", "Software",
    "Sporting Goods", "Toys & Games", "Vehicles & Parts",
]


def _item(**kw):
    base = dict(expected="", label_hs="", label_base_types="", abstain_reason="", label_source="",
                mapping_basis="", hs_exists="", in_catalogue_support="", transform="none", look_alike="",
                parent="", group="", cluster="")
    base.update(kw)
    base["cluster"] = base["cluster"] or base["item_id"]
    return base


def _perturb(name, kind, r, forbidden, own_canon, min_len=4):
    for _ in range(25):
        cand = PERTURBATIONS[kind](name, r) if kind != "typo" else PERTURBATIONS["typo"](name, r, min_len)
        if cand is None:
            return None
        c = canonical(cand)
        if c and (c == own_canon or c not in forbidden):
            if kind == "typo" and c == own_canon:
                continue
            return cand
    return None


def build(cfg, log):
    seed = cfg["seed"]
    sizes = cfg["product_design"]
    hs6, excluded = load_hs6()
    by_name, bases = catalogue()
    cat_codes = {b["hs"] for b in bases.values()}
    names_canon = set(by_name) | {b["canonical"] for b in bases.values()}
    items = []

    def cat_item(cat, bname, text, transform, expected="ANSWER", n=None):
        b = bases[bname]
        return _item(item_id=f"{cat}|{bname}|{transform}" + (f"|{n}" if n is not None else ""), subset=cat,
                     text=text, expected=expected, label_hs=b["hs"], label_base_types=bname,
                     label_source=f"catalogue:products.json base_type={bname}", mapping_basis="catalogue_asserted",
                     hs_exists=b["hs"] in hs6, in_catalogue_support=True, transform=transform, parent=bname,
                     group=f"hs4:{b['hs'][:4]}", cluster=f"base:{bname}")

    # P1 exact names: every base-type name + one seeded full catalogue name per type
    for bname in sorted(bases):
        items.append(cat_item("P1_exact", bname, bname, "base_name"))
        variants = sorted((p["Product"] for p in by_name.values()
                           if base_type(p["Product"]) == bname and canonical(p["Product"]) != bases[bname]["canonical"]))
        items.append(cat_item("P1_exact", bname, rng_for(seed, "P1", bname).choice(variants), "full_name"))

    # P2 formatting: case + whitespace/punctuation per type
    for bname in sorted(bases):
        for kind in ("case", "ws_punct"):
            t = _perturb(bname, kind, rng_for(seed, "P2", bname, kind), names_canon, bases[bname]["canonical"])
            if t:
                items.append(cat_item("P2_format", bname, t, kind))

    # P3 typos: n independent one-edit typos per type
    for bname in sorted(bases):
        for n in range(sizes["typos_per_type"]):
            t = _perturb(bname, "typo", rng_for(seed, "P3", bname, n), names_canon, bases[bname]["canonical"])
            if t:
                items.append(cat_item("P3_typo", bname, t, "typo", n=n))
            else:
                log.append(("typo_not_applicable", f"P3|{bname}|{n}"))

    # word statistics over base-type names
    word_bases = {}
    for bname, b in bases.items():
        for w in b["tokens"]:
            word_bases.setdefault(w, set()).add(bname)

    def hs_of(bset):
        return {bases[x]["hs"] for x in bset}

    # P4 shortened head noun (multi-word names) and initialisms (>=3 words); EITHER answer-or-abstain
    for bname in sorted(bases):
        words = bname.split()
        if len(words) >= 2:
            head = words[-1]
            owners = word_bases.get(singular(head.lower()), set())
            if head.isalpha() and len(head) >= 3 and len(hs_of(owners)) == 1 and canonical(head) not in names_canon:
                items.append(cat_item("P4_short", bname, head, "head_noun", expected="EITHER"))
        if len(words) >= 3:
            ini = "".join(w[0] for w in words).upper()
            if canonical(ini) not in names_canon and canonical(ini) not in word_bases:
                items.append(cat_item("P4_short", bname, ini, "initialism", expected="EITHER"))

    # P5 confusable neighbours: types sharing a word with a type of a different HS code
    for bname in sorted(bases):
        b = bases[bname]
        neighbours = {o for w in b["tokens"] for o in word_bases[w] if bases[o]["hs"] != b["hs"]}
        if not neighbours:
            continue
        shared = {w for w in b["tokens"] if any(w in bases[o]["tokens"] for o in neighbours)}
        distinct = [w for w in bname.split() if singular(w.lower()) not in shared and len(w) >= 4 and w.isalpha()]
        r = rng_for(seed, "P5", bname)
        if distinct:  # typo on the distinguishing word only
            words = bname.split()
            i = words.index(r.choice(distinct))
            for _ in range(25):
                t = PERTURBATIONS["typo"](words[i], r, 4)
                if t:
                    cand = " ".join(words[:i] + [t] + words[i + 1:])
                    if canonical(cand) not in names_canon:
                        items.append(cat_item("P5_confusable", bname, cand, "typo_distinguishing_word"))
                        break
        t = PERTURBATIONS["reorder"](bname, r)
        if t and canonical(t) not in names_canon:
            items.append(cat_item("P5_confusable", bname, t, "reorder"))

    # P6 ambiguous: (a) words shared by base types with >=2 HS codes; (b) catalogue category names spanning >=2 HS
    for w, owners in sorted(word_bases.items()):
        if len(hs_of(owners)) >= 2 and w not in {bases[o]["canonical"] for o in bases} and w.isalpha() and len(w) >= 3:
            items.append(_item(item_id=f"P6_ambiguous|word|{w}", subset="P6_ambiguous", text=w.capitalize(),
                               expected="ABSTAIN", abstain_reason="ambiguous_shared_word",
                               label_source="rule:word in base types with HS " + "/".join(sorted(hs_of(owners))),
                               mapping_basis="n/a", transform="none", group=f"ambig:{w}"))
    cat_hs = {}
    for b in bases.values():
        cat_hs.setdefault(b["category"], set()).add(b["hs"])
    for cat, hs_set in sorted(cat_hs.items()):
        if len(hs_set) >= 2:
            items.append(_item(item_id=f"P6_ambiguous|category|{cat}", subset="P6_ambiguous", text=cat,
                               expected="ABSTAIN", abstain_reason="ambiguous_category_name",
                               label_source=f"rule:catalogue category spanning {len(hs_set)} HS codes",
                               mapping_basis="n/a", transform="none", group=f"ambig:cat:{canonical(cat)}"))

    # P7 outside catalogue, informal names (Open Products Facts)
    catalogue_words = set(word_bases)
    pool_plain, pool_look = [], []
    for name, info in sorted(load_opf_categories().items()):
        if not info["roots"] or not set(info["roots"]) <= set(OPF_DISJOINT_ROOTS):
            continue
        toks = tokens(name)
        if not (1 <= len(toks) <= 6) or not name.isascii() or canonical(name) in names_canon:
            continue
        if any(bases[b]["tokens"] <= set(toks) and len(toks) == len(bases[b]["tokens"]) for b in bases):
            log.append(("opf_possible_catalogue_item_excluded", name))
            continue
        (pool_look if set(toks) & catalogue_words else pool_plain).append((name, info))
    r = rng_for(seed, "P7")
    plain = r.sample(pool_plain, min(sizes["outside_plain"], len(pool_plain)))
    look = r.sample(pool_look, min(sizes["outside_lookalike"], len(pool_look)))
    from .pilot import lookalike_decisions  # human confirmation of look-alikes (pre-declared rule)
    decisions = lookalike_decisions()
    reviewed = any(decisions.values())
    for name, info in sorted(plain + look):
        la = (name, info) in look
        if la and reviewed and decisions.get(f"P7_outside|{name}", "") != "outside":
            log.append(("lookalike_removed_after_review", f"{name}: {decisions.get(f'P7_outside|{name}', 'missing')}"))
            continue
        items.append(_item(item_id=f"P7_outside|{name}", subset="P7_outside", text=name, expected="ABSTAIN",
                           abstain_reason="outside_catalogue", look_alike=la,
                           label_source=f"OpenProductsFacts:{' > '.join(info['path'])}",
                           mapping_basis="branch_disjoint_from_catalogue", transform="none",
                           in_catalogue_support=False, group=f"opf:{info['parent'] or name}"))
    log.append(("opf_pool_sizes", f"plain={len(pool_plain)} lookalike={len(pool_look)}"))

    # P8 formal HS 2022 texts (separate out-of-register category)
    for code in sorted(cat_codes):
        if code in hs6:
            items.append(_item(item_id=f"P8_hs|in_catalogue|{code}", subset="P8_hs_formal", text=hs6[code],
                               expected="ANSWER", label_hs=code, label_source=f"HS2022(UN Comtrade mirror):{code}",
                               mapping_basis="nomenclature_definition", hs_exists=True, in_catalogue_support=True,
                               transform="in_catalogue_code", parent=code, group=f"hs4:{code[:4]}"))
    chapters = set(cfg["catalogue_chapters"])
    near = sorted(c for c in hs6 if c not in cat_codes and c[:2] in chapters)
    far = sorted(c for c in hs6 if c[:2] not in chapters)
    for kind, pool, n in (("near_domain_unsupported", near, sizes["hs_near"]), ("other_chapter", far, sizes["hs_far"])):
        for code in sorted(rng_for(seed, "P8", kind).sample(pool, n)):
            items.append(_item(item_id=f"P8_hs|{kind}|{code}", subset="P8_hs_formal", text=hs6[code],
                               expected="ABSTAIN", abstain_reason=kind, label_source=f"HS2022(UN Comtrade mirror):{code}",
                               mapping_basis="nomenclature_definition", hs_exists=True, in_catalogue_support=False,
                               transform=kind, parent=code, group=f"hs4:{code[:4]}"))
    for code, why in sorted(excluded.items()):
        log.append(("hs_code_excluded", f"{code}: {why}"))
    keyed = [dict(it, label_key=it["expected"] + ":" + it["label_hs"]) for it in items]
    return finalize(keyed, "label_key", seed, cfg["dev_fraction"], log)
