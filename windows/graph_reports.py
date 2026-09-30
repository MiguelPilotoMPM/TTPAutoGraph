"""
graph_reports.py - Report-only graph.

Nodes : one node per report.
Edges : two reports are connected if they share at least one TTP technique
        OR at least one IOC value.
Clicking a node shows how many TTPs and IOCs it shares with each neighbor.
"""

from windows.graph_base import BaseGraph, get_ttps, get_iocs


class GraphReports(BaseGraph):

    def build_graph(self, data):
        if not data:
            return [], []

        nodes = [{"id": r["file_name"], "label": r["file_name"], "type": "report"}
                 for r in data]

        self._report_ttps = {r["file_name"]: get_ttps(r) for r in data}
        self._report_iocs = {
            r["file_name"]: {f"{t}:{v}" for t, v in get_iocs(r)}
            for r in data
        }

        edges = []
        names = [r["file_name"] for r in data]
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = names[i], names[j]
                n_ttps = len(self._report_ttps[a] & self._report_ttps[b])
                n_iocs = len(self._report_iocs[a] & self._report_iocs[b])
                if n_ttps or n_iocs:
                    edges.append({"source": a, "target": b,
                                  "shared_ttps": n_ttps, "shared_iocs": n_iocs})
        return nodes, edges

    # ── Override click to show shared element counts ──────────────────────────

    def _handle_click(self, event):
        clicked = self._find_node_at(event)

        if clicked == self._selected:
            self._selected    = None
            self._highlighted = set()
            self._info.configure(text="")
            if self._on_select:
                self._on_select(None, [], [])
        else:
            self._selected = clicked
            if clicked:
                depth             = self._settings.get("neighbor_depth", 1)
                self._highlighted = self._bfs(clicked, depth)
                parts = []
                for e in self._edges:
                    if e["source"] == clicked or e["target"] == clicked:
                        other = e["target"] if e["source"] == clicked else e["source"]
                        parts.append(
                            f"{other[:20]}: {e['shared_ttps']} TTP(s), {e['shared_iocs']} IOC(s)"
                        )
                info = f"[{clicked[:30]}]"
                if parts:
                    info += "  |  " + "  //  ".join(parts)
                self._info.configure(text=info)
                n = self._nodes_data.get(clicked, {})
                if self._on_select:
                    self._on_select(n, self._data, self._edges)
            else:
                self._highlighted = set()

        self._render()
