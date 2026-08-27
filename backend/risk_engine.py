from typing import Any, Dict

from backend.schemas import Transaction


def calculate_risk(
    transaction: Transaction,
    ml_score: float | None = None,
) -> Dict[str, Any]:
    """
    Initial PAYSHIELD risk engine.

    Produces a deterministic risk score from transaction signals.
    P2's ML models will be integrated into this engine later.
    """

    score = 0.0
    explanations = []

    # 1. Transaction amount
    if transaction.amount >= 100000:
        score += 25
        explanations.append("Very high transaction amount")
    elif transaction.amount >= 50000:
        score += 15
        explanations.append("High transaction amount")
    elif transaction.amount >= 10000:
        score += 5
        explanations.append("Elevated transaction amount")

    # 2. Transaction velocity
    if transaction.velocity_1h >= 10:
        score += 25
        explanations.append("Very high transaction velocity")
    elif transaction.velocity_1h >= 5:
        score += 15
        explanations.append("High transaction velocity")
    elif transaction.velocity_1h >= 3:
        score += 5
        explanations.append("Elevated transaction velocity")

    # 3. Device risk
    if transaction.device_risk >= 0.8:
        score += 20
        explanations.append("High-risk device")
    elif transaction.device_risk >= 0.5:
        score += 10
        explanations.append("Suspicious device signal")

    # 4. IP risk
    if transaction.ip_risk >= 0.8:
        score += 15
        explanations.append("High-risk IP address")
    elif transaction.ip_risk >= 0.5:
        score += 8
        explanations.append("Suspicious IP signal")

    # 5. Country risk
    if transaction.country_risk >= 0.8:
        score += 15
        explanations.append("High-risk country signal")
    elif transaction.country_risk >= 0.5:
        score += 8
        explanations.append("Suspicious country signal")
    if ml_score is not None:
        score = combine_model_scores(score, ml_score)
    score = min(score, 100.0)

    # Decision thresholds
    if score >= 70:
        decision = "BLOCK"
    elif score >= 40:
        decision = "REVIEW"
    else:
        decision = "APPROVE"

    if not explanations:
        explanations.append("No significant risk signals detected")

    return {
        "risk_score": round(score, 2),
        "decision": decision,
        "explanation": explanations,
        "model_scores": {
            "rule_engine": round(score / 100.0, 4)
        },
        "signals": {
            "amount": transaction.amount,
            "velocity_1h": transaction.velocity_1h,
            "device_risk": transaction.device_risk,
            "ip_risk": transaction.ip_risk,
            "country_risk": transaction.country_risk,
        },
    }
def combine_model_scores(
    rule_score: float,
    ml_score: float | None = None,
) -> float:
    if ml_score is None:
        return round(rule_score, 2)

    combined = (0.4 * rule_score) + (0.6 * ml_score * 100)
    return round(min(combined, 100.0), 2)