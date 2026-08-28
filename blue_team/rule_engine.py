class RuleEngine:
    def __init__(self):
        pass

    def evaluate(self, txn: dict, user_baseline: dict = None) -> tuple[float, list[str]]:
        """
        Evaluates deterministic heuristics.
        Returns (rule_risk_score [0.0 - 1.0], triggered_rules list).
        """
        triggered = []
        score = 0.0

        amount = float(txn.get("amount", 0.0))
        seconds_prev = float(txn.get("seconds_since_prev", 86400.0))

        # Rule 1: High absolute value threshold
        if amount > 100000.0:
            triggered.append("RULE_HIGH_AMOUNT: Transaction exceeds ₹100,000 threshold")
            score = max(score, 0.9)

        # Rule 2: Burst Velocity (less than 10 seconds)
        if seconds_prev < 10.0:
            triggered.append("RULE_BURST_VELOCITY: Consecutive transaction within 10 seconds")
            score = max(score, 0.85)

        # Rule 3: Extreme baseline deviation
        if user_baseline:
            avg_amt = user_baseline.get("user_avg_amount", amount)
            if avg_amt > 0 and (amount / avg_amt) > 10.0:
                triggered.append(f"RULE_EXTREME_DEVIATION: Amount {amount / avg_amt:.1f}x higher than user baseline")
                score = max(score, 0.8)

        # Rule 4: High-risk offshore jurisdiction flag
        if txn.get("country") in ["HighRisk_Offshore", "Unknown_Zone"]:
            triggered.append("RULE_SANCTIONED_GEO: High-risk offshore jurisdiction detected")
            score = max(score, 0.95)

        return score, triggered