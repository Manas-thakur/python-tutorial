# Analysis Tests
# TODO: Test spending_by_category with sample data
# TODO: Test month_over_month calculation
# TODO: Test budget_analysis overspend detection

from decimal import Decimal
from datetime import date
from models import Transaction
from analysis import (
    spending_by_category,
    month_over_month,
    percentage_change,
    detect_trends,
    budget_analysis,
)


def test_spending_by_category():
    # TODO: verify category totals
    pass


def test_month_over_month():
    # TODO: verify monthly aggregation
    pass


def test_percentage_change():
    # TODO: verify calculation
    pass


def test_budget_analysis_on_track():
    # TODO: verify under-budget returns on_track=True
    pass


def test_budget_analysis_over_budget():
    # TODO: verify over-budget returns on_track=False
    pass
