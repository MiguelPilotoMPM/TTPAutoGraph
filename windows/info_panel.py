"""
info_panel.py - Right sidebar that shows details about the selected graph node.

Receives:  node       {"id", "label", "type", "subtype"?}
           all_data   list of report dicts (from reports_processed/)
           edges      list of {"source", "target", ...} for the current graph
"""

import customtkinter as ctk
from windows.graph_base import DEFAULT_SETTINGS, get_ttps, get_ttp_name, get_iocs

BG_COLOR     = "#0d1117"
CARD_COLOR   = "#161b22"
BORDER_COLOR = "#30363d"

TYPE_BADGE_COLORS = {
    "report": "#1f6feb",
    "ttp":    "#9a5820",
    "ioc":    "#1a5f2a",
}


class InfoPanel(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(parent, fg_color=CARD_COLOR, corner_radius=0,
                         border_width=1, border_color=BORDER_COLOR)

        # ── Header ────────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="#0d1117", corner_radius=0,
                               border_width=1, border_color=BORDER_COLOR)
        header.pack(fill="x")

        ctk.CTkLabel(
            header, text="Node Info",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#8b949e",
        ).pack(anchor="w", padx=14, pady=10)

        # ── Badge + name ──────────────────────────────────────────────────────
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=(10, 4))

        self._badge = ctk.CTkLabel(
            top, text="", font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#e6edf3", corner_radius=6,
            fg_color="#21262d", width=60, height=22,
        )
        self._badge.pack(anchor="w", pady=(0, 4))

        self._name = ctk.CTkLabel(
            top, text="Select a node", wraplength=220,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#e6edf3", anchor="w", justify="left",
        )
        self._name.pack(anchor="w")

        # ── Scrollable content ────────────────────────────────────────────────
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True, padx=6, pady=(6, 6))

        self._show_placeholder()

    # ── Public API ────────────────────────────────────────────────────────────

    def show(self, node, all_data, edges):
        self._badge.configure(
            text=node["type"].upper(),
            fg_color=TYPE_BADGE_COLORS.get(node["type"], "#21262d"),
        )
        self._name.configure(text=node.get("label", node["id"]))
        self._clear()

        if node["type"] == "report":
            self._show_report(node, all_data, edges)
        elif node["type"] == "ttp":
            self._show_ttp(node, all_data)
        elif node["type"] == "ioc":
            self._show_ioc(node, all_data)

    def clear(self):
        self._badge.configure(text="", fg_color="#21262d")
        self._name.configure(text="Select a node")
        self._clear()
        self._show_placeholder()

    # ── Content builders ──────────────────────────────────────────────────────

    def _show_report(self, node, all_data, edges):
        report = next((r for r in all_data if r["file_name"] == node["id"]), None)
        if not report:
            self._item("Report data not found", color="#f85149")
            return

        # TTPs
        ttps = list({t["technique"]: t for t in report.get("ttp_info", {}).get("ttps", [])}.values())
        self._section(f"TTPs  ({len(ttps)})")
        if ttps:
            for t in ttps:
                self._item(f"{t['technique']}: {t.get('technique_name', '')}")
        else:
            self._item("None detected", color="#4a4f57")

        # IOCs
        ioc_counts = {}
        for ioc_type, value in get_iocs(report, max_per_report=200):
            ioc_counts[ioc_type] = ioc_counts.get(ioc_type, 0) + 1

        self._section(f"IOCs  ({sum(ioc_counts.values())})")
        if ioc_counts:
            for ioc_type, count in sorted(ioc_counts.items()):
                self._item(f"{ioc_type}: {count}")
        else:
            self._item("None detected", color="#4a4f57")

        # Connected reports via current graph edges
        neighbors = []
        for e in edges:
            other = None
            if e["source"] == node["id"]:
                other = e["target"]
            elif e["target"] == node["id"]:
                other = e["source"]
            if other:
                neighbors.append((other, e))

        self._section(f"Connected Reports  ({len(neighbors)})")
        if neighbors:
            for other, e in neighbors:
                detail = ""
                if "shared_ttps" in e:
                    detail = f"{e['shared_ttps']} TTP(s), {e['shared_iocs']} IOC(s)"
                self._item(other, sub=detail)
        else:
            self._item("No connections in this view", color="#4a4f57")

    def _show_ttp(self, node, all_data):
        tid = node["id"]

        # Find all reports containing this TTP
        containing = []
        contexts   = []
        for r in all_data:
            for t in r.get("ttp_info", {}).get("ttps", []):
                if t["technique"] == tid:
                    containing.append(r["file_name"])
                    contexts.append((r["file_name"], t.get("context", "")))
                    break

        self._section(f"Found in  ({len(containing)} report(s))")
        for name in containing:
            self._item(name)

        self._section("Context sentences")
        if contexts:
            for fname, ctx in contexts:
                self._item(ctx or "(no context)", sub=fname, italic=True)
        else:
            self._item("No context available", color="#4a4f57")

    def _show_ioc(self, node, all_data):
        # node["id"] = "ioc_type:value"
        parts    = node["id"].split(":", 1)
        ioc_type = parts[0] if len(parts) == 2 else node.get("subtype", "IOC")
        value    = parts[1] if len(parts) == 2 else node["id"]

        self._section("Type")
        self._item(ioc_type)

        self._section("Value")
        self._item(value)

        # Find all reports containing this IOC
        containing = []
        for r in all_data:
            for t, v in get_iocs(r, max_per_report=200):
                if t == ioc_type and v == value:
                    containing.append(r["file_name"])
                    break

        self._section(f"Found in  ({len(containing)} report(s))")
        if containing:
            for name in containing:
                self._item(name)
        else:
            self._item("Not found in loaded reports", color="#4a4f57")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _clear(self):
        for w in self._scroll.winfo_children():
            w.destroy()

    def _show_placeholder(self):
        ctk.CTkLabel(
            self._scroll,
            text="Click on a node\nin the graph\nto see details",
            font=ctk.CTkFont(size=12), text_color="#4a4f57",
            justify="center",
        ).pack(pady=40)

    def _section(self, title):
        ctk.CTkLabel(
            self._scroll, text=title,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#4a9eff", anchor="w",
        ).pack(fill="x", padx=4, pady=(12, 2))

        ctk.CTkFrame(self._scroll, fg_color=BORDER_COLOR, height=1
                     ).pack(fill="x", padx=4, pady=(0, 4))

    def _item(self, text, sub="", color="#c9d1d9", italic=False):
        frame = ctk.CTkFrame(self._scroll, fg_color="transparent")
        frame.pack(fill="x", padx=6, pady=1)

        font = ctk.CTkFont(size=11, slant="italic" if italic else "roman")
        ctk.CTkLabel(
            frame, text=text, font=font,
            text_color=color, anchor="w", wraplength=210, justify="left",
        ).pack(anchor="w")

        if sub:
            ctk.CTkLabel(
                frame, text=sub,
                font=ctk.CTkFont(size=10), text_color="#4a4f57",
                anchor="w", wraplength=210,
            ).pack(anchor="w")
