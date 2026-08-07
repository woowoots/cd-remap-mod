import html
import re

from .models import ALLOW_CUSTOMIZE_DEFAULTS, KEY_RULE_SPECS
from .patterns import ALLOW_CUSTOMIZE_SECTION_RE, KEYBOARD_MOUSE_KEY_RE

# Explicit rule markers identify the primary customizable keyboard row.
_PRIMARY_ROW_MARKERS = tuple(s.source_key for s in KEY_RULE_SPECS if s.primary_customize_marker)


def normalize_user_key(value: str) -> str:
    token = value.strip()
    if len(token) == 1:
        return token.lower()
    return token


def _normalize_key_token(token: str) -> str:
    return normalize_user_key(html.unescape(token))


def _extract_customizable_rows(text: str) -> tuple[list[list[str]], set[str]]:
    section_match = ALLOW_CUSTOMIZE_SECTION_RE.search(text)
    if not section_match:
        return [], set()

    body = section_match.group(2)
    rows: list[list[str]] = []
    seen: set[str] = set()

    for key_match in KEYBOARD_MOUSE_KEY_RE.finditer(body):
        raw_value = key_match.group(2)
        row_tokens: list[str] = []
        for tok in raw_value.split():
            normalized = _normalize_key_token(tok)
            if normalized:
                row_tokens.append(normalized)
                seen.add(normalized)
        if row_tokens:
            rows.append(row_tokens)

    return rows, seen


def get_customizable_keys(text: str) -> list[str]:
    rows, seen = _extract_customizable_rows(text)
    if not rows:
        return sorted(set(ALLOW_CUSTOMIZE_DEFAULTS))

    ordered: list[str] = []
    ordered_seen: set[str] = set()

    for row_tokens in rows:
        for tok in row_tokens:
            if tok not in ordered_seen:
                ordered_seen.add(tok)
                ordered.append(tok)

    for tok in ALLOW_CUSTOMIZE_DEFAULTS:
        normalized = _normalize_key_token(tok)
        if normalized not in ordered_seen:
            ordered_seen.add(normalized)
            ordered.append(normalized)

    return ordered


def get_customizable_key_rows(text: str) -> list[str]:
    rows, seen = _extract_customizable_rows(text)
    if not rows:
        return [" ".join(ALLOW_CUSTOMIZE_DEFAULTS)]

    formatted_rows = [" ".join(row_tokens) for row_tokens in rows]

    missing_defaults = [tok for tok in ALLOW_CUSTOMIZE_DEFAULTS if tok not in seen]
    if missing_defaults:
        formatted_rows.append(" ".join(missing_defaults))

    return formatted_rows


def _is_primary_customize_key_entry(tokens: list[str]) -> bool:
    return (
        all(m in tokens for m in _PRIMARY_ROW_MARKERS)
        and "[" in tokens
        and "]" in tokens
    )


def extract_available_keys_from_file(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8") as opened_file:
        return get_customizable_keys(opened_file.read())


def _prepend_unique_defaults(value: str) -> str:
    merged = list(ALLOW_CUSTOMIZE_DEFAULTS)
    for tok in value.split():
        if tok not in merged:
            merged.append(tok)
    return " ".join(merged)


def patch_allow_customize(text: str) -> str:
    def replace_section(section_match: re.Match[str]) -> str:
        start_tag, body, end_tag = section_match.group(1), section_match.group(2), section_match.group(3)

        rebuilt: list[str] = []
        last_end = 0
        replaced = False

        for key_match in KEYBOARD_MOUSE_KEY_RE.finditer(body):
            rebuilt.append(body[last_end:key_match.start()])
            prefix, key_value, suffix = key_match.group(1), key_match.group(2), key_match.group(3)
            tokens = key_value.split()

            if not replaced and _is_primary_customize_key_entry(tokens):
                key_value = _prepend_unique_defaults(key_value)
                replaced = True

            rebuilt.append(f"{prefix}{key_value}{suffix}")
            last_end = key_match.end()

        rebuilt.append(body[last_end:])
        return f"{start_tag}{''.join(rebuilt)}{end_tag}"

    patched_text, _ = ALLOW_CUSTOMIZE_SECTION_RE.subn(replace_section, text, count=1)
    return patched_text
