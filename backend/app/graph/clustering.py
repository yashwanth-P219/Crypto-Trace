import networkx as nx
from typing import Dict, Any, List

class GraphClustering:
    @staticmethod
    def identify_clusters(graph: nx.MultiDiGraph) -> List[Dict[str, Any]]:
        """
        Identifies strongly connected components and community clusters in the graph.
        """
        undirected = graph.to_undirected()
        components = list(nx.connected_components(undirected))
        clusters = []

        for idx, comp in enumerate(components):
            nodes_in_comp = list(comp)
            total_vol = sum(graph.nodes[n].get("total_incoming", 0.0) for n in nodes_in_comp)
            vasp_count = sum(1 for n in nodes_in_comp if graph.nodes[n].get("entity_type") in ("VASP", "EXCHANGE"))

            clusters.append({
                "cluster_id": idx + 1,
                "node_count": len(nodes_in_comp),
                "nodes": nodes_in_comp[:10], # preview
                "total_volume": round(total_vol, 4),
                "vasp_touchpoints": vasp_count
            })

        clusters.sort(key=lambda c: c["total_volume"], reverse=True)
        return clusters
