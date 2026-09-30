import copy
import json
import platform
import customtkinter as ctk
from pathlib import Path

from windows.config_panel       import ConfigPanel
from windows.info_panel         import InfoPanel
from windows.settings_panel     import SettingsPanel
from windows.graph_reports      import GraphReports
from windows.graph_ttps         import GraphTTPs
from windows.graph_ttps_reports import GraphTTPsReports
from windows.graph_iocs_reports import GraphIOCsReports
from windows.graph_full         import GraphFull
from windows.graph_base         import DEFAULT_SETTINGS

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG_COLOR     = "#0d1117"
CARD_COLOR   = "#161b22"
BORDER_COLOR = "#30363d"
SIDEBAR_W    = 300


class BasePage(ctk.CTk):

    def __init__(self, project_path=None):
        super().__init__()
        self.project_path = Path(project_path) if project_path else None
        self.config_data  = self._load_config()

        # Shared settings dict — start from defaults then overlay saved values
        self._settings = copy.deepcopy(DEFAULT_SETTINGS)
        saved = (self.config_data or {}).get("settings", {})
        if saved:
            self._settings["node_colors"].update(saved.get("node_colors", {}))
            for key in ("neighbor_depth", "node_separation", "node_size_scale"):
                if key in saved:
                    self._settings[key] = saved[key]

        self.title((self.config_data or {}).get("project_name", "Project"))
        self.configure(fg_color=BG_COLOR)
        self._maximize()
        self._build_ui()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _maximize(self):
        self.attributes("-fullscreen", True)
        # Allow Escape to exit fullscreen
        self.bind("<Escape>", lambda _: self.attributes("-fullscreen", False))

    def _load_config(self):
        if not self.project_path:
            return None
        try:
            return json.loads((self.project_path / "config.json").read_text(encoding="utf-8"))
        except Exception:
            return None

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self._build_topbar()
        self._build_main()

    def _build_topbar(self):
        bar = ctk.CTkFrame(self, fg_color=CARD_COLOR, height=50, corner_radius=0,
                           border_width=1, border_color=BORDER_COLOR)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)

        name = (self.config_data or {}).get("project_name", "Unknown Project")
        ctk.CTkLabel(
            bar, text=name,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#e6edf3",
        ).pack(side="left", padx=20)

        ctk.CTkButton(
            bar, text="Exit", width=80, height=32,
            fg_color="#6e1c1c", hover_color="#a02020",
            border_width=1, border_color="#f85149",
            command=self.destroy,
        ).pack(side="right", padx=(0, 12), pady=9)

        ctk.CTkButton(
            bar, text="Save", width=80, height=32,
            fg_color="#1a3a1a", hover_color="#245c24",
            border_width=1, border_color="#3fb950",
            command=self._save,
        ).pack(side="right", padx=(0, 6), pady=9)

        ctk.CTkButton(
            bar, text="Refresh", width=90, height=32,
            fg_color="#21262d", hover_color="#30363d",
            border_width=1, border_color=BORDER_COLOR,
            command=self._refresh,
        ).pack(side="right", padx=(0, 6), pady=9)

    def _build_main(self):
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True)

        # ── Left sidebar ──────────────────────────────────────────────────────
        sidebar = ctk.CTkFrame(main, width=SIDEBAR_W, fg_color=CARD_COLOR,
                               corner_radius=0, border_width=1, border_color=BORDER_COLOR)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        left_tabs = ctk.CTkTabview(
            sidebar,
            fg_color="transparent",
            segmented_button_fg_color=CARD_COLOR,
            segmented_button_selected_color="#1f6feb",
            segmented_button_selected_hover_color="#388bfd",
            segmented_button_unselected_color=CARD_COLOR,
            segmented_button_unselected_hover_color="#21262d",
            border_color=BORDER_COLOR, border_width=1,
        )
        left_tabs.pack(fill="both", expand=True, padx=6, pady=6)
        left_tabs.add("Configuration")
        left_tabs.add("Settings")

        self._config_panel = ConfigPanel(
            left_tabs.tab("Configuration"),
            self.project_path,
            on_refresh=self._refresh,
        )
        self._config_panel.pack(fill="both", expand=True)

        SettingsPanel(
            left_tabs.tab("Settings"),
            settings=self._settings,
            on_change=self._on_settings_change,
        ).pack(fill="both", expand=True)

        # ── Graph area (centre) ───────────────────────────────────────────────
        centre = ctk.CTkFrame(main, fg_color="transparent")
        centre.pack(side="left", fill="both", expand=True)

        graph_tabs = ctk.CTkTabview(
            centre,
            fg_color=CARD_COLOR,
            segmented_button_fg_color="#161b22",
            segmented_button_selected_color="#1f6feb",
            segmented_button_selected_hover_color="#388bfd",
            segmented_button_unselected_color="#161b22",
            segmented_button_unselected_hover_color="#21262d",
            border_color=BORDER_COLOR, border_width=1,
        )
        graph_tabs.pack(fill="both", expand=True, padx=(0, 0), pady=10)

        # ── Right info panel ──────────────────────────────────────────────────
        self._info_panel = InfoPanel(main)
        self._info_panel.pack(side="right", fill="y", padx=(0, 10), pady=10)
        self._info_panel.configure(width=260)

        self._graph_panels = {}
        for tab_name, cls in [
            ("Reports", GraphReports),
            ("TTPs",    GraphTTPs),
            ("TTP+Rep", GraphTTPsReports),
            ("IOC+Rep", GraphIOCsReports),
            ("Full",    GraphFull),
        ]:
            try:
                graph_tabs.add(tab_name)
                panel = cls(graph_tabs.tab(tab_name), self.project_path,
                            settings=self._settings,
                            on_select=self._on_node_select)
                panel.pack(fill="both", expand=True)
                self._graph_panels[tab_name] = panel
            except Exception as e:
                print(f"[BasePage] Error loading tab '{tab_name}': {e}")

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _refresh(self):
        self.config_data = self._load_config()
        self._config_panel.refresh()
        for panel in self._graph_panels.values():
            panel.refresh()

    def _save(self):
        """Persist the current settings (colors, thresholds) to config.json."""
        if not self.project_path:
            return
        try:
            cfg_path = self.project_path / "config.json"
            cfg = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}
            cfg["settings"] = self._settings
            cfg_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            print(f"[BasePage] Save failed: {e}")

    def _on_settings_change(self):
        """Called by SettingsPanel when colors or depth change — just redraw."""
        for panel in self._graph_panels.values():
            panel.redraw()

    def _on_node_select(self, node, all_data, edges):
        """Called by any graph panel when a node is clicked."""
        if node:
            self._info_panel.show(node, all_data, edges)
        else:
            self._info_panel.clear()
