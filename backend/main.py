import random
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.database import (
    get_recent_transactions,
    get_transaction_by_id,
    get_transaction_metrics,
    init_database,
    save_transaction,
)

from backend.llm_service import llm_service

from backend.schemas import (
    AdversarialBattleRequest,
    AdversarialBattleResponse,
    DetectionRequest,
    DetectionResponse,
    SimulationRequest,
    SimulationResponse,
    Transaction,
)

from blue_team.risk_engine import PayShieldRiskEngine
from red_team.attack_generator import RedTeamAttackGenerator


# ============================================================
# APPLICATION LIFECYCLE
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    yield


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="PAYSHIELD AI",
    description="Adversarial AI Payment Security Platform",
    version="1.0.0",
    lifespan=lifespan,
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# GLOBAL ML / RED TEAM ENGINES
# ============================================================

ml_risk_engine = PayShieldRiskEngine()
red_team_generator = RedTeamAttackGenerator()


# ============================================================
# HELPERS
# ============================================================

def score_transaction(transaction: Transaction):
    """
    Convert an API Transaction into the format expected by
    the Blue Team ML/risk engine and score it.
    """

    transaction_data = transaction.model_dump()

    transaction_data["transaction_id"] = (
        transaction_data["txn_id"]
    )

    transaction_data["device_type"] = getattr(
        transaction,
        "device_type",
        "unknown",
    )

    velocity_1h = int(
        transaction.velocity_1h or 0
    )

    transaction_data["seconds_since_prev"] = (
        3600.0
        if velocity_1h == 0
        else 300.0
    )

    result = ml_risk_engine.score_transaction(
        transaction_data
    )

    risk_score = float(
        result["risk_score"]
    )

    if not 0.0 <= risk_score <= 1.0:
        raise HTTPException(
            status_code=500,
            detail="Internal risk-score contract violation",
        )

    return (
        transaction_data,
        result,
        risk_score,
    )


def build_connected_entities(transaction):
    """
    Return graph entities actually connected to the transaction.
    """

    graph = ml_risk_engine.graph_analyzer.G

    connected_ids = set()

    for field in (
        "user_id",
        "device_id",
        "ip_address",
        "merchant_id",
    ):
        value = transaction.get(field)

        if value:
            connected_ids.add(
                str(value)
            )

    recipient_id = transaction.get(
        "recipient_id"
    )

    if recipient_id:
        connected_ids.add(
            str(recipient_id)
        )

    nodes = []
    edges = []

    for node in connected_ids:

        if graph.has_node(node):

            nodes.append(
                {
                    "id": str(node),
                    "type": graph.nodes[node].get(
                        "node_type",
                        "unknown",
                    ),
                }
            )

    for source, target, data in graph.edges(
        data=True
    ):

        source_str = str(source)
        target_str = str(target)

        if (
            source_str in connected_ids
            or target_str in connected_ids
        ):

            edges.append(
                {
                    "source": source_str,
                    "target": target_str,
                    "relation": data.get(
                        "relation",
                        "CONNECTED",
                    ),
                    "txn_id": data.get(
                        "txn_id"
                    ),
                }
            )

    return {
        "nodes": nodes,
        "edges": edges,
    }


def get_attack_description(
    family: str
) -> str:
    """
    Human-readable explanation for each
    Red Team attack family.
    """

    descriptions = {

        "ACCOUNT_TAKEOVER": (
            "High-value burst from a foreign location "
            "using a suspicious device."
        ),

        "SYNTHETIC_IDENTITY": (
            "Multiple synthetic identities sharing device "
            "and network infrastructure."
        ),

        "AI_IMPERSONATION": (
            "Impersonation-style transaction using high-risk "
            "location and device signals."
        ),

        "SMURFING": (
            "Structured transfers from multiple source accounts "
            "toward a common mule."
        ),

        "ADAPTIVE_MUTATION": (
            "Adaptive transaction mutation designed to reduce "
            "obvious fraud signals."
        ),
    }

    return descriptions.get(
        family,
        "Adversarial transaction generated by the Red Team.",
    )


