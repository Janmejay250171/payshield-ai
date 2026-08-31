from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from simulator.engine import PaymentSimulator
from red_team.attack_generator import RedTeamAttackGenerator
from blue_team.risk_engine import PayShieldRiskEngine

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

# --- Pydantic API Models ---
class SimulateRequest(BaseModel):
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
def detect_transaction(txn: TransactionPayload):
    """Real-time transaction scoring against the 4-layer defense pipeline."""
    result = risk_engine.score_transaction(txn.dict())
    return result

@app.get("/api/metrics")
def get_metrics():
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