"""
settings_panel.py - Visual settings panel (left sidebar tab).

Allows the user to:
  - Change the color of each node type (Report, TTP, and every IOC subtype).
  - Set the neighbor depth used when clicking a node in the graph.
"""

from tkinter import colorchooser
import customtkinter as ctk

from windows.graph_base import DEFAULT_SETTINGS

BORDER_COLOR = "#30363d"
CARD_COLOR   = "#161b22"

# Friendly display names and ordered groups
_MAIN_TYPES = [
    ("report", "Report"),
    ("ttp",    "TTP"),
]

_IOC_TYPES = [
    ("IPv4",              "IPv4"),
    ("IPv6",              "IPv6"),
    ("MAC",               "MAC"),
    ("URL HTTP",          "URL HTTP"),
    ("URL HTTPS",         "URL HTTPS"),
    ("URL Other",         "URL Other"),
    ("Mail",              "Mail"),
    ("Hash",              "Hash"),
    ("Malicious Domain",  "Malicious Domain"),
    ("Other Domain",      "Other Domain"),
    ("Bitcoin Address",   "Bitcoin Address"),
    ("Ethereum Address",  "Ethereum Address"),
    ("File Path Windows", "File Path Windows"),
    ("File Path Unix",    "File Path Unix"),
    ("DNI/NIE",           "DNI / NIE"),
    ("IBAN",              "IBAN"),
    ("Credit Card",       "Credit Card"),
    ("UUID",              "UUID"),
]


