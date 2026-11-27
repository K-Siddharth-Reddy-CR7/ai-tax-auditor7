"""Phase D step 0: the immutable original product benchmark is available from git history and hash-identical,
and the live benchmark is in exactly one of the two permitted states."""
import hashlib
import subprocess

from _helpers import csv_rows
from _original import (AUTHORISED_P7_EXCLUSIONS, ORIGINAL_COMMIT, ORIGINAL_GIT_BLOB, ORIGINAL_PATH, ORIGINAL_SHA256,
                       REBUILT_SHA256, assert_expected_live_state, expected_rebuilt_bytes, original_product_bytes,
                       original_product_rows)

from lexeval.paths import REPO


def test_original_is_available_from_git_and_hash_identical():
    data = original_product_bytes()
    assert hashlib.sha256(data).hexdigest() == ORIGINAL_SHA256
    blob = subprocess.run(["git", "-C", REPO, "rev-parse", f"{ORIGINAL_COMMIT}:{ORIGINAL_PATH}"],
                          capture_output=True, text=True, check=True).stdout.strip()
    assert blob == ORIGINAL_GIT_BLOB
    assert hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest() == ORIGINAL_GIT_BLOB   # same bytes as the blob


def test_original_has_the_documented_composition():
    rows = original_product_rows()
    assert len(rows) == 809
    assert sum(r["split"] == "dev" for r in rows) == 272 and sum(r["split"] == "test" for r in rows) == 537
    p7 = [r for r in rows if r["subset"] == "P7_outside"]
    assert len(p7) == 116 and AUTHORISED_P7_EXCLUSIONS <= {r["item_id"] for r in p7}


def test_expected_rebuild_removes_exactly_the_four_rows():
    orig = csv_rows(original_product_bytes())
    new = csv_rows(expected_rebuilt_bytes())
    assert len(orig) - len(new) == 4
    assert {r[0] for r in orig[1:]} - {r[0] for r in new[1:]} == AUTHORISED_P7_EXCLUSIONS
    assert [r for r in orig if r[0] not in AUTHORISED_P7_EXCLUSIONS] == new


def test_live_benchmark_is_in_the_expected_state():
    assert assert_expected_live_state() == "post"
    assert hashlib.sha256(expected_rebuilt_bytes()).hexdigest() == REBUILT_SHA256   # pinned after the rebuild


def test_rebuilt_composition():
    rows = csv_rows(expected_rebuilt_bytes())[1:]
    split = rows[0].__len__() - 1   # last column is split
    assert len(rows) == 805
    assert sum(r[split] == "dev" for r in rows) == 270 and sum(r[split] == "test" for r in rows) == 535
    assert sum(r[1] == "P7_outside" for r in rows) == 112
