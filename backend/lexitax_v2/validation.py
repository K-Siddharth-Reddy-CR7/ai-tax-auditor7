"""Input validation for S1 (explicit rejection instead of silent coercion)."""
import math


def _num(value):
    if isinstance(value, bool):
        raise ValueError("boolean is not a number")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str) and value.strip():
        return float(value.strip())
    raise ValueError("missing or non-numeric")


def validate_payload(payload: dict) -> tuple[dict | None, list]:
    """Return (clean_payload, errors). errors is empty iff the payload is valid."""
    errors = []
    clean = {}
    for field in ("product_name", "destination"):
        v = payload.get(field)
        if not isinstance(v, str) or not v.strip():
            errors.append(f"{field}: required non-empty text")
        else:
            clean[field] = v.strip()
    src = payload.get("source_country", payload.get("origin"))
    clean["source_country"] = src.strip() if isinstance(src, str) and src.strip() else None

    try:
        price = _num(payload.get("price"))
        if not math.isfinite(price) or price <= 0:
            errors.append("price: must be a finite number > 0")
        clean["price"] = price
    except (ValueError, TypeError):
        errors.append("price: missing or non-numeric")
    try:
        q = _num(payload.get("quantity", 1))
        if not math.isfinite(q) or q < 1 or not float(q).is_integer():
            errors.append("quantity: must be an integer >= 1")
        else:
            clean["quantity"] = int(q)
    except (ValueError, TypeError):
        errors.append("quantity: missing or non-numeric")
    try:
        s = _num(payload.get("shipping", 0))
        if not math.isfinite(s) or s < 0:
            errors.append("shipping: must be a finite number >= 0")
        clean["shipping"] = s
    except (ValueError, TypeError):
        errors.append("shipping: missing or non-numeric")
    return (None, errors) if errors else (clean, [])
