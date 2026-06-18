# Report Generator
# TODO: Monthly report: total, by category, comparison to last month
# TODO: Category breakdown with ASCII bar chart
# TODO: Budget vs actual report

from decimal import Decimal
from models import Transaction
from analysis import spending_by_category, detect_trends, budget_analysis


def category_chart(
    totals: dict[str, Decimal], width: int = 30
) -> str:
    # TODO: generate ASCII bar chart from category totals
    pass


def monthly_report(
    txns: list[Transaction], year: int, month: int
) -> str:
    # TODO: generate full monthly spending report
    pass
