from pathlib import Path

from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.message import Message
from textual.widgets import Button, Markdown, Static

from ..content import discover_phases
from ..models import Topic
from .sidebar import TopicSelected


class SectionChanged(Message):
    def __init__(self, index: int) -> None:
        super().__init__()
        self.index = index


class ContentPanel(VerticalScroll):
    BINDINGS = [
        Binding("right", "next_section", "Next section", show=False),
        Binding("left", "prev_section", "Prev section", show=False),
        Binding("down", "next_topic", "Next topic", show=False),
        Binding("up", "prev_topic", "Prev topic", show=False),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._topic = None
        self._sections = []
        self._current_index = 0
        self._project_info = None

    def compose(self):
        yield Static("", id="project-header")
        yield Static("", id="section-heading")
        with VerticalScroll(id="section-body"):
            yield Markdown("Select a topic from the sidebar", id="content-markdown")
        with Horizontal(id="section-nav"):
            yield Button("< Prev", id="prev-section", variant="default")
            yield Button("Next >", id="next-section", variant="primary")

    def update_project_header(self, done: int, total: int, difficulty: str = "", title: str = "") -> None:
        if not self._project_info:
            return
        self._project_info["done"] = done
        self._project_info["total"] = total
        if title:
            self._project_info["title"] = title
        if difficulty:
            self._project_info["difficulty"] = difficulty
        bar = self._make_bar(done, total)
        dc = {"beginner": "green", "intermediate": "yellow", "advanced": "red"} \
            .get(self._project_info.get("difficulty", ""), "white")
        self.query_one("#project-header", Static).update(
            f"[bold white]{self._project_info['title']}[/]  "
            f"[{dc}]{self._project_info['difficulty'].upper()}[/]  "
            f"[green]{bar}[/] {done}/{total}"
        )

    def _make_bar(self, done: int, total: int, width: int = 14) -> str:
        fill = int(width * done / total) if total > 0 else 0
        empty = width - fill
        return "█" * fill + "░" * empty

    def _get_sibling_topic(self, direction: int) -> tuple | None:
        if not self._topic:
            return None
        phases = discover_phases()
        for i, phase in enumerate(phases):
            for j, topic in enumerate(phase.topics):
                if topic.filepath == self._topic.filepath:
                    if direction == 1 and j + 1 < len(phase.topics):
                        return (phase, phase.topics[j + 1])
                    if direction == -1 and j - 1 >= 0:
                        return (phase, phase.topics[j - 1])
                    if direction == 1 and i + 1 < len(phases) and phases[i + 1].topics:
                        return (phases[i + 1], phases[i + 1].topics[0])
                    if direction == -1 and i - 1 >= 0 and phases[i - 1].topics:
                        return (phases[i - 1], phases[i - 1].topics[-1])
                    return None
        return None

    def load_topic(self, topic: Topic) -> None:
        self._topic = topic
        self._sections = topic.sections
        self._current_index = 0
        self._project_info = None
        self.query_one("#project-header", Static).update("")
        self._show_section()

    def load_steps(self, sections: list, title: str = "", project_info: dict = None) -> None:
        self._topic = None
        self._sections = sections
        self._current_index = 0
        self._project_info = project_info
        if project_info:
            done, total = project_info["done"], project_info["total"]
            bar = self._make_bar(done, total)
            dc = {"beginner": "green", "intermediate": "yellow", "advanced": "red"} \
                .get(project_info.get("difficulty", ""), "white")
            self.query_one("#project-header", Static).update(
                f"[bold white]{project_info['title']}[/]  "
                f"[{dc}]{project_info['difficulty'].upper()}[/]  "
                f"[green]{bar}[/] {done}/{total}"
            )
        else:
            self.query_one("#project-header", Static).update("")
        self._show_section()

    def _show_section(self) -> None:
        if not self._sections:
            self.query_one("#section-heading", Static).update("No sections")
            self.query_one("#content-markdown", Markdown).update("_No content available_")
            return

        section = self._sections[self._current_index]
        n = self._current_index + 1
        m = len(self._sections)
        bar = self._make_bar(n, m, width=10)
        self.query_one("#section-heading", Static).update(
            f"[bold cyan]Step {n}/{m}[/]  [green]{bar}[/]  [bold]{section.heading}[/]"
        )
        self.query_one("#content-markdown", Markdown).update(section.content)
        self.query_one("#prev-section", Button).disabled = self._current_index == 0
        self.query_one("#next-section", Button).disabled = self._current_index >= len(self._sections) - 1
        self.post_message(SectionChanged(self._current_index))

    def on_markdown_link_clicked(self, event: Markdown.LinkClicked) -> None:
        href = event.href
        if not href.endswith(".md"):
            return
        target = Path(href).name
        phases = discover_phases()
        for phase in phases:
            for topic in phase.topics:
                if topic.filepath.name == target:
                    event.stop()
                    self.app.post_message(TopicSelected(phase, topic))
                    return

    def action_next_section(self) -> None:
        if self._sections and self._current_index < len(self._sections) - 1:
            self._current_index += 1
            self._show_section()

    def action_prev_section(self) -> None:
        if self._sections and self._current_index > 0:
            self._current_index -= 1
            self._show_section()

    def action_next_topic(self) -> None:
        sibling = self._get_sibling_topic(1)
        if sibling:
            phase, topic = sibling
            self.app.post_message(TopicSelected(phase, topic))

    def action_prev_topic(self) -> None:
        sibling = self._get_sibling_topic(-1)
        if sibling:
            phase, topic = sibling
            self.app.post_message(TopicSelected(phase, topic))

    def on_button_pressed(self, event) -> None:
        if event.button.id == "next-section":
            self.action_next_section()
        elif event.button.id == "prev-section":
            self.action_prev_section()

    def clear(self) -> None:
        self._topic = None
        self._sections = []
        self._current_index = 0
        self.query_one("#content-markdown", Markdown).update("Select a topic from the sidebar")
        self.query_one("#section-heading", Static).update("")
