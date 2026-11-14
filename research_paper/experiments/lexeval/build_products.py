"""Product resolution benchmark (PRB).

Label provenance per subset:
  PA  catalogue-derived texts      -> label = catalogue HS of the source base type
                                       (mapping_basis = catalogue_asserted; NOT verified as legally correct)
  PB  HS 2022 texts of the 43 catalogue codes -> label = the code itself (nomenclature_definition)
  PC  HS 2022 texts of other subheadings in the catalogue chapters -> expected ABSTAIN (unsupported_subheading)
  PD  HS 2022 texts of subheadings in all other chapters           -> expected ABSTAIN (out_of_catalogue_chapter)
  PE  rule-generated ambiguous tokens (shared by base types with different HS codes) -> expected ABSTAIN
"""
from lexitax_v2.normalize import canonical, tokens
from lexitax_v2.reference import base_type, catalogue

from .build_common import finalize
from .perturb import PERTURBATIONS, rng_for
from .refdata import load_hs6

FIELDS = ["item_id", "subset", "text", "expected", "label_hs", "abstain_reason", "label_source",
          "mapping_basis", "hs_exists", "in_catalogue_support", "transform", "parent", "group", "split"]


def _item(iid, subset, text, expected, label_hs, reason, source, basis, hs_exists, supported,
          transform, parent, group):
    return dict(item_id=iid, subset=subset, text=text, expected=expected, label_hs=label_hs,
                abstain_reason=reason, label_source=source, mapping_basis=basis,
                hs_exists=hs_exists, in_catalogue_support=supported, transform=transform,
                parent=parent, group=group)


def build(cfg, log):
    seed = cfg["seed"]
    hs6, excluded = load_hs6()
    by_name, bases = catalogue()
    cat_codes = {b["hs"] for b in bases.values()}
    all_product_canon = set(by_name) | {b["canonical"] for b in bases.values()}
    items = []

    # PA: catalogue-derived
    for bname in sorted(bases):
        b = bases[bname]
        hs = b["hs"]
        common = dict(expected="ANSWER", label_hs=hs, reason="",
                      source=f"catalogue:products.json base_type={bname}",
                      basis="catalogue_asserted", hs_exists=hs in hs6, supported=True,
                      group=f"hs4:{hs[:4]}")
        items.append(_item(f"PA|{bname}|base", "PA", bname, transform="none", parent=bname, **common))
        variants = sorted((p for p in by_name.values() if base_type(p["Product"]) == bname
                           and canonical(p["Product"]) != b["canonical"]), key=lambda p: p["Product"])
        r = rng_for(seed, "PA-full", bname)
        full = r.choice(variants)["Product"]
        items.append(_item(f"PA|{bname}|full_name", "PA", full, transform="full_name", parent=bname, **common))
        for pname in cfg["product_perturbations"]:
            r = rng_for(seed, "PA", bname, pname)
            text = None
            for _attempt in range(20):
                cand = PERTURBATIONS[pname](bname, r)
                if cand is None:
                    break
                c = canonical(cand)
                # pre-declared validity rule: a perturbation must not collide with another catalogue name
                if c and (c == b["canonical"] or c not in all_product_canon):
                    text = cand
                    break
            if text is None:
                log.append(("perturbation_not_applicable", f"PA|{bname}|{pname}"))
                continue
            items.append(_item(f"PA|{bname}|{pname}", "PA", text, transform=pname, parent=bname, **common))

    # PB: nomenclature texts of catalogue codes
    for code in sorted(cat_codes):
        if code not in hs6:
            log.append(("catalogue_code_excluded_from_PB", code))
            continue
        desc = hs6[code]
        common = dict(expected="ANSWER", label_hs=code, reason="", source=f"HS2022:{code}",
                      basis="nomenclature_definition", hs_exists=True, supported=True,
                      group=f"hs4:{code[:4]}")
        items.append(_item(f"PB|{code}|none", "PB", desc, transform="none", parent=code, **common))
        for pname in cfg["hs_in_catalogue_perturbations"]:
            r = rng_for(seed, "PB", code, pname)
            cand = PERTURBATIONS[pname](desc, r)
            if cand:
                items.append(_item(f"PB|{code}|{pname}", "PB", cand, transform=pname, parent=code, **common))

    # PC / PD: unsupported subheadings
    chapters = set(cfg["catalogue_chapters"])
    for code, desc in sorted(hs6.items()):
        if code in cat_codes:
            continue
        near = code[:2] in chapters
        subset = "PC" if near else "PD"
        items.append(_item(f"{subset}|{code}", subset, desc, "ABSTAIN", "",
                           "unsupported_subheading" if near else "out_of_catalogue_chapter",
                           f"HS2022:{code}", "nomenclature_definition", True, False, "none",
                           code, f"hs4:{code[:4]}"))

    # PE: ambiguous tokens (rule over the catalogue)
    tok_to_hs = {}
    for bname, b in bases.items():
        for t in b["tokens"]:
            tok_to_hs.setdefault(t, set()).add(b["hs"])
    base_canon = {b["canonical"] for b in bases.values()}
    for t, hs_set in sorted(tok_to_hs.items()):
        if len(hs_set) >= 2 and t not in base_canon and t.isalpha() and len(t) >= 3:
            items.append(_item(f"PE|{t}", "PE", t.capitalize(), "ABSTAIN", "", "ambiguous_rule",
                               "rule:token shared by base types with HS " + "/".join(sorted(hs_set)),
                               "n/a", "", True, "none", t, f"ambig:{t}"))

    for code, why in sorted(excluded.items()):
        log.append(("hs_code_excluded", f"{code}: {why}"))
    keyed = [dict(it, label_key=it["expected"] + ":" + it["label_hs"]) for it in items]
    return finalize(keyed, "label_key", seed, cfg["dev_fraction"], log)
