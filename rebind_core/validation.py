"""Validation helpers for user-provided remap values.

Responsibilities:
- Enforce required fields and value constraints declared by rule metadata.
- Ensure key-valued rules are part of the allowed customizable keys.
- Enforce uniqueness only for rules marked `unique` in `KEY_RULE_SPECS`.
"""

from .models import KEY_RULE_SPECS, ValidationType


def validate_values(values: dict[str, str], available_keys: list[str]) -> tuple[bool, str]:
    for spec in KEY_RULE_SPECS:
        if not values.get(spec.field, ""):
            return False, f"Please fill in '{spec.field}'."

    allowed = set(available_keys)
    for spec in KEY_RULE_SPECS:
        val = values[spec.field]
        if spec.validation == ValidationType.NON_NEGATIVE_FLOAT:
            try:
                n = float(val.strip())
            except ValueError:
                return False, f"'{spec.ui_label}' must be a number in seconds (e.g. 0, 0.2)."
            if n < 0:
                return False, f"'{spec.ui_label}' cannot be negative."
            continue

        if spec.validation == ValidationType.ALLOWED_KEY and val not in allowed:
            return False, (
                f"'{val}' is not in AllowCustomizeInputKey for '{spec.field}'.\n"
                "Pick a key from the 'Usable keyboard keys' list."
            )

    seen: dict[str, str] = {}
    for spec in KEY_RULE_SPECS:
        if not spec.unique:
            continue
        val = values[spec.field]
        if val in seen:
            return False, (
                f"The movement key '{val}' is used for both '{seen[val]}' and '{spec.field}'. "
                "Movement directions must be unique."
            )
        seen[val] = spec.field

    return True, ""
