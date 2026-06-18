from python_tutorial.models import ProjectTutorial, Section

TUTORIAL = ProjectTutorial(
    slug="expense-tracker",
    title="Build an Expense Tracker",
    description="A CLI expense tracker with SQLite storage, CSV import, spending analytics, and ASCII chart reports.",
    difficulty="beginner",
    project_dir="expense-tracker",
    prerequisites=["Functions", "File I/O", "Classes", "SQL basics"],
    steps=[
        Section(
            heading="Step 1: Project Overview",
            content='''\
Let's explore the Expense Tracker project. Here's every file and what it owns:

```
expense-tracker/
  tracker.py        # CLI entry point --- argparse dispatches subcommands
  models.py         # Transaction & Budget dataclasses --- data schemas
  database.py       # SQLite wrapper --- all CRUD lives here
  importers.py      # CSV parsers --- maps bank-specific formats
  analysis.py       # Spending analytics --- aggregation & trends
  reports.py        # Pretty-printing & ASCII bar charts
```

**Architecture --- how data flows:**

```
CLI (tracker.py)
  |  argparse subcommands: add, list, report, import, budget
  v
Database (database.py)
  |  SQLite via context manager --- zero config, file-based
  v
Models (models.py)
  |  Transaction & Budget dataclasses
  v
Analysis (analysis.py) ---> Reports (reports.py)
       aggregation              ASCII charts
       month-over-month         formatted tables
       trend detection
```

The CLI delegates to other modules --- not a monolith. The `add` command calls `database.insert_transaction()`, the `report` command calls `analysis.month_over_month()` then feeds results to `reports.category_chart()`. Each module is independently testable.

**Why this split?** Separation of concerns. You can swap SQLite for PostgreSQL later by touching only `database.py`. You can add a new chart library without rewriting analytics. Small modules = easy to reason about.''',
        ),
        Section(
            heading="Step 2: Data Models (models.py)",
            content='''\
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


@dataclass(frozen=True)
class Budget:
    category: str
    monthly_limit: Decimal
```

**Why dataclasses?** They auto-generate `__init__`, `__repr__`, `__eq__`, and `__hash__`. Without them you'd write 20+ boilerplate lines. The `frozen=True` makes instances immutable --- once a `Transaction` is created its fields can't change, preventing accidental mutation bugs.

**Dry run --- creating a Transaction:**

```python
>>> from models import Transaction
>>> from decimal import Decimal

>>> t = Transaction(amount=Decimal("25.50"), category="Food")
>>> t
Transaction(amount=Decimal('25.50'), category='Food', description='', date=datetime.date(...), id=None)

>>> t.amount
Decimal('25.50')
>>> t.category
'Food'

# Immutable --- this raises:
# t.amount = Decimal("30.00")  # FrozenInstanceError!
```

`description` defaults to `""`, `date` defaults to today. The `id` field is `None` until the record is persisted --- the database assigns the real ID.

**Why `Decimal` instead of `float`?** Floats lose precision: `0.1 + 0.2 != 0.3`. Money must be exact. `Decimal("25.50")` stays `25.50` through every calculation.''',
        ),
        Section(
            heading="Step 3: Database Layer (database.py)",
            content='''\
```python
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from models import Transaction


class Database:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_schema()

    def _init_schema(self):
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount DECIMAL(10,2) NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    date DATE NOT NULL
                );
                CREATE TABLE IF NOT EXISTS budgets (
                    category TEXT PRIMARY KEY,
                    monthly_limit DECIMAL(10,2) NOT NULL
                );
            """)

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except:
            conn.rollback()
            raise
        finally:
            conn.close()

    def insert_transaction(self, t: Transaction) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO transactions (amount, category, description, date) VALUES (?, ?, ?, ?)",
                (str(t.amount), t.category, t.description, t.date.isoformat()),
            )
            return cur.lastrowid
```

**Why a context manager for connections?** Every `with self._connect()` block auto-commits on success, auto-rollbacks on error, and always closes the connection. No dangling connections, no forgotten commits.

**Dry run --- inserting a transaction:**

```python
>>> from database import Database
>>> from models import Transaction
>>> from decimal import Decimal
>>> from pathlib import Path

>>> db = Database(Path("finance.db"))

# What happens inside:
# 1. _init_schema() runs --- CREATE TABLE IF NOT EXISTS transactions (...)
# 2. The table is ready

>>> t = Transaction(amount=Decimal("12.75"), category="Coffee", description="Morning latte")

>>> db.insert_transaction(t)
1  # <-- lastrowid

# Behind the scenes:
#   SQL: INSERT INTO transactions (amount, category, description, date)
#        VALUES ('12.75', 'Coffee', 'Morning latte', '2026-06-18')
#   conn.commit()  -- writes to disk
#   conn.close()   -- frees the connection

# Verify it's persisted:
>>> db.list_transactions()
[Transaction(amount=Decimal('12.75'), category='Coffee', description='Morning latte', date=datetime.date(2026, 6, 18), id=1)]
```

**Why SQLite?** Zero configuration (no server, no install). The entire database is a single file on disk. ACID-compliant --- your data survives crashes. Perfect for CLI tools that need persistent storage without the overhead of PostgreSQL or MySQL.''',
        ),
        Section(
            heading="Step 4: The CLI (tracker.py)",
            content='''\
```python
import argparse
from pathlib import Path
from decimal import Decimal
from database import Database
from models import Transaction


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tracker", description="Expense Tracker CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # add
    add_p = subparsers.add_parser("add", help="Add a new transaction")
    add_p.add_argument("--amount", type=Decimal, required=True)
    add_p.add_argument("--category", required=True)
    add_p.add_argument("--description", default="")
    add_p.add_argument("--date", type=str, default=None)

    # list
    list_p = subparsers.add_parser("list", help="List transactions")
    list_p.add_argument("--category")
    list_p.add_argument("--from-date")
    list_p.add_argument("--to-date")

    # report
    subparsers.add_parser("report", help="Generate spending report")

    # import
    import_p = subparsers.add_parser("import", help="Import transactions from CSV")
    import_p.add_argument("file", type=Path)

    # budget
    budget_p = subparsers.add_parser("budget", help="Set a category budget")
    budget_p.add_argument("--category", required=True)
    budget_p.add_argument("--limit", type=Decimal, required=True)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    db = Database(Path("finance.db"))

    if args.command == "add":
        t = Transaction(
            amount=args.amount,
            category=args.category,
            description=args.description,
            date=parse_date(args.date) if args.date else date.today(),
        )
        t_id = db.insert_transaction(t)
        print(f"Added transaction #{t_id}: {t.category} ${t.amount}")

    elif args.command == "list":
        txns = db.list_transactions(
            category=args.category,
            from_date=args.from_date,
            to_date=args.to_date,
        )
        # ... print formatted table
```

**Dry run --- parsing an `add` command:**

```bash
$ python tracker.py add --amount 25 --category Food --description Lunch
```

When `parser.parse_args()` runs:

1. `args.command` -> `"add"`
2. `args.amount` -> `Decimal("25")` (argparse auto-calls `Decimal()` on the string)
3. `args.category` -> `"Food"`
4. `args.description` -> `"Lunch"`

No manual string splitting, no `sys.argv[1]` checks. If the user forgets `--amount` they get a clear error: `the following arguments are required: --amount`.

**Why argparse over sys.argv?** Three reasons:

- **Automatic `--help`** --- `tracker.py add --help` prints the usage, arguments, and descriptions for the `add` subcommand.
- **Type validation** --- `type=Decimal` converts and rejects invalid input immediately.
- **Subcommand support** --- `add_subparsers()` gives you nested command trees (`add`, `list`, `report`, etc.) with separate arguments per command. Doing this with raw `sys.argv` is error-prone and verbose.''',
        ),
        Section(
            heading="Step 5: Importing Bank CSVs (importers.py)",
            content='''\
```python
import csv
from pathlib import Path
from decimal import Decimal
from datetime import datetime
from models import Transaction


COLUMN_MAP = {
    "chase": {"date": 0, "description": 1, "amount": 3},
    "wells_fargo": {"date": 0, "description": 2, "amount": 4},
    "default": {"date": 0, "description": 1, "amount": 2},
}


def detect_bank(headers: list[str]) -> str:
    if "Posting Date" in headers:
        return "chase"
    if "Transaction Date" in headers:
        return "wells_fargo"
    return "default"


def parse_amount(raw: str) -> Decimal:
    cleaned = raw.strip().replace("$", "").replace(",", "")
    return Decimal(cleaned)


def import_csv(path: Path, bank: str | None = None) -> list[Transaction]:
    transactions = []
    with open(path, newline="") as f:
        reader = csv.reader(f)
        headers = next(reader)
        bank = bank or detect_bank(headers)
        mapping = COLUMN_MAP.get(bank, COLUMN_MAP["default"])

        for row_num, row in enumerate(reader, start=2):
            if not row or all(cell.strip() == "" for cell in row):
                continue  # skip empty rows
            amount = parse_amount(row[mapping["amount"]])
            desc = row[mapping["description"]].strip()
            raw_date = row[mapping["date"]].strip()
            parsed_date = datetime.strptime(raw_date, "%m/%d/%Y").date()
            tx = Transaction(amount=abs(amount), category="Uncategorized",
                             description=desc, date=parsed_date)
            transactions.append(tx)
    return transactions
```

**Why bank-specific column mapping?** Chase exports `Posting Date, Description, ... Amount`. Wells Fargo uses `Transaction Date, ... Description, Amount`. A generic "column A is date, column B is amount" breaks on the first non-standard CSV. The `detect_bank()` function reads headers, picks the right mapping, and parses correctly.

**Dry run --- importing a CSV:**

Given `sample.csv`:
```
Posting Date,Description,Reference,Amount,Category
06/01/2026,Grocery Run,REF001,-87.23,Food
06/03/2026,Gas Station,REF002,-45.00,Transport
```

```python
>>> from importers import import_csv
>>> from pathlib import Path

>>> txns = import_csv(Path("sample.csv"))
# 1. detect_bank sees "Posting Date" in headers -> "chase"
# 2. COLUMN_MAP["chase"] -> date=0, description=1, amount=3
# 3. Row 1: date="06/01/2026", desc="Grocery Run", amount="$ -87.23"
# 4. parse_amount("-87.23") -> Decimal("-87.23")
# 5. abs(Decimal("-87.23")) -> Decimal("87.23") -- expenses are negative in bank exports
# 6. Transaction(amount=87.23, description="Grocery Run", ...)

>>> len(txns)
2
>>> txns[0].amount
Decimal('87.23')
>>> txns[0].description
'Grocery Run'
```

The `abs()` call handles the fact that banks record expenses as negative debits --- our model stores them as positive amounts. Empty rows are skipped so trailing newlines don't crash the import.''',
        ),
        Section(
            heading="Step 6: Spending Analytics (analysis.py)",
            content='''\
```python
from collections import defaultdict
from decimal import Decimal
from datetime import date
from models import Transaction


def by_category(txns: list[Transaction]) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = defaultdict(Decimal)
    for t in txns:
        totals[t.category] += t.amount
    return dict(totals)


def month_over_month(txns: list[Transaction]) -> dict[str, Decimal]:
    monthly: dict[str, Decimal] = defaultdict(Decimal)
    for t in txns:
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
```

**Why percentage change instead of raw difference?** A $50 increase on a $10 baseline (+500%) tells a very different story than $50 on $1000 (+5%). Percentage change normalizes spending growth across different categories and bases, making trends comparable.

**Dry run --- month-over-month analysis:**

```python
>>> from analysis import month_over_month, percentage_change, detect_trends
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

>>> month_over_month(txns)
{'2026-01': Decimal('180'), '2026-02': Decimal('270')}

>>> percentage_change(Decimal("180"), Decimal("270"))
Decimal('50.000')   # +50% increase from Jan to Feb

>>> detect_trends(txns)
[{'month': '2026-02', 'previous': '2026-01', 'change_pct': Decimal('50.000'), 'direction': 'up'}]
```

Jan total: 100 + 50 + 30 = **$180**
Feb total: 200 + 70 = **$270**
Change: ((270 - 180) / 180) x 100 = **+50%**

The `by_category()` function gives you breakdowns per category so `report` can show "Food: $300, Transport: $100" alongside the monthly trends.''',
        ),
        Section(
            heading="Step 7: Reports with ASCII Charts (reports.py)",
            content='''\
```python
from decimal import Decimal
from models import Transaction
from analysis import by_category, detect_trends


def category_chart(totals: dict[str, Decimal], width: int = 30) -> str:
    if not totals:
        return "(no data)"
    max_val = max(totals.values())
    lines = []
    for category, amount in sorted(totals.items(), key=lambda x: -x[1]):
        bar_len = int((amount / max_val) * width) if max_val > 0 else 0
        bar = "\\u2588" * bar_len
        lines.append(f"  {category:15s} ${amount:>8.2f}  {bar}")
    return "\\n".join(lines)


def monthly_summary(txns: list[Transaction]) -> str:
    cats = by_category(txns)
    trends = detect_trends(txns)
    lines = ["--- Spending Summary ---", ""]
    lines.append("By Category:")
    lines.append(category_chart(cats))
    lines.append("")
    if trends:
        lines.append("Trends (month-over-month):")
        for t in trends:
            arrow = "\\u25b2" if t["direction"] == "up" else "\\u25bc"
            lines.append(f"  {t['month']}  {arrow} {t['change_pct']:.1f}% vs {t['previous']}")
    return "\\n".join(lines)
```

**Why ASCII bar charts?** Zero dependencies --- no matplotlib, no terminal color libraries, no HTML. Works in every terminal emulator from `xterm` to Windows Command Prompt. The block character `\\u2588` (U+2588) is widely supported, but the same logic works with simple `#` characters if needed.

**Dry run --- generating a category chart:**

```python
>>> from reports import category_chart
>>> from decimal import Decimal

>>> data = {"Food": Decimal("150"), "Transport": Decimal("45"), "Coffee": Decimal("30")}
>>> print(category_chart(data, width=20))
  Food            $  150.00  \\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588
  Transport       $   45.00  \\u2588\\u2588\\u2588\\u2588\\u2588\\u2588
  Coffee          $   30.00  \\u2588\\u2588\\u2588\\u2588

# How the math works:
# max_val = 150
# Food bar:     (150 / 150) * 20 = 20  \\u2588\\u2588... (20 chars)
# Transport bar: (45 / 150) * 20 = 6   \\u2588\\u2588\\u2588\\u2588\\u2588\\u2588
# Coffee bar:    (30 / 150) * 20 = 4   \\u2588\\u2588\\u2588\\u2588
```

The chart scales proportionally --- the largest category always fills the full width. `sorted(..., key=lambda x: -x[1])` ensures highest-spending categories appear first. The `monthly_summary()` function combines category breakdown, bar chart, and trend arrows into one printable report.''',
        ),
        Section(
            heading="Step 8: Running and Extensions",
            content='''\
**Running the tracker --- full workflow:**

```bash
# Add transactions
python tracker.py add --amount 45.00 --category Food --description "Groceries"
python tracker.py add --amount 30.00 --category Transport --description "Gas"
python tracker.py add --amount 5.50 --category Coffee --description "Latte"

# Import from a bank CSV
python tracker.py import downloads/statement.csv

# Set monthly budgets
python tracker.py budget --category Food --limit 500

# View spending report with ASCII chart
python tracker.py report
```

Example output of `report`:
```
--- Spending Summary ---

By Category:
  Food            $  495.00  \\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588
  Transport       $  120.00  \\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588\\u2588
  Coffee          $   55.00  \\u2588\\u2588\\u2588

Trends (month-over-month):
  2026-02  \\u25b2 +50.0% vs 2026-01
  2026-03  \\u25bc -12.5% vs 2026-02
```

**What to try next** --- extend the project on your own:

| Feature | What you'd touch |
|---|---|
| **Budget enforcement** | `database.py` --- compare `spent_so_far` to `budget.monthly_limit` in `add` |
| **Recurring transactions** | `models.py` --- add `RecurringRule`; `tracker.py` --- new `schedule` subcommand |
| **PDF export** | `reports.py` --- use `reportlab` or `fpdf` to generate a PDF monthly statement |
| **Web dashboard** | Add Flask/FastAPI in a `web/` dir; reuse `analysis.py` and `reports.py` unchanged |
| **Category aliases** | `importers.py` --- fuzzy-match bank descriptions to canonical categories |
| **SQLite date queries** | `analysis.py` --- `WHERE date BETWEEN ? AND ?` for custom date ranges |

The modular design means you can add any of these by editing one or two files without touching the rest. That's the power of separating CLI, data, analytics, and presentation.''',
        ),
    ],
)
