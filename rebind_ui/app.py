import os
import sys
import tkinter as tk
from typing import Any
from tkinter import filedialog, messagebox, ttk

from rebind_core.engine import generate_rebind_outputs
from rebind_core.models import DEFAULTS, KEY_RULE_SPECS, RuleSpec
from rebind_core.parser import (
    extract_available_keys_from_file,
    get_customizable_key_rows,
    normalize_user_key,
)
from rebind_core.validation import validate_values


XML_FILE_TYPES = [("XML files", "*.xml"), ("All files", "*.*")]
FALLBACK_AVAILABLE_KEYS = sorted({"w", "a", "s", "d"})
FALLBACK_AVAILABLE_ROWS = [" ".join(FALLBACK_AVAILABLE_KEYS)]
OUTPUT_DIR_SEGMENTS = ("Movement_keys_rebind", "files", "0012", "ui")

_SPEC_SECTIONS: dict[str, list[RuleSpec]] = {}
for _spec in KEY_RULE_SPECS:
    _SPEC_SECTIONS.setdefault(_spec.ui_section, []).append(_spec)

_SECTION_NOTES: dict[str, str] = {
    "Menu action keys": (
        "Note: menu navigation (left/right) and menu slot keys can overlap by design. "
        "Only movement keys must be unique."
    ),
}

