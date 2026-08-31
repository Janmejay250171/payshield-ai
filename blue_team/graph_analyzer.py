import networkx as nx


class GraphAnalyzer:

    def __init__(self):
        self.G = nx.Graph()

    # =========================================================
    # ADD TRANSACTION TO GRAPH
    # =========================================================

    def add_transaction(
        self,
        txn_id: str,
        user_id: str,
        device_id: str,
        ip_address: str,
        recipient_id: str = None,
    ):

        # -----------------------------------------------------
        # USER NODE
        # -----------------------------------------------------

        self.G.add_node(
            user_id,
            node_type="user",
        )

        # -----------------------------------------------------
        # DEVICE NODE
        # -----------------------------------------------------

        if device_id:

            self.G.add_node(
                device_id,
                node_type="device",
            )

            self.G.add_edge(
                user_id,
                device_id,
                relation="USES_DEVICE",
            )

        # -----------------------------------------------------
        # IP NODE
        # -----------------------------------------------------

        if ip_address:

            self.G.add_node(
                ip_address,
                node_type="ip",
            )

            self.G.add_edge(
                user_id,
                ip_address,
                relation="USES_IP",
            )

        # -----------------------------------------------------
        # RECIPIENT NODE
        # -----------------------------------------------------

        if recipient_id:

            self.G.add_node(
                recipient_id,
                node_type="recipient",
            )

            self.G.add_edge(
                user_id,
                recipient_id,
                relation="TRANSFERS_TO",
                txn_id=txn_id,
            )

    # =========================================================
    # ANALYZE GRAPH RISK
    # =========================================================

    def analyze_risk(
        self,
        user_id: str,
        device_id: str,
        ip_address: str,
        recipient_id: str = None,
    ) -> tuple[float, list[str]]:

        reasons = []
        score = 0.0

        # =====================================================
        # 1. DEVICE SHARING / SYNTHETIC IDENTITY
        # =====================================================

        if device_id and self.G.has_node(device_id):

            device_users = [

                node

                for node in self.G.neighbors(device_id)

                if self.G.nodes[node].get(
                    "node_type"
                ) == "user"

            ]

            user_count = len(
                set(device_users)
            )

            # Extreme device-sharing ring

            if user_count >= 6:

                score = max(
                    score,
                    0.95,
                )

                reasons.append(

                    "GRAPH_SYNTHETIC_RING: "

                    f"Device '{device_id}' "

                    f"is shared across "

                    f"{user_count} distinct accounts"

                )

            # Suspicious device sharing

            elif user_count >= 3:

                score = max(
                    score,
                    0.65,
                )

                reasons.append(

                    "GRAPH_SHARED_DEVICE: "

                    f"Device '{device_id}' "

                    f"is shared across "

                    f"{user_count} accounts"

                )

        # =====================================================
        # 2. IP BOTNET DETECTION
        # =====================================================

        if ip_address and self.G.has_node(ip_address):

            ip_users = [

                node

                for node in self.G.neighbors(ip_address)

                if self.G.nodes[node].get(
                    "node_type"
                ) == "user"

            ]

            user_count = len(
                set(ip_users)
            )

            if user_count >= 10:

                score = max(
                    score,
                    0.90,
                )

                reasons.append(

                    "GRAPH_IP_BOTNET: "

                    f"IP '{ip_address}' "

                    f"is used by "

                    f"{user_count} distinct accounts"

                )

        # =====================================================
        # 3. SMURFING / MONEY MULE FAN-IN DETECTION
        # =====================================================

        if (
            recipient_id
            and self.G.has_node(
                recipient_id
            )
        ):

            senders = [

                node

                for node in self.G.neighbors(
                    recipient_id
                )

                if self.G.nodes[node].get(
                    "node_type"
                ) == "user"

            ]

            sender_count = len(
                set(senders)
            )

            # -------------------------------------------------
            # CONFIRMED SMURFING PATTERN
            # -------------------------------------------------

            if sender_count >= 6:

                score = max(
                    score,
                    0.95,
                )

                reasons.append(

                    "GRAPH_SMURFING_CONFIRMED: "

                    f"Recipient '{recipient_id}' "

                    f"received funds from "

                    f"{sender_count} distinct accounts"

                )

            # -------------------------------------------------
            # STRONG SMURFING SIGNAL
            # -------------------------------------------------

            elif sender_count >= 5:

                score = max(
                    score,
                    0.88,
                )

                reasons.append(

                    "GRAPH_SMURFING_HUB: "

                    f"Recipient '{recipient_id}' "

                    f"is receiving funds from "

                    f"{sender_count} separate accounts"

                )

            # -------------------------------------------------
            # EARLY WARNING
            # -------------------------------------------------

            elif sender_count >= 3:

                score = max(
                    score,
                    0.55,
                )

                reasons.append(

                    "GRAPH_SUSPICIOUS_FAN_IN: "

                    f"Recipient '{recipient_id}' "

                    f"has {sender_count} distinct senders"

                )

        # =====================================================
        # DEFAULT GRAPH SCORE
        # =====================================================

        if score == 0.0:

            score = 0.05

        return score, reasons

    # =========================================================
    # OPTIONAL GRAPH RESET
    # =========================================================

    def reset(self):

        self.G.clear()