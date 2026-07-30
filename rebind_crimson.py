#!/usr/bin/env python3

import os
import re
import sys
import html
from typing import Any


def _base_dir() -> str:
    if getattr(sys, "frozen", False):
        # PyInstaller one-file: sys.executable is the user's .exe/binary path.
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULTS = {
    "up": "w",
    "down": "s",
    "left": "a",
    "right": "d",
    "menu_left": "q",
    "menu_right": "e",
    "slot1": "q",
    "slot2": "e",
    "slot3": "r",
    "slot4": "f",
    "slot5": "t",
    "slot6": "g",
}

MOVEMENT_FIELDS = ("up", "down", "left", "right")
MENU_SLOT_FIELDS = ("slot1", "slot2", "slot3", "slot4", "slot5", "slot6")

MOVEMENT_RULE_FIELDS = (("w", "up"), ("s", "down"), ("a", "left"), ("d", "right"))
MENU_RULE_FIELDS = (("q", "slot1"), ("e", "slot2"), ("r", "slot3"), ("f", "slot4"), ("t", "slot5"), ("g", "slot6"))

INPUTMAP_MENU_REMAP_NAME_MARKERS = ("Key_MiniGame", "Key_Housing")
ALLOW_CUSTOMIZE_DEFAULTS = ("w", "a", "s", "d")

INPUT_BLOCK_RE = re.compile(r"<Input\b([^>]*)>(.*?)</>", re.DOTALL)
NAME_ATTR_RE = re.compile(r'Name="([^"]*)"')
KEYBOARD_MOUSE_KEY_RE = re.compile(r'(<KeyboardMouse\b[^>]*\bKey=")([^"]*)(")')
KEY_ATTR_RE = re.compile(r'Key="([^"]*)"')

ALLOW_CUSTOMIZE_SECTION_RE = re.compile(
    r'(<AllowCustomizeInputKey>)(.*?)(</AllowCustomizeInputKey>)',
    re.DOTALL,
)



# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------
def normalize_user_key(value: str) -> str:
    token = value.strip()
    if len(token) == 1:
        return token.lower()
    return token


def _normalize_key_token(token: str) -> str:
    return normalize_user_key(html.unescape(token))


def get_customizable_keys(text: str) -> list[str]:
    section_match = ALLOW_CUSTOMIZE_SECTION_RE.search(text)
    if not section_match:
        return sorted(set(ALLOW_CUSTOMIZE_DEFAULTS))

    body = section_match.group(2)
    ordered: list[str] = []
    seen: set[str] = set()

    for key_match in KEYBOARD_MOUSE_KEY_RE.finditer(body):
        raw_value = key_match.group(2)
        for tok in raw_value.split():
            normalized = _normalize_key_token(tok)
            if normalized and normalized not in seen:
                seen.add(normalized)
                ordered.append(normalized)

    for tok in ALLOW_CUSTOMIZE_DEFAULTS:
        normalized = _normalize_key_token(tok)
        if normalized not in seen:
            seen.add(normalized)
            ordered.append(normalized)

    return ordered


