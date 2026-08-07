#!/usr/bin/env python3
"""Crimson Desert key rebinding tool.

Compatibility facade that preserves the original public API while delegating
implementation to focused modules.
"""

from rebind_core import (
    extract_available_keys_from_file,
    generate_rebind_outputs,
    get_customizable_key_rows,
    get_customizable_keys,
    normalize_user_key,
    patch_allow_customize,
)
from rebind_core.models import (
    ALLOW_CUSTOMIZE_DEFAULTS,
    DEFAULTS,
    KEY_RULE_SPECS,
)
from rebind_ui import run_gui


__all__ = [
    "ALLOW_CUSTOMIZE_DEFAULTS",
    "DEFAULTS",
    "KEY_RULE_SPECS",
    "extract_available_keys_from_file",
    "generate_rebind_outputs",
    "get_customizable_key_rows",
    "get_customizable_keys",
    "main",
    "normalize_user_key",
    "patch_allow_customize",
    "run_gui",
    "_run_gui",
]


def _run_gui() -> None:
    """Backward-compatible alias to launch the tkinter UI."""
    run_gui()


def main() -> None:
    """Program entry point."""
    _run_gui()


if __name__ == "__main__":
    main()
