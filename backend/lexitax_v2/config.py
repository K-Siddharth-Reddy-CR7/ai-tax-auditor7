"""Configuration for the S1 pipeline.

Defaults for the product-matching parameters are *provisional*. The values
used in the reported experiments are selected on the development split only,
using the pre-declared rule in research_paper/experimental_evaluation_plan.md,
and are recorded in research_paper/experiments/results/.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class S1Config:
    # Product resolution (tier T2/T3): minimum share of input tokens that must be
    # explained by the matched base-type name ("evidence coverage", not a confidence).
    product_min_coverage: float = 0.5
    # Tier T3 typo tolerance: max Damerau-Levenshtein (OSA) edits per token and
    # the minimum catalogue-token length to which typo tolerance applies.
    product_typo_max_edits: int = 1
    product_typo_min_len: int = 5
    # Jurisdiction resolution: typo tolerance is OFF by default (ablation only).
    country_typo_max_edits: int = 0
    country_typo_min_len: int = 5
    # Do not compute duties/taxes for an unresolved product (HS-dependent in reality).
    require_product_for_costs: bool = True
