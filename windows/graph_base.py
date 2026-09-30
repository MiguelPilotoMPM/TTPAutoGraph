"""
graph_base.py - Base class for all graph panels.

Nodes: [{"id": str, "label": str, "type": str, "subtype": str (optional)}]
Edges: [{"source": str, "target": str, ...}]
"""

import copy
import json
import math
import random
import tkinter as tk
import customtkinter as ctk
from pathlib import Path

BG_COLOR = "#0d1117"
NODE_R   = 14
_DRAG_THRESHOLD = 5   # pixels — below this a release counts as a click

# ── Default settings ──────────────────────────────────────────────────────────

DEFAULT_SETTINGS = {
    "node_colors": {
        "report":            "#4a9eff",
        "ttp":               "#f0883e",
        "IPv4":              "#29b6f6",
        "IPv6":              "#0288d1",
        "MAC":               "#0277bd",
        "URL HTTP":          "#ffa726",
        "URL HTTPS":         "#ff8f00",
        "URL Other":         "#ffe082",
        "Mail":              "#ce93d8",
        "Hash":              "#ef5350",
        "Malicious Domain":  "#b71c1c",
        "Other Domain":      "#e53935",
        "Bitcoin Address":   "#ffd54f",
        "Ethereum Address":  "#ffca28",
        "File Path Windows": "#90a4ae",
        "File Path Unix":    "#b0bec5",
        "DNI/NIE":           "#26a69a",
        "IBAN":              "#66bb6a",
        "Credit Card":       "#f48fb1",
        "UUID":              "#7e57c2",
        "_ioc_default":      "#3fb950",
    },
    "neighbor_depth":   1,
    "node_separation":  1.0,   # multiplier for force-layout k (0.5 compact – 3.0 spread)
    "node_size_scale":  3.0,   # max size multiplier for the most-connected node (1.0 – 5.0)
}

TYPE_LABELS = {"report": "Report", "ttp": "TTP"}


# ── BaseGraph ─────────────────────────────────────────────────────────────────

