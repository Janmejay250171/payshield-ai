import networkx as nx

class GraphAnalyzer:
    def __init__(self):
        self.G = nx.Graph()

    def add_transaction(self, txn_id: str, user_id: str, device_id: str, ip_address: str, recipient_id: str = None):
        """
        Builds multi-entity relationships in the NetworkX graph.
        Entities: User, Device, IP, Recipient Node.
        """
        self.G.add_node(user_id, node_type="user")
        self.G.add_node(device_id, node_type="device")
        self.G.add_node(ip_address, node_type="ip")

        self.G.add_edge(user_id, device_id, relation="USES_DEVICE")
        self.G.add_edge(user_id, ip_address, relation="USES_IP")

        if recipient_id:
            self.G.add_node(recipient_id, node_type="recipient")
            self.G.add_edge(user_id, recipient_id, relation="TRANSFERS_TO", txn_id=txn_id)

    def analyze_risk(self, user_id: str, device_id: str, ip_address: str, recipient_id: str = None) -> tuple[float, list[str]]:
        """
        Calculates graph centrality, degree anomalies, and shared entity rings.
        Returns (graph_risk_score [0.0 - 1.0], explanation_reasons).
        """
        reasons = []
        score = 0.0

        if not self.G.has_node(device_id) or not self.G.has_node(ip_address):
            return 0.1, ["GRAPH: New entity node observed in network"]

        # 1. Device Sharing Ring Detection (Synthetic ID ring)
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