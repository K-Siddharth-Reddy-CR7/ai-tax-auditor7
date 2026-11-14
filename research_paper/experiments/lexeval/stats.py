"""Statistics: Wilson intervals, exact McNemar, Holm-Bonferroni, Cohen's kappa, bootstrap."""
import math
import random

from scipy.stats import binomtest


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, centre - half), min(1.0, centre + half))


def mcnemar_exact(a, b):
    """a, b: equal-length boolean lists (paired). Returns (n01, n10, p_two_sided)."""
    n01 = sum(1 for x, y in zip(a, b) if not x and y)
    n10 = sum(1 for x, y in zip(a, b) if x and not y)
    n = n01 + n10
    p = 1.0 if n == 0 else binomtest(n01, n, 0.5, alternative="two-sided").pvalue
    return n01, n10, p


def holm(pvals):
    """Holm-Bonferroni adjusted p-values (same order as input)."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * pvals[i]))
        adj[i] = running
    return adj


def cohen_kappa(x, y):
    n = len(x)
    if n == 0:
        return float("nan")
    cats = sorted(set(x) | set(y))
    po = sum(1 for a, b in zip(x, y) if a == b) / n
    pe = sum((x.count(c) / n) * (y.count(c) / n) for c in cats)
    return float("nan") if pe == 1 else (po - pe) / (1 - pe)


def bootstrap_ci(values, stat, resamples, seed, alpha=0.05):
    rng = random.Random(seed)
    n = len(values)
    est = sorted(stat([values[rng.randrange(n)] for _ in range(n)]) for _ in range(resamples))
    return est[int(alpha / 2 * resamples)], est[int((1 - alpha / 2) * resamples) - 1]