class BaseGraph(ctk.CTkFrame):

    def __init__(self, parent, project_path, settings=None, on_select=None):
        super().__init__(parent, fg_color=BG_COLOR)
        self.project_path  = Path(project_path) if project_path else None
        self._settings     = settings if settings is not None else copy.deepcopy(DEFAULT_SETTINGS)
        self._on_select    = on_select
        self._selected       = None
        self._highlighted    = set()
        self._selected_nodes = set()   # multi-selection (rubber band)
        self._positions      = {}      # nid -> (x, y)  — persists across redraws
        self._positions_sep  = None    # separation value used when positions were computed
        self._node_radii     = {}      # nid -> radius (scaled by degree)
        self._nodes_data     = {}
        self._edges          = []
        self._data           = []
        self._canvas_w       = 0
        self._canvas_h       = 0

        # Node drag state (left button)
        self._drag_node    = None
        self._drag_start   = None
        self._drag_origins = {}        # nid -> (wx,wy) at drag start — for group move
        self._is_dragging  = False

        # Rubber band selection state
        self._rubber_start = None      # (sx, sy) screen coords where rubber band started

        # Pan state (middle / right button)
        self._pan_start    = None
        self._pan_origin   = None

        # View transform (world → screen: sx = wx*zoom + pan_x)
        self._zoom  = 1.0
        self._pan_x = 0.0
        self._pan_y = 0.0

        self._canvas = tk.Canvas(self, bg=BG_COLOR, highlightthickness=0,
                                 cursor="fleur")
        self._canvas.pack(fill="both", expand=True)
        self._canvas.bind("<Configure>",        self._on_configure)
        # Node drag (left button)
        self._canvas.bind("<Button-1>",         self._on_press)
        self._canvas.bind("<B1-Motion>",        self._on_drag)
        self._canvas.bind("<ButtonRelease-1>",  self._on_release)
        # Pan (middle button)
        self._canvas.bind("<Button-2>",         self._on_pan_press)
        self._canvas.bind("<B2-Motion>",        self._on_pan_drag)
        self._canvas.bind("<ButtonRelease-2>",  self._on_pan_release)
        # Pan (right button — alternative for trackpads)
        self._canvas.bind("<Button-3>",         self._on_pan_press)
        self._canvas.bind("<B3-Motion>",        self._on_pan_drag)
        self._canvas.bind("<ButtonRelease-3>",  self._on_pan_release)
        # Zoom (scroll wheel — cross-platform)
        self._canvas.bind("<MouseWheel>",       self._on_scroll)   # Windows / macOS
        self._canvas.bind("<Button-4>",         self._on_scroll)   # Linux scroll up
        self._canvas.bind("<Button-5>",         self._on_scroll)   # Linux scroll down
        # Double-click to reset view
        self._canvas.bind("<Double-Button-1>",  self._on_double_click)

        # Info bar — wraplength updated on resize
        self._info = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=11),
            text_color="#8b949e", fg_color=BG_COLOR,
            anchor="w", justify="left",
        )
        self._info.pack(side="bottom", fill="x", padx=10, pady=4)

        self._data = self._load_data()
        self.after(300, self._render)

    # ── Public ────────────────────────────────────────────────────────────────

    def refresh(self):
        self._data           = self._load_data()
        self._positions      = {}
        self._positions_sep  = None
        self._selected       = None
        self._highlighted    = set()
        self._selected_nodes = set()
        self._info.configure(text="")
        self._reset_view()
        self._render()

    def redraw(self):
        """Redraw keeping current positions, selection and view (settings change)."""
        self._render()

    # ── Override in subclasses ────────────────────────────────────────────────

    def build_graph(self, data):
        raise NotImplementedError

    # ── Data ──────────────────────────────────────────────────────────────────

    def _load_data(self):
        if not self.project_path:
            return []
        processed = self.project_path / "reports_processed"
        if not processed.exists():
            return []
        result = []
        for f in processed.glob("*.json"):
            try:
                result.append(json.loads(f.read_text(encoding="utf-8")))
            except Exception:
                pass
        return result

    # ── Canvas configure ──────────────────────────────────────────────────────

    def _on_configure(self, event):
        self._info.configure(wraplength=max(event.width - 20, 100))
        # Only reset layout if canvas size changed significantly
        if abs(event.width - self._canvas_w) > 40 or abs(event.height - self._canvas_h) > 40:
            self._canvas_w      = event.width
            self._canvas_h      = event.height
            self._positions     = {}   # recompute layout for new size
            self._positions_sep = None
            self._reset_view()
        self._render()

    # ── Drawing ───────────────────────────────────────────────────────────────

    def _render(self):
        c = self._canvas
        w, h = c.winfo_width(), c.winfo_height()
        if w < 10 or h < 10:
            self.after(100, self._render)
            return

        c.delete("all")

        if not self._data:
            c.create_text(w // 2, h // 2, text="No reports loaded",
                          fill="#8b949e", font=("Helvetica", 14))
            return

        try:
            nodes, edges = self.build_graph(self._data)
        except Exception as e:
            c.create_text(w // 2, h // 2, text=f"Error: {e}",
                          fill="#f85149", font=("Helvetica", 12))
            return

        if not nodes:
            c.create_text(w // 2, h // 2, text="No data to display",
                          fill="#8b949e", font=("Helvetica", 14))
            return

        self._nodes_data = {n["id"]: n for n in nodes}
        self._edges      = edges

        # Recompute layout when node set changes OR separation setting changes
        sep         = self._settings.get("node_separation", 1.0)
        current_ids = set(self._positions.keys())
        wanted_ids  = {n["id"] for n in nodes}
        if current_ids != wanted_ids or sep != self._positions_sep:
            self._positions     = _force_layout(nodes, edges, w, h, separation=sep)
            self._positions_sep = sep

        # Node radii scaled by degree (1x … node_size_scale x NODE_R)
        max_scale = self._settings.get("node_size_scale", 3.0)
        degree = {}
        for e in edges:
            degree[e["source"]] = degree.get(e["source"], 0) + 1
            degree[e["target"]] = degree.get(e["target"], 0) + 1
        max_deg = max(degree.values(), default=1)
        self._node_radii = {
            n["id"]: NODE_R * (1.0 + (max_scale - 1.0) * degree.get(n["id"], 0) / max_deg)
            for n in nodes
        }

        has_sel = self._selected is not None
        z = self._zoom

        # Edges
        for e in edges:
            src, tgt = e["source"], e["target"]
            if src not in self._positions or tgt not in self._positions:
                continue
            x1, y1 = self._to_screen(*self._positions[src])
            x2, y2 = self._to_screen(*self._positions[tgt])
            in_path = has_sel and src in self._highlighted and tgt in self._highlighted
            color   = "#388bfd" if in_path else ("#2d333b" if has_sel else "#3d444d")
            c.create_line(x1, y1, x2, y2, fill=color, width=2 if in_path else 1)

        # Nodes + labels
        for n in nodes:
            nid      = n["id"]
            sx, sy   = self._to_screen(*self._positions[nid])
            r        = self._node_radii[nid] * z          # screen-space radius
            wr       = self._node_radii[nid]               # world-space radius
            active   = not has_sel or nid in self._highlighted
            color    = self._node_color(n) if active else _dim(self._node_color(n))
            in_group = nid in self._selected_nodes and len(self._selected_nodes) > 1
            if nid == self._selected:
                ow, outline = 2, "#ffffff"
            elif in_group:
                ow, outline = 2, "#388bfd"
            else:
                ow, outline = 0, ""
            c.create_oval(sx - r, sy - r, sx + r, sy + r,
                          fill=color, outline=outline, width=ow)

            lcolor = "#c9d1d9" if active else "#4a4f57"

            if n["type"] == "ttp":
                # TTP ID inside the circle — font scales with screen radius
                fsize  = max(6, min(14, int(r * 0.55)))
                icolor = "#ffffff" if active else "#555d68"
                c.create_text(sx, sy, text=_ttp_inner(nid),
                              fill=icolor, font=("Helvetica", fsize, "bold"),
                              anchor="center", justify="center")
            else:
                # External radial label in world space, then projected to screen
                wx, wy   = self._positions[nid]
                cx, cy   = w / 2, h / 2           # world-space layout centre
                dx, dy   = wx - cx, wy - cy
                dist     = math.hypot(dx, dy) or 1
                lx, ly   = self._to_screen(wx + dx / dist * (wr + 6),
                                           wy + dy / dist * (wr + 6))
                anchor   = _label_anchor(dx, dy)
                c.create_text(lx, ly, text=_short(n["label"]),
                              fill=lcolor, font=("Helvetica", 8),
                              anchor=anchor)

        self._draw_legend(c, nodes)

    def _draw_legend(self, c, nodes):
        x, y = 14, 14
        for t, label in TYPE_LABELS.items():
            if any(n["type"] == t for n in nodes):
                c.create_oval(x, y, x + 12, y + 12,
                              fill=self._settings["node_colors"].get(t, "#8b949e"), outline="")
                c.create_text(x + 18, y + 6, text=label,
                              fill="#8b949e", font=("Helvetica", 9), anchor="w")
                y += 20
        seen = list(dict.fromkeys(
            n.get("subtype", "") for n in nodes if n["type"] == "ioc"
        ))
        for subtype in seen:
            color = self._settings["node_colors"].get(
                subtype, self._settings["node_colors"].get("_ioc_default", "#3fb950")
            )
            c.create_oval(x, y, x + 12, y + 12, fill=color, outline="")
            c.create_text(x + 18, y + 6, text=subtype or "IOC",
                          fill="#8b949e", font=("Helvetica", 9), anchor="w")
            y += 20

    # ── View helpers ──────────────────────────────────────────────────────────

    def _reset_view(self):
        self._zoom  = 1.0
        self._pan_x = 0.0
        self._pan_y = 0.0

    def _to_screen(self, wx, wy):
        """World → screen coordinates."""
        return wx * self._zoom + self._pan_x, wy * self._zoom + self._pan_y

    def _to_world(self, sx, sy):
        """Screen → world coordinates."""
        return (sx - self._pan_x) / self._zoom, (sy - self._pan_y) / self._zoom

    def _find_node_at(self, event):
        """Return the nid of the node under the mouse (screen coords), or None."""
        for nid, (nx, ny) in self._positions.items():
            sx, sy = self._to_screen(nx, ny)
            r = self._node_radii.get(nid, NODE_R) * self._zoom
            if math.hypot(event.x - sx, event.y - sy) <= r + 4:
                return nid
        return None

    # ── Mouse: node drag + rubber band (left button) ─────────────────────────

    def _on_press(self, event):
        self._drag_start  = (event.x, event.y)
        self._is_dragging = False
        self._rubber_start = None
        node = self._find_node_at(event)
        self._drag_node = node
        if node is not None:
            # If the clicked node is not already in the group, start a new single selection
            if node not in self._selected_nodes:
                self._selected_nodes = {node}
            # Record world positions of every selected node for delta-based group move
            self._drag_origins = {nid: self._positions[nid]
                                  for nid in self._selected_nodes
                                  if nid in self._positions}
        else:
            # Start rubber band on empty space
            self._rubber_start = (event.x, event.y)
            self._drag_origins = {}

    def _on_drag(self, event):
        if not self._drag_start:
            return
        dx = event.x - self._drag_start[0]
        dy = event.y - self._drag_start[1]
        if math.hypot(dx, dy) > _DRAG_THRESHOLD:
            self._is_dragging = True

        if not self._is_dragging:
            return

        if self._drag_node and self._drag_origins:
            # Move all selected nodes by the same world-space delta
            ddx = dx / self._zoom
            ddy = dy / self._zoom
            for nid, (ox, oy) in self._drag_origins.items():
                self._positions[nid] = (ox + ddx, oy + ddy)
            self._render()

        elif self._rubber_start:
            # Draw rubber band rectangle directly — no full redraw needed
            self._canvas.delete("rubber_band")
            x0, y0 = self._rubber_start
            self._canvas.create_rectangle(
                x0, y0, event.x, event.y,
                outline="#388bfd", width=1, dash=(4, 4),
                tags="rubber_band",
            )

    def _on_release(self, event):
        if self._is_dragging and self._rubber_start:
            # Finish rubber band: select all nodes whose screen position is inside the rect
            x0, y0 = self._rubber_start
            x1, y1 = event.x, event.y
            rx0, rx1 = min(x0, x1), max(x0, x1)
            ry0, ry1 = min(y0, y1), max(y0, y1)
            self._selected_nodes = {
                nid for nid, (wx, wy) in self._positions.items()
                if rx0 <= self._to_screen(wx, wy)[0] <= rx1
                and ry0 <= self._to_screen(wx, wy)[1] <= ry1
            }
            self._canvas.delete("rubber_band")
            # Clear single-node info when group is selected
            if len(self._selected_nodes) != 1:
                self._selected    = None
                self._highlighted = set()
                self._info.configure(
                    text=f"{len(self._selected_nodes)} nodes selected — drag any to move the group"
                    if self._selected_nodes else ""
                )
            self._render()
        elif not self._is_dragging:
            self._handle_click(event)

        self._drag_node    = None
        self._drag_origins = {}
        self._is_dragging  = False
        self._drag_start   = None
        self._rubber_start = None

    # ── Mouse: pan (middle / right button) ────────────────────────────────────

    def _on_pan_press(self, event):
        self._pan_start  = (event.x, event.y)
        self._pan_origin = (self._pan_x, self._pan_y)

    def _on_pan_drag(self, event):
        if not self._pan_start:
            return
        dx = event.x - self._pan_start[0]
        dy = event.y - self._pan_start[1]
        self._pan_x = self._pan_origin[0] + dx
        self._pan_y = self._pan_origin[1] + dy
        self._render()

    def _on_pan_release(self, event):
        self._pan_start  = None
        self._pan_origin = None

    # ── Mouse: zoom (scroll wheel) ────────────────────────────────────────────

    def _on_scroll(self, event):
        # Determine direction (cross-platform)
        if event.num == 4 or (event.delta and event.delta > 0):
            factor = 1.15
        else:
            factor = 1.0 / 1.15

        new_zoom = max(0.1, min(20.0, self._zoom * factor))
        ratio    = new_zoom / self._zoom

        # Zoom centred on cursor position
        self._pan_x = event.x - ratio * (event.x - self._pan_x)
        self._pan_y = event.y - ratio * (event.y - self._pan_y)
        self._zoom  = new_zoom
        self._render()

    # ── Mouse: double-click resets view ───────────────────────────────────────

    def _on_double_click(self, event):
        if self._find_node_at(event) is None:   # only when clicking empty space
            self._reset_view()
            self._render()

    # ── Mouse: click / select ─────────────────────────────────────────────────

    def _handle_click(self, event):
        clicked = self._find_node_at(event)

        if clicked == self._selected:
            # Second click on same node → deselect
            self._selected       = None
            self._highlighted    = set()
            self._selected_nodes = set()
            self._info.configure(text="")
            if self._on_select:
                self._on_select(None, [], [])
        else:
            self._selected       = clicked
            self._selected_nodes = {clicked} if clicked else set()
            if clicked:
                depth             = self._settings.get("neighbor_depth", 1)
                self._highlighted = self._bfs(clicked, depth)
                n                 = self._nodes_data.get(clicked, {})
                neighbors         = len(self._highlighted) - 1
                self._info.configure(
                    text=f"[{n.get('type','').upper()}]  {n.get('label','')}  "
                         f"— {neighbors} neighbour(s) at depth {depth}"
                )
                if self._on_select:
                    self._on_select(n, self._data, self._edges)
            else:
                self._highlighted = set()

        self._render()

    def _bfs(self, start, depth):
        adj = {}
        for e in self._edges:
            adj.setdefault(e["source"], set()).add(e["target"])
            adj.setdefault(e["target"], set()).add(e["source"])
        visited, frontier = {start}, {start}
        for _ in range(depth):
            nxt = {nb for nid in frontier for nb in adj.get(nid, set()) if nb not in visited}
            visited |= nxt
            frontier = nxt
        return visited

    def _node_color(self, node):
        colors = self._settings["node_colors"]
        if node["type"] == "ioc":
            return colors.get(node.get("subtype"), colors.get("_ioc_default", "#3fb950"))
        return colors.get(node["type"], "#8b949e")


