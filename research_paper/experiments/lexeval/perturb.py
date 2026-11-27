"""Seeded, label-preserving surface perturbations."""
import random
import string

from lexitax_v2.normalize import canonical


def rng_for(seed, *keys):
    return random.Random(f"{seed}|" + "|".join(map(str, keys)))


def case(text, rng):
    style = rng.choice(["upper", "lower", "swap"])
    return {"upper": text.upper(), "lower": text.lower(), "swap": text.swapcase()}[style]


def ws_punct(text, rng):
    toks = text.split()
    sep = rng.choice(["  ", " - ", "_", ", "])
    return ("  " if rng.random() < 0.5 else "") + sep.join(toks) + rng.choice([".", " ", ";"])


def typo(text, rng, min_len=4):
    """Apply exactly one OSA edit (insert/delete/substitute/transpose) to one eligible token."""
    toks = text.split(" ")
    eligible = [i for i, t in enumerate(toks) if len(t) >= min_len and t.isalpha()]
    if not eligible:
        return None
    i = rng.choice(eligible)
    t = toks[i]
    op = rng.choice(["insert", "delete", "substitute", "transpose"])
    p = rng.randrange(1, len(t) - 1)  # keep first and last characters
    letters = string.ascii_lowercase
    if op == "insert":
        t2 = t[:p] + rng.choice(letters) + t[p:]
    elif op == "delete":
        t2 = t[:p] + t[p + 1:]
    elif op == "substitute":
        t2 = t[:p] + rng.choice([c for c in letters if c != t[p].lower()]) + t[p + 1:]
    else:
        t2 = t[:p] + t[p + 1] + t[p] + t[p + 2:]
    if canonical(t2) == canonical(t):
        return None
    toks[i] = t2
    return " ".join(toks)


def plural(text, rng):
    toks = text.split()
    last = toks[-1]
    if last.lower().endswith("s"):
        return None
    toks[-1] = last[:-1] + "ies" if last.lower().endswith("y") and last[-2:-1].lower() not in "aeiou" else last + "s"
    return " ".join(toks)


def reorder(text, rng):
    toks = text.split()
    if len(toks) < 2:
        return None
    return " ".join(reversed(toks))


PERTURBATIONS = {"case": case, "ws_punct": ws_punct, "typo": typo, "plural": plural, "reorder": reorder}
