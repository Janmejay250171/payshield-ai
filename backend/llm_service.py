import os
from typing import Any, Dict, List


class LLMService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")

    def generate_attack_scenarios(
        self,
        transaction: Dict[str, Any],
        count: int = 3,
    ) -> List[Dict[str, Any]]:
        scenarios = []

        base_amount = float(transaction.get("amount", 0))
        base_velocity = int(transaction.get("velocity_1h", 0))

        for index in range(count):
            scenarios.append(
                {
                    "scenario_id": f"ATTACK-{index + 1}",
                    "type": "transaction_manipulation",
                    "description": (
                        "Simulated adversarial variation of transaction "
                        "signals for robustness testing."
                    ),
                    "modified_amount": round(
                        base_amount * (1 + 0.1 * (index + 1)), 2
                    ),
                    "modified_velocity_1h": base_velocity + index + 1,
                }
            )

        return scenarios


llm_service = LLMService()