import os
import sys
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from blue_team.risk_engine import PayShieldRiskEngine
from simulator.engine import PaymentSimulator

app = FastAPI(title="PayShield AI Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

risk_engine = PayShieldRiskEngine(models_dir=os.path.join(ROOT_DIR, "models_saved"))
simulator = PaymentSimulator(models_dir=os.path.join(ROOT_DIR, "models_saved"))

# In-memory store for Transaction Investigation details
transaction_store: Dict[str, Any] = {}

class DetectRequest(BaseModel):
    transaction_id: str
    user_id: str
    amount: float
    transaction_type: str = "TRANSFER"
    country: str = "IN"
    device_type: str = "Android_Chrome"
    ip_address: str = "127.0.0.1"
    recipient_id: Optional[str] = None
    seconds_since_prev: float = 60.0

class SimulateRequest(BaseModel):
    count: int = 10
    attack_ratio: float = 0.3

@app.post("/api/detect")
def detect_transaction(payload: DetectRequest):
    result = risk_engine.score_transaction(payload.dict())
    transaction_store[result["transaction_id"]] = result
    return result

@app.post("/api/simulate")
def run_simulation(payload: SimulateRequest):
    results = simulator.run_simulation_batch(count=payload.count, attack_ratio=payload.attack_ratio)
    for r in results:
        t_id = r["transaction"]["transaction_id"]
        transaction_store[t_id] = r["result"]
    return {
        "status": "success",
        "processed_count": len(results),
        "current_metrics": simulator.get_telemetry()
    }

@app.get("/api/metrics")
def get_metrics():
    return simulator.get_telemetry()

@app.get("/api/adversarial-battle")
def get_adversarial_battle():
    telemetry = simulator.get_telemetry()
    attacks_gen = telemetry["red_attacks_generated"]
    attacks_blk = telemetry["red_attacks_blocked"]

    red_success_rate = round((attacks_gen - attacks_blk) / max(attacks_gen, 1), 4)
    blue_catch_rate = round(attacks_blk / max(attacks_gen, 1), 4)

    return {
        "red_attacks_generated": attacks_gen,
        "red_success_rate": red_success_rate,
        "blue_catch_rate": blue_catch_rate,
        "active_attack_families": simulator.red_team.attack_families
    }

@app.get("/api/transactions/{transaction_id}")
def get_transaction_by_id(transaction_id: str):
    if transaction_id in transaction_store:
        return transaction_store[transaction_id]

    # Deterministic fallback for ad-hoc transaction lookup in demo
    user_id = f"USER_{abs(hash(transaction_id)) % 20:04d}"
    device_id = "Device_Shared_Emulator"
    ip_addr = "185.220.101.5"
    recipient_id = "MULE_ACCOUNT_CENTRAL"

    scored = risk_engine.score_transaction({
        "transaction_id": transaction_id,
        "user_id": user_id,
        "amount": 95000.0,
        "transaction_type": "TRANSFER",
        "country": "Russia",
        "device_type": device_id,
        "ip_address": ip_addr,
        "recipient_id": recipient_id,
        "seconds_since_prev": 4.0
    })

    transaction_store[transaction_id] = scored
    return scored