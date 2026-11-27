"""The immutable ORIGINAL (pre-review) product benchmark, read from git history (Phase D step 0).

The original draft was generated at commit a0129b8 (15 Nov 2026), before any review decision existed. Tests that
need "the original rows" read it from git through this module; they never use the live
data/generated/product_benchmark.csv for that purpose. If git or the commit is unavailable, or the bytes differ
from the pinned SHA-256, the tests FAIL (they are never skipped).

The live benchmark may be in exactly one of two states:
  "pre"  - byte-identical to the original (before the Phase D production rebuild);
  "post" - byte-identical to the original with exactly the four authorised P7 rows removed (after the rebuild).
EXPECTED_LIVE_STATE fixes which state the committed repository must be in.
"""
import csv
import hashlib
import io
import subprocess

from _helpers import without_items

from lexeval.paths import REPO

ORIGINAL_COMMIT = "a0129b8df2b0469d9e3a90bc6a4a98eefc3c5edd"
ORIGINAL_PATH = "research_paper/experiments/data/generated/product_benchmark.csv"
ORIGINAL_SHA256 = "4b69c5bb24ed519831490118e4d86ca2dfb38575cde4db5479c4e3feda1b5351"
ORIGINAL_GIT_BLOB = "76a8e81ce6761896b1013b81b709c3ab2a1d81fa"
AUTHORISED_P7_EXCLUSIONS = frozenset({"P7_outside|couch and lamp", "P7_outside|toothbrush",
                                      "P7_outside|video game", "P7_outside|satellite antenna"})
# None = either state accepted (used only before the rebuild, in Phase D step 0). Since the Phase D production
# rebuild (27 Nov 2026) the committed repository must be in the "post" state.
EXPECTED_LIVE_STATE = "post"
REBUILT_SHA256 = "a6a87fc3f7057a74eebd9d5b7809809820b892e4ac3b791fe1f4dc64c5935160"
LIVE_PRODUCT = REPO + "/" + ORIGINAL_PATH

_cache = {}


def _git(*args):
    r = subprocess.run(["git", "-C", REPO, *args], capture_output=True, timeout=60)
    if r.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {r.stderr.decode(errors='replace').strip()} "
                             "(the original benchmark must be available from git history; a shallow clone is not "
                             "sufficient)")
    return r.stdout


def original_product_bytes():
    """The original product benchmark bytes from git, verified against the pinned SHA-256."""
    if "bytes" not in _cache:
        data = _git("show", f"{ORIGINAL_COMMIT}:{ORIGINAL_PATH}")
        sha = hashlib.sha256(data).hexdigest()
        if sha != ORIGINAL_SHA256:
            raise AssertionError(f"original benchmark from {ORIGINAL_COMMIT[:7]} has SHA-256 {sha}, "
                                 f"expected {ORIGINAL_SHA256}")
        _cache["bytes"] = data
    return _cache["bytes"]


def original_product_rows():
    return list(csv.DictReader(io.StringIO(original_product_bytes().decode("utf-8"), newline="")))


def expected_rebuilt_bytes():
    """The original with exactly the four authorised P7 rows removed; every other byte unchanged."""
    return without_items(original_product_bytes(), AUTHORISED_P7_EXCLUSIONS)


def live_product_state():
    """'pre' or 'post' (see module docstring); anything else is an error."""
    live = open(LIVE_PRODUCT, "rb").read()
    if live == original_product_bytes():
        return "pre"
    if live == expected_rebuilt_bytes():
        return "post"
    raise AssertionError("the live product benchmark is neither the original nor the original minus exactly the "
                         "four authorised exclusions")


def assert_expected_live_state():
    state = live_product_state()
    if EXPECTED_LIVE_STATE is not None:
        assert state == EXPECTED_LIVE_STATE, f"live product benchmark is in state {state!r}, expected " \
                                             f"{EXPECTED_LIVE_STATE!r}"
    return state
