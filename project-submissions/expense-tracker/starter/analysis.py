# Spending Analytics
# TODO: Calculate total spending by category for a period
# TODO: Find top spending categories
# TODO: Calculate month-over-month change
# TODO: Detect spending trends (increasing/decreasing)
# TODO: Compare actual vs budget

from collections import defaultdict
from decimal import Decimal
from datetime import date
from models import Transaction


def spending_by_category(
    txns: list[Transaction], period: str = "month"
) -> dict[str, Decimal]:
    # TODO: aggregate expense amounts by category
    pass


def month_over_month(
    txns: list[Transaction],
) -> dict[str, Decimal]:
    # TODO: aggregate expense amounts by year-month key
    pass


def percentage_change(before: Decimal, after: Decimal) -> Decimal:
    # TODO: calculate ((after - before) / before) * 100
    pass


def detect_trends(txns: list[Transaction]) -> list[dict]:
    # TODO: compute month-over-month spending trends
    pass


def budget_analysis(
    spending: dict[str, Decimal], budgets: dict[str, Decimal]
) -> list[dict]:
    # TODO: compare actual spending against budgets
    pass