def _base_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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
        self.available_key_rows: list[str] = []
        self.entries: dict[str, Any] = {}

        self._create_scrollable_container()
        self._build_ui()
        self._guess_paths()

    def _create_scrollable_container(self) -> None:
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.content = ttk.Frame(self.canvas)
        self.content_window = self.canvas.create_window((0, 0), window=self.content, anchor="nw")

        self.content.bind("<Configure>", self._on_content_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.bind_all("<MouseWheel>", self._on_mousewheel)
        self.bind_all("<Button-4>", lambda _event: self.canvas.yview_scroll(-1, "units"))
        self.bind_all("<Button-5>", lambda _event: self.canvas.yview_scroll(1, "units"))

    def _on_content_configure(self, _event: Any) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event: Any) -> None:
        self.canvas.itemconfigure(self.content_window, width=event.width)

    def _on_mousewheel(self, event: Any) -> None:
        target = self.canvas
        if hasattr(self, "keys_tree") and self._widget_is_child_of(event.widget, self.keys_tree):
            target = self.keys_tree

        if event.delta > 0:
            target.yview_scroll(-1, "units")
        elif event.delta < 0:
            target.yview_scroll(1, "units")

    def _widget_is_child_of(self, widget: Any, parent: Any) -> bool:
        current = widget
        while current is not None:
            if current == parent:
                return True
            current = getattr(current, "master", None)
        return False

    def _build_ui(self) -> None:
        pad = {"padx": 8, "pady": 6}

        file_frame = ttk.LabelFrame(self.content, text="Vanilla source files", padding=10)
        file_frame.pack(fill="x", padx=10, pady=8)

        ttk.Label(file_frame, text="inputmap.xml").grid(row=0, column=0, sticky="w", **pad)
        ttk.Entry(file_frame, textvariable=self.inputmap_path, width=55).grid(row=0, column=1, **pad)
        ttk.Button(file_frame, text="Browse", command=self._browse_inputmap).grid(row=0, column=2, **pad)

        ttk.Label(file_frame, text="inputmap_common.xml").grid(row=1, column=0, sticky="w", **pad)
        ttk.Entry(file_frame, textvariable=self.inputmap_common_path, width=55).grid(row=1, column=1, **pad)
        ttk.Button(file_frame, text="Browse", command=self._browse_inputmap_common).grid(row=1, column=2, **pad)

        key_list_frame = ttk.LabelFrame(self.content, text="Usable keyboard keys", padding=10)
        key_list_frame.pack(fill="x", padx=10, pady=8)

        key_tree_frame = ttk.Frame(key_list_frame)
        key_tree_frame.pack(fill="both", expand=True)

        self.keys_tree = ttk.Treeview(
            key_tree_frame,
            columns=("keys",),
            show="",
            height=8,
            selectmode="none",
        )
        self.keys_tree.column("keys", width=740, anchor="w", stretch=True)

        key_tree_scroll = ttk.Scrollbar(key_tree_frame, orient="vertical", command=self.keys_tree.yview)
        self.keys_tree.configure(yscrollcommand=key_tree_scroll.set)

        self.keys_tree.pack(side="left", fill="both", expand=True)
        key_tree_scroll.pack(side="right", fill="y")

        ttk.Label(
            key_list_frame,
            text="Only keys from this list will be accepted as valid bindings.",
            foreground="gray",
        ).pack(anchor="w", pady=(6, 0))

        for section_title, specs in _SPEC_SECTIONS.items():
            frame = ttk.LabelFrame(self.content, text=section_title, padding=10)
            frame.pack(fill="x", padx=10, pady=8)
            self._build_key_section(frame, specs, pad)
            if section_title in _SECTION_NOTES:
                ttk.Label(
                    self.content,
                    text=_SECTION_NOTES[section_title],
                    foreground="gray",
                    wraplength=680,
                    justify="left",
                ).pack(fill="x", padx=12, pady=(0, 6))

        ttk.Button(self.content, text="Generate files", command=self._generate).pack(pady=12)
        self.status = ttk.Label(self.content, text="Ready", foreground="gray")
        self.status.pack(pady=(0, 10))

    def _create_entry(
        self,
        parent: Any,
        key: str,
        row: int,
        column: int,
        width: int,
        justify: str,
        pad: dict[str, int],
        sticky: str | None = None,
    ) -> Any:
        entry = ttk.Entry(parent, width=width, justify=justify)
        entry.insert(0, DEFAULTS[key])
        grid_args = {"row": row, "column": column, **pad}
        if sticky is not None:
            grid_args["sticky"] = sticky
        entry.grid(**grid_args)
        self.entries[key] = entry
        return entry

    def _build_key_section(self, frame: Any, specs: list[RuleSpec], pad: dict) -> None:
        for col, spec in enumerate(specs):
            ttk.Label(frame, text=spec.ui_label).grid(row=0, column=col, **pad)
            self._create_entry(
                frame, spec.field, row=1, column=col,
                width=spec.ui_width, justify="center",
                sticky=spec.ui_entry_sticky or None,
                pad=pad,
            )

    def _default_available_keys(self) -> tuple[list[str], list[str]]:
        return FALLBACK_AVAILABLE_KEYS.copy(), FALLBACK_AVAILABLE_ROWS.copy()

    def _guess_paths(self) -> None:
        vanilla = os.path.join(self.base_dir, "vanilla_sources_files")
        guessed_files = (
            ("inputmap.xml", self.inputmap_path),
            ("inputmap_common.xml", self.inputmap_common_path),
        )
        for filename, target_var in guessed_files:
            candidate = os.path.join(vanilla, filename)
            if os.path.isfile(candidate):
                target_var.set(candidate)
        self._refresh_available_keys()

    def _browse_inputmap(self) -> None:
        path = filedialog.askopenfilename(filetypes=XML_FILE_TYPES)
        if path:
            self.inputmap_path.set(path)
            self._refresh_available_keys()

    def _browse_inputmap_common(self) -> None:
        path = filedialog.askopenfilename(filetypes=XML_FILE_TYPES)
        if path:
            self.inputmap_common_path.set(path)

    def _refresh_available_keys(self) -> None:
        source = self.inputmap_path.get().strip()
        keys: list[str]
        rows: list[str]

        if source and os.path.isfile(source):
            try:
                keys = extract_available_keys_from_file(source)
                with open(source, "r", encoding="utf-8") as opened_file:
                    text = opened_file.read()
                rows = get_customizable_key_rows(text)
            except Exception:
                keys, rows = self._default_available_keys()
        else:
            keys, rows = self._default_available_keys()

        self.available_keys = keys
        self.available_key_rows = rows

        for item in self.keys_tree.get_children():
            self.keys_tree.delete(item)
        for row in rows:
            self.keys_tree.insert("", "end", values=(row,))

    def _get_values(self) -> dict[str, str]:
        return {key: normalize_user_key(ent.get()) for key, ent in self.entries.items()}

    def _validate(self, values: dict[str, str]) -> bool:
        if not self.available_keys:
            self._refresh_available_keys()

        is_valid, message = validate_values(values, self.available_keys)
        if is_valid:
            return True

        if message.startswith("Please fill in"):
            messagebox.showerror("Missing value", message)
        elif "must be a number" in message or "cannot be negative" in message:
            messagebox.showerror("Invalid value", message)
        elif message.startswith("The movement key"):
            messagebox.showerror("Duplicate key", message)
        else:
            messagebox.showerror("Unsupported key", message)
        return False

    def _generate(self) -> None:
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

        key_values = {spec.field: values[spec.field] for spec in KEY_RULE_SPECS}

        try:
            im_text, imc_text = generate_rebind_outputs(
                im_path,
                imc_path,
                key_values,
            )

            out_dir = os.path.join(self.base_dir, *OUTPUT_DIR_SEGMENTS)
            os.makedirs(out_dir, exist_ok=True)

            out_im = os.path.join(out_dir, "inputmap.xml")
            out_imc = os.path.join(out_dir, "inputmap_common.xml")

            with open(out_im, "w", encoding="utf-8") as f:
                f.write(im_text)
            with open(out_imc, "w", encoding="utf-8") as f:
                f.write(imc_text)

            self.status.config(
                text=f"Generated: {out_im} and {out_imc}. Run again to overwrite.",
                foreground="green",
            )
            messagebox.showinfo(
                "Files generated",
                f"Successfully generated:\n\n{out_im}\n{out_imc}\n\n"
                "Running 'Generate files' again will overwrite these files.",
            )
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to generate files:\n{exc}")
            self.status.config(text="Generation failed", foreground="red")


def run_gui() -> None:
    app = RebindApp()
    app.mainloop()
