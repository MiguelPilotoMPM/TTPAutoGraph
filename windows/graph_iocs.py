"""
graph_iocs.py - IOCs shared between reports.

Nodes : IOC values that appear in at least 2 reports (or all if < 2 reports loaded).
        Capped at MAX_IOCS to keep the graph readable.
Edges : two IOCs linked if they co-appear in the same report.
"""

from windows.graph_base import BaseGraph, get_iocs

MAX_IOCS = 40   # max nodes to display


class GraphIOCs(BaseGraph):

    def build_graph(self, data):
        # ioc_value -> set of report names that contain it
        ioc_reports = {}

        for report in data:
            rname = report["file_name"]
            for ioc_type, value in get_iocs(report):
                key = f"{ioc_type}:{value}"
                ioc_reports.setdefault(key, {"type": ioc_type, "value": value, "reports": set()})
                ioc_reports[key]["reports"].add(rname)

        # Filter: only keep IOCs in >=2 reports when we have >1 report
        if len(data) > 1:
            ioc_reports = {k: v for k, v in ioc_reports.items() if len(v["reports"]) >= 2}

        # Sort by frequency descending, cap at MAX_IOCS
        sorted_iocs = sorted(ioc_reports.items(), key=lambda x: -len(x[1]["reports"]))
        selected    = dict(sorted_iocs[:MAX_IOCS])

        nodes = [
            {"id": k, "label": v["value"], "type": "ioc", "subtype": v["type"]}
            for k, v in selected.items()
        ]

        # Edges: two IOCs linked if they appear together in the same report
        report_iocs = {}
        for report in data:
            rname = report["file_name"]
            keys  = [f"{t}:{v}" for t, v in get_iocs(report) if f"{t}:{v}" in selected]
            report_iocs[rname] = keys

        edge_set = set()
        for keys in report_iocs.values():
            for i in range(len(keys)):
                for j in range(i + 1, len(keys)):
                    a, b = sorted([keys[i], keys[j]])
                    edge_set.add((a, b))

        edges = [{"source": a, "target": b} for a, b in edge_set]
        return nodes, edges
