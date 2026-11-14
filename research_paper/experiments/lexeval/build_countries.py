"""Jurisdiction resolution benchmark (JRB).

Identification label (expected_iso) and tax-data availability are separate fields.
  CA  table names + surface noise                       (source: taxes.json; ISO via fixed mapping)
  CB  ISO 3166-1 forms of all 249 countries            (alpha-2/alpha-3/name/official/common)
  CC  one-edit typos of ISO/table names                (label by construction)
  CD  CLDR v47 localised names (de/fr/es/it/nl/pt)     (held out from S1's alias table)
  CE  ambiguous tokens shared by >=2 ISO names          (expected: no identification)
  CF  CLDR non-country region names                     (expected: no identification)
"""
from lexitax_v2.jurisdiction import ALIAS_FIELDS, alias_index
from lexitax_v2.normalize import normalize_text, singular
from lexitax_v2.reference import ISO_TO_TABLE, TABLE_TO_ISO

from .build_common import finalize
from .perturb import PERTURBATIONS, rng_for
from .refdata import cldr_names, cldr_regions, iso_countries

FIELDS = ["item_id", "subset", "text", "expected_iso", "label_kind", "tax_data_available",
          "expected_behaviour", "label_source", "transform", "group", "split"]


def _item(iid, subset, text, iso, kind, source, transform, group):
    avail = bool(iso) and iso in ISO_TO_TABLE
    return dict(item_id=iid, subset=subset, text=text, expected_iso=iso or "", label_kind=kind,
                tax_data_available=avail, expected_behaviour="COMPUTE" if avail else "REFUSE",
                label_source=source, transform=transform, group=group)


def build(cfg, log):
    seed = cfg["seed"]
    idx = alias_index()
    items = []
    for name, iso in sorted(TABLE_TO_ISO.items()):
        items.append(_item(f"CA|{iso}|table", "CA", name, iso, "country", "taxes.json+ISO", "none", iso))
        for p in ("case", "ws_punct"):
            items.append(_item(f"CA|{iso}|{p}", "CA", PERTURBATIONS[p](name, rng_for(seed, "CA", iso, p)),
                               iso, "country", "taxes.json+ISO", p, iso))
    for c in iso_countries():
        for f in ALIAS_FIELDS:
            v = getattr(c, f, None)
            if v:
                items.append(_item(f"CB|{c.alpha_2}|{f}", "CB", v, c.alpha_2, "country",
                                   f"ISO3166-1(pycountry):{f}", "none", c.alpha_2))
        base = ISO_TO_TABLE.get(c.alpha_2, c.name)
        r = rng_for(seed, "CC", c.alpha_2)
        for _ in range(20):
            t = PERTURBATIONS["typo"](base, r, min_len=4)
            if t and normalize_text(t) not in idx:  # pre-declared: typo must not equal any alias
                items.append(_item(f"CC|{c.alpha_2}|typo", "CC", t, c.alpha_2, "country",
                                   "rule:one-edit typo of " + base, "typo", c.alpha_2))
                break
        else:
            log.append(("typo_not_generated", c.alpha_2))
    cldr = cldr_names(cfg["cldr_locales"])
    norm_to_isos = {}
    for iso, names in cldr.items():
        for loc, name in names:
            norm_to_isos.setdefault(normalize_text(name), set()).add(iso)
    for iso, names in sorted(cldr.items()):
        for loc, name in names:
            n = normalize_text(name)
            if not n or n in idx:
                continue  # empty or not held out (already an ISO/table alias)
            if len(norm_to_isos[n]) > 1:
                log.append(("cldr_cross_country_collision_excluded", f"{loc}:{name}"))
                continue
            items.append(_item(f"CD|{iso}|{loc}", "CD", name, iso, "country", f"CLDR47:{loc}", "localised", iso))
    tok_countries = {}
    for c in iso_countries():
        for f in ("name", "common_name"):
            v = getattr(c, f, None)
            for t in set(normalize_text(v).split()) if v else ():
                tok_countries.setdefault(t, set()).add(c.alpha_2)
    for t, isos in sorted(tok_countries.items()):
        if len(isos) >= 2 and len(t) >= 4 and t.isalpha() and t not in idx:
            items.append(_item(f"CE|{t}", "CE", t.capitalize(), "", "ambiguous",
                               "rule:token in names of " + ",".join(sorted(isos)), "none", f"ambig:{singular(t)}"))
    for code, name in sorted(cldr_regions().items()):
        if normalize_text(name) in idx:
            continue
        items.append(_item(f"CF|{code}", "CF", name, "", "non_country", f"CLDR47:en region {code}", "none", f"region:{code}"))
    return finalize([dict(it, label_key=it["expected_iso"] + ":" + it["label_kind"]) for it in items],
                    "label_key", seed, cfg["dev_fraction"], log)
