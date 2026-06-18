from decimal import Decimal
from datetime import date
from models import Transaction, Budget


def test_transaction_creation():
    t = Transaction(
        amount=Decimal("25.50"),
        category="Food",
        description="Lunch",
        date=date(2026, 6, 1),
    )
    assert t.amount == Decimal("25.50")
    assert t.category == "Food"
    assert t.description == "Lunch"
    assert t.date == date(2026, 6, 1)
    assert t.id is None
    assert t.type == "expense"


def test_transaction_to_dict():
    t = Transaction(
        amount=Decimal("25.50"),
        category="Food",
        date=date(2026, 6, 1),
        id=1,
    )
    d = t.to_dict()
    assert d["amount"] == "25.50"
    assert d["category"] == "Food"
    assert d["id"] == 1
    assert d["type"] == "expense"


def test_transaction_from_dict():
    data = {
        "id": 1,
        "amount": "25.50",
        "category": "Food",
        "description": "Lunch",
        "date": "2026-06-01",
        "type": "expense",
    }
    t = Transaction.from_dict(data)
    assert t.amount == Decimal("25.50")
    assert t.category == "Food"
    assert t.id == 1
    assert t.date == date(2026, 6, 1)


def test_transaction_from_dict_round_trip():
    original = Transaction(
        amount=Decimal("99.99"),
        category="Utilities",
        description="Electric bill",
        date=date(2026, 6, 15),
        id=42,
        type="expense",
    )
    restored = Transaction.from_dict(original.to_dict())
    assert original == restored


def test_budget_creation():
    b = Budget(category="Food", monthly_limit=Decimal("500"))
    assert b.category == "Food"
    assert b.monthly_limit == Decimal("500")


def test_budget_to_dict():
    b = Budget(category="Food", monthly_limit=Decimal("500"))
    d = b.to_dict()
    assert d["category"] == "Food"
    assert d["monthly_limit"] == "500"


def test_budget_from_dict():
    data = {"category": "Food", "monthly_limit": "500"}
    b = Budget.from_dict(data)
    assert b.category == "Food"
    assert b.monthly_limit == Decimal("500")
