# Data Models
# TODO: Transaction dataclass: id, amount, category, date, description, type
# TODO: Budget dataclass: category, monthly_limit
# TODO: to_dict / from_dict methods for serialization

from dataclasses import dataclass
from decimal import Decimal
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class Transaction:
    # TODO: define fields: amount, category, description, date, id, type
    pass

    def to_dict(self) -> dict:
        # TODO: implement this
        pass

    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        # TODO: implement this
        pass


@dataclass(frozen=True)
class Budget:
    # TODO: define fields: category, monthly_limit
    pass

    def to_dict(self) -> dict:
        # TODO: implement this
        pass

    @classmethod
    def from_dict(cls, data: dict) -> "Budget":
        # TODO: implement this
        pass
