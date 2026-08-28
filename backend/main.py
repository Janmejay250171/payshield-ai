import random
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException

from backend.database import (
    get_recent_transactions,
    get_transaction_by_id,
    get_transaction_metrics,
    init_database,
    save_transaction,
)
from backend.risk_engine import calculate_risk
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

    result = calculate_risk(transaction)

    transaction_data = transaction.model_dump()
    transaction_data.update(
        {
            "risk_score": result["risk_score"],
            "decision": result["decision"],
        }
    )

    save_transaction(transaction_data)

    return DetectionResponse(
        txn_id=transaction.txn_id,
        risk_score=result["risk_score"],
        decision=result["decision"],
        explanation=result["explanation"],
        model_scores=result["model_scores"],
        signals=result["signals"],
    )


@app.get("/api/metrics")
def metrics():
    return get_transaction_metrics()

@app.get("/api/transactions")
def get_transactions(limit: int = 20):
    limit = max(1, min(limit, 100))
    return get_recent_transactions(limit)

@app.get("/api/transactions/{txn_id}")
def get_transaction(txn_id: str):
    transaction = get_transaction_by_id(txn_id)

    if transaction is None:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found",
        )

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

        result = calculate_risk(transaction)

        transaction_data = transaction.model_dump()
        transaction_data.update(
            {
                "risk_score": result["risk_score"],
                "decision": result["decision"],
            }
        )

        save_transaction(transaction_data)

        transactions.append(transaction)

    return SimulationResponse(transactions=transactions)
@app.post(
    "/api/adversarial-battle",
    response_model=AdversarialBattleResponse,
)
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

        detection = calculate_risk(modified_transaction)

        results.append(
            {
                "scenario_id": scenario["scenario_id"],
                "attack_type": scenario["type"],
                "description": scenario["description"],
                "risk_score": detection["risk_score"],
                "decision": detection["decision"],
            }
        )

    return AdversarialBattleResponse(
        rounds_completed=len(results),
        results=results,
    )