class SettingsPanel(ctk.CTkFrame):

    def __init__(self, parent, settings, on_change=None):
        """
        settings  : shared dict (DEFAULT_SETTINGS structure)
        on_change : callable — called whenever a setting is modified
        """
        super().__init__(parent, fg_color="transparent")
        self._settings   = settings
        self._on_change  = on_change
        self._color_btns = {}   # key -> CTkButton (color swatch)
        self._build()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=6, pady=6)

        # ── Node colors ───────────────────────────────────────────────────────
        self._section_label(scroll, "Node Colors")

        self._section_label(scroll, "Main", small=True)
        for key, label in _MAIN_TYPES:
            self._color_row(scroll, key, label)

        self._section_label(scroll, "IOC types", small=True)
        for key, label in _IOC_TYPES:
            self._color_row(scroll, key, label)

        # ── Neighbor depth ────────────────────────────────────────────────────
        self._section_label(scroll, "Neighbor Depth")

        depth_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        depth_frame.pack(fill="x", padx=4, pady=(4, 2))

        ctk.CTkLabel(
            depth_frame,
            text="Highlight neighbors within distance:",
            font=ctk.CTkFont(size=11), text_color="#8b949e", anchor="w",
        ).pack(fill="x")

        slider_row = ctk.CTkFrame(depth_frame, fg_color="transparent")
        slider_row.pack(fill="x", pady=(4, 0))

        self._depth_label = ctk.CTkLabel(
            slider_row,
            text=str(self._settings.get("neighbor_depth", 1)),
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#4a9eff", width=24,
        )
        self._depth_label.pack(side="right", padx=(6, 0))

        self._slider = ctk.CTkSlider(
            slider_row,
            from_=1, to=6, number_of_steps=5,
            progress_color="#1f6feb",
            command=self._on_depth_change,
        )
        self._slider.set(self._settings.get("neighbor_depth", 1))
        self._slider.pack(side="left", fill="x", expand=True)

        # ── Node separation ───────────────────────────────────────────────────
        self._section_label(scroll, "Node Separation")

        sep_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        sep_frame.pack(fill="x", padx=4, pady=(4, 2))

        ctk.CTkLabel(
            sep_frame,
            text="Space between nodes in the graph layout:",
            font=ctk.CTkFont(size=11), text_color="#8b949e", anchor="w",
        ).pack(fill="x")

        sep_row = ctk.CTkFrame(sep_frame, fg_color="transparent")
        sep_row.pack(fill="x", pady=(4, 0))

        init_sep = self._settings.get("node_separation", 1.0)
        self._sep_label = ctk.CTkLabel(
            sep_row,
            text=f"{init_sep:.1f}x",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#4a9eff", width=36,
        )
        self._sep_label.pack(side="right", padx=(6, 0))

        self._sep_slider = ctk.CTkSlider(
            sep_row,
            from_=0.5, to=3.0, number_of_steps=10,
            progress_color="#1f6feb",
            command=self._on_sep_change,
        )
        self._sep_slider.set(init_sep)
        self._sep_slider.pack(side="left", fill="x", expand=True)

        # ── Node size scale ───────────────────────────────────────────────────
        self._section_label(scroll, "Node Size Scale")

        scale_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        scale_frame.pack(fill="x", padx=4, pady=(4, 2))

        ctk.CTkLabel(
            scale_frame,
            text="Max size of the most-connected node:",
            font=ctk.CTkFont(size=11), text_color="#8b949e", anchor="w",
        ).pack(fill="x")

        scale_row = ctk.CTkFrame(scale_frame, fg_color="transparent")
        scale_row.pack(fill="x", pady=(4, 0))

        init_scale = self._settings.get("node_size_scale", 3.0)
        self._scale_label = ctk.CTkLabel(
            scale_row,
            text=f"{init_scale:.1f}x",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#4a9eff", width=36,
        )
        self._scale_label.pack(side="right", padx=(6, 0))

        self._scale_slider = ctk.CTkSlider(
            scale_row,
            from_=1.0, to=5.0, number_of_steps=8,
            progress_color="#1f6feb",
            command=self._on_scale_change,
        )
        self._scale_slider.set(init_scale)
        self._scale_slider.pack(side="left", fill="x", expand=True)

    # ── Widgets ───────────────────────────────────────────────────────────────

    def _section_label(self, parent, text, small=False):
        size  = 10 if small else 12
        color = "#4a4f57" if small else "#4a9eff"
        ctk.CTkLabel(
            parent, text=text,
            font=ctk.CTkFont(size=size, weight="bold"),
            text_color=color, anchor="w",
        ).pack(fill="x", padx=4, pady=(10 if not small else 4, 2))

    def _color_row(self, parent, key, label):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=1)

        current = self._settings["node_colors"].get(key, "#8b949e")

        btn = ctk.CTkButton(
            row, text="", width=22, height=22, corner_radius=4,
            fg_color=current, hover_color=current,
            border_width=1, border_color=BORDER_COLOR,
            command=lambda k=key: self._pick_color(k),
        )
        btn.pack(side="left", padx=(4, 8))
        self._color_btns[key] = btn

        ctk.CTkLabel(
            row, text=label,
            font=ctk.CTkFont(size=11), text_color="#c9d1d9", anchor="w",
        ).pack(side="left", fill="x", expand=True)

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _pick_color(self, key):
        current = self._settings["node_colors"].get(key, "#8b949e")
        result  = colorchooser.askcolor(color=current, title=f"Color for {key}")
        new_color = result[1]
        if new_color:
            self._settings["node_colors"][key] = new_color
            btn = self._color_btns[key]
            btn.configure(fg_color=new_color, hover_color=new_color)
            if self._on_change:
                self._on_change()

    def _on_depth_change(self, value):
        depth = int(round(value))
        self._settings["neighbor_depth"] = depth
        self._depth_label.configure(text=str(depth))
        if self._on_change:
            self._on_change()

    def _on_sep_change(self, value):
        # Snap to nearest 0.25 step for a clean display
        sep = round(round(value / 0.25) * 0.25, 2)
        self._settings["node_separation"] = sep
        self._sep_label.configure(text=f"{sep:.1f}x")
        if self._on_change:
            self._on_change()

    def _on_scale_change(self, value):
        # Snap to nearest 0.5 step (range 1.0 – 5.0)
        scale = round(round(value / 0.5) * 0.5, 1)
        self._settings["node_size_scale"] = scale
        self._scale_label.configure(text=f"{scale:.1f}x")
        if self._on_change:
            self._on_change()
