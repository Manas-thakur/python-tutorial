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

        if sandbox_file.is_file():
            fresh_code = sandbox_file.read_text().strip()
            if fresh_code and fresh_code != sandbox_code:
                try:
                    code_panel.query_one("#code-editor").text = fresh_code
                except Exception:
                    pass

    def _seed_playground_projects(self, projects_dir: Path) -> None:
        projects_dir.mkdir(parents=True)
        starter_projects = {
            "number-guessing-game": {
                "README.md": "# Number Guessing Game\n\nTry to guess the secret number before you run out of tries!\n\n## Files\n- `game.py` -- main game loop (you write this)\n- `hints.py` -- generates hints based on your guess\n- `scores.py` -- tracks high scores\n\n## How to play\nRun `python game.py` and follow the prompts.",
                "game.py": "# Number Guessing Game\n# TODO: Import hints and scores modules\n# TODO: Generate a random number between 1-100\n# TODO: Loop: ask for guess, check, give hints, track score\n# TODO: Save score when game ends\n\nprint(\"Welcome to the Number Guessing Game!\")\nprint(\"I'm thinking of a number between 1 and 100.\")\n",
                "hints.py": "# Hint Generator\n# TODO: Write a function that returns \"too high\", \"too low\",\n#       \"getting warm\", or \"freezing\" based on the guess\n\ndef get_hint(guess: int, secret: int) -> str:\n    pass\n",
                "scores.py": "# High Score Tracker\n# TODO: Load/save scores from a JSON file\n# TODO: Return top 5 scores formatted as a string\n\ndef save_score(name: str, guesses: int) -> None:\n    pass\n\ndef top_scores() -> str:\n    pass\n",
            },
            "todo-list-cli": {
                "README.md": "# Todo List CLI\n\nA command-line todo app with categories, priorities, and persistence.\n\n## Files\n- `todo.py` -- main menu and command loop\n- `storage.py` -- load/save todos to JSON\n- `models.py` -- Todo item data structure\n\n## Commands\nRun `python todo.py` to start.",
                "todo.py": "# Todo List CLI\n# TODO: Display menu: add, list, complete, delete, quit\n# TODO: Read user choice and call appropriate functions\n# TODO: Load existing todos on startup\n\nfrom models import TodoItem\nfrom storage import load_todos, save_todos\n\nprint(\"=== Todo List ===\")\n",
                "storage.py": "# JSON Storage\n# TODO: load_todos() -- read todos from a JSON file\n# TODO: save_todos(items) -- write todos to a JSON file\n# TODO: Handle file-not-found gracefully\n\nimport json\n\ndef load_todos() -> list[dict]:\n    pass\n\ndef save_todos(todos: list[dict]) -> None:\n    pass\n",
                "models.py": "# Todo Data Model\n# TODO: Create a TodoItem dataclass with:\n#       - id, title, category, priority, done\n# TODO: Add a method to display as a formatted string\n\ndef create_todo(title: str, category: str, priority: int) -> dict:\n    pass\n",
            },
            "text-adventure": {
                "README.md": "# Text Adventure Game\n\nExplore a mysterious castle. Find treasure, avoid traps!\n\n## Files\n- `adventure.py` -- main game loop and parser\n- `player.py` -- Player class (health, inventory, score)\n- `rooms.py` -- Room classes connected by exits\n- `items.py` -- Item classes you can find and use\n\n## How to play\nRun `python adventure.py` and type directions like `north`, `take key`.",
                "adventure.py": "# Text Adventure Game\n# TODO: Import Player, Room, Item classes\n# TODO: Build the map of rooms\n# TODO: Main loop: parse input, move, interact\n# TODO: Win condition: find the treasure!\n\nprint(\"You wake up in a dark castle. Your goal: find the treasure!\")\nprint(\"Type 'help' for commands.\")\n",
                "player.py": "# Player Class\n# TODO: __init__(name) -- set starting health, inventory, score\n# TODO: take(item) -- add to inventory\n# TODO: has(item) -- check inventory\n# TODO: damage(amount) -- reduce health, return alive status\n# TODO: __str__ -- show stats\n\nclass Player:\n    pass\n",
                "rooms.py": "# Room Classes\n# TODO: Base Room class with name, description, exits, items\n# TODO: TreasureRoom subclass with win condition\n# TODO: TrapRoom subclass that damages the player\n# TODO: connect(room, direction) -- link rooms\n\nclass Room:\n    pass\n",
                "items.py": "# Item Classes\n# TODO: Base Item class with name and description\n# TODO: Key subclass -- can unlock certain rooms\n# TODO: Potion subclass -- restores health\n# TODO: Treasure subclass -- the win condition item\n\nclass Item:\n    pass\n",
            },
            "password-toolkit": {
                "README.md": "# Password Toolkit\n\nGenerate strong passwords, check their strength, and store them safely.\n\n## Files\n- `generator.py` -- generates random passwords\n- `strength.py` -- analyzes password strength\n- `vault.py` -- stores and retrieves passwords (encrypted)\n\n## Try it\nRun `python generator.py` to generate a password.",
                "generator.py": "# Password Generator\n# TODO: Use random.choices to generate passwords\n# TODO: Support options: length, uppercase, digits, symbols\n# TODO: Add a decorator that retries until minimum strength\n\ndef generate_password(length: int = 16, use_symbols: bool = True) -> str:\n    pass\n",
                "strength.py": "# Password Strength Checker\n# TODO: Score a password based on length, character variety\n# TODO: Return rating: weak / fair / strong / very strong\n# TODO: Give specific tips to improve weak passwords\n\ndef check_strength(password: str) -> dict:\n    pass\n",
                "vault.py": "# Password Vault\n# TODO: Store passwords in an encrypted JSON file\n# TODO: Master password to unlock the vault\n# TODO: search(service) -- find stored passwords\n\nMASTER_HASH = \"\"\nVAULT_FILE = \"vault.json\"\n\ndef unlock(master_password: str) -> bool:\n    pass\n",
            },
            "url-health-checker": {
                "README.md": "# URL Health Checker\n\nAsync tool that checks multiple URLs and reports which are up or down.\n\n## Files\n- `checker.py` -- async checker using asyncio\n- `reporter.py` -- formats and displays results\n- `urls.txt` -- list of URLs to check\n\n## Try it\nRun `python checker.py` to check all URLs.",
                "checker.py": "# Async URL Checker\n# TODO: Define an async function to check a single URL\n# TODO: Use asyncio.gather to check all URLs concurrently\n# TODO: Track response times and status codes\n\nimport asyncio\n\n# Simulated URL check (replace with real HTTP calls later)\nasync def check_url(url: str) -> dict:\n    await asyncio.sleep(0.5)\n    return {\"url\": url, \"status\": 200, \"time\": 0.5}\n\n\nasync def check_all(urls: list[str]) -> list[dict]:\n    pass\n",
                "reporter.py": "# Result Reporter\n# TODO: Display results in a formatted table\n# TODO: Show up/down count, average response time\n# TODO: Highlight slow or failing URLs in red\n\ndef show_report(results: list[dict]) -> None:\n    pass\n",
                "urls.txt": "# URLs to check (one per line)\nhttps://example.com\nhttps://httpbin.org/delay/1\nhttps://google.com\nhttps://github.com\nhttps://nonexistent-site-12345.com\n",
            },
            "unit-converter": {
                "README.md": "# Unit Converter CLI\n\nA well-tested CLI tool for converting between units.\n\n## Files\n- `converter.py` -- main CLI with argparse\n- `converters/` -- conversion functions by category\n  - `__init__.py`\n  - `temperature.py`\n  - `distance.py`\n  - `weight.py`\n- `tests/` -- unit tests\n  - `test_temperature.py`\n  - `test_distance.py`\n\n## Try it\nRun `python converter.py --help` to see available commands.",
                "converter.py": "# Unit Converter CLI\n# TODO: Use argparse to accept: value, from-unit, to-unit\n# TODO: Import converter modules and call the right function\n# TODO: Handle errors gracefully (unknown units, invalid values)\n\nimport argparse\n\ndef main():\n    pass\n\n\nif __name__ == \"__main__\":\n    main()\n",
                "converters/__init__.py": "from .temperature import celsius_to_fahrenheit, fahrenheit_to_celsius\nfrom .distance import km_to_miles, miles_to_km\nfrom .weight import kg_to_lbs, lbs_to_kg\n",
                "converters/temperature.py": "# Temperature Conversions\n\ndef celsius_to_fahrenheit(c: float) -> float:\n    return (c * 9/5) + 32\n\ndef fahrenheit_to_celsius(f: float) -> float:\n    return (f - 32) * 5/9\n",
                "converters/distance.py": "# Distance Conversions\n\ndef km_to_miles(km: float) -> float:\n    return km * 0.621371\n\ndef miles_to_km(miles: float) -> float:\n    return miles / 0.621371\n",
                "converters/weight.py": "# Weight Conversions\n\ndef kg_to_lbs(kg: float) -> float:\n    return kg * 2.20462\n\ndef lbs_to_kg(lbs: float) -> float:\n    return lbs / 2.20462\n",
                "tests/test_temperature.py": "# Unit Tests for Temperature\n# TODO: Write tests for celsius_to_fahrenheit and fahrenheit_to_celsius\n# TODO: Test edge cases: absolute zero, boiling, freezing\n\ndef test_celsius_to_fahrenheit():\n    pass\n",
                "tests/test_distance.py": "# Unit Tests for Distance\n# TODO: Write tests for km_to_miles and miles_to_km\n# TODO: Test that 0 returns 0, 1 returns expected value\n\ndef test_km_to_miles():\n    pass\n",
            },
            "data-analyzer": {
                "README.md": "# Data Analyzer\n\nLoad a CSV file, clean the data, compute statistics, and generate a report.\n\n## Files\n- `analyzer.py` -- main analysis pipeline\n- `loader.py` -- CSV loading with validation\n- `stats.py` -- statistical computations\n- `reports.py` -- text-based reports and charts\n- `data/` -- sample datasets\n  - `sales.csv`\n  - `employees.csv`\n\n## Try it\nRun `python analyzer.py data/sales.csv`.",
                "analyzer.py": "# Data Analyzer Pipeline\n# TODO: Load CSV data\n# TODO: Clean and validate\n# TODO: Compute statistics\n# TODO: Generate a report\n\nimport sys\nfrom loader import load_csv\nfrom stats import compute_stats\nfrom reports import generate_report\n\n\ndef main():\n    if len(sys.argv) < 2:\n        print(\"Usage: python analyzer.py <csv_file>\")\n        return\n    pass\n\n\nif __name__ == \"__main__\":\n    main()\n",
                "loader.py": "# CSV Loader\n# TODO: Load a CSV file and return rows as dicts\n# TODO: Handle missing values, wrong types\n# TODO: Validate required columns exist\n\ndef load_csv(filepath: str) -> list[dict]:\n    pass\n",
                "stats.py": "# Statistics Module\n# TODO: Implement functions:\n#       - mean(values)\n#       - median(values)\n#       - min_max(values)\n#       - count_by_category(data, column)\n#       - top_n(data, column, n)\n\ndef mean(values: list[float]) -> float:\n    pass\n\ndef median(values: list[float]) -> float:\n    pass\n",
                "reports.py": "# Report Generator\n# TODO: Generate a text report with:\n#       - Summary statistics\n#       - ASCII bar chart for category counts\n#       - Top N items\n\ndef generate_report(data: list[dict], stats: dict) -> str:\n    pass\n",
                "data/sales.csv": "product,category,price,quantity\nWidget A,Gadgets,19.99,150\nWidget B,Gadgets,29.99,85\nGizmo X,Gadgets,49.99,42\nSuper Tool,Tools,89.99,30\nMini Tool,Tools,14.99,200\nAccessory Pack,Accessories,9.99,500\nPremium Kit,Kits,129.99,15\nEco Widget,Gadgets,24.99,110\n",
                "data/employees.csv": "name,department,salary,years\nAlice,Engineering,95000,5\nBob,Marketing,72000,3\nCharlie,Engineering,110000,8\nDiana,Sales,65000,2\nEve,Engineering,105000,6\nFrank,Marketing,68000,4\nGrace,Sales,71000,3\nHenry,Engineering,120000,10\n",
            },
        }
        for project_name, files in starter_projects.items():
            project_dir = projects_dir / project_name
            project_dir.mkdir()
            for filename, content in files.items():
                filepath = project_dir / filename
                filepath.parent.mkdir(parents=True, exist_ok=True)
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
