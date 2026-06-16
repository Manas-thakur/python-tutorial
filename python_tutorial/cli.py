import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.box import ROUNDED

from .models import Phase, Topic
from .content import discover_phases, get_phase, get_topic, get_quiz_questions
from .renderer import (
    console,
    show_banner,
    show_phase_list,
    show_topic_list,
    show_topic_summary,
    render_section,
    render_completion,
    render_quiz_result,
)
from .quiz import run_quiz
from .progress import ProgressTracker

app = typer.Typer(
    name="python-tutorial",
    help="Interactive Python tutorial from fundamentals to AI",
    add_completion=False,
    rich_markup_mode="rich",
)
progress = ProgressTracker()

CONTENT_DIR_OPTION = typer.Option(
    None,
    "--content-dir",
    "-c",
    help="Path to the content directory (defaults to bundled content)",
    exists=True,
    file_okay=False,
    dir_okay=True,
    readable=True,
)


def _load_phases(content_dir: Optional[Path] = None) -> list[Phase]:
    return discover_phases(content_dir)


def _get_phase_or_exit(num: int, phases: list[Phase]) -> Phase:
    for p in phases:
        if p.number == num:
            return p
    console.print(f"[red]Phase {num} not found.[/]")
    raise typer.Exit(code=1)


def _get_topic_or_exit(phase: Phase, num: int) -> Topic:
    if num < 1 or num > len(phase.topics):
        console.print(f"[red]Topic {num} not found in {phase.label}.[/]")
        raise typer.Exit(code=1)
    return phase.topics[num - 1]


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context, content_dir: Optional[Path] = CONTENT_DIR_OPTION):
    """🐍 Python Interactive Tutorial - Learn Python from the terminal."""
    if ctx.invoked_subcommand is not None:
        return
    interactive_loop(content_dir)


def interactive_loop(content_dir: Optional[Path] = None):
    """Main interactive loop."""
    try:
        show_banner()
        phases = _load_phases(content_dir)

        while True:
            show_phase_list(phases, progress)
            choice = Prompt.ask(
                "\n[bold]Select a phase (number)[/] or [bold cyan]q[/] to quit",
                default="q",
            )
            if choice.lower() in ("q", "quit", "exit"):
                console.print("[dim]Happy coding! 🐍[/]")
                break

            if not choice.isdigit():
                continue
            phase_num = int(choice)
            phase = _get_phase_or_exit(phase_num, phases)

            phase_menu(phase, content_dir)

    except (KeyboardInterrupt, EOFError):
        console.print("\n[dim]Goodbye! 👋[/]")
        sys.exit(0)


def phase_menu(phase: Phase, content_dir: Optional[Path] = None):
    """Menu for a specific phase."""
    while True:
        show_topic_list(phase, progress)
        console.print("\n[dim]Options:[/]")
        console.print("  [bold]number[/] - View topic")
        console.print("  [bold]q[/] - Back to phase list")
        console.print("  [bold]quiz[/] - Take quiz for all topics in this phase")
        console.print("  [bold]progress[/] - View detailed progress")

        choice = Prompt.ask(f"\n[bold]{phase.label}[/]", default="q")

        if choice.lower() in ("q", "back"):
            break
        if choice.lower() == "quiz":
            run_phase_quiz(phase, content_dir)
            continue
        if choice.lower() == "progress":
            show_detailed_progress()
            continue
        if choice.isdigit():
            topic_num = int(choice)
            topic = _get_topic_or_exit(phase, topic_num)
            view_topic(phase.number, topic, content_dir)


def view_topic(phase_num: int, topic: Topic, content_dir: Optional[Path] = None):
    """Display a topic section by section with quiz at the end."""
    show_topic_summary(topic)
    sections = topic.sections
    total = len(sections)

    for i, section in enumerate(sections, start=1):
        render_section(section, i, total, topic.title)
        if i < total:
            Prompt.ask("[dim]Press Enter to continue[/]", default="")
        else:
            Prompt.ask("[dim]Press Enter for Knowledge Check[/]", default="")

    # Quiz
    questions = get_quiz_questions(topic)
    if questions:
        correct, total_q = run_quiz(questions)
        render_quiz_result(correct, total_q)

    progress.mark_complete(phase_num, topic.number)
    render_completion(phase_num, topic.number, topic.title)


