"""Deterministic group-level dev/test assignment (no group straddles splits)."""
import hashlib


def split_of(group, seed, dev_fraction):
    h = hashlib.sha256(f"{seed}|{group}".encode()).hexdigest()
    u = int(h[:12], 16) / float(16 ** 12)
    return "dev" if u < dev_fraction else "test"
