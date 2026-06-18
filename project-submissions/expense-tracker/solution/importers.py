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


def is_duplicate(
    t: Transaction, existing: list[Transaction]
) -> bool:
    for ex in existing:
        if (
            ex.amount == t.amount
            and ex.description == t.description
            and ex.date == t.date
        ):
            return True
    return False


def import_csv(
    filepath: str, bank: Optional[str] = None
) -> list[Transaction]:
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

                for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y", "%m-%d-%Y"):
                    try:
                        parsed_date = datetime.strptime(
                            raw_date, fmt
                        ).date()
                        break
                    except ValueError:
                        continue
                else:
                    print(
                        f"Row {row_num}: skipping — "
                        f"unrecognized date '{raw_date}'"
                    )
                    continue

                try:
                    category = row[mapping["category"]].strip()
                except (IndexError, KeyError):
                    category = "Uncategorized"

                tx_type = "expense" if amount < 0 else "income"
                t = Transaction(
                    amount=abs(amount),
                    category=category,
                    description=desc,
                    date=parsed_date,
                    type=tx_type,
                )

                if not is_duplicate(t, transactions):
                    transactions.append(t)
                else:
                    print(
                        f"Row {row_num}: skipping duplicate — "
                        f"{desc} ${amount}"
                    )

            except (ValueError, IndexError) as e:
                print(f"Row {row_num}: skipping — {e}")
                continue

    return transactions