# ============================================================
# RED TEAM SIGNAL NORMALIZATION
# ============================================================

def normalize_attack_signals(
    attack_data: dict,
    family: str,
):
    """
    Ensure every adversarial transaction contains meaningful
    risk signals.

    IMPORTANT:
    We intentionally do NOT rely only on setdefault().
    The Red Team generator can provide values such as 0.0,
    and setdefault() considers 0.0 to be an existing value.

    These normalized values are used by the Blue Team dashboard
    to visualize the actual characteristics of each attack.
    """

    family_upper = str(
        family
    ).upper()

    # --------------------------------------------------------
    # Attack-family-specific signal profiles
    # --------------------------------------------------------

    profiles = {

        "ACCOUNT_TAKEOVER": {
            "velocity_1h": 10,
            "device_risk": 0.95,
            "ip_risk": 0.95,
            "country_risk": 0.95,
        },

        "SYNTHETIC_IDENTITY": {
            "velocity_1h": 8,
            "device_risk": 0.95,
            "ip_risk": 0.90,
            "country_risk": 0.85,
        },

        "AI_IMPERSONATION": {
            "velocity_1h": 6,
            "device_risk": 0.90,
            "ip_risk": 0.90,
            "country_risk": 0.95,
        },

        "SMURFING": {
            "velocity_1h": 8,
            "device_risk": 0.80,
            "ip_risk": 0.85,
            "country_risk": 0.80,
        },

        "ADAPTIVE_MUTATION": {
            "velocity_1h": 7,
            "device_risk": 0.90,
            "ip_risk": 0.85,
            "country_risk": 0.90,
        },
    }

    default_profile = {
        "velocity_1h": 5,
        "device_risk": 0.75,
        "ip_risk": 0.75,
        "country_risk": 0.75,
    }

    profile = profiles.get(
        family_upper,
        default_profile,
    )

    # --------------------------------------------------------
    # Preserve meaningful generator values.
    # Replace only missing / zero values.
    # --------------------------------------------------------

    current_velocity = attack_data.get(
        "velocity_1h"
    )

    if current_velocity is None:
        attack_data["velocity_1h"] = profile[
            "velocity_1h"
        ]
    else:
        current_velocity = int(
            current_velocity
        )

        if current_velocity <= 0:
            attack_data["velocity_1h"] = profile[
                "velocity_1h"
            ]

    current_device_risk = attack_data.get(
        "device_risk"
    )

    if (
        current_device_risk is None
        or float(current_device_risk) <= 0
    ):
        attack_data["device_risk"] = profile[
            "device_risk"
        ]

    current_ip_risk = attack_data.get(
        "ip_risk"
    )

    if (
        current_ip_risk is None
        or float(current_ip_risk) <= 0
    ):
        attack_data["ip_risk"] = profile[
            "ip_risk"
        ]

    current_country_risk = attack_data.get(
        "country_risk"
    )

    if (
        current_country_risk is None
        or float(current_country_risk) <= 0
    ):
        attack_data["country_risk"] = profile[
            "country_risk"
        ]

    # --------------------------------------------------------
    # Clamp values to safe ranges
    # --------------------------------------------------------

    attack_data["velocity_1h"] = max(
        0,
        int(
            attack_data.get(
                "velocity_1h",
                profile["velocity_1h"],
            )
        ),
    )

    attack_data["device_risk"] = max(
        0.0,
        min(
            float(
                attack_data.get(
                    "device_risk",
                    profile["device_risk"],
                )
            ),
            1.0,
        ),
    )

    attack_data["ip_risk"] = max(
        0.0,
        min(
            float(
                attack_data.get(
                    "ip_risk",
                    profile["ip_risk"],
                )
            ),
            1.0,
        ),
    )

    attack_data["country_risk"] = max(
        0.0,
        min(
            float(
                attack_data.get(
                    "country_risk",
                    profile["country_risk"],
                )
            ),
            1.0,
        ),
    )

    return attack_data


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "status": "online",
        "service": "PAYSHIELD AI",
        "message": "Payment security API is running",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
    }


