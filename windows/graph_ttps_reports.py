"""
graph_ttps_reports.py - Bipartite graph: Reports <-> TTPs.

Nodes : Report nodes (inner ring) + TTP nodes (outer ring).
Edges : report -> TTP (report contains that TTP).
"""

from windows.graph_base import BaseGraph, get_ttps, get_ttp_name


class GraphTTPsReports(BaseGraph):

    def build_graph(self, data):
        nodes    = []
        edges    = []
        seen_ttp = {}   # tid -> name

        for report in data:
            rname = report["file_name"]
            nodes.append({"id": rname, "label": rname, "type": "report"})

            for tid in get_ttps(report):
                if tid not in seen_ttp:
                    seen_ttp[tid] = get_ttp_name(report, tid)
                edges.append({"source": rname, "target": tid})

        for tid, name in seen_ttp.items():
            nodes.append({"id": tid, "label": f"{tid}: {name}", "type": "ttp"})

        return nodes, edges
