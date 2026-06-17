from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Static, Button, Label
from textual.containers import Container

from ..progress import ProgressTracker
from ..session import SessionState, save_session, load_session
from ..content import discover_phases
from .sidebar import Sidebar
from .content_panel import ContentPanel
from .code_panel import CodePanel
from .status_bar import TutorialStatusBar
from .screens import FlashcardScreen, QuizScreen, SearchScreen, TutorDashboardScreen, HelpScreen, PlaygroundCheatSheetScreen


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

    PlaygroundCheatSheetScreen {
        align: center middle;
    }

    PlaygroundCheatSheetScreen > #pcs-title {
        height: auto;
        text-style: bold;
        text-align: center;
    }

    PlaygroundCheatSheetScreen > #pcs-subtitle {
        height: auto;
        text-align: center;
        margin-bottom: 1;
    }

    PlaygroundCheatSheetScreen > #pcs-content {
        width: 80%;
        height: 80%;
        overflow-y: auto;
        overflow-x: auto;
    }

    PlaygroundCheatSheetScreen > #pcs-content .section-header {
        height: auto;
        margin-top: 1;
        margin-bottom: 0;
    }

    PlaygroundCheatSheetScreen > #pcs-content .cheat-table {
        height: auto;
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
        Binding("ctrl+shift+p", "playground_cheatsheet", "Play Keys", show=True),
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
        import subprocess
        import os
        import sys
        import json

        if sys.platform == "linux":
            bin_name = "playground"
        elif sys.platform == "win32":
            bin_name = "playground.exe"
        elif sys.platform == "darwin":
            import platform
            arch = platform.machine()
            if arch in ("x86_64", "amd64"):
                bin_name = "playground-x86_64-apple-darwin"
            elif arch in ("arm64", "aarch64"):
                bin_name = "playground-aarch64-apple-darwin"
            else:
                self.notify(
                    f"Unsupported macOS architecture: {arch}",
                    title="Playground",
                    timeout=5,
                )
                return
        else:
            self.notify(
                "Playground is only supported on Linux, Windows, and macOS.",
                title="Playground",
                timeout=5,
            )
            return

        playground_bin = Path(__file__).resolve().parent.parent / "playground" / bin_name
        if not playground_bin.is_file():
            self.notify(
                "Playground binary not found. Reinstall the package.",
                title="Playground",
                timeout=5,
            )
            return

        if not os.access(str(playground_bin), os.X_OK):
            playground_bin.chmod(playground_bin.stat().st_mode | 0o111)

        playground_dir = Path.home() / ".local" / "state" / "python-tutorial" / "playground"
        playground_dir.mkdir(parents=True, exist_ok=True)

        projects_dir = playground_dir / "projects"
        if not projects_dir.is_dir():
            self._seed_playground_projects(projects_dir)

        if not (playground_dir / "main.py").is_file():
            (playground_dir / "main.py").write_text(
                "# Python Playground\n# Write your project code here\n\nprint('Hello from Playground!')\n"
            )

        sandbox_file = playground_dir / "sandbox-code.py"
        code_panel = self.query_one(CodePanel)
        try:
            sandbox_code = code_panel.query_one("#code-editor").text.strip()
        except Exception:
            sandbox_code = ""
        if sandbox_code:
            sandbox_file.write_text(sandbox_code)

        open_files = [str(playground_dir / "main.py")]
        if sandbox_code:
            open_files.insert(0, str(sandbox_file))

        theme_path = Path(__file__).resolve().parent.parent / "playground" / "tokyo-night-theme.json"
        config_path = playground_dir / "playground-config.json"
        config_path.write_text(json.dumps({
            "theme": theme_path.as_uri(),
            "keybindings": [
                {
                    "key": "t",
                    "modifiers": ["ctrl", "shift"],
                    "action": "quit",
                },
            ],
        }))

        self.notify(
            f"Opening Playground in {playground_dir}",
            title="Playground",
            timeout=3,
        )
        with self.suspend():
            subprocess.run(
                [str(playground_bin), "--config", str(config_path), *open_files],
                cwd=playground_dir,
            )

    def _seed_playground_projects(self, projects_dir: Path) -> None:
        projects_dir.mkdir(parents=True)
        starter_projects = {
            "phase-1-fundamentals": {
                "README.md": "# Phase 1: Python Fundamentals\n\nPractice variables, data types, conditionals, and loops.\n\n## Getting Started\n- Open hello.py and complete the exercises\n- Run with F5 in Fresh or `python hello.py` in the terminal",
                "hello.py": "# Phase 1: Python Fundamentals\n# Practice: variables, types, conditionals, loops\n\nname = input(\"What's your name? \")\nprint(f\"Hello, {name}!\")\n\n# TODO: Ask for their age and print the year they were born\n",
            },
            "phase-2-core-python": {
                "README.md": "# Phase 2: Core Python\n\nPractice strings, lists, dicts, functions, and error handling.\n\n## Exercises\n- Open data_types.py and complete each section\n- Test edge cases with invalid input",
                "data_types.py": "# Phase 2: Core Python\n# Practice: strings, lists, dicts, functions\n\ndef analyze_text(text: str) -> dict:\n    \"\"\"Return word count, char count, and unique words.\"\"\"\n    # TODO: Implement this function\n    pass\n\n\n# Test your function\nsample = \"Hello world! Hello Python!\"\nprint(analyze_text(sample))\n",
            },
            "phase-3-oop": {
                "README.md": "# Phase 3: Object-Oriented Programming\n\nPractice classes, inheritance, polymorphism, and dunder methods.\n\n## Exercises\n- Open classes.py and implement the BankAccount class\n- Add a SavingsAccount subclass with interest",
                "classes.py": "# Phase 3: OOP\n# Practice: classes, inheritance, dunder methods\n\nclass BankAccount:\n    def __init__(self, owner: str, balance: float = 0.0):\n        self.owner = owner\n        self.balance = balance\n\n    def deposit(self, amount: float) -> None:\n        # TODO: Add amount to balance\n        pass\n\n    def withdraw(self, amount: float) -> bool:\n        # TODO: Deduct amount if sufficient balance\n        pass\n\n    def __str__(self) -> str:\n        return f\"{self.owner}'s account: ${self.balance:.2f}\"\n",
            },
            "phase-4-intermediate": {
                "README.md": "# Phase 4: Intermediate Python\n\nPractice decorators, generators, context managers, and itertools.\n\n## Starter\nCreate your own decorator or generator below.",
                "intermediate.py": "# Phase 4: Intermediate Python\n# Practice: decorators, generators, context managers\n\nfrom contextlib import contextmanager\nimport time\n\n\n@contextmanager\ndef timer(label: str = \"\"):\n    # TODO: Measure and print elapsed time\n    pass\n\n\n# Test your context manager\nwith timer(\"sleep\"):\n    time.sleep(0.5)\n",
            },
            "phase-5-advanced": {
                "README.md": "# Phase 5: Advanced Python\n\nPractice metaclasses, descriptors, async/await, and concurrency.\n\n## Starter\nImplement an async fetcher below.",
                "advanced.py": "# Phase 5: Advanced Python\n# Practice: async/await, concurrency\n\nimport asyncio\n\n\nasync def fetch_data(url: str) -> str:\n    # TODO: Simulate fetching data from a URL\n    await asyncio.sleep(1)\n    return f\"Data from {url}\"\n\n\nasync def main():\n    # TODO: Fetch multiple URLs concurrently\n    pass\n\n\nasyncio.run(main())\n",
            },
            "phase-6-engineering": {
                "README.md": "# Phase 6: Python for Engineering\n\nPractice testing, profiling, packaging, and CLI tools.\n\n## Starter\nWrite tests and a small CLI tool.",
                "cli_tool.py": "# Phase 6: Python for Engineering\n# Practice: CLI tools, testing\n\nimport argparse\n\n\ndef main():\n    parser = argparse.ArgumentParser(description=\"A useful CLI tool\")\n    # TODO: Add arguments\n    args = parser.parse_args()\n    print(args)\n\n\nif __name__ == \"__main__\":\n    main()\n",
            },
            "phase-7-ai": {
                "README.md": "# Phase 7: Python for AI Engineering\n\nPractice numpy, data pipelines, and ML concepts.\n\n## Starter\nImplement a simple data pipeline below.",
                "pipeline.py": "# Phase 7: Python for AI Engineering\n# Practice: data processing pipelines\n\ndef load_data(path: str) -> list[dict]:\n    # TODO: Load data from a CSV or JSON file\n    pass\n\n\ndef clean_data(records: list[dict]) -> list[dict]:\n    # TODO: Remove invalid records, fill missing values\n    pass\n\n\ndef transform_data(records: list[dict]) -> list[dict]:\n    # TODO: Normalize fields, create derived features\n    pass\n",
            },
        }
        for project_name, files in starter_projects.items():
            project_dir = projects_dir / project_name
            project_dir.mkdir()
            for filename, content in files.items():
                (project_dir / filename).write_text(content.lstrip("\n"))

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

    def action_playground_cheatsheet(self) -> None:
        self.push_screen(PlaygroundCheatSheetScreen())

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
