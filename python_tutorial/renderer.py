from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.syntax import Syntax
from rich.text import Text
from rich.style import Style
from rich.box import ROUNDED
from rich.progress import Progress, BarColumn, TextColumn
from rich.prompt import Prompt, Confirm
from pathlib import Path

from .models import Phase, Topic, Section
from .themes import TokyoNightStyle

console = Console()


def show_banner():
    console.rule("[bold cyan]Python Interactive Tutorial[/]", style="cyan")
    console.print("[dim]Learn Python from fundamentals to AI[/]", justify="center")
    console.print()


def show_phase_list(phases: list[Phase], progress: dict):
    table = Table(box=ROUNDED, title="[bold cyan]Python Roadmap[/]", title_style="bold cyan")
    table.add_column("#", style="dim", width=4)
    table.add_column("Phase", style="bold yellow", no_wrap=True)
    table.add_column("Topics", justify="right", width=8)
    table.add_column("Progress", width=22)

    for p in phases:
        done, total = progress.get_phase_progress(p.number, len(p.topics))
        bar = _progress_bar(done, total, width=15)
        unlocked = progress.is_phase_unlocked(p.number)
        label = p.title if unlocked else f"{p.title} [dim](locked)[/]"
        table.add_row(str(p.number), label, f"{done}/{total}", bar)

    console.print(table)


def show_topic_list(phase: Phase, progress):
    console.print(f"\n[bold cyan]{phase.label}[/]")
    console.print("[dim]" + "-" * console.width + "[/]")

    table = Table(box=ROUNDED, show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=4)
    table.add_column("Topic", style="bold white")
    table.add_column("Status", width=14)

    for t in phase.topics:
        status = "[green]Done[/]" if progress.is_complete(phase.number, t.number) else "[dim]Pending[/]"
        table.add_row(str(t.number), t.title, status)

    console.print(table)


def _progress_bar(done: int, total: int, width: int = 20) -> str:
    if total == 0:
        return "[dim]no topics[/]"
    filled = int((done / total) * width) if total else 0
    bar = "█" * filled + "░" * (width - filled)
    return f"[green]{bar}[/]"


def render_section(section: Section, index: int, total: int, topic_title: str):
    header = Text(f"\n[{index}/{total}] {section.heading}", style="bold cyan")
    console.print(header)

    content_text = section.content.strip()
    if not content_text:
        console.print("[dim](no content)[/]")
        return

    has_code = "```" in content_text

    if has_code:
        parts = content_text.split("```")
        for i, part in enumerate(parts):
            if i % 2 == 0:
                if part.strip():
                    console.print(Markdown(part.strip()), width=console.width)
            else:
                lines = part.splitlines()
                lang = lines[0].strip() if lines else ""
                code = "\n".join(lines[1:] if lang else lines)
                if not lang:
                    lang = "python"
                try:
                    syntax = Syntax(code.strip(), lang, theme=TokyoNightStyle, line_numbers=False)
                    console.print(Panel(syntax, border_style="bright_blue"))
                except Exception:
                    console.print(Panel(code.strip(), border_style="bright_blue"))
    else:
        md = Markdown(content_text)
        console.print(Panel(md, border_style="blue"))


def show_topic_summary(topic: Topic):
    total_sections = len(topic.sections)
    console.print(f"\n[bold yellow]{topic.label}[/] - {total_sections} sections")
    console.print(f"[dim]{topic.filepath.name}[/]")


def render_completion(phase_num: int, topic_num: int, title: str, badges: list[dict] = None, xp_gained: int = 0, leveled_up: bool = False):
    panel_content = f"[bold green]Topic Complete[/]\n\n[bold]{title}[/]"
    if xp_gained:
        level_text = " [bold yellow](LEVEL UP!)[/]" if leveled_up else ""
        panel_content += f"\n\n[bold]+{xp_gained} XP[/]{level_text}"
    if badges:
        earned = [b for b in badges if b["name"] in [x["name"] for x in (badges or [])]]
        if earned:
            badge_line = "  ".join(b['name'] for b in badges[-3:])
            panel_content += f"\n\n[bold yellow]Badges:[/]\n{badge_line}"
    console.print()
    console.print(Panel(
        panel_content,
        border_style="green",
    ))
    console.print()


def render_badges(badges: list[dict]):
    if not badges:
        return
    console.print("\n[bold cyan]Your Badges[/]")
    for b in badges:
        console.print(f"  [bold]{b['name']}[/] - [dim]{b['desc']}[/]")


def render_quiz_result(correct: int, total: int):
    pct = (correct / total) * 100 if total else 0
    color = "green" if pct >= 80 else "yellow" if pct >= 50 else "red"
    console.print()
    console.print(Panel(
        f"[bold]Score: [/{color}]{correct}/{total} ({pct:.0f}%)[/{color}][/]",
        title="[bold]Quiz Results[/]",
        border_style=color,
    ))
    console.print()
