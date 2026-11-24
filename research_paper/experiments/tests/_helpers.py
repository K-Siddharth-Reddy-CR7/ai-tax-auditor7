"""Shared test helpers (not a test module)."""
import csv
import io


def csv_rows(data):
    """Parse CSV bytes into a list of raw row lists (header first)."""
    return list(csv.reader(io.StringIO(data.decode("utf-8"), newline="")))


def rewrite(rows):
    """Serialise raw rows exactly as csv.DictWriter/csv.writer do (default dialect, CRLF)."""
    buf = io.StringIO(newline="")
    csv.writer(buf).writerows(rows)
    return buf.getvalue().encode("utf-8")


def without_items(data, item_ids):
    """CSV bytes with the rows whose first column is in `item_ids` removed and every other byte unchanged.
    Raises if an id is not present exactly once, or if re-serialisation would not round-trip the input."""
    rows = csv_rows(data)
    assert rewrite(rows) == data, "CSV does not round-trip; byte comparison would be unreliable"
    for iid in item_ids:
        assert sum(r[0] == iid for r in rows[1:]) == 1, f"{iid} not present exactly once"
    return rewrite([rows[0]] + [r for r in rows[1:] if r[0] not in set(item_ids)])
