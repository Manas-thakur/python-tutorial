from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel
from rich.box import ROUNDED
from rich.markdown import Markdown
from rich.syntax import Syntax

from .models import Phase, Topic
from .content import (
    discover_phases,
    get_phase,
    get_topic,
    get_quiz_questions,
    search_content,
    get_revision_notes,
)
from .renderer import (
    console,
    show_banner,
    show_phase_list,
    show_topic_list,
    show_topic_summary,
    render_section,
    render_completion,
    render_quiz_result,
    render_badges,
)
from .quiz import run_quiz
from .progress import ProgressTracker
from .sandbox import sandbox_loop, run_challenge_code
from .challenges import get_challenge, get_all_challenges, show_challenge
from .flashcards import run_flashcard_session

app = typer.Typer(
    name="python-tutorial",
    help="Interactive Python tutorial: read, code, quiz, and track progress",
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
    """Python Interactive Tutorial - Learn Python from the terminal."""
    if ctx.invoked_subcommand is not None:
        return
    interactive_loop(content_dir)


def interactive_loop(content_dir: Optional[Path] = None):
    """Main interactive loop."""
    try:
        progress.add_streak()
        phases = _load_phases(content_dir)
        show_banner()
        _show_level_banner()

        # Check for bookmark
        bookmark = progress.get_bookmark()
        if bookmark:
            should_resume = Confirm.ask(
                f"[yellow]You were last viewing Phase {bookmark['phase']}, Topic {bookmark['topic']}. "
                "Resume?[/]",
                default=True,
            )
            if should_resume:
                phase = get_phase(bookmark["phase"], content_dir)
                if phase and bookmark["topic"] <= len(phase.topics):
                    topic = phase.topics[bookmark["topic"] - 1]
                    view_topic(bookmark["phase"], topic, content_dir)
                    progress.clear_bookmark()
                    return

        while True:
            show_phase_list(phases, progress)
            _show_global_hints()

            choice = Prompt.ask(
                "\n[bold]Select[/] [dim](phase#, search, flashcards, sandbox, q)[/]",
                default="q",
            )

            if choice.lower() in ("q", "quit", "exit"):
                console.print("\n[dim]Happy coding![/]")
                break
            if choice.lower() in ("search", "s"):
                run_search(phases)
                continue
            if choice.lower() in ("flashcards", "fc"):
                run_flashcard_session()
                continue
            if choice.lower() in ("sandbox", "py", "play"):
                sandbox_loop()
                continue
            if choice.lower() in ("progress", "p", "stats"):
                show_detailed_progress()
                continue
            if choice.lower() in ("badges",):
                render_badges(progress.get_badges())
                continue

            if not choice.isdigit():
                continue
            phase_num = int(choice)
            phase = _get_phase_or_exit(phase_num, phases)

            if not progress.is_phase_unlocked(phase_num):
                prev_phase = next((p for p in phases if p.number == phase_num - 1), None)
                if prev_phase:
                    done, total = progress.get_phase_progress(phase_num - 1, len(prev_phase.topics))
                    console.print(f"[red]Phase {phase.label} is locked[/] - complete 70% of {prev_phase.label} first. [dim]({int(done/total*100)}% done)[/]")
                continue

            phase_menu(phase, content_dir)

    except (KeyboardInterrupt, EOFError):
        console.print("\n[dim]Goodbye![/]")
        sys.exit(0)


def _show_level_banner():
    info = progress.get_level_info()
    bar = _bar(info["xp_current"], info["xp_needed"], 20)
    console.print(f"[bold]Level [cyan]{info['level']}[/]  {bar}  [dim]{info['xp_current']}/{info['xp_needed']} XP[/]")


def _show_global_hints():
    streak = progress.get_streak()
    streak_text = f" streak {streak}d" if streak else ""
    completed = progress.get_total_completed()
    level = progress.get_level()
    xp = progress.get_xp()
    console.print(f"[dim]{completed}/56 topics | Lv.{level} | {xp}XP{streak_text} | "
                  f"search, flashcards, sandbox, progress[/]")


def phase_menu(phase: Phase, content_dir: Optional[Path] = None):
    """Menu for a specific phase."""
    while True:
        show_topic_list(phase, progress)
        console.print("\n[dim]Options:[/]")
        console.print("  [bold]number[/] - View topic")
        console.print("  [bold]c <n>[/] - Do coding challenge for topic n")
        console.print("  [bold]quiz[/] - Take phase quiz")
        console.print("  [bold]flashcards[/] - Review phase flashcards")
        console.print("  [bold]sandbox[/] - Open code playground")
        console.print("  [bold]revision[/] - Show revision notes for all topics")
        console.print("  [bold]q[/] - Back")

        choice = Prompt.ask(f"\n[bold]{phase.label}[/]", default="q")

        if choice.lower() in ("q", "back"):
            break
        if choice.lower() == "quiz":
            run_phase_quiz(phase, content_dir)
            continue
        if choice.lower() == "flashcards":
            run_flashcard_session(phase.number)
            continue
        if choice.lower() == "sandbox":
            sandbox_loop()
            continue
        if choice.lower() == "revision":
            show_phase_revision(phase)
            continue

        if choice.lower().startswith("c "):
            try:
                topic_num = int(choice.split()[1])
                topic = _get_topic_or_exit(phase, topic_num)
                run_coding_challenge(phase.number, topic_num, topic.title)
            except (ValueError, IndexError):
                console.print("[red]Usage: c <topic_number>[/]")
            continue
        if choice.isdigit():
            topic_num = int(choice)
            topic = _get_topic_or_exit(phase, topic_num)
            view_topic(phase.number, topic, content_dir)
            progress.set_bookmark(phase.number, topic_num)
            progress.add_streak()


def view_topic(phase_num: int, topic: Topic, content_dir: Optional[Path] = None):
    """Display a topic section by section with quiz + challenge at the end."""
    show_topic_summary(topic)
    sections = topic.sections
    total = len(sections)

    for i, section in enumerate(sections, start=1):
        # Check for special sandbox trigger
        if "```" in section.content:
            render_section(section, i, total, topic.title)
            if i < total:
                try_it = Confirm.ask("[dim]Try this code?[/]", default=False)
                if try_it:
                    _extract_and_run(section.content)
                Prompt.ask("[dim]Press Enter to continue[/]", default="")
            else:
                Prompt.ask("[dim]Press Enter for exercises[/]", default="")
        else:
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

    # Coding challenge
    challenge = get_challenge(phase_num, topic.number)
    if challenge:
        do_challenge = Confirm.ask("\n[bold cyan]Try a coding challenge?[/]", default=True)
        if do_challenge:
            run_coding_challenge(phase_num, topic.number, topic.title)

    # Award XP
    xp_gained = 10  # base for completing topic
    if questions:
        xp_gained += 10  # bonus for having quiz
    leveled_up = progress.add_xp(xp_gained)
    progress.mark_complete(phase_num, topic.number)
    badges = progress.get_badges()
    progress.add_streak()
    render_completion(phase_num, topic.number, topic.title, badges, xp_gained, leveled_up)

    # Show revision notes
    notes = get_revision_notes(topic)
    if notes:
        show_revision = Prompt.ask(
            "[dim]Show revision summary? (y/n)[/]", default="y"
        )
        if show_revision.lower() == "y":
            console.print(f"\n[bold cyan]Revision: {topic.title}[/]")
            console.print(Markdown(notes))


def _extract_and_run(content: str):
    """Extract code blocks from content and offer to run them."""
    import re as _re
    blocks = _re.findall(r"```python\n(.*?)```", content, _re.DOTALL)
    blocks += _re.findall(r"```\n(.*?)```", content, _re.DOTALL)
    if not blocks:
        return
    original = blocks[0].strip()
    if not original:
        return

    console.print("\n[dim]--- Example code ---[/]")
    console.print(Syntax(original, "python", theme="monokai"))

    choice = Prompt.ask(
        "[dim]Run as-is[/dim] [bold](r)[/bold][dim] or type it yourself[/dim] [bold](t)[/bold][dim]?[/dim]",
        choices=["r", "t"],
        default="r",
    )

    if choice == "r":
        code = original
    else:
        console.print("\n[bold]Type the code yourself (type [red]done[/] on a new line when finished):[/]")
        console.print("[dim]Type 'show' to see the example again[/]")
        lines: list[str] = []
        while True:
            try:
                raw = input("  >> ")
            except EOFError:
                break
            if raw.strip().lower() == "done":
                break
            if raw.strip().lower() == "show":
                console.print(Syntax(original, "python", theme="monokai"))
                continue
            lines.append(raw)
        if not lines:
            console.print("[dim]Skipped.[/]")
            return
        code = "\n".join(lines)

    from .sandbox import run_code
    result = run_code(code)
    if result["stdout"]:
        console.print("[bold]Output:[/]")
        console.print(result["stdout"].rstrip())
    if result["stderr"]:
        console.print(f"[red]{result['stderr'].rstrip()}[/]")
    if choice == "t" and code != original:
        console.print("[dim]--- Original was ---[/]")
        console.print(Syntax(original, "python", theme="monokai"))


def run_coding_challenge(phase_num: int, topic_num: int, title: str):
    """Interactive coding challenge for a topic."""
    challenges = get_all_challenges(phase_num, topic_num)
    if not challenges:
        console.print("[yellow]No challenges for this topic yet.[/]")
        console.print("[dim]Open 'sandbox' to practice on your own.[/]")
        return

    for idx, challenge in enumerate(challenges, start=1):
        if len(challenges) > 1:
            console.print(f"\n[bold cyan]Challenge {idx}/{len(challenges)}[/]")
        show_challenge(challenge, console)

        console.print("\n[bold]Write your solution below (type [red]done[/] on a new line when finished):[/]")
        console.print("[dim]Type 'hint' for help, 'skip' to move on[/]")

        lines: list[str] = []
        while True:
            try:
                raw = input("  >> ")
            except EOFError:
                break
            if raw.strip().lower() == "done":
                break
            if raw.strip().lower() == "hint":
                console.print(f"[yellow]Hint: {challenge.hint}[/]")
                continue
            if raw.strip().lower() == "skip":
                lines = []
                break
            lines.append(raw)

        if not lines:
            console.print("[dim]Skipped.[/]")
            continue

        code = "\n".join(lines)
        result = run_challenge_code(code)

        console.print("\n[bold]Output:[/]")
        if result["stdout"]:
            console.print(Syntax(result["stdout"].rstrip(), "python", theme="monokai"))
        if result["stderr"]:
            console.print(f"[red]{result['stderr'].rstrip()}[/]")

        if challenge.expected_output is not None:
            actual = result["stdout"]
            expected = challenge.expected_output
            if actual == expected:
                xp_reward = {"easy": 15, "medium": 25, "hard": 40}.get(challenge.difficulty, 20)
                leveled_up = progress.add_xp(xp_reward)
                level_notice = " [yellow]LEVEL UP![/]" if leveled_up else ""
                console.print(f"[bold green]Passed! Great job! +{xp_reward}XP{level_notice}[/]")
            else:
                console.print(f"[bold yellow]Output doesn't match expected.[/]")
                console.print(f"[dim]Expected:[/] {repr(expected)}")
                console.print(f"[dim]Got:[/]      {repr(actual)}")
                retry = Confirm.ask("[dim]Try again?[/]", default=True)
                if retry:
                    run_coding_challenge(phase_num, topic_num, title)
                    return
        else:
            if result["success"]:
                console.print("[bold green]Code ran successfully![/]")
            else:
                console.print("[bold red]There was an error.[/]")

    console.print("[bold green]All challenges complete for this topic![/]")


def run_phase_quiz(phase: Phase, content_dir: Optional[Path] = None):
    """Quiz across all topics in a phase."""
    all_questions = []
    for topic in phase.topics:
        questions = get_quiz_questions(topic)
        all_questions.extend(questions)

    if not all_questions:
        console.print("[yellow]No quiz questions found in this phase.[/]")
        return

    console.print(Panel(
        f"[bold cyan]Phase Quiz: {phase.label}[/]\n\n"
        f"[bold]{len(all_questions)} questions across {len(phase.topics)} topics[/]",
        border_style="cyan",
    ))
    correct, total = run_quiz(all_questions)
    render_quiz_result(correct, total)


def show_phase_revision(phase: Phase):
    """Show revision notes for all topics in a phase."""
    for t in phase.topics:
        notes = get_revision_notes(t)
        if notes:
            console.print(f"\n[bold cyan]{t.label}[/]")
            console.print(Markdown(notes[:2000]))
        Prompt.ask("[dim]Press Enter to continue[/]", default="")


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
    phase: int = typer.Argument(None, help="Phase number (optional - all phases if omitted)"),
    content_dir: Optional[Path] = CONTENT_DIR_OPTION,
):
    """Take a quiz for a phase or all phases."""
    phases = _load_phases(content_dir)

    if phase is not None:
        p = _get_phase_or_exit(phase, phases)
        run_phase_quiz(p, content_dir)
        return

    all_q = []
    for p in phases:
        for t in p.topics:
            all_q.extend(get_quiz_questions(t))

    console.print(Panel(
        f"[bold cyan]Full Roadmap Quiz[/]\n\n"
        f"[bold]{len(all_q)} questions across all phases[/]",
        border_style="cyan",
    ))
    correct, total = run_quiz(all_q)
    render_quiz_result(correct, total)


