from contextlib import asynccontextmanager

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