import sqlite3
from pathlib import Path
from typing import Any, Dict, List


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "payshield.db"


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_database() -> None:
    connection = get_connection()

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
    connection.close()


def save_transaction(transaction: Dict[str, Any]) -> None:
    connection = get_connection()

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
    connection.close()


def get_transaction_metrics() -> Dict[str, Any]:
    connection = get_connection()

    total = connection.execute(
        "SELECT COUNT(*) AS count FROM transactions"
    ).fetchone()["count"]

    approved = connection.execute(
        "SELECT COUNT(*) AS count FROM transactions WHERE decision = 'APPROVE'"
    ).fetchone()["count"]

    reviewed = connection.execute(
        "SELECT COUNT(*) AS count FROM transactions WHERE decision = 'REVIEW'"
    ).fetchone()["count"]

    blocked = connection.execute(
        "SELECT COUNT(*) AS count FROM transactions WHERE decision = 'BLOCK'"
    ).fetchone()["count"]

    average = connection.execute(
        "SELECT COALESCE(AVG(risk_score), 0) AS average FROM transactions"
    ).fetchone()["average"]

    connection.close()

    return {
        "total_transactions": total,
        "approved": approved,
        "reviewed": reviewed,
        "blocked": blocked,
        "average_risk_score": round(float(average), 4),
    }
def get_transaction_by_id(txn_id: str) -> Dict[str, Any] | None:
    connection = get_connection()

    row = connection.execute(
        "SELECT * FROM transactions WHERE txn_id = ?",
        (txn_id,),
    ).fetchone()

    connection.close()

    if row is None:
        return None

    return dict(row)
def get_recent_transactions(limit: int = 20) -> List[Dict[str, Any]]:
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT *
        FROM transactions
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    connection.close()

    return [dict(row) for row in rows]