"""Product resolution benchmark (PRB) — v3 design, eight categories.

Category                     expected   label provenance
P1 exact catalogue names     ANSWER     catalogue record itself (identity)
P2 formatting variants       ANSWER     catalogue record (label-preserving case/space/punctuation edits)
P3 typos                     ANSWER     catalogue record (one seeded edit; collision-checked)
P4 underspecified short form ABSTAIN    rule: the last word of a multi-word type name with its qualifying
                                        word(s) removed (e.g. "Kettle" from "Electric Kettle"). The dropped
                                        qualifier distinguishes the catalogue good from goods outside it
                                        (stovetop vs electric kettle), so the text is underspecified
P5 confusable neighbours     ANSWER     catalogue record (typo/reorder applied to a base type that shares
                                        a word with a base type of a different HS code)
P6 ambiguous / underspecified ABSTAIN   pre-declared rules over the catalogue (shared words; category names)
P7 outside catalogue          ABSTAIN   Unicode CLDR emoji short names (emoji-test.txt 16.0, Unicode License v3)
   (informal names)                     from pre-declared sub-groups of tangible goods disjoint from the catalogue;
                                        look-alikes (sharing a word with a catalogue type) need human confirmation
P8 formal HS 2022 texts       ANSWER for the 43 catalogue codes (by definition), ABSTAIN otherwise;
                                        reported as a SEPARATE out-of-register category

"Catalogue record" labels are catalogue-asserted: they say which catalogue entry is meant, not that the
catalogue's HS assignment is legally correct.
"""
import re

from lexitax_v2.normalize import canonical, singular, tokens
from lexitax_v2.reference import base_type, catalogue

from .build_common import finalize
from .perturb import PERTURBATIONS, rng_for
from .refdata import load_emoji_names, load_hs6

FIELDS = ["item_id", "subset", "text", "expected", "label_hs", "label_base_types", "abstain_reason",
          "label_source", "mapping_basis", "hs_exists", "in_catalogue_support", "transform", "look_alike",
          "parent", "group", "cluster", "split"]

# Pre-declared (15 Nov 2026): emoji sub-groups denoting tangible goods. Sub-groups that overlap the catalogue
# domain (phone, computer, light & video, sound, music) and non-goods (places, weather, faces, symbols) are excluded.
EMOJI_GOODS_SUBGROUPS = [
    "food-fruit", "food-vegetable", "food-prepared", "food-asian", "food-sweet", "drink", "dishware",
    "sport", "game", "arts & crafts", "award-medal", "clothing", "musical-instrument", "book-paper",
    "money", "mail", "writing", "office", "lock", "tool", "science", "medical", "household",
    "transport-ground", "transport-water", "transport-air",
]
EMOJI_NAME_EXCLUDE = re.compile(r"(o’clock|thirty|face|chart|e-mail|arrow|flag|departure|arrival|station|"
                                r"sign|button|symbol|light|\bpassing\b|oncoming|\bsuit\b|pouring|x-ray|"
                                r"construction|cooking|joker|bullseye|drop of blood|dna|mahjong)", re.I)
# The pattern above was fixed on 15 Nov 2026 by reading emoji NAMES only (no system outputs): it removes
# names that denote scenes, activities, symbols or abstract things rather than tradeable goods.

EXCLUDED_FIELDS = FIELDS + ["exclusion_reason", "decision_source", "review_item_no", "recorded_decision",
                            "authorised_by", "authorised_on", "authorisation_record"]


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


def build(cfg, log, audit=None, pilot_dir=None, treatments_path=None):
    """Build the product benchmark. P7 review treatments come ONLY from the authoritative decisions file
    (pilot/authorised_review_treatments_v1.csv), validated against the review records before any generation.
    Authorised exclusions are removed after finalisation, so every other row is generated exactly as before;
    the full original rows of excluded items are appended to `audit` (if given)."""
    from .pilot import apply_review_treatments, load_treatments, provenance_log_entries
    treatments = load_treatments(path=treatments_path, pilot_dir=pilot_dir)  # aborts on any problem
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

    # P4 underspecified short forms: head noun of multi-word names, qualifier removed -> ABSTAIN
    for bname in sorted(bases):
        words = bname.split()
        if len(words) >= 2:
            head = words[-1]
            owners = word_bases.get(singular(head.lower()), set())
            if head.isalpha() and len(head) >= 3 and len(hs_of(owners)) == 1 and canonical(head) not in names_canon:
                items.append(_item(item_id=f"P4_short|{bname}|head_noun", subset="P4_short", text=head,
                                   expected="ABSTAIN", abstain_reason="underspecified_qualifier_removed",
                                   label_base_types=bname,
                                   label_source=f"rule:head noun of catalogue type '{bname}' with qualifier removed",
                                   mapping_basis="n/a", transform="head_noun", parent=bname,
                                   group=f"hs4:{bases[bname]['hs'][:4]}", cluster=f"base:{bname}"))

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

    # P7 outside catalogue, informal names (Unicode CLDR emoji short names, licence: Unicode License v3)
    catalogue_words = set(word_bases)

    def confusable_types(toks):
        """Catalogue types sharing a whole (singularised) word with the name."""
        hits = set()
        for t in toks:
            hits |= word_bases.get(t, set())
        return sorted(hits)

    pool_plain, pool_look, seen = [], [], set()
    for group, sub, name in load_emoji_names():
        if sub not in EMOJI_GOODS_SUBGROUPS or EMOJI_NAME_EXCLUDE.search(name) or not name.isascii():
            continue
        toks = tokens(name)
        key = canonical(name)
        if not toks or key in seen or key in names_canon:
            continue
        seen.add(key)
        conf = confusable_types(toks)
        (pool_look if conf else pool_plain).append((name, group, sub, conf))
    r = rng_for(seed, "P7")
    plain = r.sample(pool_plain, min(sizes["outside_plain"], len(pool_plain)))
    look = r.sample(pool_look, min(sizes["outside_lookalike_max"], len(pool_look)))
    # Review decisions are NOT applied here: see apply_review_treatments() after finalisation.
    for name, group, sub, conf in sorted(plain + look):
        la = bool(conf)
        iid = f"P7_outside|{name}"
        items.append(_item(item_id=iid, subset="P7_outside", text=name, expected="ABSTAIN",
                           abstain_reason="outside_catalogue", look_alike=la,
                           label_base_types=";".join(conf),
                           label_source=f"UnicodeEmoji16.0:{group} > {sub}",
                           mapping_basis="subgroup_disjoint_from_catalogue", transform="none",
                           in_catalogue_support=False, group=f"emoji:{tokens(name)[-1]}"))
    log.append(("emoji_pool_sizes", f"plain={len(pool_plain)} lookalike={len(pool_look)}"))

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
    rows = finalize(keyed, "label_key", seed, cfg["dev_fraction"], log)
    log.extend(provenance_log_entries(pilot_dir=pilot_dir, path=treatments_path))
    return apply_review_treatments(rows, treatments, log, audit)