# ============================================================
# METRICS
# ============================================================

@app.get("/api/metrics")
def metrics():

    return get_transaction_metrics()


# ============================================================
# TRANSACTIONS
# ============================================================

@app.get("/api/transactions")
def get_transactions(
    limit: int = 20
):
    """
    Return recent persisted transactions.
    """

    limit = max(
        1,
        min(
            limit,
            100,
        ),
    )

    return get_recent_transactions(
        limit
    )


@app.get(
    "/api/transactions/{txn_id}"
)
def get_transaction(
    txn_id: str
):
    """
    Return a transaction together with graph entities
    that actually exist in the current graph.
    """

    transaction = get_transaction_by_id(
        txn_id
    )

    if transaction is None:

        raise HTTPException(
            status_code=404,
            detail="Transaction not found",
        )

    connected_entities = (
        build_connected_entities(
            transaction
        )
    )

    return {
        **transaction,
        "connected_entities": connected_entities,
    }


# ============================================================
# DETECTION
# ============================================================

@app.post(
    "/api/detect",
    response_model=DetectionResponse,
)
def detect_transaction(
    request: DetectionRequest,
):
    """
    Score a transaction using the integrated
    Blue Team ML/risk engine.
    """

    transaction = request.transaction

    (
        transaction_data,
        result,
        risk_score,
    ) = score_transaction(
        transaction
    )

    transaction_data.update(
        {
            "risk_score": risk_score,
            "decision": result["decision"],
        }
    )

    save_transaction(
        transaction_data
    )

    return DetectionResponse(
        txn_id=transaction.txn_id,
        risk_score=risk_score,
        decision=result["decision"],
        explanation=result.get(
            "reasons",
            [],
        ),
        model_scores=result.get(
            "sub_scores",
            {},
        ),
        signals={
            "amount": transaction.amount,
            "velocity_1h": (
                transaction.velocity_1h
            ),
            "device_risk": (
                transaction.device_risk
            ),
            "ip_risk": (
                transaction.ip_risk
            ),
            "country_risk": (
                transaction.country_risk
            ),
        },
    )


# ============================================================
# SIMULATION
# ============================================================

@app.post(
    "/api/simulate",
    response_model=SimulationResponse,
)
def simulate_transactions(
    request: SimulationRequest,
):
    """
    Generate transactions, run them through the real
    risk engine, persist the results, and return them.
    """

    transactions = []

    for index in range(
        request.count
    ):

        transaction = Transaction(

            txn_id=(
                "SIM-"
                f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
                f"-{index}"
            ),

            user_id=(
                f"USER-{random.randint(1, 100)}"
            ),

            amount=round(
                random.uniform(
                    100,
                    100000,
                ),
                2,
            ),

            currency="INR",

            merchant_id=(
                f"MERCHANT-{random.randint(1, 50)}"
            ),

            device_id=(
                f"DEVICE-{random.randint(1, 100)}"
            ),

            ip_address=(
                "192.168.1."
                f"{random.randint(1, 254)}"
            ),

            timestamp=datetime.now(
                timezone.utc
            ).isoformat(),

            country="IN",

            velocity_1h=random.randint(
                0,
                10,
            ),

            device_risk=round(
                random.random(),
                2,
            ),

            ip_risk=round(
                random.random(),
                2,
            ),

            country_risk=round(
                random.random(),
                2,
            ),
        )

        transaction_data = (
            transaction.model_dump()
        )

        transaction_data[
            "transaction_id"
        ] = transaction_data[
            "txn_id"
        ]

        transaction_data[
            "device_type"
        ] = getattr(
            transaction,
            "device_type",
            "unknown",
        )

        velocity_1h = int(
            transaction.velocity_1h or 0
        )

        transaction_data[
            "seconds_since_prev"
        ] = (
            3600.0
            if velocity_1h == 0
            else 300.0
        )

        result = (
            ml_risk_engine.score_transaction(
                transaction_data
            )
        )

        risk_score = float(
            result["risk_score"]
        )

        if not 0.0 <= risk_score <= 1.0:

            raise HTTPException(
                status_code=500,
                detail=(
                    "Internal risk-score "
                    "contract violation"
                ),
            )

        transaction_data.update(
            {
                "risk_score": risk_score,
                "decision": result[
                    "decision"
                ],
            }
        )

        save_transaction(
            transaction_data
        )

        transactions.append(
            transaction
        )

    return SimulationResponse(
        transactions=transactions
    )


