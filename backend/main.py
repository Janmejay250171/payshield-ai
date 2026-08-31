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

def score_transaction(
    transaction: Transaction,
    extra_data: dict = None,
):
    """
    Convert an API Transaction into the format expected by
    the Blue Team ML/risk engine and score it.

    extra_data is used for fields that may not be part of
    the Transaction Pydantic schema, such as recipient_id.
    """

    transaction_data = transaction.model_dump()

    transaction_data["transaction_id"] = (
        transaction.txn_id
    )

    transaction_data["device_type"] = (
        getattr(
            transaction,
            "device_type",
            "unknown",
        )
    )

    # --------------------------------------------------------
    # Preserve additional graph intelligence
    # --------------------------------------------------------

    if extra_data:

        recipient_id = extra_data.get(
            "recipient_id"
        )

        if recipient_id:

            transaction_data[
                "recipient_id"
            ] = str(
                recipient_id
            )

    # --------------------------------------------------------
    # Velocity timing
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Blue Team risk scoring
    # --------------------------------------------------------

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

    return (
        transaction_data,
        result,
        risk_score,
    )


def build_connected_entities(
    transaction: dict,
):
    """
    Return graph entities actually connected to
    the transaction.
    """

    graph = (
        ml_risk_engine
        .graph_analyzer
        .G
    )

    connected_ids = set()

    for field in (
        "user_id",
        "device_id",
        "ip_address",
        "merchant_id",
    ):

        value = transaction.get(
            field
        )

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

        if graph.has_node(
            node
        ):

            nodes.append(
                {
                    "id": str(node),
                    "type": graph.nodes[
                        node
                    ].get(
                        "node_type",
                        "unknown",
                    ),
                }
            )

    for (
        source,
        target,
        data,
    ) in graph.edges(
        data=True
    ):

        source_str = str(
            source
        )

        target_str = str(
            target
        )

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
    family: str,
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
        (
            "Adversarial transaction generated "
            "by the Red Team."
        ),
    )


# ============================================================
# RED TEAM SIGNAL NORMALIZATION
# ============================================================

