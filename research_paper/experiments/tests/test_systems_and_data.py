import os

import pytest

from lexeval.build_common import read_csv
from lexeval.paths import GEN
from lexeval.systems import run_composite, run_S0, run_S1

KEYS = ("status", "prod_hs", "prod_fabricated", "country_iso", "default_rates", "duty_rate", "gst_rate",
        "landing_cost", "policy_id", "fx_substituted")

pytestmark = pytest.mark.skipif(not os.path.exists(os.path.join(GEN, "product_benchmark.csv")),
                                reason="benchmarks not built")


def _dev_sample(name, n=250):
    rows = [r for r in read_csv(os.path.join(GEN, name)) if r["split"] == "dev"]
    return rows[:: max(1, len(rows) // n)]


def test_ladder_L0_equals_original_S0_on_dev_inputs():
    for r in _dev_sample("product_benchmark.csv"):
        a = (r["text"], "India", 100.0, 2, 10.0)
        s0, l0 = run_S0(*a), run_composite(*a)
        assert {k: s0[k] for k in KEYS} == {k: l0[k] for k in KEYS}, r["item_id"]
    for r in _dev_sample("country_benchmark.csv"):
        a = ("Laptop", r["text"], 100.0, 2, 10.0)
        s0, l0 = run_S0(*a), run_composite(*a)
        assert {k: s0[k] for k in KEYS} == {k: l0[k] for k in KEYS}, r["item_id"]


def test_ladder_L5_equals_S1_on_dev_inputs():
    k1 = ("status", "prod_hs", "country_iso", "duty_rate", "gst_rate", "landing_cost", "policy_id")
    for name, mk in (("product_benchmark.csv", lambda t: (t, "India", 100.0, 2, 10.0)),
                     ("country_benchmark.csv", lambda t: ("Laptop", t, 100.0, 2, 10.0))):
        for r in _dev_sample(name):
            a = mk(r["text"])
            s1 = run_S1(*a)
            l5 = run_composite(*a, validate=True, product_mode="s1", country_mode="iso_refuse")
            assert {k: s1[k] for k in k1} == {k: l5[k] for k in k1}, r["item_id"]


def test_build_is_deterministic(tmp_path):
    """A temporary-directory build with the authoritative review treatments reproduces the committed files.

    The build is a function of config, reference data and pilot/authorised_review_treatments_v1.csv only.
    The committed product draft was built at a0129b8, before any review decision existed, so until the
    Phase D production rebuild it must equal the build output with exactly the authorised exclusion rows
    added back (every byte of every other row identical). After the rebuild it must be byte-identical.
    A partially applied state is never accepted. Country file: always byte-identical."""
    import hashlib

    from _helpers import without_items

    from lexeval import build_countries, build_products
    from lexeval.build_common import write_csv
    from lexeval.paths import PILOT, config
    from lexeval.pilot import load_treatments
    records = sorted(f for f in os.listdir(PILOT) if os.path.isfile(os.path.join(PILOT, f)))
    sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()  # noqa: E731
    before = {f: sha(os.path.join(PILOT, f)) for f in records}
    cfg = config()
    write_csv(tmp_path / "p.csv", build_products.build(cfg, []), build_products.FIELDS)
    write_csv(tmp_path / "c.csv", build_countries.build(cfg, []), build_countries.FIELDS)
    assert before == {f: sha(os.path.join(PILOT, f)) for f in records}, "build modified pilot/ files"
    committed = open(os.path.join(GEN, "product_benchmark.csv"), "rb").read()
    excl = {i for i, t in load_treatments().items() if t["authorised_treatment"] == "exclude"}
    present = excl & {r["item_id"] for r in read_csv(os.path.join(GEN, "product_benchmark.csv"))}
    assert present in (set(), excl), f"committed draft applies the exclusions only partially: {present}"
    expected = committed if not present else without_items(committed, excl)
    assert (tmp_path / "p.csv").read_bytes() == expected
    assert (tmp_path / "c.csv").read_bytes() == open(os.path.join(GEN, "country_benchmark.csv"), "rb").read()


def test_every_item_has_provenance_and_split():
    for name in ("product_benchmark.csv", "country_benchmark.csv"):
        for r in read_csv(os.path.join(GEN, name)):
            assert r["label_source"] and r["group"] and r["split"] in ("dev", "test")
