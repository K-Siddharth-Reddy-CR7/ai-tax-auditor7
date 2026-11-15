import math

from lexeval import scoring
from lexeval.stats import cohen_kappa, holm, mcnemar_exact, wilson


def test_wilson_known_values():
    lo, hi = wilson(8, 10)
    assert math.isclose(lo, 0.4902, abs_tol=1e-4) and math.isclose(hi, 0.9433, abs_tol=1e-4)
    assert wilson(0, 10)[0] == 0.0


def test_mcnemar_exact():
    a = [True] * 10 + [False] * 10
    b = [True] * 10 + [True] * 10   # 10 discordant pairs, all one direction
    n01, n10, p = mcnemar_exact(a, b)
    assert (n01, n10) == (10, 0) and math.isclose(p, 2 * 0.5 ** 10)
    assert mcnemar_exact(a, a)[2] == 1.0


def test_holm():
    adj = holm([0.01, 0.04, 0.03])
    assert [round(x, 4) for x in adj] == [0.03, 0.06, 0.06]


def test_kappa():
    assert cohen_kappa(list("aabb"), list("aabb")) == 1.0
    assert math.isclose(cohen_kappa(list("aabb"), list("abab")), 0.0)


def _o(**kw):
    base = dict(status="OK", prod_hs=None, country_iso=None, landing_cost=None, duty_rate=None,
                gst_rate=None, default_rates=False)
    base.update(kw)
    return base


def test_product_outcomes():
    ans = {"expected": "ANSWER", "label_hs": "847130"}
    abst = {"expected": "ABSTAIN", "label_hs": ""}
    assert scoring.product_outcome(ans, _o(prod_hs="847130")) == scoring.CORRECT
    assert scoring.product_outcome(ans, _o(prod_hs="847160")) == scoring.SILENT
    assert scoring.product_outcome(ans, _o()) == scoring.OVER
    assert scoring.product_outcome(abst, _o()) == scoring.SAFE
    assert scoring.product_outcome(abst, _o(prod_hs="847130")) == scoring.SILENT
    assert scoring.product_outcome(ans, _o(status="ERROR")) == scoring.FAIL


def test_identification_separate_from_tax_availability():
    unsupported = {"gold_iso": "NE", "gold_tax_action": "REFUSE"}
    # correct identification of a country without tax data is CORRECT for identification...
    assert scoring.identification_outcome(unsupported, _o(country_iso="NE")) == scoring.CORRECT
    # ...and computing with default rates is a silent error for the tax-behaviour task
    out = _o(country_iso=None, landing_cost=100.0, duty_rate=5.0, gst_rate=10.0, default_rates=True)
    assert scoring.tax_behaviour_outcome(unsupported, out, None) == (scoring.SILENT, "default_rates")
    assert scoring.tax_behaviour_outcome(unsupported, _o(country_iso="NE"), None) == (scoring.SAFE, "refused")


def test_masked_correct_rates_wrong_country():
    item = {"gold_iso": "NL", "gold_tax_action": "COMPUTE"}
    out = _o(country_iso="BE", landing_cost=1.0, duty_rate=8.0, gst_rate=21.0)
    assert scoring.tax_behaviour_outcome(item, out, (8.0, 21.0)) == (scoring.CORRECT, "correct_rates_wrong_or_no_country")


def test_gold_vs_system_behaviour_country():
    # gold identity NZ; a system lacking the alias that abstains is safe but not correct
    item = {"gold_iso": "NZ", "gold_tax_action": "COMPUTE"}
    assert scoring.identification_outcome(item, _o(country_iso=None)) == scoring.OVER
    assert scoring.is_safe(scoring.OVER) and not scoring.is_safe(scoring.SILENT)
    assert scoring.identification_outcome(item, _o(country_iso="NZ")) == scoring.CORRECT
    assert scoring.identification_outcome(item, _o(country_iso="AU")) == scoring.SILENT


def test_cluster_bootstrap_widens_with_correlation():
    from lexeval.stats import cluster_bootstrap_ci
    vals = [1] * 50 + [0] * 50
    indep = cluster_bootstrap_ci(vals, list(range(100)), 2000, 1)
    clustered = cluster_bootstrap_ci(vals, [i // 25 for i in range(100)], 2000, 1)  # 4 clusters of 25
    assert (clustered[1] - clustered[0]) > (indep[1] - indep[0])


def test_cluster_paired_test():
    from lexeval.stats import cluster_paired_test
    a = [False] * 40
    b = [True] * 40
    diff, lo, hi, p, k = cluster_paired_test(a, b, [i // 2 for i in range(40)], 2000, 1)
    assert diff == 1.0 and k == 20 and p < 0.001
    diff, lo, hi, p, k = cluster_paired_test(a, a, list(range(40)), 2000, 1)
    assert diff == 0.0 and p == 1.0
