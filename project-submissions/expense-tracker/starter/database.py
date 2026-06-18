# SQLite Database Layer
# TODO: Initialize database and create tables
# TODO: insert_transaction(t) -- add a new transaction
# TODO: get_transactions(filters) -- query with date/category filters
# TODO: get_monthly_summary(year, month) -- aggregate by category
# TODO: set_budget / get_budgets -- budget CRUD

import sqlite3
from decimal import Decimal
from datetime import date
from typing import Optional
from models import Transaction, Budget

DB_FILE = "expenses.db"


def init_db(db_path: str = DB_FILE):
    # TODO: create transactions and budgets tables
    pass


def insert_transaction(t: Transaction, db_path: str = DB_FILE) -> int:
    # TODO: insert a transaction row, return lastrowid
    pass


def get_transactions(
    category: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db_path: str = DB_FILE,
) -> list[Transaction]:
    # TODO: build dynamic query with optional filters
    pass


def get_monthly_summary(year: int, month: int, db_path: str = DB_FILE) -> list[dict]:
    # TODO: aggregate spending by category for a given month
    pass


def set_budget(b: Budget, db_path: str = DB_FILE):
    # TODO: insert or replace a budget row
    pass


def get_budgets(db_path: str = DB_FILE) -> list[Budget]:
    # TODO: return all budgets
    pass
