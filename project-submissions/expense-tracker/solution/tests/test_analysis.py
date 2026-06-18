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


def _sample_transactions():
    return [
        Transaction(
            amount=Decimal("100"),
            category="Food",
            date=date(2026, 1, 5),
        ),
        Transaction(
            amount=Decimal("50"),
            category="Food",
            date=date(2026, 1, 12),
        ),
        Transaction(
            amount=Decimal("30"),
            category="Transport",
            date=date(2026, 1, 15),
        ),
        Transaction(
            amount=Decimal("200"),
            category="Food",
            date=date(2026, 2, 3),
        ),
        Transaction(
            amount=Decimal("70"),
            category="Transport",
            date=date(2026, 2, 10),
        ),
    ]


def test_spending_by_category():
    txns = _sample_transactions()
    result = spending_by_category(txns)
    assert result["Food"] == Decimal("350")
    assert result["Transport"] == Decimal("100")


def test_spending_by_category_ignores_income():
    txns = _sample_transactions()
    txns.append(
        Transaction(
            amount=Decimal("5000"),
            category="Salary",
            date=date(2026, 1, 1),
            type="income",
        )
    )
    result = spending_by_category(txns)
    assert "Salary" not in result


def test_month_over_month():
    txns = _sample_transactions()
    result = month_over_month(txns)
    assert result["2026-01"] == Decimal("180")
    assert result["2026-02"] == Decimal("270")


def test_percentage_change():
    assert percentage_change(
        Decimal("180"), Decimal("270")
    ) == Decimal("50.000")
    assert percentage_change(
        Decimal("200"), Decimal("100")
    ) == Decimal("-50.000")
    assert percentage_change(Decimal("0"), Decimal("100")) == Decimal("0")


def test_detect_trends():
    txns = _sample_transactions()
    trends = detect_trends(txns)
    assert len(trends) == 1
    assert trends[0]["month"] == "2026-02"
    assert trends[0]["direction"] == "up"


def test_budget_analysis_on_track():
    spending = {"Food": Decimal("300"), "Transport": Decimal("100")}
    budgets = {"Food": Decimal("500"), "Transport": Decimal("150")}
    results = budget_analysis(spending, budgets)
    assert all(r["on_track"] for r in results)


def test_budget_analysis_over_budget():
    spending = {"Food": Decimal("600"), "Transport": Decimal("100")}
    budgets = {"Food": Decimal("500"), "Transport": Decimal("150")}
    results = budget_analysis(spending, budgets)
    food_result = [r for r in results if r["category"] == "Food"][0]
    assert not food_result["on_track"]
    assert food_result["remaining"] == Decimal("-100")
