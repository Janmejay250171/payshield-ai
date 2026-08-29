import networkx as nx

class GraphAnalyzer:
    def __init__(self):
        self.G = nx.Graph()

    def add_transaction(self, txn_id: str, user_id: str, device_id: str, ip_address: str, recipient_id: str = None):
        """
        Builds multi-entity relationships in the NetworkX graph.
        Entities: User, Device, IP, Recipient Node.
        """
        self.G.add_node(user_id, label=user_id, node_type="user")
        self.G.add_node(device_id, label=device_id, node_type="device")
        self.G.add_node(ip_address, label=ip_address, node_type="ip")

        self.G.add_edge(user_id, device_id, relation="USES_DEVICE")
        self.G.add_edge(user_id, ip_address, relation="USES_IP")

        if recipient_id:
            self.G.add_node(recipient_id, label=recipient_id, node_type="recipient")
            self.G.add_edge(user_id, recipient_id, relation="TRANSFERS_TO", txn_id=txn_id)

    def analyze_risk(self, user_id: str, device_id: str, ip_address: str, recipient_id: str = None) -> tuple[float, list[str]]:
        reasons = []
        score = 0.0

        if not self.G.has_node(device_id) or not self.G.has_node(ip_address):
            return 0.1, ["GRAPH: New entity node observed in network"]

        # 1. Device Sharing Ring Detection
        device_users = [n for n in self.G.neighbors(device_id) if self.G.nodes[n].get("node_type") == "user"]
        if len(device_users) > 5:
            score = max(score, 0.95)
            reasons.append(f"GRAPH_SYNTHETIC_RING: Device '{device_id}' is shared across {len(device_users)} distinct user accounts")
        elif len(device_users) > 2:
            score = max(score, 0.65)
            reasons.append(f"GRAPH_SHARED_DEVICE: Device shared by {len(device_users)} accounts")

        # 2. IP Botnet Clustering
        ip_users = [n for n in self.G.neighbors(ip_address) if self.G.nodes[n].get("node_type") == "user"]
        if len(ip_users) > 10:
            score = max(score, 0.90)
            reasons.append(f"GRAPH_IP_BOTNET: IP '{ip_address}' concentrated across {len(ip_users)} accounts")

        # 3. Smurfing / Central Fan-In Hub Detection
        if recipient_id and self.G.has_node(recipient_id):
            senders = [n for n in self.G.neighbors(recipient_id) if self.G.nodes[n].get("node_type") == "user"]
            if len(senders) >= 5:
                score = max(score, 0.85)
                reasons.append(f"GRAPH_SMURFING_HUB: Recipient node '{recipient_id}' is receiving aggregated funds from {len(senders)} separate accounts")

        return score, reasons

    def get_subgraph(self, user_id: str, depth: int = 1) -> dict:
        """
        Returns connected nodes and edges formatted for frontend visualization.
        """
        if not self.G.has_node(user_id):
            return {"nodes": [{"id": user_id, "label": user_id, "type": "user"}], "edges": []}

        # Extract ego network (neighbors up to depth)
        sub_nodes = set([user_id])
        frontier = [user_id]
        for _ in range(depth):
            next_frontier = []
            for n in frontier:
                neighbors = list(self.G.neighbors(n))
                sub_nodes.update(neighbors)
                next_frontier.extend(neighbors)
            frontier = next_frontier

        subgraph = self.G.subgraph(sub_nodes)

        nodes_data = [
            {
                "id": str(node),
                "label": str(subgraph.nodes[node].get("label", node)),
                "type": subgraph.nodes[node].get("node_type", "unknown")
            }
            for node in subgraph.nodes()
        ]

        edges_data = [
            {
                "source": str(u),
                "target": str(v),
                "relation": subgraph.edges[u, v].get("relation", "CONNECTED_TO")
            }
            for u, v in subgraph.edges()
        ]

        return {"nodes": nodes_data, "edges": edges_data}