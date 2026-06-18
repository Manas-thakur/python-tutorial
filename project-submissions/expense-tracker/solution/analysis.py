from collections import defaultdict
from decimal import Decimal
from datetime import date
from models import Transaction


def spending_by_category(
    txns: list[Transaction], period: str = "month"
) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = defaultdict(Decimal)
    for t in txns:
        if t.type == "expense":
            totals[t.category] += t.amount
    return dict(totals)


def month_over_month(
    txns: list[Transaction],
) -> dict[str, Decimal]:
    monthly: dict[str, Decimal] = defaultdict(Decimal)
    for t in txns:
        if t.type == "expense":
            key = t.date.strftime("%Y-%m")
            monthly[key] += t.amount
    return dict(monthly)


def percentage_change(before: Decimal, after: Decimal) -> Decimal:
    if before == 0:
        return Decimal("0")
    return ((after - before) / before) * 100


def detect_trends(txns: list[Transaction]) -> list[dict]:
    monthly = month_over_month(txns)
    sorted_months = sorted(monthly.keys())
    trends = []
    for i in range(1, len(sorted_months)):
        prev_m, curr_m = sorted_months[i - 1], sorted_months[i]
        change = percentage_change(monthly[prev_m], monthly[curr_m])
        direction = (
            "up" if change > 0 else ("down" if change < 0 else "flat")
        )
        trends.append(
            {
                "month": curr_m,
                "previous": prev_m,
                "change_pct": change,
                "direction": direction,
            }
        )
    return trends


def budget_analysis(
    spending: dict[str, Decimal], budgets: dict[str, Decimal]
) -> list[dict]:
    results = []
    for category, limit in budgets.items():
        spent = spending.get(category, Decimal("0"))
        remaining = limit - spent
        pct = (spent / limit * 100) if limit > 0 else Decimal("0")
        results.append(
            {
                "category": category,
                "budget": limit,
                "spent": spent,
                "remaining": remaining,
                "pct_used": pct,
                "on_track": spent <= limit,
            }
        )
    return results
