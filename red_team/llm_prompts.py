import random

class AdaptiveMutator:
    """
    Implements the Adversarial Mutation Loop from Section 11 of the Blueprint.
    Inspects why a transaction was blocked and dynamically mutates payload parameters.
    """
    def __init__(self):
        pass

    def mutate_payload(self, blocked_txn: dict, block_reasons: list[str]) -> dict:
        mutated = blocked_txn.copy()
        mutated["transaction_id"] = f"MUT_{random.randint(100000, 999999)}"
        mutated["attack_family"] = "ADAPTIVE_MUTATION"

        reasons_text = " ".join(block_reasons).upper()

        # Mutation Strategy 1: Lower amount to evade high-value rules
        if "AMOUNT" in reasons_text or "DEVIATION" in reasons_text:
            mutated["amount"] = round(float(blocked_txn.get("amount", 80000.0)) * random.uniform(0.15, 0.35), 2)

        # Mutation Strategy 2: Increase delay to evade burst velocity
        if "VELOCITY" in reasons_text or "SECONDS" in reasons_text:
            mutated["seconds_since_prev"] = float(blocked_txn.get("seconds_since_prev", 5.0)) + random.uniform(700.0, 1800.0)

        # Mutation Strategy 3: Shift to domestic IP/location to evade geo blacklists
        if "GEO" in reasons_text or "COUNTRY" in reasons_text or "OFFSHORE" in reasons_text:
            mutated["country"] = "India"
            mutated["ip_address"] = f"103.{random.randint(10, 200)}.{random.randint(1, 250)}.{random.randint(1, 250)}"

        # Mutation Strategy 4: Spoof standard browser headers
        if "DEVICE" in reasons_text or "UNRECOGNIZED" in reasons_text or "TOR" in reasons_text:
            mutated["device_type"] = "Chrome_Desktop"

        return mutated