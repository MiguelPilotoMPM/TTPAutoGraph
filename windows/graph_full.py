"""
graph_full.py - Full graph: Reports + TTPs + IOCs.

Nodes : Report nodes (inner) + TTP nodes (middle) + IOC nodes (outer, capped).
Edges : report->TTP, report->IOC.
"""

from windows.graph_base import BaseGraph, get_ttps, get_ttp_name, get_iocs

MAX_IOCS = 30


class GraphFull(BaseGraph):

    def build_graph(self, data):
        # Count IOC frequency to pick top ones
        ioc_freq = {}
        for report in data:
            for ioc_type, value in get_iocs(report):
                key = f"{ioc_type}:{value}"
                ioc_freq[key] = ioc_freq.get(key, 0) + 1

        top_iocs = set(
            k for k, _ in sorted(ioc_freq.items(), key=lambda x: -x[1])[:MAX_IOCS]
        )

        nodes    = []
        edges    = []
        seen_ttp = {}
        seen_ioc = {}

        for report in data:
            rname = report["file_name"]
            nodes.append({"id": rname, "label": rname, "type": "report"})

            # TTP edges
            for tid in get_ttps(report):
                if tid not in seen_ttp:
                    seen_ttp[tid] = get_ttp_name(report, tid)
                edges.append({"source": rname, "target": tid})

            # IOC edges
            for ioc_type, value in get_iocs(report):
                key = f"{ioc_type}:{value}"
                if key not in top_iocs:
                    continue
                if key not in seen_ioc:
                    seen_ioc[key] = value
                edges.append({"source": rname, "target": key})

        for tid, name in seen_ttp.items():
            nodes.append({"id": tid, "label": f"{tid}: {name}", "type": "ttp"})

        for key, label in seen_ioc.items():
            subtype = key.split(":", 1)[0]
            nodes.append({"id": key, "label": label, "type": "ioc", "subtype": subtype})

        return nodes, edges
