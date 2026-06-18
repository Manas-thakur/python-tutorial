# Expense Tracker CLI
# TODO: Use argparse with subcommands: add, list, report, import, budget
# TODO: add -- create a new transaction
# TODO: list -- show transactions with filters (date range, category)
# TODO: report -- generate monthly summary
# TODO: import -- parse CSV and bulk insert
# TODO: budget -- set and check category budgets

import argparse
from pathlib import Path
from decimal import Decimal
from datetime import date, datetime
from database import (
    init_db,
    insert_transaction,
    get_transactions,
    set_budget,
    get_budgets,
)
from models import Transaction, Budget
from reports import monthly_report
from importers import import_csv


def build_parser() -> argparse.ArgumentParser:
    # TODO: add subcommands: add, list, report, import, budget
    # TODO: each subcommand needs its own arguments
    pass


def main():
    # TODO: initialize database
    # TODO: parse arguments
    # TODO: dispatch to command handler based on args.command
    pass


if __name__ == "__main__":
    main()
