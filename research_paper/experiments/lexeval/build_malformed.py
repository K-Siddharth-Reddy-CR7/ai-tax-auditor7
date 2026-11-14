"""Malformed-input set M (expected: explicit rejection)."""

FIELDS = ["item_id", "product_name", "destination", "price", "quantity", "shipping", "defect"]

GOOD = {"product_name": "Laptop", "destination": "India", "price": 800, "quantity": 2, "shipping": 100}
CASES = [
    ("blank_product", {"product_name": "   "}), ("empty_product", {"product_name": ""}),
    ("blank_destination", {"destination": "  "}), ("empty_destination", {"destination": ""}),
    ("negative_price", {"price": -100}), ("zero_price", {"price": 0}),
    ("nan_price", {"price": "nan"}), ("inf_price", {"price": "inf"}),
    ("text_price", {"price": "eight hundred"}), ("missing_price", {"price": None}),
    ("zero_quantity", {"quantity": 0}), ("negative_quantity", {"quantity": -3}),
    ("fractional_quantity", {"quantity": 2.5}), ("fractional_quantity_text", {"quantity": "2.7"}),
    ("text_quantity", {"quantity": "two"}), ("negative_shipping", {"shipping": -10}),
    ("nan_shipping", {"shipping": "nan"}), ("text_shipping", {"shipping": "free"}),
]


def build():
    rows = []
    for name, override in CASES:
        r = dict(GOOD)
        r.update(override)
        rows.append({"item_id": f"M|{name}", "defect": name, **r})
    return rows