# ── Force-directed layout ─────────────────────────────────────────────────────

def _force_layout(nodes, edges, w, h, iterations=120, separation=1.0):
    """Fruchterman-Reingold spring embedder.

    separation : multiplier on the ideal spring length k (0.5 = compact, 3.0 = spread).
    """
    n = len(nodes)
    if n == 0:
        return {}
    if n == 1:
        return {nodes[0]["id"]: (w / 2, h / 2)}

    margin = 60
    area   = (w - 2 * margin) * (h - 2 * margin)
    k      = math.sqrt(area / n) * 0.85 * max(0.1, separation)

    # Seed positions on a circle so we start spread out
    pos = {}
    cx, cy = w / 2, h / 2
    r0 = min(w, h) * 0.35
    for i, nd in enumerate(nodes):
        angle = 2 * math.pi * i / n
        pos[nd["id"]] = [
            cx + r0 * math.cos(angle) + random.uniform(-5, 5),
            cy + r0 * math.sin(angle) + random.uniform(-5, 5),
        ]

    # Edge set for fast lookup
    edge_pairs = [(e["source"], e["target"]) for e in edges
                  if e["source"] in pos and e["target"] in pos]

    for step in range(iterations):
        t = k * max(0.05, 1.0 - step / iterations)   # cooling temperature
        disp = {nid: [0.0, 0.0] for nid in pos}

        # Repulsion between all pairs
        ids = list(pos.keys())
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                a, b = ids[i], ids[j]
                dx = pos[b][0] - pos[a][0]
                dy = pos[b][1] - pos[a][1]
                d  = max(math.hypot(dx, dy), 0.1)
                f  = k * k / d
                ux, uy = dx / d, dy / d
                disp[a][0] -= f * ux
                disp[a][1] -= f * uy
                disp[b][0] += f * ux
                disp[b][1] += f * uy

        # Attraction along edges
        for src, tgt in edge_pairs:
            dx = pos[tgt][0] - pos[src][0]
            dy = pos[tgt][1] - pos[src][1]
            d  = max(math.hypot(dx, dy), 0.1)
            f  = d * d / k
            ux, uy = dx / d, dy / d
            disp[src][0] += f * ux
            disp[src][1] += f * uy
            disp[tgt][0] -= f * ux
            disp[tgt][1] -= f * uy

        # Apply displacement with temperature cap — no boundary clamping,
        # nodes spread freely; the user can pan/zoom to see them all.
        for nid in pos:
            dx, dy = disp[nid]
            d = max(math.hypot(dx, dy), 0.1)
            scale = min(d, t) / d
            pos[nid][0] += dx * scale
            pos[nid][1] += dy * scale

    return {nid: (p[0], p[1]) for nid, p in pos.items()}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _label_anchor(dx, dy):
    """Choose tk anchor so the label sits outside the node."""
    if abs(dx) < 0.3 * abs(dy):
        return "n" if dy < 0 else "s"
    if abs(dy) < 0.3 * abs(dx):
        return "e" if dx > 0 else "w"
    if dx > 0:
        return "ne" if dy < 0 else "se"
    return "nw" if dy < 0 else "sw"


def _dim(hex_color, factor=0.25):
    try:
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        return f"#{int(r*factor):02x}{int(g*factor):02x}{int(b*factor):02x}"
    except Exception:
        return "#1a1a1a"


def _short(label, max_len=22):
    return label if len(label) <= max_len else label[:max_len - 2] + ".."


def _ttp_inner(ttp_id):
    """Format a TTP technique ID for display inside the node circle.

    'T1059'     -> 'T1059'
    'T1059.001' -> 'T1059\n.001'
    """
    if "." in ttp_id:
        base, sub = ttp_id.split(".", 1)
        return f"{base}\n.{sub}"
    return ttp_id


def get_ttps(report):
    return {item["technique"] for item in report.get("ttp_info", {}).get("ttps", [])}


def get_ttp_name(report, tid):
    for item in report.get("ttp_info", {}).get("ttps", []):
        if item["technique"] == tid:
            return item.get("technique_name", tid)
    return tid


def get_iocs(report, max_per_report=30):
    result = []
    for category, patterns in report.get("cti_info", {}).items():
        for ioc_type, values in patterns.items():
            for v in values:
                if v:
                    result.append((ioc_type, v))
                    if len(result) >= max_per_report:
                        return result
    return result
