from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Static, Button, Label
from textual.containers import Container

from ..progress import ProgressTracker
from ..session import SessionState, save_session, load_session
from ..content import discover_phases
from .sidebar import Sidebar, TopicSelected
from .content_panel import ContentPanel
from .code_panel import CodePanel
from .status_bar import TutorialStatusBar
from .screens import FlashcardScreen, QuizScreen, SearchScreen, TutorDashboardScreen, HelpScreen


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
        width: 35%;
    }

    MainContainer.content-collapsed > CodePanel {
        width: 65%;
    }

    MainContainer.sidebar-collapsed > ContentPanel {
        width: 60%;
    }

    MainContainer.sidebar-collapsed > CodePanel {
        width: 40%;
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
        height: 3;
    }

    TutorialStatusBar > #status-container {
        height: 1;
    }

    TutorialStatusBar > #keybind-bar-1,
    TutorialStatusBar > #keybind-bar-2 {
        height: 1;
        width: 100%;
    }

    #keybind-bar-1 > Static,
    #keybind-bar-2 > Static {
        margin: 0 1;
    }

    #status-container > Static {
        margin: 0 1;
    }

    #status-container > ProgressBar {
        width: 15;
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
        Binding("f2", "playground", "Playground", show=True),
        Binding("f5", "run_code", "Run", show=True),
        Binding("ctrl+f", "search", "Search", show=True),
        Binding("ctrl+q", "quiz", "Quiz", show=True),
        Binding("ctrl+shift+f", "flashcards", "Flashcards", show=True),
        Binding("ctrl+t", "tutor", "Tutor", show=True),
        Binding("ctrl+b", "toggle_sidebar", "Sidebar", show=True),
        Binding("c", "toggle_content_panel", "Contents", show=True),
        Binding("?", "help", "Help", show=True),
        Binding("r", "reset_progress", "Reset", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.progress = ProgressTracker()
        self.current_phase = None
        self.current_topic = None
        self.current_section_index = 0
        self._session = load_session()
        self.sidebar_collapsed = self._session.sidebar_collapsed
        self.content_collapsed = self._session.content_collapsed

    def compose(self) -> ComposeResult:
        yield Static("[bold]Python Interactive Tutorial[/]", id="title-bar")
        yield MainContainer()
        yield TutorialStatusBar(self.progress)

    def on_mount(self) -> None:
        self.title = "Python Interactive Tutorial"
        self.progress.add_streak()
        sidebar = self.query_one(Sidebar)
        sidebar.progress = self.progress
        sidebar.load_phases()
        if self._session.is_valid():
            for p in discover_phases():
                for t in p.topics:
                    if p.number == self._session.phase and t.number == self._session.topic:
                        self._load_topic(p, t)
                        break
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
        save_session(SessionState(
            phase=self.current_phase.number if self.current_phase else None,
            topic=self.current_topic.number if self.current_topic else None,
            sidebar_collapsed=self.sidebar_collapsed,
            content_collapsed=self.content_collapsed,
        ))
        self.query_one(TutorialStatusBar).refresh()

    def action_quit(self) -> None:
        phase_num = self.current_phase.number if self.current_phase else None
        topic_num = self.current_topic.number if self.current_topic else None
        save_session(SessionState(
            phase=phase_num,
            topic=topic_num,
            sidebar_collapsed=self.sidebar_collapsed,
            content_collapsed=self.content_collapsed,
        ))
        self.exit()

    def action_run_code(self) -> None:
        self.query_one(CodePanel).run_code()

    def action_playground(self) -> None:
        from pathlib import Path
        import subprocess
        import sys
        import shutil

        fresh_path = shutil.which("fresh")
        if fresh_path is None:
            def _on_confirm(confirmed: bool):
                if confirmed:
                    self._install_fresh()
            self.push_screen(
                ConfirmScreen(
                    "Fresh IDE Not Found",
                    "Fresh IDE is required for the playground.\n\n"
                    "Install it with:\n"
                    "  curl https://raw.githubusercontent.com/sinelaw/fresh/refs/heads/master/scripts/install.sh | sh\n\n"
                    "Or via npm:\n"
                    "  npm install -g @fresh-editor/fresh-editor\n\n"
                    "Install now via npx (no install needed)?",
                    _on_confirm,
                )
            )
            return

        playground_dir = Path.home() / ".local" / "state" / "python-tutorial" / "playground"
        playground_dir.mkdir(parents=True, exist_ok=True)
        if not any(playground_dir.iterdir()):
            (playground_dir / "main.py").write_text(
                "# Python Playground\n# Write your project code here\n\nprint('Hello from Playground!')\n"
            )

        self.notify(
            f"Opening Fresh IDE in {playground_dir}",
            title="Playground",
            timeout=3,
        )
        with self.suspend():
            subprocess.run(
                ["fresh", str(playground_dir)],
                cwd=playground_dir,
            )

    def _install_fresh(self) -> None:
        import webbrowser
        webbrowser.open("https://getfresh.dev/")
        self.notify("Visit https://getfresh.dev/ for install instructions, then press F2 again.", title="Playground", timeout=5)

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

    def action_tutor(self) -> None:
        self.push_screen(TutorDashboardScreen(self.progress, self))

    def action_help(self) -> None:
        self.push_screen(HelpScreen())

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
        self._load_topic(message.phase, message.topic)

    def _load_topic(self, phase, topic) -> None:
        self.current_phase = phase
        self.current_topic = topic
        self.current_section_index = 0
        self.query_one(ContentPanel).load_topic(topic)
        self.query_one(CodePanel).load_topic(topic)
        self.progress.set_bookmark(phase.number, topic.number)
        self.query_one(TutorialStatusBar).refresh()
        self._update_nav_hints()

    def _update_nav_hints(self) -> None:
        panel = self.query_one(ContentPanel)
        has_prev = panel._get_sibling_topic(-1) is not None
        has_next = panel._get_sibling_topic(1) is not None
        self.query_one(TutorialStatusBar).update_nav(has_prev, has_next)


def main():
    app = TutorialApp()
    app.run()
