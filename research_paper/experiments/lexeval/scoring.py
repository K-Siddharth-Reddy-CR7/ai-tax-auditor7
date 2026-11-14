"""Per-item outcome taxonomy (definitions fixed before evaluation)."""

CORRECT, SILENT, SAFE, OVER, FAIL = "CORRECT", "SILENT_ERROR", "SAFE_ABSTENTION", "OVER_ABSTENTION", "EXPLICIT_FAILURE"
OUTCOMES = [CORRECT, SAFE, OVER, FAIL, SILENT]


def product_outcome(item, out):
    """Product task. Answer = an HS-6 code shown without a 'not resolved' marker."""
    if out["status"] in ("ERROR", "INVALID"):
        return FAIL
    answered = out["prod_hs"] is not None
    if item["expected"] == "ANSWER":
        if not answered:
            return OVER
        return CORRECT if out["prod_hs"] == item["label_hs"] else SILENT
    return SILENT if answered else SAFE


def identification_outcome(item, out):
    """Country identification task (independent of tax-data availability)."""
    if out["status"] in ("ERROR", "INVALID"):
        return FAIL
    got, exp = out["country_iso"], item["expected_iso"] or None
    if exp:
        if got is None:
            return OVER
        return CORRECT if got == exp else SILENT
    return SILENT if got else SAFE


def tax_behaviour_outcome(item, out, true_rates):
    """Tax-data availability task: compute with the true jurisdiction's rates, or refuse.

    true_rates: (duty, gst) of the labelled jurisdiction if it is in the tax table, else None.
    Returns (outcome, subtype)."""
    if out["status"] in ("ERROR", "INVALID"):
        return FAIL, "error"
    computed = out["landing_cost"] is not None
    if item["expected_behaviour"] == "COMPUTE":
        if not computed:
            return OVER, "refused"
        if (out["duty_rate"], out["gst_rate"]) == true_rates:
            masked = out["country_iso"] != item["expected_iso"]
            return CORRECT, "correct_rates_wrong_or_no_country" if masked else "correct"
        return SILENT, "default_rates" if out["default_rates"] else "other_country_rates"
    if not computed:
        return SAFE, "refused"
    return SILENT, "default_rates" if out["default_rates"] else "other_country_rates"


def summarise(outcomes):
    n = len(outcomes)
    c = {k: sum(1 for o in outcomes if o == k) for k in OUTCOMES}
    answered = c[CORRECT] + c[SILENT]
    return dict(n=n, **c, answered=answered,
                coverage=answered / n if n else float("nan"),
                decision_accuracy=(c[CORRECT] + c[SAFE]) / n if n else float("nan"),
                silent_error_rate=c[SILENT] / n if n else float("nan"),
                selective_accuracy=c[CORRECT] / answered if answered else float("nan"))
