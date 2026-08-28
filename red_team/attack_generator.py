import random
from datetime import datetime

class RedTeamAttackGenerator:
    def __init__(self):
        self.attack_families = [
            "ACCOUNT_TAKEOVER",
            "SYNTHETIC_IDENTITY",
            "AI_IMPERSONATION",
            "SMURFING",
            "ADAPTIVE_MUTATION"
        ]

    def generate_attack(self, family: str = None, mutation_context: dict = None) -> list[dict]:
        if not family:
            family = random.choice(self.attack_families)

        txns = []
        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        if family == "ACCOUNT_TAKEOVER":
            # High amount burst from foreign country & unknown device
            user_id = f"USER_{random.randint(1, 100):04d}"
            for i in range(3):
                txns.append({
                    "transaction_id": f"ATO_{random.randint(100000, 999999)}",
                    "user_id": user_id,
                    "amount": round(random.uniform(75000, 120000), 2),
                    "transaction_type": "TRANSFER",
                    "country": "Russia",
                    "device_type": "Tor_Browser",
                    "ip_address": "185.220.101.5",
                    "timestamp": now_str,
                    "seconds_since_prev": 5.0,
                    "attack_family": "ACCOUNT_TAKEOVER"
                })

        elif family == "SYNTHETIC_IDENTITY":
            # Multiple synthetic users routing through 1 single device & IP
            shared_device = f"DEVICE_EMULATOR_{random.randint(10, 99)}"
            shared_ip = "192.168.4.101"
            for i in range(6):
                txns.append({
                    "transaction_id": f"SYNTH_{random.randint(100000, 999999)}",
                    "user_id": f"SYNTH_USER_{i:04d}",
                    "amount": round(random.uniform(15000, 35000), 2),
                    "transaction_type": "PAYMENT",
                    "country": "India",
                    "device_type": shared_device,
                    "ip_address": shared_ip,
                    "timestamp": now_str,
                    "seconds_since_prev": 60.0,
                    "attack_family": "SYNTHETIC_IDENTITY"
                })

        elif family == "SMURFING":
            # 6 accounts sending structured amounts to a single money mule
            collector = "MULE_ACCOUNT_CENTRAL"
            for i in range(6):
                txns.append({
                    "transaction_id": f"SMURF_{random.randint(100000, 999999)}",
                    "user_id": f"SMURF_SRC_{i:04d}",
                    "recipient_id": collector,
                    "amount": round(random.uniform(4900, 4999), 2),
                    "transaction_type": "TRANSFER",
                    "country": "India",
                    "device_type": f"Mobile_App_{i}",
                    "ip_address": f"10.0.0.{i+10}",
                    "timestamp": now_str,
                    "seconds_since_prev": 8.0,
                    "attack_family": "SMURFING"
                })

        elif family == "AI_IMPERSONATION":
            txns.append({
                "transaction_id": f"AI_IMP_{random.randint(100000, 999999)}",
                "user_id": f"USER_{random.randint(1, 100):04d}",
                "amount": round(random.uniform(45000, 85000), 2),
                "transaction_type": "TRANSFER",
                "country": "HighRisk_Offshore",
                "device_type": "Chrome_Mac",
                "ip_address": "45.33.32.156",
                "timestamp": now_str,
                "seconds_since_prev": 3600.0,
                "attack_family": "AI_IMPERSONATION"
            })

        elif family == "ADAPTIVE_MUTATION":
            base_amt = mutation_context.get("amount", 85000.0) if mutation_context else 85000.0
            mutated_amt = round(base_amt * 0.45, 2)
            txns.append({
                "transaction_id": f"ADAPT_{random.randint(100000, 999999)}",
                "user_id": f"USER_{random.randint(1, 100):04d}",
                "amount": mutated_amt,
                "transaction_type": "PAYMENT",
                "country": "India",
                "device_type": "Android",
                "ip_address": "103.21.244.2",
                "timestamp": now_str,
                "seconds_since_prev": 450.0,
                "attack_family": "ADAPTIVE_MUTATION"
            })

        return txns