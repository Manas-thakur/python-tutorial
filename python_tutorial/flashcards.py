import random
import time

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from .content import discover_phases, get_quiz_questions

console = Console()


def run_flashcard_session(phase_number: int = None):
    """Run a flashcard review session for one or all phases."""
    phases = discover_phases()

    card_scores: dict[tuple[int, int, int], int] = {}
    all_cards: list[tuple[int, int, int, str, str]] = []

    for p in phases:
        if phase_number is not None and p.number != phase_number:
            continue
        for t in p.topics:
            questions = get_quiz_questions(t)
            for qi, q in enumerate(questions):
                all_cards.append((p.number, t.number, qi, q.question, q.answer))

    if not all_cards:
        console.print("[yellow]No flashcards available.[/]")
        return

    random.shuffle(all_cards)

    phase_label = f"Phase {phase_number}" if phase_number else "All Phases"
    console.print(Panel(
        f"[bold cyan]Flashcard Review: {phase_label}[/]\n\n"
        f"[bold]{len(all_cards)} cards[/] loaded. You'll be shown a question - "
        "think of the answer, then reveal it. Rate yourself.",
        border_style="cyan",
    ))

    correct = 0
    total = len(all_cards)
    start = time.time()

    for phase_num, topic_num, qi, question, answer in all_cards:
        phase_label = f"P{phase_num}"
        console.print(f"\n[bold yellow][{phase_label}.{topic_num}] Q:[/] {question}")

        Prompt.ask("[dim]Press Enter when ready to see the answer[/]", default="")
        console.print(f"  [bold green]A:[/] {answer}")

        rating = Prompt.ask(
            "[bold]How did you do?[/]",
            choices=["1", "2", "3", "4"],
            default="2",
        )
        rating = int(rating)
        if rating >= 3:
            correct += 1

        card_scores[(phase_num, topic_num, qi)] = rating

    elapsed = time.time() - start
    mins = int(elapsed // 60)
    secs = int(elapsed % 60)

    console.print()
    console.print(Panel(
        f"[bold]Session Summary[/]\n\n"
        f"Cards reviewed: {total}\n"
        f"Got it right: {correct}/{total} ({correct / total * 100:.0f}%)\n"
        f"Time: {mins}m {secs}s",
        border_style="green",
    ))

    weak_cards = [
        (q, a) for (pn, tn, qi), r in card_scores.items()
        if r <= 2
        for p in [p for p in discover_phases() if p.number == pn]
        for t in p.topics if t.number == tn
        for qq in [get_quiz_questions(t)]
        for qa in [(qq[qi].question, qq[qi].answer)] if r <= 2
    ][:3]

    if weak_cards:
        console.print("\n[bold yellow]Review these weak cards:[/]")
        for i, (q, a) in enumerate(weak_cards, 1):
            console.print(f"  {i}. [dim]Q:[/] {q}")
            console.print(f"     [dim]A:[/] {a}")
