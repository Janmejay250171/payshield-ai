import random
import time
import pandas as pd
from blue_team.risk_engine import PayShieldRiskEngine
from red_team.attack_generator import RedTeamAttackGenerator

class PaymentSimulator:
    def __init__(self):
        self.risk_engine = PayShieldRiskEngine()
        self.red_team = RedTeamAttackGenerator()
        self.known_profiles = self.risk_engine.profiles
        self.metrics = {
            "total_processed": 0,
            "approved": 0,
            "reviewed": 0,
            "blocked": 0,
            "red_attacks_generated": 0,
            "red_attacks_blocked": 0,
            "resilience_score": 100.0
        }

    def generate_normal_txn(self) -> dict:
        # Sample an existing legitimate user from training profiles if available
        if not self.known_profiles.empty:
            sample_user = self.known_profiles.sample(1).iloc[0]
            user_id = sample_user["user_id"]
            avg_amt = float(sample_user["user_avg_amount"])
            std_amt = float(sample_user["user_std_amount"])
            country = sample_user["common_country"]
            device = sample_user["common_device"]
            amount = max(10.0, round(random.gauss(avg_amt, std_amt * 0.2), 2))
        else:
            user_id = f"USER_{random.randint(10, 50)}"
            amount = round(random.uniform(500.0, 2000.0), 2)
            country = "India"
            device = "Android"

        return {
            "transaction_id": f"TXN_{random.randint(1000000, 9999999)}",
            "user_id": user_id,
            "amount": amount,
            "transaction_type": "PAYMENT",
            "country": country,
            "device_type": device,
            "ip_address": f"49.36.{random.randint(1, 254)}.{random.randint(1, 254)}",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "seconds_since_prev": random.uniform(3600.0, 86400.0),
            "attack_family": "NONE"
        }

    def run_simulation_batch(self, count: int = 50, attack_ratio: float = 0.3) -> list[dict]:
        results = []
        for _ in range(count):
            is_attack = random.random() < attack_ratio
            if is_attack:
                txns = self.red_team.generate_attack()
                for t in txns:
                    self.metrics["red_attacks_generated"] += 1
                    res = self.risk_engine.score_transaction(t)
                    self._update_metrics(res, is_attack=True)
                    results.append({"transaction": t, "result": res})
            else:
                t = self.generate_normal_txn()
                res = self.risk_engine.score_transaction(t)
                self._update_metrics(res, is_attack=False)
                results.append({"transaction": t, "result": res})
        return results

    def _update_metrics(self, res: dict, is_attack: bool):
        self.metrics["total_processed"] += 1
        decision = res["decision"]
        if decision == "BLOCK":
            self.metrics["blocked"] += 1
            if is_attack:
                self.metrics["red_attacks_blocked"] += 1
        elif decision == "REVIEW":
            self.metrics["reviewed"] += 1
        else:
            self.metrics["approved"] += 1

        if self.metrics["red_attacks_generated"] > 0:
            catch_rate = self.metrics["red_attacks_blocked"] / self.metrics["red_attacks_generated"]
            self.metrics["resilience_score"] = round(catch_rate * 100.0, 2)