import random
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI

from backend.database import (
    get_transaction_metrics,
    init_database,
    save_transaction,
)
from backend.risk_engine import calculate_risk
from backend.schemas import (
    DetectionRequest,
    DetectionResponse,
    SimulationRequest,
    SimulationResponse,
    Transaction,
)



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


@app.post("/api/simulate", response_model=SimulationResponse)
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