def extract_available_keys_from_file(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8") as f:
        return get_customizable_keys(f.read())


def transform_input_block(
    match: re.Match[str],
    rules: dict[str, str],
    menu_rules: dict[str, str],
    special_left: str,
    special_right: str,
    remap_menu_in_selected_blocks: bool,
) -> str:
    attrs = match.group(1)
    body = match.group(2)

    name_match = NAME_ATTR_RE.search(attrs)
    input_name = name_match.group(1) if name_match else ""

    is_special_left = "MenuMoveLeft" in input_name
    is_special_right = "MenuMoveRight" in input_name
    is_selected_menu_block = (
        remap_menu_in_selected_blocks
        and any(marker in input_name for marker in INPUTMAP_MENU_REMAP_NAME_MARKERS)
    )

    def replace_key(key_match: re.Match[str]) -> str:
        raw_value = key_match.group(1)
        tokens = raw_value.split()
        new_tokens = []
        for tok in tokens:
            new_tok = tok
            # Special menu left/right handling
            if is_special_left and tok == "q":
                new_tok = special_left
            elif is_special_right and tok == "e":
                new_tok = special_right
            elif is_selected_menu_block and tok in menu_rules:
                new_tok = menu_rules[tok]
            else:
                new_tok = rules.get(tok, tok)
            new_tokens.append(new_tok)
        return 'Key="' + " ".join(new_tokens) + '"'

    new_body = KEY_ATTR_RE.sub(replace_key, body)
    return f"<Input{attrs}>{new_body}</>"


def process_file(
    path: str,
    movement: dict[str, str],
    menu: dict[str, str],
    special_left: str,
    special_right: str,
    apply_menu: bool,
) -> str:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    rules = dict(movement)
    if apply_menu:
        rules.update(menu)

    text = INPUT_BLOCK_RE.sub(
        lambda m: transform_input_block(
            m,
            rules,
            menu,
            special_left,
            special_right,
            remap_menu_in_selected_blocks=not apply_menu,
        ),
        text
    )
    return text


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

            if not replaced and "q" in tokens and "e" in tokens and "[" in tokens and "]" in tokens:
                key_value = _prepend_unique_defaults(key_value)
                replaced = True

            rebuilt.append(f"{prefix}{key_value}{suffix}")
            last_end = key_match.end()

        rebuilt.append(body[last_end:])
        return f"{start_tag}{''.join(rebuilt)}{end_tag}"

    patched_text, _ = ALLOW_CUSTOMIZE_SECTION_RE.subn(replace_section, text, count=1)
    return patched_text


def generate_rebind_outputs(
    inputmap_path: str,
    inputmap_common_path: str,
    movement: dict[str, str],
    menu: dict[str, str],
    special_left: str,
    special_right: str,
) -> tuple[str, str]:
    im_text = process_file(
        inputmap_path,
        movement,
        menu,
        special_left,
        special_right,
        apply_menu=False,
    )
    im_text = patch_allow_customize(im_text)

    imc_text = process_file(
        inputmap_common_path,
        movement,
        menu,
        special_left,
        special_right,
        apply_menu=True,
    )
    return im_text, imc_text


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------
def _run_gui():
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    class RebindApp(tk.Tk):
  
        def __init__(self):
            super().__init__()
            self.title("Crimson Desert Key Rebind")
            self.geometry("760x760" if os.name == "nt" else "860x780")
            self.minsize(740, 720)
            self.resizable(True, True)
            self.base_dir = _base_dir()

            self.inputmap_path = tk.StringVar()
            self.inputmap_common_path = tk.StringVar()
            self.available_keys: list[str] = []

            self.entries: dict[str, Any] = {}

            self._build_ui()
            self._guess_paths()

        def _build_ui(self) -> None:
            pad = {"padx": 8, "pady": 6}

            # File selection
            file_frame = ttk.LabelFrame(self, text="Vanilla source files", padding=10)
            file_frame.pack(fill="x", padx=10, pady=8)

            ttk.Label(file_frame, text="inputmap.xml").grid(row=0, column=0, sticky="w", **pad)
            ttk.Entry(file_frame, textvariable=self.inputmap_path, width=55).grid(row=0, column=1, **pad)
            ttk.Button(file_frame, text="Browse", command=self._browse_inputmap).grid(row=0, column=2, **pad)

            ttk.Label(file_frame, text="inputmap_common.xml").grid(row=1, column=0, sticky="w", **pad)
            ttk.Entry(file_frame, textvariable=self.inputmap_common_path, width=55).grid(row=1, column=1, **pad)
            ttk.Button(file_frame, text="Browse", command=self._browse_inputmap_common).grid(row=1, column=2, **pad)

            # Available keyboard keys
            key_list_frame = ttk.LabelFrame(self, text="Usable keyboard keys", padding=10)
            key_list_frame.pack(fill="both", expand=True, padx=10, pady=8)

            self.keys_listbox = tk.Listbox(key_list_frame, height=7)
            self.keys_listbox.pack(fill="both", expand=True)

            ttk.Label(
                key_list_frame,
                text="Validation uses this list (+ w a s d).",
                foreground="gray",
            ).pack(anchor="w", pady=(6, 0))

            # Movement keys
            move_frame = ttk.LabelFrame(self, text="Movement keys", padding=10)
            move_frame.pack(fill="x", padx=10, pady=8)

            for col, (label, key) in enumerate([
                ("Up", "up"),
                ("Down", "down"),
                ("Left", "left"),
                ("Right", "right"),
            ]):
                ttk.Label(move_frame, text=label).grid(row=0, column=col, **pad)
                ent = ttk.Entry(move_frame, width=8, justify="center")
                ent.insert(0, DEFAULTS[key])
                ent.grid(row=1, column=col, **pad)
                self.entries[key] = ent

            # Menu navigation
            nav_frame = ttk.LabelFrame(self, text="Menu navigation", padding=10)
            nav_frame.pack(fill="x", padx=10, pady=8)

            ttk.Label(nav_frame, text="Menu Left").grid(row=0, column=0, **pad)
            ent = ttk.Entry(nav_frame, width=8, justify="center")
            ent.insert(0, DEFAULTS["menu_left"])
            ent.grid(row=1, column=0, **pad)
            self.entries["menu_left"] = ent

            ttk.Label(nav_frame, text="Menu Right").grid(row=0, column=1, **pad)
            ent = ttk.Entry(nav_frame, width=8, justify="center")
            ent.insert(0, DEFAULTS["menu_right"])
            ent.grid(row=1, column=1, **pad)
            self.entries["menu_right"] = ent

            # Menu action keys
            menu_frame = ttk.LabelFrame(self, text="Menu action keys", padding=10)
            menu_frame.pack(fill="x", padx=10, pady=8)

            for col, slot in enumerate(MENU_SLOT_FIELDS):
                ttk.Label(menu_frame, text=f"Slot {col + 1}").grid(row=0, column=col, **pad)
                ent = ttk.Entry(menu_frame, width=8, justify="center")
                ent.insert(0, DEFAULTS[slot])
                ent.grid(row=1, column=col, **pad)
                self.entries[slot] = ent

            ttk.Label(
                self,
                text=(
                    "Note: menu navigation (left/right) and menu slot keys can overlap by design. "
                    "Only movement keys must be unique."
                ),
                foreground="gray",
                wraplength=680,
                justify="left",
            ).pack(fill="x", padx=12, pady=(0, 6))

            # Generate button
            ttk.Button(self, text="Generate files", command=self._generate).pack(pady=12)

            # Status label
            self.status = ttk.Label(self, text="Ready", foreground="gray")
            self.status.pack(pady=(0, 10))

        def _guess_paths(self) -> None:
            """Auto-fill source file paths from vanilla_sources_files when present."""
            vanilla = os.path.join(self.base_dir, "vanilla_sources_files")
            im = os.path.join(vanilla, "inputmap.xml")
            imc = os.path.join(vanilla, "inputmap_common.xml")
            if os.path.isfile(im):
                self.inputmap_path.set(im)
            if os.path.isfile(imc):
                self.inputmap_common_path.set(imc)
            self._refresh_available_keys()

        def _browse_inputmap(self) -> None:
            """Pick inputmap.xml through a file chooser."""
            path = filedialog.askopenfilename(filetypes=[("XML files", "*.xml"), ("All files", "*.*")])
            if path:
                self.inputmap_path.set(path)
                self._refresh_available_keys()

        def _browse_inputmap_common(self) -> None:
            """Pick inputmap_common.xml through a file chooser."""
            path = filedialog.askopenfilename(filetypes=[("XML files", "*.xml"), ("All files", "*.*")])
            if path:
                self.inputmap_common_path.set(path)

        def _refresh_available_keys(self) -> None:
            """Rebuild the displayed/validated key list from inputmap.xml."""
            source = self.inputmap_path.get().strip()
            keys: list[str]

            if source and os.path.isfile(source):
                try:
                    keys = extract_available_keys_from_file(source)
                except Exception:
                    keys = sorted(set(ALLOW_CUSTOMIZE_DEFAULTS))
            else:
                keys = sorted(set(ALLOW_CUSTOMIZE_DEFAULTS))

            self.available_keys = keys
            self.keys_listbox.delete(0, "end")
            for key in keys:
                self.keys_listbox.insert("end", key)

        def _get_values(self) -> dict[str, str]:
            """Read and normalize all user-entered key values."""
            return {key: normalize_user_key(ent.get()) for key, ent in self.entries.items()}

        def _validate(self, values: dict[str, str]) -> bool:
            """Validate required values and movement-key uniqueness rules."""
            # All fields must be non-empty key tokens.
            for key, val in values.items():
                if not val:
                    messagebox.showerror("Missing value", f"Please fill in '{key}'.")
                    return False

            if not self.available_keys:
                self._refresh_available_keys()

            allowed = set(self.available_keys)
            for key, val in values.items():
                if val not in allowed:
                    messagebox.showerror(
                        "Unsupported key",
                        f"'{val}' is not in AllowCustomizeInputKey for '{key}'.\n"
                        "Pick a key from the 'Usable keyboard keys' list."
                    )
                    return False

            # Keep movement directions unique; menu/nav keys may overlap by design.
            seen: dict[str, str] = {}
            for key in MOVEMENT_FIELDS:
                val = values[key]
                if val in seen:
                    messagebox.showerror(
                        "Duplicate key",
                        f"The movement key '{val}' is used for both '{seen[val]}' and '{key}'. "
                        "Movement directions must be unique."
                    )
                    return False
                seen[val] = key
            return True

        def _generate(self) -> None:
            """Generate output files from current settings and show result status."""
            values = self._get_values()
            if not self._validate(values):
                return

            im_path = self.inputmap_path.get()
            imc_path = self.inputmap_common_path.get()

            if not os.path.isfile(im_path):
                messagebox.showerror("File not found", f"inputmap.xml not found:\n{im_path}")
                return
            if not os.path.isfile(imc_path):
                messagebox.showerror("File not found", f"inputmap_common.xml not found:\n{imc_path}")
                return

            movement = {source: values[field] for source, field in MOVEMENT_RULE_FIELDS}
            menu = {source: values[field] for source, field in MENU_RULE_FIELDS}

            try:
                im_text, imc_text = generate_rebind_outputs(
                    im_path,
                    imc_path,
                    movement,
                    menu,
                    values["menu_left"],
                    values["menu_right"],
                )

                # Output paths
                out_dir = os.path.join(self.base_dir, "Movement_keys_rebind", "files", "0012", "ui")
                os.makedirs(out_dir, exist_ok=True)

                out_im = os.path.join(out_dir, "inputmap.xml")
                out_imc = os.path.join(out_dir, "inputmap_common.xml")

                with open(out_im, "w", encoding="utf-8") as f:
                    f.write(im_text)
                with open(out_imc, "w", encoding="utf-8") as f:
                    f.write(imc_text)

                self.status.config(
                    text=f"Generated: {out_im} and {out_imc}. Run again to overwrite.",
                    foreground="green"
                )
                messagebox.showinfo(
                    "Files generated",
                    f"Successfully generated:\n\n{out_im}\n{out_imc}\n\n"
                    "Running 'Generate files' again will overwrite these files."
                )
            except Exception as exc:
                messagebox.showerror("Error", f"Failed to generate files:\n{exc}")
                self.status.config(text="Generation failed", foreground="red")

    app = RebindApp()
    app.mainloop()


def main():
    """Program entry point."""
    _run_gui()


if __name__ == "__main__":
    main()
