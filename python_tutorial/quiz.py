from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from .models import QuizQuestion

console = Console()


def run_quiz(questions: list[QuizQuestion]) -> tuple[int, int]:
    """Run an interactive quiz. Returns (correct, total)."""
    if not questions:
        console.print("[yellow]No quiz questions available for this topic.[/]")
        return 0, 0

    correct = 0
    total = len(questions)

    console.print(Panel(
        "[bold cyan]Knowledge Check[/]\n\n"
        "Test your understanding of the topic.",
        border_style="cyan",
    ))

    for i, q in enumerate(questions, start=1):
        console.print(f"\n[bold yellow]Q{i}.[/] {q.question}")

        if q.is_mcq:
            for j, opt in enumerate(q.options, start=1):
                console.print(f"  [dim]{j}.[/] {opt}")
            answer = Prompt.ask(
                "[bold]Your answer[/]",
                choices=[str(k) for k in range(1, len(q.options) + 1)],
                default="1",
            )
            choice = int(answer) - 1
            if choice == q.answer_index:
                console.print("  [bold green]Correct![/]")
                correct += 1
            else:
                console.print(f"  [bold red]Incorrect.[/] The answer was: [green]{q.answer}[/]")
        else:
            # Simple Q&A - think then reveal
            console.print("[dim]Press Enter when ready to see the answer...[/]")
            Prompt.ask("", default="")
            console.print(f"  [bold]Answer:[/] [green]{q.answer}[/]")
            ok = Prompt.ask("[bold]Did you get it right? (y/n)[/]", default="y")
            if ok.strip().lower() == "y":
                correct += 1

    return correct, total