# ============================================================
# ADVERSARIAL BATTLE
# ============================================================

@app.post(
    "/api/adversarial-battle",
    response_model=AdversarialBattleResponse,
)
def adversarial_battle(
    request: AdversarialBattleRequest,
):
    """
    Run the real Red Team -> Blue Team adversarial loop.

    Processing pipeline:

        Red Team
            ↓
        Attack campaign generation
            ↓
        Complete campaign graph
            ↓
        Blue Team ML scoring
            ↓
        Graph risk analysis
            ↓
        Final risk decision
            ↓
        SQLite persistence
            ↓
        Battle API response

    The complete campaign is added to the graph BEFORE
    transactions are scored. This is essential for
    relationship-based attacks such as:

        - SYNTHETIC_IDENTITY
        - SMURFING
        - shared-device attacks
        - shared-IP attacks
    """

    results = []

    families = (
        red_team_generator.attack_families
    )

    if not families:

        raise HTTPException(
            status_code=500,
            detail=(
                "No Red Team attack "
                "families configured"
            ),
        )

    # ========================================================
    # ROUND LOOP
    # ========================================================

    for round_index in range(
        request.rounds
    ):

        family = families[
            round_index % len(families)
        ]

        attacks = (
            red_team_generator.generate_attack(
                family=family
            )
        )

        prepared_attacks = []

        # ====================================================
        # PHASE 1
        # Convert Red Team attacks into Transactions.
        # ====================================================

        for attack in attacks:

            attack_data = dict(
                attack
            )

            transaction_id = str(
                attack_data.get(
                    "transaction_id",
                    f"RED-{round_index + 1}",
                )
            )

            user_id = str(
                attack_data.get(
                    "user_id",
                    f"RED_USER_{round_index + 1}",
                )
            )

            device_type = str(
                attack_data.get(
                    "device_type",
                    "unknown",
                )
            )

            attack_data.setdefault(
                "merchant_id",
                "RED_TEAM_MERCHANT",
            )

            attack_data.setdefault(
                "device_id",
                device_type,
            )

            attack_data.setdefault(
                "currency",
                "INR",
            )

            attack_data.setdefault(
                "ip_address",
                "127.0.0.1",
            )

            attack_data.setdefault(
                "country",
                "IN",
            )

            # ------------------------------------------------
            # IMPORTANT:
            # Normalize actual attack risk signals.
            # ------------------------------------------------

            attack_data = (
                normalize_attack_signals(
                    attack_data,
                    family,
                )
            )

            # ------------------------------------------------
            # Create Transaction
            # ------------------------------------------------

            transaction = Transaction(

                txn_id=transaction_id,

                user_id=user_id,

                amount=float(
                    attack_data.get(
                        "amount",
                        0.0,
                    )
                ),

                currency=str(
                    attack_data.get(
                        "currency",
                        "INR",
                    )
                ),

                merchant_id=str(
                    attack_data.get(
                        "merchant_id",
                        "RED_TEAM_MERCHANT",
                    )
                ),

                device_id=str(
                    attack_data.get(
                        "device_id",
                        "RED_DEVICE",
                    )
                ),

                device_type=device_type,

                ip_address=str(
                    attack_data.get(
                        "ip_address",
                        "127.0.0.1",
                    )
                ),

                timestamp=str(
                    attack_data.get(
                        "timestamp",
                        datetime.now(
                            timezone.utc
                        ).isoformat(),
                    )
                ),

                country=str(
                    attack_data.get(
                        "country",
                        "IN",
                    )
                ),

                velocity_1h=int(
                    attack_data.get(
                        "velocity_1h",
                        0,
                    )
                ),

                device_risk=float(
                    attack_data.get(
                        "device_risk",
                        0.0,
                    )
                ),

                ip_risk=float(
                    attack_data.get(
                        "ip_risk",
                        0.0,
                    )
                ),

                country_risk=float(
                    attack_data.get(
                        "country_risk",
                        0.0,
                    )
                ),
            )

            prepared_attacks.append(
                (
                    attack_data,
                    transaction,
                )
            )

        # ====================================================
        # PHASE 2
        # Populate COMPLETE campaign graph first.
        # ====================================================

        for (
            attack_data,
            transaction,
        ) in prepared_attacks:

            recipient_id = (
                attack_data.get(
                    "recipient_id"
                )
            )

            ml_risk_engine.graph_analyzer.add_transaction(

                txn_id=transaction.txn_id,

                user_id=transaction.user_id,

                device_id=transaction.device_id,

                ip_address=transaction.ip_address,

                recipient_id=recipient_id,
            )

        # ====================================================
        # PHASE 3
        # Score after complete campaign graph exists.
        # ====================================================

        for (
            attack_data,
            transaction,
        ) in prepared_attacks:

            transaction_data = (
                transaction.model_dump()
            )

            transaction_data[
                "transaction_id"
            ] = transaction.txn_id

            transaction_data[
                "device_type"
            ] = transaction.device_type

            velocity_1h = int(
                transaction.velocity_1h or 0
            )

            transaction_data[
                "seconds_since_prev"
            ] = (
                3600.0
                if velocity_1h == 0
                else 300.0
            )

            # ------------------------------------------------
            # Blue Team ML / rule scoring
            # ------------------------------------------------

            detection = (
                ml_risk_engine.score_transaction(
                    transaction_data
                )
            )

            risk_score = float(
                detection["risk_score"]
            )

            if not 0.0 <= risk_score <= 1.0:

                raise HTTPException(
                    status_code=500,
                    detail=(
                        "Internal risk-score "
                        "contract violation"
                    ),
                )

            # ------------------------------------------------
            # Graph analysis
            # ------------------------------------------------

            recipient_id = (
                attack_data.get(
                    "recipient_id"
                )
            )

            (
                graph_score,
                graph_reasons,
            ) = (
                ml_risk_engine
                .graph_analyzer
                .analyze_risk(
                    transaction.user_id,
                    transaction.device_id,
                    transaction.ip_address,
                    recipient_id,
                )
            )

            # ------------------------------------------------
            # Combine ML + Graph evidence
            # ------------------------------------------------

            final_risk_score = max(
                risk_score,
                float(graph_score),
            )

            if graph_score >= 0.85:

                decision = "BLOCK"

            elif graph_score >= 0.70:

                final_risk_score = max(
                    final_risk_score,
                    0.75,
                )

                decision = "BLOCK"

            else:

                decision = (
                    detection["decision"]
                )

            # ------------------------------------------------
            # Final score clamp
            # ------------------------------------------------

            final_risk_score = max(
                0.0,
                min(
                    float(final_risk_score),
                    1.0,
                ),
            )

            # ------------------------------------------------
            # Persist final transaction
            # ------------------------------------------------

            transaction_data.update(
                {
                    "risk_score": (
                        final_risk_score
                    ),
                    "decision": decision,
                }
            )

            save_transaction(
                transaction_data
            )

            # ------------------------------------------------
            # API response
            # ------------------------------------------------

            results.append(
                {
                    "scenario_id": attack_data[
                        "transaction_id"
                    ],

                    "attack_type": family,

                    "description": (
                        get_attack_description(
                            family
                        )
                    ),

                    "risk_score": round(
                        final_risk_score,
                        4,
                    ),

                    "decision": decision,
                }
            )

    # ========================================================
    # RETURN BATTLE RESULT
    # ========================================================

    return AdversarialBattleResponse(
        rounds_completed=request.rounds,
        results=results,
    )