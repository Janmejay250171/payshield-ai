import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "payshield.db"


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(str(DB_PATH))
    connection.row_factory = sqlite3.Row
    return connection


def init_database() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                txn_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                amount REAL NOT NULL,
                currency TEXT NOT NULL,
                merchant_id TEXT NOT NULL,
                device_id TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                country TEXT NOT NULL,
                velocity_1h INTEGER DEFAULT 0,
                device_risk REAL DEFAULT 0.0,
                ip_risk REAL DEFAULT 0.0,
                country_risk REAL DEFAULT 0.0,
                risk_score REAL DEFAULT 0.0,
                decision TEXT DEFAULT 'APPROVE'
            )
            """
        )
        connection.commit()


def save_transaction(transaction: Dict[str, Any]) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO transactions (
                txn_id,
                user_id,
                amount,
                currency,
                merchant_id,
                device_id,
                ip_address,
                timestamp,
                country,
                velocity_1h,
                device_risk,
                ip_risk,
                country_risk,
                risk_score,
                decision
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                transaction["txn_id"],
                transaction["user_id"],
                transaction["amount"],
                transaction["currency"],
                transaction["merchant_id"],
                transaction["device_id"],
                transaction["ip_address"],
                transaction["timestamp"],
                transaction["country"],
                transaction.get("velocity_1h", 0),
                transaction.get("device_risk", 0.0),
                transaction.get("ip_risk", 0.0),
                transaction.get("country_risk", 0.0),
                transaction.get("risk_score", 0.0),
                transaction.get("decision", "APPROVE"),
            ),
        )
        connection.commit()


def get_transaction_metrics() -> Dict[str, Any]:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                COUNT(*) AS total_transactions,

                COALESCE(
                    SUM(
                        CASE
                            WHEN decision = 'APPROVE' THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS approved,

                COALESCE(
                    SUM(
                        CASE
                            WHEN decision = 'REVIEW' THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS reviewed,

                COALESCE(
                    SUM(
                        CASE
                            WHEN decision = 'BLOCK' THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS blocked,

                COALESCE(
                    AVG(risk_score),
                    0.0
                ) AS average_risk_score

            FROM transactions
            """
        ).fetchone()

    return {
        "total_transactions": int(row["total_transactions"]),
        "approved": int(row["approved"]),
        "reviewed": int(row["reviewed"]),
        "blocked": int(row["blocked"]),
        "average_risk_score": round(
            float(row["average_risk_score"]),
            4,
        ),
    }


def get_transaction_by_id(
    txn_id: str,
) -> Optional[Dict[str, Any]]:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM transactions
            WHERE txn_id = ?
            """,
            (txn_id,),
        ).fetchone()

    if row is None:
        return None

    return dict(row)


def get_recent_transactions(
    limit: int = 20,
) -> List[Dict[str, Any]]:
    limit = max(1, min(int(limit), 100))

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM transactions
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]


def get_database_info() -> Dict[str, Any]:
    with get_connection() as connection:
        total = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM transactions
            """
        ).fetchone()["count"]

        latest_id = connection.execute(
            """
            SELECT MAX(id) AS max_id
            FROM transactions
            """
        ).fetchone()["max_id"]

    return {
        "database_path": str(DB_PATH),
        "database_exists": DB_PATH.exists(),
        "total_transactions": int(total),
        "latest_id": latest_id,
    }
