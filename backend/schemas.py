from typing import Any, Dict, List

from pydantic import BaseModel, Field


class Transaction(BaseModel):
    txn_id: str
    user_id: str
    amount: float = Field(ge=0)
    currency: str = "INR"
    merchant_id: str
    device_id: str
    device_type: str = "mobile"
    ip_address: str
    timestamp: str
    country: str = "IN"

    velocity_1h: int = Field(default=0, ge=0)
    device_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    ip_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    country_risk: float = Field(default=0.0, ge=0.0, le=1.0)

class DetectionRequest(BaseModel):
    transaction: Transaction


class DetectionResponse(BaseModel):
    txn_id: str
    risk_score: float
    decision: str
    explanation: List[str]
    model_scores: Dict[str, float] = {}
    signals: Dict[str, Any] = {}


class SimulationRequest(BaseModel):
    count: int = Field(default=10, ge=1, le=1000)


class SimulationResponse(BaseModel):
    transactions: List[Transaction]


class MetricsResponse(BaseModel):
    total_transactions: int
    approved: int
    reviewed: int
    blocked: int
    average_risk_score: float


class AdversarialBattleRequest(BaseModel):
    rounds: int = Field(default=3, ge=1, le=20)


class AdversarialBattleResponse(BaseModel):
    rounds_completed: int
    results: List[Dict[str, Any]]