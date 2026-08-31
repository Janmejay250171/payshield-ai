import os
import sys
import random
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.database import (
    get_recent_transactions,
    get_transaction_by_id,
    get_transaction_metrics,
    init_database,
    save_transaction,
)
from blue_team.risk_engine import PayShieldRiskEngine
from backend.schemas import (
    AdversarialBattleRequest,
    AdversarialBattleResponse,
    DetectionRequest,
    DetectionResponse,
    SimulationRequest,
    SimulationResponse,
    Transaction,
)
from backend.llm_service import llm_service
from simulator.engine import PaymentSimulator

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    yield

app = FastAPI(
    title="PAYSHIELD AI",
    description="Adversarial AI Payment Security Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

risk_engine = PayShieldRiskEngine(models_dir=os.path.join(ROOT_DIR, "models_saved"))
simulator = PaymentSimulator()

# In-memory store for Transaction Investigation details
transaction_store: Dict[str, Any] = {}

class SimulateRequest(BaseModel):
    count: int = Field(default=50, example=50)
    attack_ratio: float = Field(default=0.3, example=0.3)

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "PAYSHIELD AI",
        "message": "Payment security API is running",
    }

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }

@app.post("/api/detect", response_model=DetectionResponse)
def detect_transaction(request: DetectionRequest):
    transaction = request.transaction
    transaction_data = transaction.model_dump()
    transaction_data["transaction_id"] = transaction_data["txn_id"]
    transaction_data["device_type"] = transaction.device_type
    transaction_data["seconds_since_prev"] = (
        3600 if transaction.velocity_1h == 0 else 300
    )

    result = risk_engine.score_transaction(transaction_data)

    transaction_data.update({
        "risk_score": result["risk_score"],
        "decision": result["decision"],
    })

    save_transaction(transaction_data)
    transaction_store[transaction.txn_id] = result

    return DetectionResponse(
        txn_id=transaction.txn_id,
        risk_score=result["risk_score"],
        decision=result["decision"],
        explanation=result.get("reasons", []),
        model_scores=result.get("sub_scores", {}),
        signals={
            "amount": transaction.amount,
            "velocity_1h": transaction.velocity_1h,
            "device_risk": transaction.device_risk,
            "ip_risk": transaction.ip_risk,
            "country_risk": transaction.country_risk,
        },
    )

@app.get("/api/metrics")
def metrics():
    db_metrics = get_transaction_metrics()
    sim_metrics = simulator.get_telemetry()
    return {**db_metrics, **sim_metrics}

@app.get("/api/transactions")
def get_transactions(limit: int = 20):
    limit = max(1, min(limit, 100))
    return get_recent_transactions(limit)

@app.get("/api/transactions/{txn_id}")
def get_transaction(txn_id: str):
    if txn_id in transaction_store:
        return transaction_store[txn_id]
        
    transaction = get_transaction_by_id(txn_id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

@app.post("/api/simulate", response_model=SimulationResponse)
def simulate_transactions(request: SimulationRequest):
    transactions = []
    for index in range(request.count):
        transaction = Transaction(
            txn_id=f"SIM-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{index}",
            user_id=f"USER-{random.randint(1, 100)}",
            amount=round(random.uniform(100, 100000), 2),
            currency="INR",
            merchant_id=f"MERCHANT-{random.randint(1, 50)}",
            device_id=f"DEVICE-{random.randint(1, 100)}",
            ip_address=f"192.168.1.{random.randint(1, 254)}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            country="IN",
            velocity_1h=random.randint(0, 10),
            device_risk=round(random.random(), 2),
            ip_risk=round(random.random(), 2),
            country_risk=round(random.random(), 2),
        )

        transaction_data = transaction.model_dump()
        transaction_data["transaction_id"] = transaction_data["txn_id"]

        result = risk_engine.score_transaction(transaction_data)
        transaction_data.update({
            "risk_score": result["risk_score"],
            "decision": result["decision"],
        })

        save_transaction(transaction_data)
        transaction_store[transaction.txn_id] = result
        transactions.append(transaction)

    return SimulationResponse(transactions=transactions)

@app.post("/api/adversarial-battle", response_model=AdversarialBattleResponse)
def adversarial_battle(request: AdversarialBattleRequest):
    transaction = Transaction(
        txn_id="BATTLE-BASE-001",
        user_id="USER-BATTLE",
        amount=50000,
        currency="INR",
        merchant_id="MERCHANT-BATTLE",
        device_id="DEVICE-BATTLE",
        ip_address="192.168.1.100",
        timestamp=datetime.now(timezone.utc).isoformat(),
        country="IN",
        velocity_1h=2,
        device_risk=0.2,
        ip_risk=0.2,
        country_risk=0.1,
    )

    scenarios = llm_service.generate_attack_scenarios(
        transaction.model_dump(),
        request.rounds,
    )

    results = []
    for scenario in scenarios:
        modified_transaction = transaction.model_copy(
            update={
                "amount": scenario["modified_amount"],
                "velocity_1h": scenario["modified_velocity_1h"],
            }
        )

        transaction_data = modified_transaction.model_dump()
        transaction_data["transaction_id"] = transaction_data["txn_id"]

        detection = risk_engine.score_transaction(transaction_data)

        results.append({
            "scenario_id": scenario["scenario_id"],
            "attack_type": scenario["type"],
            "description": scenario["description"],
            "risk_score": detection["risk_score"],
            "decision": detection["decision"],
        })

    return AdversarialBattleResponse(
        rounds_completed=len(results),
        results=results,
    )

@app.get("/api/adversarial-battle-stats")
def get_adversarial_battle_stats():
    telemetry = simulator.get_telemetry()
    attacks_gen = telemetry.get("red_attacks_generated", 0)
    attacks_blk = telemetry.get("red_attacks_blocked", 0)

    red_success_rate = round((attacks_gen - attacks_blk) / max(attacks_gen, 1), 4)
    blue_catch_rate = round(attacks_blk / max(attacks_gen, 1), 4)

    return {
        "red_attacks_generated": attacks_gen,
        "red_success_rate": red_success_rate,
        "blue_catch_rate": blue_catch_rate,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)