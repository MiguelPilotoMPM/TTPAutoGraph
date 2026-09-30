"""
graph_ttps.py - TTPs in common between reports.

Nodes : unique TTP techniques found across all reports.
Edges : two TTPs are linked if they co-appear in the same report.
"""

from windows.graph_base import BaseGraph, get_ttps, get_ttp_name


class GraphTTPs(BaseGraph):

    def build_graph(self, data):
        # Collect unique TTPs and which reports contain each
        ttp_info    = {}   # tid -> {"name": str, "reports": set}
        report_ttps = {}   # report_name -> set of tids

        for report in data:
            rname = report["file_name"]
            tids  = get_ttps(report)
            report_ttps[rname] = tids
            for tid in tids:
                if tid not in ttp_info:
                    ttp_info[tid] = {"name": get_ttp_name(report, tid), "reports": set()}
                ttp_info[tid]["reports"].add(rname)

        nodes = [
            {"id": tid, "label": f"{tid}: {v['name']}", "type": "ttp"}
            for tid, v in ttp_info.items()
        ]

        # Edges: two TTPs linked if they co-occur in the same report.
        # Only draw edge once per pair.
        edge_set = set()
        for tids in report_ttps.values():
            tids = list(tids)
            for i in range(len(tids)):
                for j in range(i + 1, len(tids)):
                    a, b = sorted([tids[i], tids[j]])
                    edge_set.add((a, b))

        edges = [{"source": a, "target": b} for a, b in edge_set]
        return nodes, edges
