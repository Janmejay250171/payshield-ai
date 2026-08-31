import os
import sys
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

<<<<<<< HEAD
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
simulator = PaymentSimulator()

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
=======
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="PayShield AI — Adaptive Adversarial Defense Lab",
    version="1.0.0",
    description="Mastercard Innovation Challenge @ GFF 2026 Core Engine"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory shared state for the simulation environment
sim = PaymentSimulator()
risk_engine = PayShieldRiskEngine()
red_team = RedTeamAttackGenerator()
>>>>>>> fdbe63f4ce5742024e4ca8e8f6b28f3ffbfa9353

class SimulateRequest(BaseModel):
<<<<<<< HEAD
    count: int = 10
    attack_ratio: float = 0.3
=======
    count: int = Field(default=50, example=50)
    attack_ratio: float = Field(default=0.3, example=0.3)

class TransactionPayload(BaseModel):
    transaction_id: str = Field(..., example="TXN_991823")
    user_id: str = Field(..., example="USER_0042")
    amount: float = Field(..., example=85000.0)
    transaction_type: str = Field(default="PAYMENT", example="TRANSFER")
    country: str = Field(default="India", example="Russia")
    device_type: str = Field(default="Android", example="Tor_Browser")
    ip_address: str = Field(default="127.0.0.1", example="185.220.101.5")
    recipient_id: Optional[str] = Field(default=None, example="MULE_CENTRAL")
    timestamp: Optional[str] = Field(default=None)
    seconds_since_prev: float = Field(default=86400.0, example=15.0)

class GenerateAttackRequest(BaseModel):
    family: str = Field(..., example="ACCOUNT_TAKEOVER")

# --- Blueprint Contract Endpoints (Section 12) ---

@app.post("/api/simulate")
def run_simulation(req: SimulateRequest):
    """Generates a batch of transactions and processes them through the defense pipeline."""
    batch = sim.run_simulation_batch(count=req.count, attack_ratio=req.attack_ratio)
    return {
        "status": "completed",
        "batch_processed": len(batch),
        "current_metrics": sim.metrics,
        "sample_results": batch[:5]
    }
>>>>>>> fdbe63f4ce5742024e4ca8e8f6b28f3ffbfa9353

@app.post("/api/generate-attacks")
def generate_attacks(req: GenerateAttackRequest):
    """Injects a specific attack family into the live simulation."""
    import time
    sim.metrics["last_attack_family"] = req.family
    sim.metrics["last_attack_time"] = time.time()
    
    txns = sim.red_team.generate_attack(family=req.family)
    results = []
    for t in txns:
        sim.metrics["red_attacks_generated"] += 1
        res = sim.risk_engine.score_transaction(t)
        sim._update_metrics(res, is_attack=True)
        results.append({"transaction": t, "result": res})
    return {
        "status": "completed",
        "attacks_injected": len(txns),
        "results": results
    }


@app.post("/api/detect")
def detect_transaction(payload: DetectRequest):
    result = risk_engine.score_transaction(payload.dict())
    t_id = payload.transaction_id; result["transaction_id"] = t_id; transaction_store[t_id] = result
    return result

@app.post("/api/simulate")
def run_simulation(payload: SimulateRequest):
    results = simulator.run_simulation_batch(count=payload.count, attack_ratio=payload.attack_ratio)
    for r in results:
        t_id = r["transaction"]["transaction_id"]
        transaction_store[t_id] = r.get("assessment", r.get("result", {}))
    return {
        "status": "success",
        "processed_count": len(results),
        "current_metrics": simulator.get_telemetry()
    }

@app.get("/api/metrics")
def get_metrics():
<<<<<<< HEAD
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
=======
    """Returns aggregated telemetry for the Command Center & Blue Team dashboards."""
    total = max(1, sim.metrics["total_processed"])
    return {
        "total_processed": sim.metrics["total_processed"],
        "approved": sim.metrics["approved"],
        "reviewed": sim.metrics["reviewed"],
        "blocked": sim.metrics["blocked"],
        "fpr": round(sim.metrics["reviewed"] / total, 4),
        "threat_level": "CRITICAL" if sim.metrics["blocked"] > 20 else "ELEVATED",
        "resilience_score": sim.metrics["resilience_score"],
        "feature_importance": [
            {"feature": "Device Age", "importance": 0.35},
            {"feature": "IP Velocity", "importance": 0.28},
            {"feature": "Card Country Match", "importance": 0.15},
            {"feature": "Txn Amount Diff", "importance": 0.12},
            {"feature": "Time of Day", "importance": 0.10}
        ],
        "active_rules": [
            {"id": "R-101", "name": "Velocity Threshold Breach", "status": "Active", "severity": "High"},
            {"id": "R-102", "name": "Known Bad IP Subnet", "status": "Active", "severity": "Critical"},
            {"id": "R-103", "name": "Impossible Travel", "status": "Active", "severity": "Medium"},
            {"id": "R-104", "name": "Device Fingerprint Mismatch", "status": "Active", "severity": "High"}
        ]
    }

@app.get("/api/adversarial-battle")
def get_adversarial_battle():
    """Returns the real-time tug-of-war stats for the live Red vs Blue battle view."""
    gen = sim.get_live_threat_load()
    catch_rate = sim.get_live_mitigation_rate()
    return {
        "red_attacks_generated": gen,
        "red_success_rate": round(max(0.0, 1.0 - catch_rate), 4),
        "blue_catch_rate": round(catch_rate, 4),
        "active_attack_families": red_team.attack_families
    }

@app.get("/api/transactions/{tx_id}")
def get_transaction(tx_id: str):
    """Deep dive investigation payload for a single transaction."""
    # Since there's no DB, we generate a deterministic-looking response for the frontend
    import random
    
    score = random.randint(85, 99)
    return {
        "id": tx_id,
        "amount": random.choice([45000.0, 12500.0, 99999.0]),
        "currency": "INR",
        "status": "BLOCKED",
        "merchant": {
            "name": "CryptoExchange_XYZ",
            "category": "High-Risk Finance"
        },
        "user": {
            "id": f"USER_{random.randint(1000, 9999)}",
            "ip_address": f"185.{random.randint(10, 255)}.101.{random.randint(1, 255)}"
        },
        "xgboost_score": score,
        "rules_triggered": [
            {"name": "Velocity_Spike_1H", "severity": "High"},
            {"name": "IP_Geolocation_Mismatch", "severity": "Critical"},
            {"name": "New_Device_High_Amount", "severity": "Medium"}
        ],
        "connected_entities": [
            {"entity_type": "Device_ID", "risk_weight": 40},
            {"entity_type": "Shared_IP", "risk_weight": 35},
            {"entity_type": "Previous_Fraud_Acct", "risk_weight": 25}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
>>>>>>> fdbe63f4ce5742024e4ca8e8f6b28f3ffbfa9353
