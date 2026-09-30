"""
graph_iocs_reports.py - Bipartite graph: Reports <-> IOCs.

Nodes : Report nodes (inner ring) + IOC nodes (outer ring, capped at MAX_IOCS).
Edges : report -> IOC (report contains that IOC value).
"""

from windows.graph_base import BaseGraph, get_iocs

MAX_IOCS = 40


class GraphIOCsReports(BaseGraph):

    def build_graph(self, data):
        # Count IOC frequency across reports to pick the most relevant ones
        ioc_freq = {}
        for report in data:
            for ioc_type, value in get_iocs(report):
                key = f"{ioc_type}:{value}"
                ioc_freq[key] = ioc_freq.get(key, 0) + 1

        # Keep top MAX_IOCS by frequency
        top_iocs = set(
            k for k, _ in sorted(ioc_freq.items(), key=lambda x: -x[1])[:MAX_IOCS]
        )

        nodes = []
        edges = []
        seen_ioc = {}  # key -> value label

        for report in data:
            rname = report["file_name"]
            nodes.append({"id": rname, "label": rname, "type": "report"})

            for ioc_type, value in get_iocs(report):
                key = f"{ioc_type}:{value}"
                if key not in top_iocs:
                    continue
                if key not in seen_ioc:
                    seen_ioc[key] = value
                edges.append({"source": rname, "target": key})

        for key, label in seen_ioc.items():
            subtype = key.split(":", 1)[0]   # key = "ioc_type:value"
            nodes.append({"id": key, "label": label, "type": "ioc", "subtype": subtype})

        return nodes, edges