def run_phase_quiz(phase: Phase, content_dir: Optional[Path] = None):
    """Quiz across all topics in a phase."""
    all_questions = []
    for topic in phase.topics:
        questions = get_quiz_questions(topic)
        for q in questions:
            all_questions.append(q)

    if not all_questions:
        console.print("[yellow]No quiz questions found in this phase.[/]")
        return

    console.print(Panel(
        f"[bold cyan]📝 Phase Quiz: {phase.label}[/]\n\n"
        f"[bold]{len(all_questions)} questions across {len(phase.topics)} topics[/]",
        border_style="cyan",
    ))

    correct, total = run_quiz(all_questions)
    render_quiz_result(correct, total)


# ---- CLI Commands ----


@app.command()
def list(content_dir: Optional[Path] = CONTENT_DIR_OPTION):
    """List all phases and their topics."""
    show_banner()
    phases = _load_phases(content_dir)
    show_phase_list(phases, progress)


@app.command()
def view(
    phase: int = typer.Argument(..., help="Phase number"),
    topic: int = typer.Argument(..., help="Topic number"),
    content_dir: Optional[Path] = CONTENT_DIR_OPTION,
):
    """View a specific topic by phase and topic number."""
    phases = _load_phases(content_dir)
    p = _get_phase_or_exit(phase, phases)
    t = _get_topic_or_exit(p, topic)
    view_topic(phase, t, content_dir)


@app.command()
def quiz(
    phase: int = typer.Argument(None, help="Phase number (optional — all phases if omitted)"),
    content_dir: Optional[Path] = CONTENT_DIR_OPTION,
):
    """Take a quiz for a phase or all phases."""
    phases = _load_phases(content_dir)

    if phase is not None:
        p = _get_phase_or_exit(phase, phases)
        run_phase_quiz(p, content_dir)
        return

    # Quiz for all phases
    all_q = []
    for p in phases:
        for t in p.topics:
            all_q.extend(get_quiz_questions(t))

    console.print(Panel(
        f"[bold cyan]📝 Full Roadmap Quiz[/]\n\n"
        f"[bold]{len(all_q)} questions across all phases[/]",
        border_style="cyan",
    ))
    correct, total = run_quiz(all_q)
    render_quiz_result(correct, total)


@app.command()
def status(content_dir: Optional[Path] = CONTENT_DIR_OPTION):
    """Show your learning progress."""
    show_detailed_progress()


def show_detailed_progress():
    """Display detailed progress across all phases."""
    phases = _load_phases()
    if not phases:
        console.print("[red]No content found. Use --content-dir to specify a path.[/]")
        return

    total_done = 0
    total_all = 0

    console.print(f"\n[bold cyan]📊 Learning Progress[/]")
    console.print(f"[dim]Progress saved to: {Path.home() / '.python_tutorial_progress.json'}[/]\n")

    table = Table(box=ROUNDED, header_style="bold magenta")
    table.add_column("Phase", style="bold yellow")
    table.add_column("Done", justify="right")
    table.add_column("Total", justify="right")
    table.add_column("Progress", width=30)

    for p in phases:
        done, total = progress.get_phase_progress(p.number, len(p.topics))
        total_done += done
        total_all += total
        pct = f"{done}/{total}"
        bar = _bar(done, total, 25)
        table.add_row(p.label, str(done), str(total), bar)

    bar = _bar(total_done, total_all, 25)
    table.add_row(
        "[bold]Total[/]", str(total_done), str(total_all), f"[bold]{bar}[/]"
    )
    console.print(table)

    pct = (total_done / total_all * 100) if total_all else 0
    if pct == 100:
        console.print("\n[bold green]🎉 All topics completed! You're a Python master![/]")
    else:
        console.print(f"\n[cyan]Overall progress: {pct:.1f}%[/]")


def _bar(done: int, total: int, width: int) -> str:
    if total == 0:
        return "░" * width
    filled = int((done / total) * width)
    return "█" * filled + "░" * (width - filled)


@app.command()
def reset():
    """Reset all progress."""
    if Confirm.ask("[red]This will delete ALL progress. Are you sure?[/]"):
        progress.reset()
        console.print("[green]Progress reset successfully.[/]")
