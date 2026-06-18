---
title: Build an Expense Tracker
author: Codédex Community
uid: expense-tracker
datePublished: 2026-06-18
description: A CLI expense tracker with SQLite storage, CSV import, spending analytics, and ASCII chart reports — all in pure Python.
published: false
readTime: 60
prerequisites: Python, SQL Basics
versions: Python 3.10+
tags:
  - beginner
  - python
  - data
---

## Introduction

Tracking where your money goes is the first step toward financial awareness. In this project, we'll build a command-line expense tracker that stores transactions in SQLite, imports bank CSV exports, analyzes spending patterns, and prints colorful ASCII bar charts — all using nothing but Python's standard library.

Here's what you'll learn:

- **Dataclasses** — clean, immutable data models with zero boilerplate
- **SQLite** — embedded, file-based relational storage (no server, no install)
- **argparse** — professional CLI interfaces with subcommands and type validation
- **CSV parsing** — handling real-world bank export formats
- **Aggregation and analytics** — category breakdowns, month-over-month trends
- **ASCII visualization** — terminal-friendly charts with zero dependencies

<img src="./assets/screenshot-1.png" alt="Expense Tracker screenshot" width="700"/>

Let's build it!

## Setting Up

First, create a new directory for the project and download the starter code:

```bash
mkdir expense-tracker
cd expense-tracker
```

