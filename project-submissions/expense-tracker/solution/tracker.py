import argparse
from pathlib import Path
from decimal import Decimal
from datetime import date, datetime
from database import (
    init_db,
    insert_transaction,
    get_transactions,
    get_monthly_summary,
    set_budget,
    get_budgets,
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
    add_p.add_argument(
        "--type", choices=["expense", "income"], default="expense"
    )

    list_p = subparsers.add_parser("list", help="List transactions")
    list_p.add_argument("--category")
    list_p.add_argument("--from-date")
    list_p.add_argument("--to-date")

    subparsers.add_parser("report", help="Generate spending report")

    import_p = subparsers.add_parser(
        "import", help="Import transactions from CSV"
    )
    import_p.add_argument("file", type=Path)

    budget_p = subparsers.add_parser(
        "budget", help="Set a category budget"
    )
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
    print(
        f"{'ID':>4}  {'Date':>10}  {'Category':<15}  "
        f"{'Amount':>8}  {'Description'}"
    )
    print("-" * 60)
    for t in txns:
        print(
            f"{t.id:>4}  {t.date.isoformat():>10}  {t.category:<15}  "
            f"${t.amount:>7.2f}  {t.description}"
        )
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
