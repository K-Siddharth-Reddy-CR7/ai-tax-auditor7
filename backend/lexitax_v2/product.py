"""Product resolution to a catalogue base type (and its HS-6 code) with abstention.

No numerical confidence score is produced. Resolution is decided by explicit,
measurable evidence:
  T1  exact normalised match to a catalogue product name or base-type name;
  T2  whole-token containment of a base-type name in the input, with
      (a) maximality (drop candidates subsumed by a longer matched name),
      (b) uniqueness of the implied HS-6 code, and
      (c) evidence coverage |base tokens| / |input tokens| >= threshold;
  T3  as T2 but tokens may differ by a bounded number of typo edits.
Otherwise the resolver abstains and states why.
"""
from .normalize import canonical, osa_distance, tokens
from .reference import base_type, catalogue


def _containment(inp_tokens, bases, typo_max_edits=0, typo_min_len=5):
    inp = set(inp_tokens)
    matches = []
    for name, b in bases.items():
        matched = True
        for bt in b["tokens"]:
            if bt in inp:
                continue
            if typo_max_edits and len(bt) >= typo_min_len and any(
                    osa_distance(bt, it, typo_max_edits) <= typo_max_edits for it in inp):
                continue
            matched = False
            break
        if matched:
            matches.append(name)
    # maximality: drop a candidate whose token set is a strict subset of another candidate's
    maximal = [m for m in matches
               if not any(bases[m]["tokens"] < bases[o]["tokens"] for o in matches if o != m)]
    return sorted(maximal)


def resolve_product(text, min_coverage=0.5, typo_max_edits=1, typo_min_len=5) -> dict:
    by_name, bases = catalogue()
    canon = canonical(text)
    toks = tokens(text)
    out = {"input": text, "status": None, "tier": None, "reason": None, "base_type": None,
           "product": None, "hs_code": None, "category": None, "unit": None,
           "candidates": [], "coverage": None}

    def _resolve(bname, tier, product=None, coverage=None):
        b = bases[bname]
        p = product or b["example_product"]
        out.update(status="RESOLVED", tier=tier, base_type=bname, product=p["Product"],
                   hs_code=b["hs"], category=b["category"], unit=b["unit"],
                   coverage=coverage, candidates=[bname])
        return out

    if not canon:
        out.update(status="ABSTAINED", reason="empty_description")
        return out
    # T1: exact catalogue product name, then exact base-type name
    if canon in by_name:
        p = by_name[canon]
        return _resolve(base_type(p["Product"]), "T1_exact_product", product=p, coverage=1.0)
    for bname, b in bases.items():
        if b["canonical"] == canon:
            return _resolve(bname, "T1_exact_base", coverage=1.0)
    # T2 / T3: token containment
    for tier, k in (("T2_token_containment", 0), ("T3_typo_containment", typo_max_edits)):
        if tier.startswith("T3") and k <= 0:
            break
        cands = _containment(toks, bases, k, typo_min_len)
        if not cands:
            continue
        out["candidates"] = cands
        hs_set = {bases[c]["hs"] for c in cands}
        if len(hs_set) > 1:
            out.update(status="ABSTAINED", tier=tier, reason="ambiguous_multiple_hs")
            return out
        best = max(cands, key=lambda c: (len(bases[c]["tokens"]), c))
        explained = set().union(*(bases[c]["tokens"] for c in cands))
        cov = min(len(explained), len(toks)) / max(len(toks), 1)
        if cov < min_coverage:
            out.update(status="ABSTAINED", tier=tier, reason="insufficient_evidence_coverage",
                       coverage=round(cov, 4))
            return out
        res = _resolve(best, tier, coverage=round(cov, 4))
        res["candidates"] = cands
        return res
    out.update(status="ABSTAINED", reason="no_catalogue_evidence")
    return out
