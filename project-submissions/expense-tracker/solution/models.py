from dataclasses import dataclass
from decimal import Decimal
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class Transaction:
    amount: Decimal
    category: str
    description: str = ""
    date: date = date.today()
    id: Optional[int] = None
    type: str = "expense"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "amount": str(self.amount),
            "category": self.category,
            "description": self.description,
            "date": self.date.isoformat(),
            "type": self.type,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        return cls(
            id=data.get("id"),
            amount=Decimal(data["amount"]),
            category=data["category"],
            description=data.get("description", ""),
            date=(
                date.fromisoformat(data["date"])
                if isinstance(data["date"], str)
                else data["date"]
            ),
            type=data.get("type", "expense"),
        )


@dataclass(frozen=True)
class Budget:
    category: str
    monthly_limit: Decimal

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "monthly_limit": str(self.monthly_limit),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Budget":
        return cls(
            category=data["category"],
            monthly_limit=Decimal(data["monthly_limit"]),
        )
