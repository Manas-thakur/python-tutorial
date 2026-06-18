import sqlite3
from decimal import Decimal
from datetime import date
from typing import Optional
from models import Transaction, Budget

DB_FILE = "expenses.db"


def _connect(db_path: str = DB_FILE):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DB_FILE):
    conn = _connect(db_path)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount DECIMAL(10,2) NOT NULL,
            category TEXT NOT NULL,
            description TEXT DEFAULT '',
            date DATE NOT NULL,
            type TEXT DEFAULT 'expense'
        );
        CREATE TABLE IF NOT EXISTS budgets (
            category TEXT PRIMARY KEY,
            monthly_limit DECIMAL(10,2) NOT NULL
        );
    """
    )
    conn.commit()
    conn.close()


def insert_transaction(t: Transaction, db_path: str = DB_FILE) -> int:
    conn = _connect(db_path)
    cur = conn.execute(
        "INSERT INTO transactions (amount, category, description, date, type) VALUES (?, ?, ?, ?, ?)",
        (str(t.amount), t.category, t.description, t.date.isoformat(), t.type),
    )
    conn.commit()
    conn.close()
    return cur.lastrowid


def get_transactions(
    category: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db_path: str = DB_FILE,
) -> list[Transaction]:
    conn = _connect(db_path)
    query = "SELECT * FROM transactions WHERE 1=1"
    params = []
    if category:
        query += " AND category = ?"
        params.append(category)
    if from_date:
        query += " AND date >= ?"
        params.append(from_date)
    if to_date:
        query += " AND date <= ?"
        params.append(to_date)
    query += " ORDER BY date DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [_row_to_transaction(r) for r in rows]


def get_monthly_summary(year: int, month: int, db_path: str = DB_FILE) -> list[dict]:
    conn = _connect(db_path)
    rows = conn.execute(
        """SELECT category, SUM(amount) as total, COUNT(*) as count
           FROM transactions
           WHERE strftime('%%Y', date) = ? AND strftime('%%m', date) = ?
           GROUP BY category
           ORDER BY total DESC""",
        (str(year), f"{month:02d}"),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def set_budget(b: Budget, db_path: str = DB_FILE):
    conn = _connect(db_path)
    conn.execute(
        "INSERT OR REPLACE INTO budgets (category, monthly_limit) VALUES (?, ?)",
        (b.category, str(b.monthly_limit)),
    )
    conn.commit()
    conn.close()


def get_budgets(db_path: str = DB_FILE) -> list[Budget]:
    conn = _connect(db_path)
    rows = conn.execute("SELECT * FROM budgets").fetchall()
    conn.close()
    return [
        Budget(category=r["category"], monthly_limit=Decimal(str(r["monthly_limit"])))
        for r in rows
    ]


def _row_to_transaction(row) -> Transaction:
    return Transaction(
        id=row["id"],
        amount=Decimal(str(row["amount"])),
        category=row["category"],
        description=row["description"],
        date=date.fromisoformat(row["date"]),
        type=row["type"],
    )