@app.command()
def challenge(
    phase: int = typer.Argument(..., help="Phase number"),
    topic: int = typer.Argument(..., help="Topic number"),
    content_dir: Optional[Path] = CONTENT_DIR_OPTION,
):
    """Run a coding challenge for a specific topic."""
    phases = _load_phases(content_dir)
    p = _get_phase_or_exit(phase, phases)
    t = _get_topic_or_exit(p, topic)
    run_coding_challenge(phase, topic, t.title)


@app.command()
def sandbox():
    """Open the interactive Python code playground."""
    sandbox_loop()


@app.command()
def search(
    query: str = typer.Argument(..., help="Search term"),
    content_dir: Optional[Path] = CONTENT_DIR_OPTION,
):
    """Search across all topics for a keyword."""
    phases = _load_phases(content_dir)
    run_search(phases, query)


def run_search(phases: list[Phase], query: str = None):
    """Interactive search across all topics."""
    if not query:
        query = Prompt.ask("[bold]Search for[/]")
    if not query or not query.strip():
        return
    query = query.strip()
    results = search_content(query, phases)

    if not results:
        console.print(f"[yellow]No results found for '{query}'[/]")
        return

    console.print(f"\n[bold cyan]Search results for '{query}'[/] ({len(results)} topics)")
    for r in results[:15]:
        console.print(f"\n[bold yellow]P{r['phase']}.{r['topic']}[/] {r['title']}")
        for line_no, text in r["matches"][:5]:
            truncated = text[:100] + "..." if len(text) > 100 else text
            console.print(f"  [dim]L{line_no}:[/] {truncated}")

    if results:
        view_one = Prompt.ask(
            "[bold]View a topic? (phase.topic or Enter to skip)[/]", default=""
        )
        if view_one and "." in view_one:
            try:
                pn, tn = view_one.split(".")
                p = _get_phase_or_exit(int(pn), phases)
                t = _get_topic_or_exit(p, int(tn))
                view_topic(int(pn), t)
            except (ValueError, typer.Exit):
                pass


