from decimal import Decimal
from models import Transaction
from analysis import spending_by_category, detect_trends, budget_analysis


def category_chart(
    totals: dict[str, Decimal], width: int = 30
) -> str:
    if not totals:
        return "(no data)"
    max_val = max(totals.values())
    lines = []
    for category, amount in sorted(
        totals.items(), key=lambda x: -x[1]
    ):
        bar_len = (
            int((amount / max_val) * width) if max_val > 0 else 0
        )
        bar = "\u2588" * bar_len
        lines.append(
            f"  {category:15s} ${amount:>8.2f}  {bar}"
        )
    return "\n".join(lines)


def monthly_report(
    txns: list[Transaction], year: int, month: int
) -> str:
    total = sum(t.amount for t in txns if t.type == "expense")
    income = sum(t.amount for t in txns if t.type == "income")
    cats = spending_by_category(txns)
    trends = detect_trends(txns)

    lines = [
        f"--- Spending Report: {year}-{month:02d} ---",
        "",
    ]
    lines.append(f"Total expenses: ${total:.2f}")
    lines.append(f"Total income:   ${income:.2f}")
    lines.append(f"Net:            ${income - total:.2f}")
    lines.append("")

    if cats:
        lines.append("By Category:")
        lines.append(category_chart(cats))
        lines.append("")

    if trends:
        lines.append("Trends (month-over-month):")
        for t in trends:
            arrow = (
                "\u25b2" if t["direction"] == "up" else "\u25bc"
            )
            lines.append(
                f"  {t['month']}  {arrow} {t['change_pct']:.1f}% vs {t['previous']}"
            )
        lines.append("")

    budgets = _load_and_compare_budgets(cats)
    if budgets:
        lines.append("Budget Check:")
        lines.append(
            f"  {'Category':<15} {'Budget':>8} {'Spent':>8} "
            f"{'Remain':>8} {'Use%':>6} Status"
        )
        for b in budgets:
            status = "\u2713" if b["on_track"] else "\u26a0 OVER"
            lines.append(
                f"  {b['category']:<15} ${b['budget']:>7.2f} "
                f"${b['spent']:>7.2f} ${b['remaining']:>7.2f} "
                f"{b['pct_used']:>5.1f}% {status}"
            )

    return "\n".join(lines)


def _load_and_compare_budgets(
    cats: dict[str, Decimal],
) -> list[dict]:
    try:
        from database import get_budgets

        budgets = get_budgets()
        if not budgets:
            return []
        budget_dict = {b.category: b.monthly_limit for b in budgets}
        return budget_analysis(cats, budget_dict)
    except Exception:
        return []
