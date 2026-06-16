from textual.widgets import Static, Markdown, Button
from textual.containers import Horizontal
from textual.widget import Widget
from textual.binding import Binding

from ..models import Topic


class ContentPanel(Widget):
    BINDINGS = [
        Binding("right", "next_section", "Next", show=False),
        Binding("left", "prev_section", "Prev", show=False),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._topic = None
        self._sections = []
        self._current_index = 0

    def compose(self):
        yield Static("", id="section-heading")
        yield Markdown("Select a topic from the sidebar")
        with Horizontal(id="section-nav"):
            yield Button("< Prev", id="prev-section", variant="default")
            yield Button("Next >", id="next-section", variant="primary")

    def load_topic(self, topic: Topic) -> None:
        self._topic = topic
        self._sections = topic.sections
        self._current_index = 0
        self._show_section()

    def _show_section(self) -> None:
        if not self._sections:
            self.query_one("#section-heading", Static).update("No sections")
            self.query_one(Markdown).update("_No content available_")
            return

        section = self._sections[self._current_index]
        self.query_one("#section-heading", Static).update(
            f"[bold cyan][{self._current_index + 1}/{len(self._sections)}] {section.heading}[/]"
        )
        self.query_one(Markdown).update(section.content)
        self.query_one("#prev-section", Button).disabled = self._current_index == 0
        self.query_one("#next-section", Button).disabled = self._current_index >= len(self._sections) - 1

    def next_section(self) -> None:
        if self._sections and self._current_index < len(self._sections) - 1:
            self._current_index += 1
            self._show_section()

    def prev_section(self) -> None:
        if self._sections and self._current_index > 0:
            self._current_index -= 1
            self._show_section()

    def clear(self) -> None:
        self._topic = None
        self._sections = []
        self._current_index = 0
        self.query_one(Markdown).update("Select a topic from the sidebar")
        self.query_one("#section-heading", Static).update("")

    def on_button_pressed(self, event) -> None:
        if event.button.id == "next-section":
            self.next_section()
        elif event.button.id == "prev-section":
            self.prev_section()
