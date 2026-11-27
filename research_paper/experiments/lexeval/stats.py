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


def cluster_bootstrap_ci(values, clusters, resamples, seed, alpha=0.05):
    """Percentile CI for a mean of item-level values, resampling whole clusters (items within a cluster
    are correlated, e.g. several perturbations of one product type)."""
    by = {}
    for v, c in zip(values, clusters):
        by.setdefault(c, []).append(float(v))
    keys = sorted(by)
    if not keys:
        return (float("nan"), float("nan"))
    rng = random.Random(seed)
    sums = [(sum(by[k]), len(by[k])) for k in keys]
    est = []
    for _ in range(resamples):
        s = n = 0.0
        for _ in keys:
            a, b = sums[rng.randrange(len(keys))]
            s += a
            n += b
        est.append(s / n)
    est.sort()
    return est[int(alpha / 2 * resamples)], est[int((1 - alpha / 2) * resamples) - 1]


def cluster_paired_test(xa, xb, clusters, resamples, seed):
    """Paired comparison of two systems on the same items with clustered items.

    Statistic: mean(xb - xa) over items. Two-sided sign-flip permutation test at cluster level
    (under H0 the sign of each cluster's summed difference is exchangeable) and a cluster
    bootstrap 95% CI for the difference. Returns (diff, ci_low, ci_high, p_value, n_clusters)."""
    by = {}
    for a, b, c in zip(xa, xb, clusters):
        d = by.setdefault(c, [0.0, 0])
        d[0] += float(b) - float(a)
        d[1] += 1
    keys = sorted(by)
    n_items = sum(by[k][1] for k in keys)
    diffs = [by[k][0] for k in keys]
    obs = sum(diffs) / n_items
    rng = random.Random(seed)
    nonzero = [d for d in diffs if d != 0]
    if not nonzero:
        p = 1.0
    elif len(nonzero) <= 16:  # exact enumeration
        import itertools
        tot = cnt = 0
        for signs in itertools.product((1, -1), repeat=len(nonzero)):
            tot += 1
            cnt += abs(sum(s * d for s, d in zip(signs, nonzero))) >= abs(sum(nonzero)) - 1e-12
        p = cnt / tot
    else:
        cnt = 0
        for _ in range(resamples):
            if abs(sum(d if rng.random() < 0.5 else -d for d in nonzero)) >= abs(sum(nonzero)) - 1e-12:
                cnt += 1
        p = (cnt + 1) / (resamples + 1)
    boot = []
    pairs = [(by[k][0], by[k][1]) for k in keys]
    for _ in range(resamples):
        s = n = 0.0
        for _ in keys:
            a, b = pairs[rng.randrange(len(keys))]
            s += a
            n += b
        boot.append(s / n)
    boot.sort()
    return obs, boot[int(0.025 * resamples)], boot[int(0.975 * resamples) - 1], p, len(keys)
