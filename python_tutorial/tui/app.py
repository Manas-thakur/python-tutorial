from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Static, Button, Label
from textual.containers import Container

from ..progress import ProgressTracker
from .sidebar import Sidebar
from .content_panel import ContentPanel
from .code_panel import CodePanel
from .status_bar import TutorialStatusBar
from .screens import FlashcardScreen, QuizScreen, SearchScreen


class ConfirmScreen(Screen):
    def __init__(self, title: str, message: str, callback):
        super().__init__()
        self._title = title
        self._message = message
        self._callback = callback

    def compose(self):
        yield Static(f"[bold yellow]{self._title}[/]", id="confirm-title")
        yield Label(self._message, id="confirm-message")
        with Container(id="confirm-buttons"):
            yield Button("Yes", id="confirm-yes", variant="error")
            yield Button("No", id="confirm-no", variant="primary")

    def on_button_pressed(self, event):
        self._callback(event.button.id == "confirm-yes")
        self.app.pop_screen()


class MainContainer(Container):
    def compose(self) -> ComposeResult:
        yield Sidebar()
        yield ContentPanel()
        yield CodePanel()


class TutorialApp(App):
    CSS = """
    MainContainer {
        layout: horizontal;
        height: 1fr;
    }

    MainContainer > Sidebar {
        width: 25%;
        height: 100%;
        border: solid $primary;
    }

    MainContainer.sidebar-collapsed > Sidebar {
        display: none;
    }

    MainContainer > ContentPanel {
        width: 40%;
        height: 100%;
        border: solid $secondary;
    }

    MainContainer.content-collapsed > ContentPanel {
        display: none;
    }

    MainContainer.content-collapsed > Sidebar {
        width: 25%;
    }

    MainContainer.content-collapsed > CodePanel {
        width: 75%;
    }

    MainContainer.sidebar-collapsed > ContentPanel {
        width: 65%;
    }

    MainContainer.sidebar-collapsed > CodePanel {
        width: 35%;
    }

    MainContainer.sidebar-collapsed.content-collapsed > ContentPanel {
        display: none;
    }

    MainContainer.sidebar-collapsed.content-collapsed > CodePanel {
        width: 100%;
    }

    ContentPanel {
        layout: vertical;
        height: 100%;
    }

    ContentPanel > #section-heading {
        height: auto;
    }

    ContentPanel > #section-body {
        height: 1fr;
        min-height: 0;
        overflow-y: auto;
    }

    ContentPanel > #section-body > Markdown {
        width: 100%;
        height: auto;
    }

    ContentPanel > #section-nav {
        height: auto;
    }

    MainContainer > CodePanel {
        width: 35%;
        height: 100%;
        border: solid $accent;
    }

    TutorialStatusBar {
        dock: bottom;
        height: 1;
    }

    #title-bar {
        dock: top;
        height: 1;
        background: $primary;
        color: $text;
        text-style: bold;
        text-align: center;
    }

    ConfirmScreen {
        align: center middle;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("f5", "run_code", "Run", show=True),
        Binding("ctrl+p", "search", "Search", show=True),
        Binding("ctrl+q", "quiz", "Quiz", show=True),
        Binding("ctrl+b", "toggle_sidebar", "Sidebar", show=True),
        Binding("ctrl+f", "flashcards", "Flashcards", show=True),
        Binding("c", "toggle_content_panel", "Contents", show=True),
        Binding("r", "reset_progress", "Reset", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.progress = ProgressTracker()
        self.current_phase = None
        self.current_topic = None
        self.current_section_index = 0
        self.sidebar_collapsed = False
        self.content_collapsed = False

    def compose(self) -> ComposeResult:
        yield Static("[bold]Python Interactive Tutorial[/]", id="title-bar")
        yield MainContainer()
        yield TutorialStatusBar(self.progress)

    def on_mount(self) -> None:
        self.title = "Python Interactive Tutorial"
        self.progress.add_streak()
        # Pass progress to widgets that need it
        sidebar = self.query_one(Sidebar)
        sidebar.progress = self.progress
        sidebar.load_phases()
        self._sync_layout_state()

    def _sync_layout_state(self) -> None:
        main_container = self.query_one(MainContainer)
        if self.sidebar_collapsed:
            main_container.add_class("sidebar-collapsed")
        else:
            main_container.remove_class("sidebar-collapsed")
        if self.content_collapsed:
            main_container.add_class("content-collapsed")
        else:
            main_container.remove_class("content-collapsed")
        self.query_one(TutorialStatusBar).refresh()

    def action_quit(self) -> None:
        self.exit()

    def action_run_code(self) -> None:
        self.query_one(CodePanel).run_code()

    def action_search(self) -> None:
        self.push_screen(SearchScreen(self.progress))

    def action_toggle_sidebar(self) -> None:
        self.sidebar_collapsed = not self.sidebar_collapsed
        self._sync_layout_state()

    def action_toggle_content_panel(self) -> None:
        self.content_collapsed = not self.content_collapsed
        self._sync_layout_state()

    def action_quiz(self) -> None:
        if self.current_phase:
            self.push_screen(QuizScreen(self.progress, self.current_phase))

    def action_flashcards(self) -> None:
        self.push_screen(FlashcardScreen(self.progress, self.current_phase))

    def action_reset_progress(self) -> None:
        def on_confirm(confirmed: bool):
            if confirmed:
                self.progress.reset()
                self.query_one(Sidebar).load_phases()
                self.query_one(ContentPanel).clear()
                self.query_one(TutorialStatusBar).refresh()
        self.push_screen(
            ConfirmScreen("Reset Progress", "This will delete ALL progress. Are you sure?", on_confirm)
        )

    def on_topic_selected(self, message) -> None:
        phase = message.phase
        topic = message.topic
        self.current_phase = phase
        self.current_topic = topic
        self.current_section_index = 0
        self.query_one(ContentPanel).load_topic(topic)
        self.query_one(CodePanel).load_topic(topic)
        self.progress.set_bookmark(phase.number, topic.number)
        self.query_one(TutorialStatusBar).refresh()


def main():
    app = TutorialApp()
    app.run()