@app.command()
def flashcards(
    phase: int = typer.Argument(None, help="Phase number (optional)"),
):
    """Review flashcards for a phase or all phases."""
    run_flashcard_session(phase)


@app.command()
def status(content_dir: Optional[Path] = CONTENT_DIR_OPTION):
    """Show your learning progress, streak, and badges."""
    show_detailed_progress()


@app.command()
def badges():
    """Show earned badges."""
    render_badges(progress.get_badges())


def show_detailed_progress():
    """Display detailed progress across all phases."""
    phases = _load_phases()
    if not phases:
        console.print("[red]No content found. Use --content-dir to specify a path.[/]")
        return

    total_done = 0
    total_all = 0
    level_info = progress.get_level_info()

    console.print(f"\n[bold cyan]Learning Progress[/]")
    # Level XP bar
    xp_bar = _bar(level_info["xp_current"], level_info["xp_needed"], 20)
    console.print(f"[bold]Level {level_info['level']}[/] {xp_bar} [dim]{level_info['xp_current']}/{level_info['xp_needed']} XP ({level_info['xp_total']} total)[/]")
    streak = progress.get_streak()
    if streak:
        console.print(f"[yellow]{streak}-day learning streak![/]")
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
        bar = _bar(done, total, 25)
        table.add_row(p.label, str(done), str(total), bar)

    bar = _bar(total_done, total_all, 25)
    table.add_row(
        "[bold]Total[/]", str(total_done), str(total_all), f"[bold]{bar}[/]"
    )
    console.print(table)

    pct = (total_done / total_all * 100) if total_all else 0
    if pct == 100:
        console.print("\n[bold green]All topics completed! You're a Python master![/]")
    else:
        remaining = total_all - total_done
        console.print(f"\n[cyan]Overall: {pct:.1f}% ({remaining} topics remaining)[/]")

    badges = progress.get_badges()
    if badges:
        render_badges(badges)


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


@app.command()
def bookmark():
    """Show your current bookmark."""
    bm = progress.get_bookmark()
    if bm:
        console.print(f"[yellow]Bookmark: Phase {bm['phase']}, Topic {bm['topic']}[/]")
    else:
        console.print("[dim]No bookmark set.[/]")
