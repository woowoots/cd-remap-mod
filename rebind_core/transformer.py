import re
from dataclasses import dataclass

from .models import (
    RebindConfig,
    KEY_RULE_SPECS,
    RuleSelector,
    SourceFile,
)
from .patterns import (
    INPUT_BLOCK_RE,
    NAME_ATTR_RE,
)


@dataclass(frozen=True)
class _CompiledRule:
    field: str
    source_key: str
    markers: tuple[str, ...]
    selector: RuleSelector


TAG_RE = re.compile(r"<([A-Za-z_][A-Za-z0-9_]*)\b[^>]*?/?>")


def _attr_value(tag: str, attr: str) -> str | None:
    match = re.search(rf'\b{re.escape(attr)}="([^"]*)"', tag)
    return match.group(1) if match else None


def _set_attr_value(tag: str, attr: str, value: str) -> str:
    attr_re = re.compile(rf'\b{re.escape(attr)}="[^"]*"')
    replacement = f'{attr}="{value}"'

    if attr_re.search(tag):
        return attr_re.sub(replacement, tag, count=1)
    return tag


def _selector_matches_tag(selector: RuleSelector, tag_name: str, tag: str) -> bool:

    if selector.tag and selector.tag != tag_name:
        return False
    if selector.names:
        name_value = _attr_value(tag, "Name")
        if name_value not in selector.names:
            return False
    if selector.attribute and _attr_value(tag, selector.attribute) is None:
        return False
    return True


def _target_for_source(spec, source_file: SourceFile):
    return next((candidate for candidate in spec.targets if candidate.source_file == source_file), None)


def _matches_markers(input_name: str, markers: tuple[str, ...]) -> bool:
    if not markers:
        return True
    return any(marker in input_name for marker in markers)


_RULES_BY_SOURCE: dict[SourceFile, tuple[_CompiledRule, ...]] = {
    source_file: tuple(
        _CompiledRule(
            field=spec.field,
            source_key=spec.source_key,
            markers=target.markers,
            selector=spec.selector,
        )
        for spec in KEY_RULE_SPECS
        for target in [_target_for_source(spec, source_file)]
        if target is not None and not target.ignore
    )
    for source_file in SourceFile
}


def transform_input_block(
    match: re.Match[str],
    config: RebindConfig,
    source_file: SourceFile,
) -> str:
    attrs = match.group(1)
    body = match.group(2)

    name_match = NAME_ATTR_RE.search(attrs)
    input_name = name_match.group(1) if name_match else ""

    applicable_rules = tuple(
        rule
        for rule in _RULES_BY_SOURCE[source_file]
        if _matches_markers(input_name, rule.markers)
    )

    token_rules = [rule for rule in applicable_rules if rule.source_key]
    direct_rules = [rule for rule in applicable_rules if not rule.source_key]

    active_remaps: dict[str, str] = {}
    key_selectors: list[RuleSelector] = []
    for rule in token_rules:
        # Keep first-match precedence from KEY_RULE_SPECS declaration order.
        active_remaps.setdefault(rule.source_key, config.key_values[rule.field])
        key_selectors.append(rule.selector)

    def replace_key_in_tag(tag_match: re.Match[str]) -> str:
        tag_name = tag_match.group(1)
        tag = tag_match.group(0)
        selector = next((s for s in key_selectors if _selector_matches_tag(s, tag_name, tag)), None)
        if selector is None:
            return tag

        raw_value = _attr_value(tag, selector.attribute)
        if raw_value is None:
            return tag

        tokens = raw_value.split()
        new_tokens = [active_remaps.get(tok, tok) for tok in tokens]
        remapped_value = " ".join(new_tokens)
        if remapped_value == raw_value:
            return tag
        return _set_attr_value(tag, selector.attribute, remapped_value)

    new_body = TAG_RE.sub(replace_key_in_tag, body)

    if direct_rules:
        def replace_direct_in_tag(tag_match: re.Match[str]) -> str:
            tag_name = tag_match.group(1)
            current_tag = tag_match.group(0)
            for rule in direct_rules:
                selector = rule.selector
                if not _selector_matches_tag(selector, tag_name, current_tag):
                    continue
                current_tag = _set_attr_value(
                    current_tag,
                    selector.attribute,
                    config.key_values[rule.field],
                )
            return current_tag

        new_body = TAG_RE.sub(replace_direct_in_tag, new_body)

    return f"<Input{attrs}>{new_body}</>"


def process_text(text: str, config: RebindConfig, source_file: SourceFile) -> str:
    return INPUT_BLOCK_RE.sub(
        lambda m: transform_input_block(m, config, source_file),
        text,
    )
