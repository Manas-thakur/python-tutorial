# CSV Importer
# TODO: Detect CSV format (columns, delimiter)
# TODO: Parse common bank CSV formats
# TODO: Map bank columns to internal fields
# TODO: Validate and clean data
# TODO: Handle duplicates (skip or warn)
# TODO: Return list of Transaction objects

import csv
from pathlib import Path
from decimal import Decimal
from datetime import datetime
from typing import Optional
from models import Transaction


def detect_bank(headers: list[str]) -> str:
    # TODO: identify bank from CSV headers
    pass


def parse_amount(raw: str) -> Decimal:
    # TODO: clean and convert amount string to Decimal
    pass


def is_duplicate(
    t: Transaction, existing: list[Transaction]
) -> bool:
    # TODO: check if transaction already exists in batch
    pass


def import_csv(
    filepath: str, bank: Optional[str] = None
) -> list[Transaction]:
    # TODO: read CSV file, parse rows, return Transaction list
    pass
