import math


def parse_amount(value):
    """Parse a money amount from JSON input, rounded to cents.

    Returns None unless the value is a finite number (or numeric string).
    """
    if isinstance(value, bool):
        return None
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(amount):
        return None
    return round(amount, 2)
