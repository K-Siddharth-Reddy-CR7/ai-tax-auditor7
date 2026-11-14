"""Deterministic text normalisation shared by product and jurisdiction resolution."""
import re
import unicodedata

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def normalize_text(text) -> str:
    """NFKD, strip diacritics, casefold, map non-alphanumerics to single spaces."""
    if text is None:
        return ""
    s = unicodedata.normalize("NFKD", str(text))
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.casefold()
    return _NON_ALNUM.sub(" ", s).strip()


def singular(token: str) -> str:
    """Conservative English plural folding (applied identically to inputs and catalogue)."""
    t = token
    if len(t) <= 3 or t.isdigit():
        return t
    if t.endswith("ies"):
        return t[:-3] + "y"
    if t.endswith(("ches", "shes", "xes", "sses")):
        return t[:-2]
    if t.endswith("s") and not t.endswith(("ss", "us", "is")):
        return t[:-1]
    return t


def tokens(text) -> list:
    norm = normalize_text(text)
    return [singular(t) for t in norm.split()] if norm else []


def canonical(text) -> str:
    """Normalised, plural-folded string used for exact matching."""
    return " ".join(tokens(text))


def osa_distance(a: str, b: str, max_dist: int | None = None) -> int:
    """Optimal string alignment (restricted Damerau-Levenshtein) distance."""
    if a == b:
        return 0
    la, lb = len(a), len(b)
    if max_dist is not None and abs(la - lb) > max_dist:
        return max_dist + 1
    prev2 = None
    prev = list(range(lb + 1))
    for i in range(1, la + 1):
        cur = [i] + [0] * lb
        for j in range(1, lb + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
            if (prev2 is not None and i > 1 and j > 1 and a[i - 1] == b[j - 2]
                    and a[i - 2] == b[j - 1]):
                cur[j] = min(cur[j], prev2[j - 2] + 1)
        prev2, prev = prev, cur
    return prev[lb]