def normalize_attack_signals(
    attack_data: dict,
    family: str,
):
    """
    Ensure every adversarial transaction contains
    meaningful risk signals.
    """

    family_upper = str(
        family
    ).upper()

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
    # VELOCITY
    # --------------------------------------------------------

    current_velocity = attack_data.get(
        "velocity_1h"
    )

    if current_velocity is None:

        attack_data[
            "velocity_1h"
        ] = profile[
            "velocity_1h"
        ]

    else:

        current_velocity = int(
            current_velocity
        )

        if current_velocity <= 0:

            attack_data[
                "velocity_1h"
            ] = profile[
                "velocity_1h"
            ]

    # --------------------------------------------------------
    # DEVICE RISK
    # --------------------------------------------------------

    current_device_risk = attack_data.get(
        "device_risk"
    )

    if (
        current_device_risk is None
        or float(
            current_device_risk
        ) <= 0
    ):

        attack_data[
            "device_risk"
        ] = profile[
            "device_risk"
        ]

    # --------------------------------------------------------
    # IP RISK
    # --------------------------------------------------------

    current_ip_risk = attack_data.get(
        "ip_risk"
    )

    if (
        current_ip_risk is None
        or float(
            current_ip_risk
        ) <= 0
    ):

        attack_data[
            "ip_risk"
        ] = profile[
            "ip_risk"
        ]

    # --------------------------------------------------------
    # COUNTRY RISK
    # --------------------------------------------------------

    current_country_risk = attack_data.get(
        "country_risk"
    )

    if (
        current_country_risk is None
        or float(
            current_country_risk
        ) <= 0
    ):

        attack_data[
            "country_risk"
        ] = profile[
            "country_risk"
        ]

    # --------------------------------------------------------
    # CLAMP VALUES
    # --------------------------------------------------------

    attack_data[
        "velocity_1h"
    ] = max(
        0,
        int(
            attack_data.get(
                "velocity_1h",
                profile[
                    "velocity_1h"
                ],
            )
        ),
    )

    attack_data[
        "device_risk"
    ] = max(
        0.0,
        min(
            float(
                attack_data.get(
                    "device_risk",
                    profile[
                        "device_risk"
                    ],
                )
            ),
            1.0,
        ),
    )

    attack_data[
        "ip_risk"
    ] = max(
        0.0,
        min(
            float(
                attack_data.get(
                    "ip_risk",
                    profile[
                        "ip_risk"
                    ],
                )
            ),
            1.0,
        ),
    )

    attack_data[
        "country_risk"
    ] = max(
        0.0,
        min(
            float(
                attack_data.get(
                    "country_risk",
                    profile[
                        "country_risk"
                    ],
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
        "message": (
            "Payment security API is running"
        ),
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
    limit: int = 20,
):

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
    txn_id: str,
):

    transaction = (
        get_transaction_by_id(
            txn_id
        )
    )

    if transaction is None:

        raise HTTPException(
            status_code=404,
            detail=(
                "Transaction not found"
            ),
        )

    connected_entities = (
        build_connected_entities(
            transaction
        )
    )

    return {
        **transaction,
        "connected_entities":
            connected_entities,
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

    transaction = (
        request.transaction
    )

    (
        transaction_data,
        result,
        risk_score,
    ) = score_transaction(
        transaction
    )

    transaction_data.update(
        {
            "risk_score":
                risk_score,

            "decision":
                result["decision"],
        }
    )

    save_transaction(
        transaction_data
    )

    return DetectionResponse(

        txn_id=transaction.txn_id,

        risk_score=risk_score,

        decision=result[
            "decision"
        ],

        explanation=result.get(
            "reasons",
            [],
        ),

        model_scores=result.get(
            "sub_scores",
            {},
        ),

        signals={

            "amount":
                transaction.amount,

            "velocity_1h":
                transaction.velocity_1h,

            "device_risk":
                transaction.device_risk,

            "ip_risk":
                transaction.ip_risk,

            "country_risk":
                transaction.country_risk,
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

        (
            transaction_data,
            result,
            risk_score,
        ) = score_transaction(
            transaction
        )

        transaction_data.update(
            {
                "risk_score":
                    risk_score,

                "decision":
                    result[
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
    Run the Red Team -> Blue Team
    adversarial detection pipeline.

    Pipeline:

        Red Team Attack Generation
                  ↓
        Complete Campaign Graph
                  ↓
        Blue Team Risk Engine
                  ↓
        Final Risk Decision
                  ↓
        Persistence
                  ↓
        API Response

    Complete graph population happens BEFORE
    scoring so graph-based attacks such as
    Smurfing and Synthetic Identity can be
    detected immediately.
    """

    results = []

    families = (
        red_team_generator
        .attack_families
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
            round_index
            % len(families)
        ]

        attacks = (
            red_team_generator
            .generate_attack(
                family=family
            )
        )

        prepared_attacks = []

        # ====================================================
        # PHASE 1
        # Prepare Transactions
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

            # -----------------------------------------------
            # Normalize risk signals
            # -----------------------------------------------

            attack_data = (
                normalize_attack_signals(
                    attack_data,
                    family,
                )
            )

            # -----------------------------------------------
            # Create API Transaction
            # -----------------------------------------------

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
        # BUILD COMPLETE CAMPAIGN GRAPH FIRST
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

                txn_id=(
                    transaction.txn_id
                ),

                user_id=(
                    transaction.user_id
                ),

                device_id=(
                    transaction.device_id
                ),

                ip_address=(
                    transaction.ip_address
                ),

                recipient_id=(
                    str(recipient_id)
                    if recipient_id
                    else None
                ),
            )

        # ====================================================
        # PHASE 3
        # SCORE COMPLETE CAMPAIGN
        # ====================================================

        for (
            attack_data,
            transaction,
        ) in prepared_attacks:

            # ================================================
            # CRITICAL SMURFING FIX
            # ================================================
            #
            # Transaction.model_dump() does not necessarily
            # include recipient_id because recipient_id may not
            # exist in the Transaction Pydantic schema.
            #
            # We explicitly pass attack_data into
            # score_transaction() so recipient_id survives and
            # reaches GraphAnalyzer.analyze_risk().
            # ================================================

            (
                transaction_data,
                detection,
                risk_score,
            ) = score_transaction(
                transaction,
                extra_data=attack_data,
            )

            # ================================================
            # FINAL SCORE VALIDATION
            # ================================================

            final_risk_score = max(
                0.0,
                min(
                    risk_score,
                    1.0,
                ),
            )

            decision = str(
                detection[
                    "decision"
                ]
            )

            # ================================================
            # PERSIST TRANSACTION
            # ================================================

            transaction_data.update(
                {
                    "risk_score":
                        final_risk_score,

                    "decision":
                        decision,
                }
            )

            save_transaction(
                transaction_data
            )

            # ================================================
            # BATTLE RESULT
            # ================================================

            results.append(
                {
                    "scenario_id":
                        attack_data.get(
                            "transaction_id",
                            transaction.txn_id,
                        ),

                    "attack_type":
                        family,

                    "description":
                        get_attack_description(
                            family
                        ),

                    "risk_score":
                        round(
                            final_risk_score,
                            4,
                        ),

                    "decision":
                        decision,
                }
            )

    # ========================================================
    # RETURN RESULTS
    # ========================================================

    return AdversarialBattleResponse(

        rounds_completed=(
            request.rounds
        ),

        results=results,
    )