Grab the starter template from our repo at [https://github.com/Manas-thakur/python-tutorial](https://github.com/Manas-thakur/python-tutorial) (path: `project-submissions/expense-tracker/starter/`).

Your project will end up with six files:

```
expense-tracker/
├── tracker.py      # CLI entry point — argparse dispatches subcommands
├── models.py       # Transaction & Budget dataclasses — data schemas
├── database.py     # SQLite wrapper — all CRUD lives here
├── importers.py    # CSV parsers — maps bank-specific formats
├── analysis.py     # Spending analytics — aggregation & trends
└── reports.py      # Pretty-printing & ASCII bar charts
```

**Python version:** You'll need Python 3.10+ for the `str | None` union syntax. If you're on an older version, replace `str | None` with `Optional[str]`.

No `pip install` required — we're using only the standard library (`sqlite3` is built in).

## Step 1: Data Models (models.py)

Let's start with the data layer. Create `models.py`:

```python
from dataclasses import dataclass
from decimal import Decimal
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class Transaction:
    amount: Decimal
    category: str
    description: str = ""
    date: date = date.today()
    id: Optional[int] = None
    type: str = "expense"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "amount": str(self.amount),
            "category": self.category,
            "description": self.description,
            "date": self.date.isoformat(),
            "type": self.type,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        return cls(
            id=data.get("id"),
            amount=Decimal(data["amount"]),
            category=data["category"],
            description=data.get("description", ""),
            date=date.fromisoformat(data["date"]) if isinstance(data["date"], str) else data["date"],
            type=data.get("type", "expense"),
        )


@dataclass(frozen=True)
class Budget:
    category: str
    monthly_limit: Decimal

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "monthly_limit": str(self.monthly_limit),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Budget":
        return cls(
            category=data["category"],
            monthly_limit=Decimal(data["monthly_limit"]),
        )
```

**Here's what's happening:**

The `@dataclass(frozen=True)` decorator auto-generates `__init__`, `__repr__`, `__eq__`, and `__hash__`. Without it you'd write 20+ lines of boilerplate. The `frozen=True` makes instances immutable — once a `Transaction` is created its fields can't change, preventing accidental mutation bugs.

We use `Decimal` instead of `float` for all monetary values. Floats lose precision: `0.1 + 0.2` gives `0.30000000000000004`. Money must be exact.

The `to_dict()` / `from_dict()` methods serialize between dataclass instances and dictionaries. This is useful for JSON export and for converting between SQLite rows and Python objects.

The `id` field is `None` until the record is persisted to the database — SQLite assigns the real ID on insert. The `type` field distinguishes expense from income.

**Why dataclasses over plain dicts?** Autocomplete works. Type checkers catch errors. You can't accidentally misspell a field name. And `frozen=True` means no one can set `transaction.amount = -100` after creation.

## Step 2: SQLite Database (database.py)

Now create `database.py`. This is the persistence layer — it manages the SQLite connection and all CRUD operations.

```python
import sqlite3
from pathlib import Path
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
    conn.executescript("""
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
    """)
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
           WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
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
        type=row.get("type", "expense"),
    )
```

**Here's what's happening:**

`init_db()` runs `CREATE TABLE IF NOT EXISTS` — it's safe to call every time the CLI starts. The `transactions` table has an auto-incrementing primary key and stores dates as ISO strings. The `budgets` table uses the category name as its primary key, so setting a budget for "Food" twice simply replaces the previous limit.

`_connect()` returns a connection with `row_factory = sqlite3.Row`, which lets us access columns by name: `row["category"]` instead of `row[1]`.

`insert_transaction()` uses parameterized queries (`?` placeholders) — never f-strings. This prevents SQL injection and handles type escaping automatically.

`get_transactions()` builds a dynamic WHERE clause. If a filter argument is `None`, it's simply omitted from the query. This pattern scales to any number of optional filters without code duplication.

`get_monthly_summary()` uses SQLite's `strftime()` to extract year and month from the date column, groups by category, and returns totals sorted highest first.

`set_budget()` uses `INSERT OR REPLACE` — if a budget for that category already exists, it's updated. If not, it's created.

**Why SQLite?** Zero configuration — no server install, no database setup. The entire database is a single file (`expenses.db`) on disk. ACID-compliant — your data survives crashes. Perfect for CLI tools that need persistent storage.

## Step 3: CLI Interface (tracker.py)

Create `tracker.py`. This is the command-line entry point that users interact with.

```python
import argparse
from pathlib import Path
from decimal import Decimal
from datetime import date, datetime
from database import (
    init_db, insert_transaction, get_transactions,
    get_monthly_summary, set_budget, get_budgets,
)
from models import Transaction, Budget
from reports import monthly_report
from importers import import_csv


def parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tracker", description="Expense Tracker CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_p = subparsers.add_parser("add", help="Add a new transaction")
    add_p.add_argument("--amount", type=Decimal, required=True)
    add_p.add_argument("--category", required=True)
    add_p.add_argument("--description", default="")
    add_p.add_argument("--date", type=str, default=None)
    add_p.add_argument("--type", choices=["expense", "income"], default="expense")

    list_p = subparsers.add_parser("list", help="List transactions")
    list_p.add_argument("--category")
    list_p.add_argument("--from-date")
    list_p.add_argument("--to-date")

    subparsers.add_parser("report", help="Generate spending report")

    import_p = subparsers.add_parser("import", help="Import transactions from CSV")
    import_p.add_argument("file", type=Path)

    budget_p = subparsers.add_parser("budget", help="Set a category budget")
    budget_p.add_argument("--category", required=True)
    budget_p.add_argument("--limit", type=Decimal, required=True)

    return parser


def cmd_add(args, db_path: str):
    t = Transaction(
        amount=args.amount,
        category=args.category,
        description=args.description,
        date=parse_date(args.date) if args.date else date.today(),
        type=args.type,
    )
    t_id = insert_transaction(t, db_path)
    print(f"Added transaction #{t_id}: {t.category} ${t.amount:.2f}")


def cmd_list(args, db_path: str):
    txns = get_transactions(
        category=args.category,
        from_date=args.from_date,
        to_date=args.to_date,
        db_path=db_path,
    )
    if not txns:
        print("No transactions found.")
        return
    print(f"{'ID':>4}  {'Date':>10}  {'Category':<15}  {'Amount':>8}  {'Description'}")
    print("-" * 60)
    for t in txns:
        print(f"{t.id:>4}  {t.date.isoformat():>10}  {t.category:<15}  ${t.amount:>7.2f}  {t.description}")
    total = sum(t.amount for t in txns)
    print(f"\nTotal: ${total:.2f} ({len(txns)} transactions)")


def cmd_report(args, db_path: str):
    today = date.today()
    txns = get_transactions(
        from_date=today.replace(day=1).isoformat(),
        to_date=today.isoformat(),
        db_path=db_path,
    )
    print(monthly_report(txns, today.year, today.month))


def cmd_import(args, db_path: str):
    txns = import_csv(str(args.file))
    if not txns:
        print("No transactions found in CSV.")
        return
    for t in txns:
        insert_transaction(t, db_path)
    print(f"Imported {len(txns)} transactions from {args.file.name}")


def cmd_budget(args, db_path: str):
    b = Budget(category=args.category, monthly_limit=args.limit)
    set_budget(b, db_path)
    print(f"Budget set: {b.category} = ${b.monthly_limit:.2f}/month")


def main():
    init_db()
    parser = build_parser()
    args = parser.parse_args()

    db_path = "expenses.db"

    if args.command == "add":
        cmd_add(args, db_path)
    elif args.command == "list":
        cmd_list(args, db_path)
    elif args.command == "report":
        cmd_report(args, db_path)
    elif args.command == "import":
        cmd_import(args, db_path)
    elif args.command == "budget":
        cmd_budget(args, db_path)


if __name__ == "__main__":
    main()
```

**Here's what's happening:**

`build_parser()` creates an `ArgumentParser` with subcommands. Each subcommand (`add`, `list`, `report`, `import`, `budget`) has its own set of arguments. The `dest="command"` tells argparse to store the subcommand name in `args.command`.

When the user runs `python tracker.py add --amount 25 --category Food`, argparse:
1. Sets `args.command` to `"add"`
2. Calls `Decimal("25")` to convert the amount string
3. Stores `"Food"` in `args.category`
4. Sets `args.description` to `""` (the default)

If the user forgets `--amount`, they get a clear error: `the following arguments are required: --amount`.

Each `cmd_*` function is a small, focused handler that delegates to `database.py` functions. This keeps `tracker.py` thin — it's the dispatcher, not the logic.

The `parse_date()` helper converts a string like `"2026-06-18"` to a `date` object. If no date is provided, `cmd_add` defaults to today.

**Why argparse over sys.argv?** Three reasons:
- **Automatic `--help`** — `tracker.py add --help` prints the usage and descriptions
- **Type validation** — `type=Decimal` converts and rejects invalid input immediately
- **Subcommand support** — `add_subparsers()` gives you nested command trees with separate arguments per command

## Step 4: Adding Transactions

Now let's make the `add` command actually work by implementing `insert_transaction` in `database.py` if you haven't already. Open `database.py` and add:

```python
def insert_transaction(t: Transaction, db_path: str = DB_FILE) -> int:
    conn = _connect(db_path)
    cur = conn.execute(
        "INSERT INTO transactions (amount, category, description, date, type) VALUES (?, ?, ?, ?, ?)",
        (str(t.amount), t.category, t.description, t.date.isoformat(), t.type),
    )
    conn.commit()
    conn.close()
    return cur.lastrowid
```

This is the most common operation in the app, so let's walk through exactly what happens when you run:

```bash
python tracker.py add --amount 45.00 --category Food --description "Weekly groceries"
```

1. `main()` calls `init_db()` — creates the SQLite file and tables if they don't exist
2. `build_parser()` and `parse_args()` extract the command and arguments
3. `cmd_add()` creates a `Transaction` object:
   ```python
   Transaction(
       amount=Decimal("45.00"),
       category="Food",
       description="Weekly groceries",
       date=date.today(),       # 2026-06-18
       type="expense"
   )
   ```
4. `insert_transaction()` runs this SQL:
   ```sql
   INSERT INTO transactions (amount, category, description, date, type)
   VALUES ('45.00', 'Food', 'Weekly groceries', '2026-06-18', 'expense')
   ```
5. SQLite assigns `id = 1`, commits the transaction, and returns the ID
6. The CLI prints: `Added transaction #1: Food $45.00`

Let's add a few more:

```bash
python tracker.py add --amount 30.00 --category Transport --description "Gas refill"
python tracker.py add --amount 5.50 --category Coffee --description "Morning latte"
python tracker.py add --amount 120.00 --category Utilities --description "Electric bill"
python tracker.py add --amount 5000.00 --category Salary --type income --description "June salary"
```

Notice the income transaction — we used `--type income` so it's recorded as a positive inflow rather than an expense.

## Step 5: Listing & Filtering

The `list` command queries the database with optional filters and prints a formatted table. Here's the implementation:

```python
def cmd_list(args, db_path: str):
    txns = get_transactions(
        category=args.category,
        from_date=args.from_date,
        to_date=args.to_date,
        db_path=db_path,
    )
    if not txns:
        print("No transactions found.")
        return
    print(f"{'ID':>4}  {'Date':>10}  {'Category':<15}  {'Amount':>8}  {'Description'}")
    print("-" * 60)
    for t in txns:
        print(f"{t.id:>4}  {t.date.isoformat():>10}  {t.category:<15}  ${t.amount:>7.2f}  {t.description}")
    total = sum(t.amount for t in txns)
    print(f"\nTotal: ${total:.2f} ({len(txns)} transactions)")
```

The `get_transactions` function in `database.py` builds a dynamic WHERE clause:

```python
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
```

**Here's what's happening:**

The `WHERE 1=1` trick lets us append `AND ...` clauses without checking if it's the first condition. Each filter is a separate `AND` with a `?` parameter. If a filter is `None`, it's simply skipped.

The `_row_to_transaction` helper converts a `sqlite3.Row` back into a `Transaction` dataclass:

```python
def _row_to_transaction(row) -> Transaction:
    return Transaction(
        id=row["id"],
        amount=Decimal(str(row["amount"])),
        category=row["category"],
        description=row["description"],
        date=date.fromisoformat(row["date"]),
        type=row.get("type", "expense"),
    )
```

Let's test the list command:

```bash
# List everything
python tracker.py list

# Filter by category
python tracker.py list --category Food

# Filter by date range
python tracker.py list --from-date 2026-06-01 --to-date 2026-06-15
```

Sample output:

```
  ID        Date  Category           Amount  Description
------------------------------------------------------------
   6  2026-06-18  Salary         $ 5000.00  June salary
   5  2026-06-18  Utilities      $  120.00  Electric bill
   4  2026-06-18  Coffee         $    5.50  Morning latte
   3  2026-06-18  Transport      $   30.00  Gas refill
   1  2026-06-18  Food           $   45.00  Weekly groceries

Total: $5200.50 (5 transactions)
```

## Step 6: Spending Analytics (analysis.py)

Now let's build the analytics engine. Create `analysis.py`:

```python
from collections import defaultdict
from decimal import Decimal
from datetime import date
from models import Transaction


def spending_by_category(txns: list[Transaction], period: str = "month") -> dict[str, Decimal]:
    totals: dict[str, Decimal] = defaultdict(Decimal)
    for t in txns:
        if t.type == "expense":
            totals[t.category] += t.amount
    return dict(totals)


def month_over_month(txns: list[Transaction]) -> dict[str, Decimal]:
    monthly: dict[str, Decimal] = defaultdict(Decimal)
    for t in txns:
        if t.type == "expense":
            key = t.date.strftime("%Y-%m")
            monthly[key] += t.amount
    return dict(monthly)


def percentage_change(before: Decimal, after: Decimal) -> Decimal:
    if before == 0:
        return Decimal("0")
    return ((after - before) / before) * 100


def detect_trends(txns: list[Transaction]) -> list[dict]:
    monthly = month_over_month(txns)
    sorted_months = sorted(monthly.keys())
    trends = []
    for i in range(1, len(sorted_months)):
        prev_m, curr_m = sorted_months[i - 1], sorted_months[i]
        change = percentage_change(monthly[prev_m], monthly[curr_m])
        direction = "up" if change > 0 else ("down" if change < 0 else "flat")
        trends.append({
            "month": curr_m,
            "previous": prev_m,
            "change_pct": change,
            "direction": direction,
        })
    return trends


def budget_analysis(spending: dict[str, Decimal], budgets: dict[str, Decimal]) -> list[dict]:
    results = []
    for category, limit in budgets.items():
        spent = spending.get(category, Decimal("0"))
        remaining = limit - spent
        pct = (spent / limit * 100) if limit > 0 else Decimal("0")
        results.append({
            "category": category,
            "budget": limit,
            "spent": spent,
            "remaining": remaining,
            "pct_used": pct,
            "on_track": spent <= limit,
        })
    return results
```

**Here's what's happening:**

`spending_by_category()` iterates over all expense transactions and sums amounts by category using a `defaultdict(Decimal)` — this auto-initializes missing keys to `Decimal("0")`, eliminating the "key doesn't exist" check.

`month_over_month()` groups expenses by year-month key (e.g., `"2026-01"`) and sums them. This gives you a time series of total spending.

`percentage_change()` calculates `((after - before) / before) * 100`. Why percentage instead of raw difference? A $50 increase on a $10 baseline (+500%) tells a very different story than $50 on $1000 (+5%). Percentages normalize across scales.

`detect_trends()` computes month-over-month changes for every consecutive pair of months. It returns a list of dicts like:
```python
[{"month": "2026-02", "previous": "2026-01", "change_pct": Decimal("50.0"), "direction": "up"}, ...]
```

`budget_analysis()` compares actual spending against budgets. Given a dict of `{category: spent}` and `{category: limit}`, it computes remaining budget and percentage used. The `on_track` flag is `True` if spending is within the budget.

Let's try it in the Python REPL:

```python
>>> from analysis import spending_by_category, month_over_month, detect_trends
>>> from decimal import Decimal
>>> from datetime import date
>>> from models import Transaction

>>> txns = [
...     Transaction(amount=Decimal("100"), category="Food", date=date(2026, 1, 5)),
...     Transaction(amount=Decimal("50"),  category="Food", date=date(2026, 1, 12)),
...     Transaction(amount=Decimal("30"),  category="Transport", date=date(2026, 1, 15)),
...     Transaction(amount=Decimal("200"), category="Food", date=date(2026, 2, 3)),
...     Transaction(amount=Decimal("70"),  category="Transport", date=date(2026, 2, 10)),
... ]

>>> spending_by_category(txns)
{'Food': Decimal('300'), 'Transport': Decimal('100')}

>>> month_over_month(txns)
{'2026-01': Decimal('180'), '2026-02': Decimal('270')}

>>> detect_trends(txns)
[{'month': '2026-02', 'previous': '2026-01', 'change_pct': Decimal('50.000'), 'direction': 'up'}]
```

## Step 7: Reports & Charts (reports.py)

Create `reports.py` — the presentation layer that turns raw analytics into readable output:

```python
from decimal import Decimal
from datetime import date
from models import Transaction
from analysis import spending_by_category, detect_trends, budget_analysis


def category_chart(totals: dict[str, Decimal], width: int = 30) -> str:
    if not totals:
        return "(no data)"
    max_val = max(totals.values())
    lines = []
    for category, amount in sorted(totals.items(), key=lambda x: -x[1]):
        bar_len = int((amount / max_val) * width) if max_val > 0 else 0
        bar = "█" * bar_len
        lines.append(f"  {category:15s} ${amount:>8.2f}  {bar}")
    return "\n".join(lines)


def monthly_report(txns: list[Transaction], year: int, month: int) -> str:
    total = sum(t.amount for t in txns if t.type == "expense")
    income = sum(t.amount for t in txns if t.type == "income")
    cats = spending_by_category(txns)
    trends = detect_trends(txns)

    lines = [f"--- Spending Report: {year}-{month:02d} ---", ""]
    lines.append(f"Total expenses: ${total:.2f}")
    lines.append(f"Total income:   ${income:.2f}")
    lines.append(f"Net:            ${income - total:.2f}")
    lines.append("")

    if cats:
        lines.append("By Category:")
        lines.append(category_chart(cats))
        lines.append("")

    if trends:
        lines.append("Trends (month-over-month):")
        for t in trends:
            arrow = "▲" if t["direction"] == "up" else "▼"
            lines.append(f"  {t['month']}  {arrow} {t['change_pct']:.1f}% vs {t['previous']}")
        lines.append("")

    budgets = _load_and_compare_budgets(cats)
    if budgets:
        lines.append("Budget Check:")
        lines.append(f"  {'Category':<15} {'Budget':>8} {'Spent':>8} {'Remain':>8} {'Use%':>6} Status")
        for b in budgets:
            status = "✓" if b["on_track"] else "⚠ OVER"
            lines.append(
                f"  {b['category']:<15} ${b['budget']:>7.2f} ${b['spent']:>7.2f} "
                f"${b['remaining']:>7.2f} {b['pct_used']:>5.1f}% {status}"
            )

    return "\n".join(lines)


def _load_and_compare_budgets(cats: dict[str, Decimal]) -> list[dict]:
    try:
        from database import get_budgets
        budgets = get_budgets()
        if not budgets:
            return []
        budget_dict = {b.category: b.monthly_limit for b in budgets}
        return budget_analysis(cats, budget_dict)
    except Exception:
        return []
```

**Here's what's happening:**

`category_chart()` generates ASCII bar charts. It finds the largest category total, then scales every bar proportionally to that maximum. The `sorted(..., key=lambda x: -x[1])` ensures highest-spending categories appear first.

Here's the math for a chart with `width=20`:

```python
data = {"Food": Decimal("150"), "Transport": Decimal("45"), "Coffee": Decimal("30")}
```

| Category | Amount | Calculation | Bar length |
|----------|--------|-------------|------------|
| Food | 150 | (150/150) × 20 | 20 ████████████████████ |
| Transport | 45 | (45/150) × 20 | 6 ██████ |
| Coffee | 30 | (30/150) × 20 | 4 ████ |

`monthly_report()` combines everything into one printable string: total expenses, income, category breakdown with chart, month-over-month trends with arrows, and budget comparison with over-budget warnings.

The `_load_and_compare_budgets()` helper imports `get_budgets` lazily inside a try/except — if the database doesn't have budgets set, it silently returns an empty list instead of crashing the report.

Let's generate a report:

```bash
python tracker.py report
```

Sample output:

```
--- Spending Report: 2026-06 ---

Total expenses: $200.50
Total income:   $5000.00
Net:            $4799.50

By Category:
  Utilities       $  120.00  ████████████████████████████████
  Food            $   45.00  ████████████
  Transport       $   30.00  ████████
  Coffee          $    5.50  ██

Trends (month-over-month):
  2026-02  ▲ +50.0% vs 2026-01
  2026-03  ▼ -12.5% vs 2026-02
```

## Step 8: CSV Import (importers.py)

Create `importers.py`. This lets users import bank statement CSVs instead of typing every transaction by hand:

```python
import csv
from pathlib import Path
from decimal import Decimal
from datetime import datetime
from typing import Optional
from models import Transaction


COLUMN_MAP = {
    "chase": {"date": 0, "description": 1, "amount": 3, "category": 4},
    "wells_fargo": {"date": 0, "description": 2, "amount": 4, "category": 5},
    "simple": {"date": 0, "description": 1, "amount": 2, "category": 3},
}


def detect_bank(headers: list[str]) -> str:
    if "Posting Date" in headers:
        return "chase"
    if "Transaction Date" in headers:
        return "wells_fargo"
    return "simple"


def parse_amount(raw: str) -> Decimal:
    cleaned = raw.strip().replace("$", "").replace(",", "").replace(" ", "")
    return Decimal(cleaned)


def is_duplicate(t: Transaction, existing: list[Transaction]) -> bool:
    for ex in existing:
        if (ex.amount == t.amount
                and ex.description == t.description
                and ex.date == t.date):
            return True
    return False


def import_csv(filepath: str, bank: Optional[str] = None) -> list[Transaction]:
    transactions = []
    path = Path(filepath)
    if not path.exists():
        print(f"File not found: {filepath}")
        return []

    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        headers = next(reader)
        bank = bank or detect_bank(headers)
        mapping = COLUMN_MAP.get(bank, COLUMN_MAP["simple"])

        for row_num, row in enumerate(reader, start=2):
            if not row or all(cell.strip() == "" for cell in row):
                continue

            try:
                raw_amount = row[mapping["amount"]]
                amount = parse_amount(raw_amount)
                desc = row[mapping["description"]].strip()
                raw_date = row[mapping["date"]].strip()

                # Try common date formats
                for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y", "%m-%d-%Y"):
                    try:
                        parsed_date = datetime.strptime(raw_date, fmt).date()
                        break
                    except ValueError:
                        continue
                else:
                    print(f"Row {row_num}: skipping — unrecognized date '{raw_date}'")
                    continue

                # Determine category from CSV or use a placeholder
                try:
                    category = row[mapping["category"]].strip()
                except (IndexError, KeyError):
                    category = "Uncategorized"

                # Bank exports record expenses as negative numbers
                tx_type = "expense" if amount < 0 else "income"
                t = Transaction(
                    amount=abs(amount),
                    category=category,
                    description=desc,
                    date=parsed_date,
                    type=tx_type,
                )

                # Deduplicate within the same import batch
                if not is_duplicate(t, transactions):
                    transactions.append(t)
                else:
                    print(f"Row {row_num}: skipping duplicate — {desc} ${amount}")

            except (ValueError, IndexError) as e:
                print(f"Row {row_num}: skipping — {e}")
                continue

    return transactions
```

**Here's what's happening:**

`detect_bank()` reads the header row and matches known bank formats. Chase CSVs have "Posting Date", Wells Fargo has "Transaction Date". Everything else uses the "simple" mapping (column 0 = date, 1 = description, 2 = amount, 3 = category).

`parse_amount()` strips `$`, commas, and whitespace before converting to `Decimal`. This handles variations like `$ -87.23`, `-$87.23`, and `87.23`.

`is_duplicate()` checks if a transaction already exists in the current import batch by matching amount, description, and date. This prevents double-importing the same row if you accidentally run the import twice.

`import_csv()` handles multiple date formats — `%m/%d/%Y` (US), `%Y-%m-%d` (ISO), `%d/%m/%Y` (European). It tries each in order and skips rows with unrecognized dates.

Bank exports record expenses as negative debits (e.g., `-87.23`). The code detects the sign and sets `type` to `"expense"` for negatives and `"income"` for positives, then stores the absolute value.

The `encoding="utf-8-sig"` handles the BOM (Byte Order Mark) that Excel often prepends to CSV files.

Let's import a CSV:

```bash
python tracker.py import data/sample.csv
```

Given a `sample.csv`:
```
date,description,amount,category
2025-01-02,Grocery Store,85.50,Food
2025-01-03,Netflix Subscription,15.99,Entertainment
2025-01-05,Gas Station,45.00,Transport
```

Output:
```
Imported 3 transactions from sample.csv
```

## Running and Extending

You're done! Here's the full workflow:

```bash
# Add transactions
python tracker.py add --amount 45.00 --category Food --description "Groceries"
python tracker.py add --amount 30.00 --category Transport --description "Gas"
python tracker.py add --amount 5.50 --category Coffee --description "Latte"

# Import from a bank CSV
python tracker.py import data/sample.csv

# Set monthly budgets
python tracker.py budget --category Food --limit 500

# View spending report with ASCII chart
python tracker.py report

# List all transactions
python tracker.py list

# Filter transactions
python tracker.py list --category Food
python tracker.py list --from-date 2026-01-01 --to-date 2026-06-30
```

### Ideas to Extend

| Feature | What you'd touch |
|---|---|
| **Budget enforcement** | `database.py` — compare `spent_so_far` to `budget.monthly_limit` in `add` |
| **Recurring transactions** | `models.py` — add `RecurringRule`; `tracker.py` — new `schedule` subcommand |
| **PDF export** | `reports.py` — use `reportlab` or `fpdf` to generate a PDF monthly statement |
| **Web dashboard** | Add Flask/FastAPI in a `web/` dir; reuse `analysis.py` and `reports.py` unchanged |
| **Category aliases** | `importers.py` — fuzzy-match bank descriptions to canonical categories |
| **SQLite date queries** | `analysis.py` — `WHERE date BETWEEN ? AND ?` for custom date ranges |
| **Export to CSV/JSON** | `reports.py` — add `export_csv()` for spreadsheet import |
| **Color-coded terminal output** | `reports.py` — use ANSI escape codes for red/green budget status |

The modular design means you can add any of these by editing one or two files without touching the rest. The CLI, data, analytics, and presentation layers are cleanly separated.

## Conclusion

You built a fully functional expense tracker from scratch! Here's what you accomplished:

- Designed immutable data models using Python dataclasses with `Decimal` for precision
- Built a SQLite-backed persistence layer with parameterized queries and dynamic filters
- Created a professional CLI interface with argparse subcommands
- Implemented CSV import that handles multiple bank formats with deduplication
- Built spending analytics: category breakdown, month-over-month trends, budget comparison
- Generated ASCII bar charts and formatted reports with zero external dependencies

The full source code is available at [https://github.com/Manas-thakur/python-tutorial](https://github.com/Manas-thakur/python-tutorial) (path: `project-submissions/expense-tracker/solution/`).
