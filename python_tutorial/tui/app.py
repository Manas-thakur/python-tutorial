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
from .screens import FlashcardScreen, QuizScreen, SearchScreen, TutorDashboardScreen, HelpScreen, PlaygroundCheatSheetScreen, ProjectsScreen, ProjectSelected


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
        Binding("f3", "projects", "Projects", show=True),
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
        self.current_project = None
        self.current_project_step = 0
        self._project_mode = False
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

        config_path = playground_dir / "playground-config.json"
        config_path.write_text(json.dumps({
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
            "markdown-blog": {
                "README.md": "# Markdown Blog Engine\n\nA static site generator that converts Markdown to HTML with themes, a dev server, and RSS support.\n\n## Structure\n- `build.py` -- builds the entire site\n- `serve.py` -- dev server with live reload\n- `parser.py` -- Markdown to HTML converter\n- `renderer.py` -- template engine with inheritance\n- `content/` -- sample blog posts (Markdown)\n- `themes/default/` -- HTML templates and CSS\n\n## Try it\n```\npython build.py\npython serve.py\n```\n\n## Extensions\nAdd syntax highlighting, tag pages, an RSS feed, or deploy to GitHub Pages.",
                "build.py": "# Site Builder\n# TODO: Walk content/ directory for .md files\n# TODO: Parse frontmatter (title, date, tags)\n# TODO: Convert Markdown body to HTML\n# TODO: Render through theme templates\n# TODO: Write output to _site/ directory\n# TODO: Generate index page, tag pages, RSS feed\n\nimport os\nfrom pathlib import Path\n\nCONTENT_DIR = Path(\"content\")\nOUTPUT_DIR = Path(\"_site\")\nTHEME_DIR = Path(\"themes/default\")\n\n\ndef build():\n    pass\n\n\nif __name__ == \"__main__\":\n    build()\n",
                "serve.py": "# Dev Server\n# TODO: Serve _site/ on http://localhost:8000\n# TODO: Watch content/ and themes/ for changes\n# TODO: Auto-rebuild and notify browser via SSE\n\nimport http.server\n\n\ndef serve(port: int = 8000):\n    pass\n\n\nif __name__ == \"__main__\":\n    serve()\n",
                "parser.py": "# Markdown Parser\n# TODO: Parse # headings, **bold**, *italic*\n# TODO: Parse code blocks with language tags\n# TODO: Parse lists (ordered and unordered)\n# TODO: Parse links and images\n# TODO: Parse frontmatter between --- lines\n# TODO: Return HTML string\n\ndef parse_frontmatter(text: str) -> tuple[dict, str]:\n    pass\n\ndef markdown_to_html(markdown: str) -> str:\n    pass\n",
                "renderer.py": "# Template Engine\n# TODO: Load HTML template with {{ variable }} placeholders\n# TODO: Support {% for %} and {% if %} block tags\n# TODO: Support {% include \"file.html\" %} partials\n# TODO: Support template inheritance ({% extends %})\n# TODO: Auto-escape HTML in variables\n\ndef render_template(template_path: str, context: dict) -> str:\n    pass\n\ndef render_post(post: dict, template: str = \"post.html\") -> str:\n    pass\n\ndef render_index(posts: list[dict], template: str = \"index.html\") -> str:\n    pass\n",
                "themes/default/base.html": "<!DOCTYPE html>\n<html>\n<head>\n    <title>{{ title }} - My Blog</title>\n    <meta charset=\"utf-8\">\n    <link rel=\"stylesheet\" href=\"/style.css\">\n</head>\n<body>\n    <header>\n        <h1><a href=\"/\">My Blog</a></h1>\n        <nav>\n            <a href=\"/\">Home</a>\n            <a href=\"/tags\">Tags</a>\n            <a href=\"/about\">About</a>\n        </nav>\n    </header>\n    <main>\n        {% block content %}{% endblock %}\n    </main>\n    <footer>\n        <p>Powered by the Markdown Blog Engine</p>\n    </footer>\n</body>\n</html>\n",
                "themes/default/post.html": "{% extends \"base.html\" %}\n{% block content %}\n<article>\n    <h2>{{ title }}</h2>\n    <p class=\"meta\">{{ date }} &middot; {{ tags }}</p>\n    <div class=\"content\">\n        {{ body }}\n    </div>\n</article>\n{% endblock %}\n",
                "themes/default/style.css": "body { max-width: 800px; margin: 0 auto; padding: 20px; font-family: Georgia, serif; line-height: 1.6; color: #333; }\nh1, h2, h3 { color: #222; }\n.meta { color: #888; font-size: 0.9em; }\npre { background: #f4f4f4; padding: 10px; border-radius: 4px; overflow-x: auto; }\ncode { background: #f4f4f4; padding: 2px 4px; border-radius: 2px; }\nimg { max-width: 100%; }\n",
                "content/hello-world.md": "---\ntitle: Hello World\ndate: 2025-01-15\ntags: general, python\n---\n\nWelcome to my blog! This is a **Markdown** post.\n\n## Code Example\n\n```python\ndef greet(name):\n    return f\"Hello, {name}!\"\n\nprint(greet(\"World\"))\n```\n\n## Lists\n\n- Item one\n- Item two\n- Item three\n",
                "content/python-tips.md": "---\ntitle: Python Tips for Beginners\ndate: 2025-01-20\ntags: python, tips\n---\n\nHere are some useful Python tips.\n\n## List Comprehensions\n\n```python\nsquares = [x**2 for x in range(10)]\n```\n\n## Context Managers\n\n```python\nwith open(\"file.txt\") as f:\n    content = f.read()\n```\n\n## Type Hints\n\n```python\ndef add(a: int, b: int) -> int:\n    return a + b\n```\n",
                "tests/test_parser.py": "# Tests for Markdown Parser\n# TODO: Test heading parsing\n# TODO: Test bold/italic parsing\n# TODO: Test code block parsing\n# TODO: Test frontmatter parsing\n\ndef test_heading():\n    pass\n\ndef test_bold():\n    pass\n",
                "tests/test_renderer.py": "# Tests for Template Engine\n# TODO: Test variable substitution\n# TODO: Test for loop rendering\n# TODO: Test template inheritance\n\ndef test_variable():\n    pass\n",
            },
            "chat-server": {
                "README.md": "# Chat Server & Client\n\nA multi-client TCP chat application with user authentication, rooms, and slash commands.\n\n## Files\n- `server.py` -- async chat server (asyncio)\n- `client.py` -- terminal chat client\n- `protocol.py` -- message serialization format\n- `auth.py` -- user authentication and storage\n- `commands.py` -- slash command handler (/nick, /join, /pm)\n- `tests/` -- protocol and server tests\n\n## Try it\nTerminal 1: `python server.py`\nTerminal 2: `python client.py`\n\n## Commands\n- `/nick <name>` -- change display name\n- `/join <room>` -- join a chat room\n- `/pm <user> <msg>` -- private message\n- `/users` -- list users in room\n- `/quit` -- disconnect\n\n## Extensions\nAdd message history persistence, file sharing, or end-to-end encryption.",
                "server.py": "# Chat Server\n# TODO: Accept multiple client connections via asyncio\n# TODO: Handle join/part messages\n# TODO: Route messages to correct rooms\n# TODO: Track connected users and their rooms\n# TODO: Implement rate limiting per user\n\nimport asyncio\n\n\nclass ChatServer:\n    def __init__(self, host: str = \"localhost\", port: int = 9000):\n        self.host = host\n        self.port = port\n        self.rooms: dict[str, set] = {\"general\": set()}\n        self.users: dict = {}\n\n    async def start(self):\n        pass\n\n    async def handle_client(self, reader, writer):\n        pass\n\n    async def broadcast(self, room: str, message: str, exclude=None):\n        pass\n\n\nif __name__ == \"__main__\":\n    server = ChatServer()\n    asyncio.run(server.start())\n",
                "client.py": "# Chat Client\n# TODO: Connect to server via asyncio\n# TODO: Read user input in one thread, receiver in another\n# TODO: Handle /slash commands locally\n# TODO: Display messages with timestamps and colors\n# TODO: Handle disconnection gracefully\n\nimport asyncio\n\n\nclass ChatClient:\n    def __init__(self, host: str = \"localhost\", port: int = 9000):\n        self.host = host\n        self.port = port\n        self.nick = \"anonymous\"\n        self.room = \"general\"\n\n    async def connect(self):\n        pass\n\n    async def send_loop(self):\n        pass\n\n    async def receive_loop(self):\n        pass\n\n\nif __name__ == \"__main__\":\n    client = ChatClient()\n    asyncio.run(client.connect())\n",
                "protocol.py": "# Message Protocol\n# TODO: Define message format: JSON with type, sender, room, body, timestamp\n# TODO: Serialize/deserialize messages\n# TODO: Define message types: JOIN, PART, MSG, PM, NICK, USERS, ERROR\n\nimport json\nfrom datetime import datetime\n\nMSG_TYPES = [\"JOIN\", \"PART\", \"MSG\", \"PM\", \"NICK\", \"USERS\", \"ERROR\"]\n\n\ndef encode(msg_type: str, sender: str, body: str, room: str = \"\", target: str = \"\") -> bytes:\n    pass\n\ndef decode(data: bytes) -> dict:\n    pass\n",
                "auth.py": "# Authentication\n# TODO: Store users in JSON file with hashed passwords\n# TODO: register(username, password) -- hash and save\n# TODO: login(username, password) -- verify credentials\n# TODO: generate_token() / verify_token() -- session tokens\n\nimport hashlib\nimport os\n\nUSERS_FILE = \"users.json\"\n\n\ndef register(username: str, password: str) -> bool:\n    pass\n\ndef login(username: str, password: str) -> bool:\n    pass\n",
                "commands.py": "# Slash Commands\n# TODO: Parse input for /command args\n# TODO: Handle /nick, /join, /pm, /users, /quit\n# TODO: Validate command arguments\n# TODO: Return response messages\n\ndef parse_command(text: str) -> tuple[str, list[str]]:\n    pass\n\ndef handle_command(cmd: str, args: list[str], client_state: dict) -> str:\n    pass\n",
                "tests/test_protocol.py": "# Protocol Tests\n# TODO: Test encode/decode round-trip\n# TODO: Test all message types\n# TODO: Test malformed message handling\n\nfrom protocol import encode, decode\n\n\ndef test_encode_decode():\n    pass\n",
                "tests/test_server.py": "# Server Tests\n# TODO: Test client connect/disconnect\n# TODO: Test message broadcast\n# TODO: Test room join/part\n# TODO: Test private messaging\n\ndef test_connect():\n    pass\n",
            },
            "expense-tracker": {
                "README.md": "# Expense Tracker\n\nA personal finance CLI app backed by SQLite. Track spending, generate reports, import bank CSVs, and analyze your habits.\n\n## Files\n- `tracker.py` -- main CLI with subcommands\n- `models.py` -- data models (Transaction, Category, Budget)\n- `database.py` -- SQLite wrapper (create, insert, query)\n- `analysis.py` -- spending analytics and trends\n- `reports.py` -- monthly reports, category breakdowns, charts\n- `importers.py` -- CSV import from bank statements\n- `data/` -- sample bank CSV for testing\n- `tests/` -- model and analysis tests\n\n## Try it\n```\npython tracker.py add --amount 25 --category Food --note \"Lunch\"\npython tracker.py report --month 2025-01\npython tracker.py import data/sample.csv\n```\n\n## Extensions\nAdd budgets, recurring transactions, export to PDF, or a web dashboard.",
                "tracker.py": "# Expense Tracker CLI\n# TODO: Use argparse with subcommands: add, list, report, import, budget\n# TODO: add -- create a new transaction\n# TODO: list -- show transactions with filters (date range, category)\n# TODO: report -- generate monthly summary\n# TODO: import -- parse CSV and bulk insert\n# TODO: budget -- set and check category budgets\n\nimport argparse\n\n\ndef main():\n    pass\n\n\nif __name__ == \"__main__\":\n    main()\n",
                "models.py": "# Data Models\n# TODO: Transaction dataclass: id, amount, category, date, note, type\n# TODO: Category dataclass: name, icon, monthly_limit\n# TODO: Budget dataclass: category, month, limit, spent\n# TODO: to_dict / from_dict methods for SQLite serialization\n\nfrom dataclasses import dataclass\nfrom datetime import date\n\n\n@dataclass\nclass Transaction:\n    pass\n\n\n@dataclass\nclass Budget:\n    pass\n",
                "database.py": "# SQLite Database Layer\n# TODO: Initialize database and create tables\n# TODO: insert_transaction(t) -- add a new transaction\n# TODO: get_transactions(filters) -- query with date/category filters\n# TODO: get_monthly_summary(year, month) -- aggregate by category\n# TODO: get_category_totals(start, end) -- spending by category\n\nimport sqlite3\n\nDB_FILE = \"expenses.db\"\n\n\ndef init_db():\n    pass\n\ndef insert_transaction(t) -> int:\n    pass\n\ndef get_monthly_summary(year: int, month: int) -> list[dict]:\n    pass\n",
                "analysis.py": "# Spending Analytics\n# TODO: Calculate total spending by category for a period\n# TODO: Find top spending categories\n# TODO: Calculate month-over-month change\n# TODO: Detect spending trends (increasing/decreasing)\n# TODO: Compare actual vs budget\n# TODO: Predict next month's spending\n\ndef spending_by_category(transactions: list, period: str = \"month\") -> dict:\n    pass\n\ndef month_over_month(transactions: list) -> dict:\n    pass\n\ndef budget_analysis(spending: dict, budgets: dict) -> list[dict]:\n    pass\n",
                "reports.py": "# Report Generator\n# TODO: Monthly report: total, by category, comparison to last month\n# TODO: Category breakdown with ASCII bar chart\n# TODO: Top 10 transactions this month\n# TODO: Budget vs actual report\n# TODO: Save report to text file\n\ndef monthly_report(transactions: list, year: int, month: int) -> str:\n    pass\n\ndef category_chart(spending: dict, width: int = 40) -> str:\n    pass\n",
                "importers.py": "# CSV Importer\n# TODO: Detect CSV format (columns, delimiter)\n# TODO: Parse common bank CSV formats\n# TODO: Map bank columns to internal fields\n# TODO: Validate and clean data\n# TODO: Handle duplicates (skip or warn)\n# TODO: Return list of Transaction objects\n\ndef import_csv(filepath: str) -> list:\n    pass\n",
                "data/sample.csv": "date,description,amount,category\n2025-01-02,Grocery Store,85.50,Food\n2025-01-03,Netflix Subscription,15.99,Entertainment\n2025-01-05,Gas Station,45.00,Transport\n2025-01-07,Restaurant Lunch,32.50,Food\n2025-01-10,Electric Bill,120.00,Utilities\n2025-01-12,Amazon Purchase,67.30,Shopping\n2025-01-15,Salary Deposit,5000.00,Income\n2025-01-18,Pharmacy,28.40,Health\n2025-01-22,Internet Bill,79.99,Utilities\n2025-01-28,Date Night,95.00,Entertainment\n",
                "tests/test_models.py": "# Model Tests\n# TODO: Test Transaction dataclass creation\n# TODO: Test to_dict / from_dict round-trip\n\ndef test_transaction():\n    pass\n",
                "tests/test_analysis.py": "# Analysis Tests\n# TODO: Test spending_by_category with sample data\n# TODO: Test month_over_month calculation\n# TODO: Test budget_analysis overspend detection\n\ndef test_spending_by_category():\n    pass\n",
            },
            "tui-text-editor": {
                "README.md": "# TUI Text Editor\n\nA minimal terminal-based text editor written from scratch. Features syntax highlighting, undo/redo, file dialogs, and a command palette.\n\n## Files\n- `editor.py` -- main editor loop and key handling\n- `buffer.py` -- text buffer with gap buffer and undo stack\n- `screen.py` -- terminal rendering (raw mode, cursor, colors)\n- `syntax.py` -- syntax highlighting rules engine\n- `files.py` -- file open/save with encoding detection\n- `tests/` -- unit tests for buffer and syntax\n\n## Try it\n```\npython editor.py          # new file\npython editor.py readme.md # open existing\n```\n\n## Keybindings\n- Ctrl+S -- save\n- Ctrl+O -- open\n- Ctrl+Z -- undo\n- Ctrl+Y -- redo\n- Ctrl+F -- find\n- Ctrl+Q -- quit\n\n## Extensions\nAdd split panes, a file explorer sidebar, or a minimap.",
                "editor.py": "# Main Editor\n# TODO: Initialize curses or raw terminal mode\n# TODO: Main loop: read key, dispatch to handler\n# TODO: Handle arrow keys, page up/down, home/end\n# TODO: Handle Ctrl+key combinations\n# TODO: Coordinate buffer, screen, and syntax modules\n# TODO: Implement command palette (Ctrl+P)\n\nimport sys\n\n\ndef main():\n    pass\n\n\ndef run_editor(filepath: str = None):\n    pass\n\n\nif __name__ == \"__main__\":\n    main()\n",
                "buffer.py": "# Text Buffer\n# TODO: Implement gap buffer for efficient insert/delete\n# TODO: Track cursor position (row, col)\n# TODO: Implement undo/redo stack (snapshot-based)\n# TODO: insert_char(c) -- insert at cursor\n# TODO: delete_char() -- delete before cursor\n# TODO: move_cursor(direction) -- navigate\n# TODO: get_line(n) -- return line content\n# TODO: search(text) -- find next occurrence\n\nclass GapBuffer:\n    def __init__(self, text: str = \"\"):\n        pass\n\n    def insert(self, char: str, pos: int = None):\n        pass\n\n    def delete(self, pos: int = None):\n        pass\n\n    def __str__(self) -> str:\n        pass\n\n\nclass UndoStack:\n    def __init__(self, max_size: int = 100):\n        pass\n\n    def push(self, state):\n        pass\n\n    def undo(self):\n        pass\n\n    def redo(self):\n        pass\n",
                "screen.py": "# Terminal Screen\n# TODO: Enter raw mode (disable echo, line buffering)\n# TODO: Render buffer lines to terminal with line numbers\n# TODO: Render cursor at correct position\n# TODO: Handle terminal resize events\n# TODO: Render status bar (filename, position, mode)\n# TODO: Support scrolling when buffer exceeds screen height\n# TODO: Color support via ANSI escape codes\n\ndef enter_raw_mode():\n    pass\n\ndef exit_raw_mode():\n    pass\n\ndef render(buffer, cursor_row: int, cursor_col: int, offset: int = 0):\n    pass\n\ndef clear_screen():\n    pass\n",
                "syntax.py": "# Syntax Highlighting\n# TODO: Define token types: KEYWORD, STRING, COMMENT, NUMBER, TYPE\n# TODO: Write regex patterns for Python tokens\n# TODO: Return list of (token_type, text) for a line\n# TODO: Support multi-line strings and comments\n# TODO: Make language definitions extensible (add JSON, HTML)\n\nKEYWORDS = {\"def\", \"class\", \"if\", \"else\", \"elif\", \"for\", \"while\",\n            \"return\", \"import\", \"from\", \"try\", \"except\", \"finally\",\n            \"with\", \"as\", \"pass\", \"break\", \"continue\", \"and\", \"or\",\n            \"not\", \"in\", \"is\", \"lambda\", \"yield\", \"async\", \"await\"}\n\n\ndef tokenize_line(line: str) -> list[tuple[str, str]]:\n    pass\n",
                "files.py": "# File Operations\n# TODO: read_file(path) -- detect encoding and read content\n# TODO: write_file(path, content) -- save with backup\n# TODO: get_filetype(path) -- detect file type from extension\n# TODO: list_directory(path) -- for file explorer\n# TODO: get_file_info(path) -- size, modified time, permissions\n\ndef read_file(path: str) -> tuple[str, str]:\n    pass\n\ndef write_file(path: str, content: str) -> None:\n    pass\n",
                "tests/test_buffer.py": "# Buffer Tests\n# TODO: Test insertion at various positions\n# TODO: Test deletion\n# TODO: Test undo/redo\n# TODO: Test cursor movement\n# TODO: Test search\n\ndef test_insert():\n    pass\n\ndef test_undo():\n    pass\n",
                "tests/test_syntax.py": "# Syntax Tests\n# TODO: Test keyword tokenization\n# TODO: Test string tokenization\n# TODO: Test comment tokenization\n# TODO: Test number tokenization\n\ndef test_keyword_tokens():\n    pass\n",
            },
            "task-scheduler": {
                "README.md": "# Task Scheduler\n\nA cron-like task scheduler with persistent storage, multiple trigger types, dependency management, and a web dashboard.\n\n## Files\n- `scheduler.py` -- main scheduler loop\n- `tasks.py` -- task definitions and decorators\n- `storage.py` -- persistent task storage (SQLite)\n- `triggers.py` -- cron, interval, and event triggers\n- `executor.py` -- task execution in subprocesses\n- `web/` -- optional Flask web dashboard\n  - `app.py`\n  - `templates/`\n- `tests/` -- scheduler and trigger tests\n\n## Try it\n```\npython scheduler.py\n```\n\n## Example Task\n```python\n@scheduler.every(interval=60)\ndef check_disk_space():\n    import shutil\n    usage = shutil.disk_usage(\"/\")\n    print(f\"Disk: {usage.free / usage.total * 100:.0f}% free\")\n```\n\n## Extensions\nAdd email/SMS notifications, task chaining, or a REST API.",
                "scheduler.py": "# Main Scheduler\n# TODO: Load tasks from storage\n# TODO: Main loop: check triggers, dispatch ready tasks\n# TODO: Run tasks concurrently with ThreadPoolExecutor\n# TODO: Handle task timeouts and retries\n# TODO: Log all executions\n# TODO: Graceful shutdown on SIGINT/SIGTERM\n\nimport time\nimport signal\n\n\nclass Scheduler:\n    def __init__(self):\n        self.tasks = []\n        self.running = False\n\n    def add_task(self, task):\n        pass\n\n    def start(self):\n        pass\n\n    def stop(self):\n        pass\n\n    def tick(self):\n        pass\n\n\nif __name__ == \"__main__\":\n    sched = Scheduler()\n    sched.start()\n",
                "tasks.py": "# Task Definitions\n# TODO: Task dataclass: id, name, fn, trigger, timeout, retries\n# TODO: TaskResult dataclass: success, output, duration, error\n# TODO: @every(interval) decorator -- run every N seconds\n# TODO: @cron(expr) decorator -- cron expression support\n# TODO: @on_event(event) decorator -- event-driven tasks\n\nfrom dataclasses import dataclass\n\n\n@dataclass\nclass Task:\n    pass\n\n\ndef every(interval: int):\n    pass\n\n\ndef cron(expression: str):\n    pass\n\n\ndef on_event(event_name: str):\n    pass\n",
                "storage.py": "# Persistent Storage\n# TODO: Store/load tasks from JSON file\n# TODO: Store execution history\n# TODO: Get next scheduled run times\n# TODO: Handle concurrent access with file locking\n\nimport json\n\nTASKS_FILE = \"tasks.json\"\nHISTORY_FILE = \"history.json\"\n\n\ndef load_tasks() -> list[dict]:\n    pass\n\ndef save_tasks(tasks: list) -> None:\n    pass\n\ndef log_execution(task_id: str, result: dict) -> None:\n    pass\n",
                "triggers.py": "# Trigger Types\n# TODO: IntervalTrigger -- run every N seconds\n# TODO: CronTrigger -- parse cron expression, compute next run\n# TODO: EventTrigger -- fire when an event is signaled\n# TODO: OnceTrigger -- run at a specific datetime\n# TODO: CompositeTrigger -- combine multiple triggers (AND/OR)\n\nfrom datetime import datetime\n\n\nclass IntervalTrigger:\n    def __init__(self, interval: int):\n        self.interval = interval\n\n    def next_run(self, last_run: datetime = None) -> datetime:\n        pass\n\n\nclass CronTrigger:\n    def __init__(self, expression: str):\n        self.expression = expression\n\n    def next_run(self, last_run: datetime = None) -> datetime:\n        pass\n\n\nclass OnceTrigger:\n    def __init__(self, run_at: datetime):\n        self.run_at = run_at\n\n    def next_run(self, last_run: datetime = None) -> datetime:\n        pass\n",
                "executor.py": "# Task Executor\n# TODO: Run task function in a subprocess\n# TODO: Enforce timeout (kill if exceeded)\n# TODO: Capture stdout/stderr\n# TODO: Implement retry logic with backoff\n# TODO: Return TaskResult\n\nimport subprocess\nimport time\n\n\ndef execute(task, timeout: int = 30) -> dict:\n    pass\n\n\ndef execute_with_retry(task, max_retries: int = 3) -> dict:\n    pass\n",
                "web/app.py": "# Web Dashboard (Flask)\n# TODO: Show list of tasks and their status\n# TODO: Show execution history\n# TODO: Manually trigger a task\n# TODO: Add/remove tasks via web form\n# TODO: Display live logs via WebSocket or polling\n\ndef create_app(scheduler):\n    pass\n",
                "web/templates/index.html": "<!DOCTYPE html>\n<html>\n<head><title>Task Dashboard</title></head>\n<body>\n    <h1>Task Scheduler</h1>\n    <table>\n        <tr><th>Task</th><th>Last Run</th><th>Status</th><th>Action</th></tr>\n        {% for task in tasks %}\n        <tr>\n            <td>{{ task.name }}</td>\n            <td>{{ task.last_run }}</td>\n            <td>{{ task.status }}</td>\n            <td><button>Run Now</button></td>\n        </tr>\n        {% endfor %}\n    </table>\n</body>\n</html>\n",
                "tests/test_scheduler.py": "# Scheduler Tests\n# TODO: Test task registration\n# TODO: Test tick finds ready tasks\n# TODO: Test concurrent execution\n# TODO: Test graceful shutdown\n\ndef test_add_task():\n    pass\n",
                "tests/test_triggers.py": "# Trigger Tests\n# TODO: Test IntervalTrigger.next_run\n# TODO: Test CronTrigger with simple expressions\n# TODO: Test OnceTrigger\n\ndef test_interval():\n    pass\n",
            },
            "pixel-editor": {
                "README.md": "# Pixel Editor\n\nA terminal-based ASCII art and pixel editor with drawing tools, layers, filters, and multiple export formats.\n\n## Files\n- `editor.py` -- main editor loop and key bindings\n- `canvas.py` -- pixel grid data structure\n- `tools.py` -- drawing tools (pen, line, rect, fill, picker)\n- `layers.py` -- layer management (add, merge, reorder)\n- `filters.py` -- image filters (invert, blur, edge detect)\n- `formats.py` -- import/export (PNG, ASCII, SVG)\n- `tests/` -- canvas and filter tests\n\n## Try it\n```\npython editor.py\n```\n\n## Keybindings\n- Arrow keys -- move cursor\n- Space -- draw pixel\n- D -- toggle draw/erase mode\n- L -- line tool\n- R -- rectangle tool\n- G -- flood fill\n- F -- filters menu\n- Ctrl+S -- save\n\n## Extensions\nAdd animation frames, palette management, or collaborative editing.",
                "editor.py": "# Pixel Editor Main Loop\n# TODO: Initialize canvas with default size\n# TODO: Main loop: read key, dispatch to tool\n# TODO: Render canvas to terminal with pixel characters\n# TODO: Show tool palette, color picker, and layer list\n# TODO: Handle file open/save dialogs\n# TODO: Undo/redo for drawing operations\n\nimport sys\n\n\ndef main():\n    pass\n\n\ndef run_editor(width: int = 64, height: int = 32):\n    pass\n\n\nif __name__ == \"__main__\":\n    main()\n",
                "canvas.py": "# Pixel Canvas\n# TODO: 2D grid of pixels (color values as strings)\n# TODO: get_pixel(x, y) -- return color\n# TODO: set_pixel(x, y, color) -- draw a pixel\n# TODO: clear(fill_color) -- reset canvas\n# TODO: resize(new_w, new_h) -- crop or expand\n# TODO: render() -- return string representation\n# TODO: Support transparency (None value)\n\nclass Canvas:\n    def __init__(self, width: int = 64, height: int = 32):\n        self.width = width\n        self.height = height\n        self.pixels = {}\n\n    def set_pixel(self, x: int, y: int, color: str):\n        pass\n\n    def get_pixel(self, x: int, y: int):\n        pass\n\n    def render(self, palette: dict = None) -> str:\n        pass\n\n    def to_ascii(self, char_map: dict = None) -> str:\n        pass\n",
                "tools.py": "# Drawing Tools\n# TODO: PenTool -- draw single pixels on click/drag\n# TODO: LineTool -- draw lines using Bresenham algorithm\n# TODO: RectTool -- draw rectangles (outline or filled)\n# TODO: FloodFillTool -- bucket fill connected region\n# TODO: EyedropperTool -- pick color from canvas\n# TODO: EraserTool -- set pixels to background\n# TODO: SelectionTool -- select rectangular region for copy/paste\n\nclass Tool:\n    def __init__(self, name: str):\n        self.name = name\n\n    def on_click(self, canvas, x: int, y: int, color: str):\n        pass\n\n    def on_drag(self, canvas, x1: int, y1: int, x2: int, y2: int, color: str):\n        pass\n\n\nclass PenTool(Tool):\n    pass\n\n\nclass LineTool(Tool):\n    pass\n\n\nclass FloodFillTool(Tool):\n    pass\n",
                "layers.py": "# Layer Management\n# TODO: Layer class: name, canvas, visible, opacity\n# TODO: add_layer(name) -- add new layer above current\n# TODO: remove_layer(index) -- delete a layer\n# TODO: merge_down(index) -- merge layer into the one below\n# TODO: move_layer(from_idx, to_idx) -- reorder\n# TODO: composite() -- render all visible layers combined\n# TODO: Support blending modes (normal, multiply, screen)\n\nclass Layer:\n    def __init__(self, name: str, width: int, height: int):\n        self.name = name\n        self.canvas = None\n        self.visible = True\n        self.opacity = 1.0\n\n\nclass LayerStack:\n    def __init__(self):\n        self.layers = []\n\n    def add(self, name: str, width: int, height: int):\n        pass\n\n    def composite(self) -> str:\n        pass\n",
                "filters.py": "# Image Filters\n# TODO: InvertFilter -- invert all colors\n# TODO: GrayscaleFilter -- convert to grayscale\n# TODO: BrightnessFilter -- adjust brightness\n# TODO: ContrastFilter -- adjust contrast\n# TODO: BlurFilter -- simple box blur\n# TODO: EdgeDetectFilter -- Sobel edge detection\n# TODO: PixelateFilter -- reduce resolution for mosaic effect\n\ndef apply_invert(canvas) -> None:\n    pass\n\ndef apply_grayscale(canvas) -> None:\n    pass\n\ndef apply_blur(canvas, radius: int = 3) -> None:\n    pass\n\ndef apply_edge_detect(canvas) -> None:\n    pass\n",
                "formats.py": "# Import/Export Formats\n# TODO: Export as ASCII art (characters based on brightness)\n# TODO: Export as HTML table (colored cells for web)\n# TODO: Export as SVG rectangles\n# TODO: Import from PNG (simplified, if PIL available)\n# TODO: Import from text/ASCII art files\n\ndef export_ascii(canvas, chars: str = \"@%#*+=-:. \") -> str:\n    pass\n\ndef export_svg(canvas, cell_size: int = 8) -> str:\n    pass\n\ndef import_ascii(text: str) -> object:\n    pass\n",
                "tests/test_canvas.py": "# Canvas Tests\n# TODO: Test get/set pixel\n# TODO: Test clear\n# TODO: Test render consistency\n\ndef test_set_get_pixel():\n    pass\n\ndef test_clear():\n    pass\n",
                "tests/test_filters.py": "# Filter Tests\n# TODO: Test invert filter\n# TODO: Test grayscale filter\n# TODO: Test blur filter\n\ndef test_invert():\n    pass\n",
            },
            "api-framework": {
                "README.md": "# API Framework\n\nA minimal web API framework inspired by Flask/FastAPI. Includes URL routing, middleware, JSON responses, error handling, and example apps.\n\n## Files\n- `framework.py` -- core App class with route registration\n- `server.py` -- WSGI-compatible HTTP server\n- `routing.py` -- URL pattern matching with path parameters\n- `middleware.py` -- request/response middleware chain\n- `responses.py` -- JSON, HTML, and error response helpers\n- `request.py` -- Request object (parsed headers, body, query)\n- `examples/` -- example API apps\n  - `hello.py` -- basic hello world\n  - `todo_api.py` -- CRUD todo API with in-memory storage\n- `tests/` -- routing and response tests\n\n## Try it\n```\npython examples/todo_api.py\n# In another terminal: curl http://localhost:8000/todos\n```\n\n## Your API\n```python\nfrom framework import App\n\napp = App()\n\n@app.route(\"/hello/{name}\")\ndef hello(request, name):\n    return {\"message\": f\"Hello, {name}!\"}\n```\n\n## Extensions\nAdd ORM integration, WebSocket support, OpenAPI docs, or authentication.",
                "framework.py": "# Web Framework Core\n# TODO: App class: register routes, handle requests\n# TODO: @app.route(path) decorator for GET\n# TODO: @app.route(path, methods=[\"POST\"]) for other methods\n# TODO: Request handling pipeline: parse -> route -> middleware -> response\n# TODO: Error handling with try/except wrapper\n# TODO: Static file serving for development\n\nfrom .routing import Router\nfrom .request import Request\nfrom .responses import json_response, html_response, error_response\n\n\nclass App:\n    def __init__(self):\n        self.router = Router()\n        self.middleware = []\n\n    def route(self, path: str, methods: list[str] = None):\n        pass\n\n    def use(self, middleware_fn):\n        pass\n\n    def handle(self, environ: dict, start_response) -> list[bytes]:\n        pass\n\n    def run(self, host: str = \"localhost\", port: int = 8000):\n        pass\n",
                "server.py": "# HTTP Server\n# TODO: Create a WSGI-compatible server using http.server or sockets\n# TODO: Parse incoming HTTP request into environ dict\n# TODO: Pass to App.handle() and send response\n# TODO: Handle concurrent connections (ThreadingHTTPServer)\n# TODO: Graceful shutdown on SIGINT\n\nimport http.server\nimport json\n\n\nclass WSGIServer:\n    def __init__(self, app, host: str = \"localhost\", port: int = 8000):\n        self.app = app\n        self.host = host\n        self.port = port\n\n    def start(self):\n        pass\n",
                "routing.py": "# URL Router\n# TODO: Route class: path pattern, handler, methods\n# TODO: Router.register(path, handler, methods)\n# TODO: Router.match(path, method) -- find handler, extract params\n# TODO: Support path parameters: /users/{id}\n# TODO: Support query string parsing\n# TODO: Return 404 if no route matches\n\nimport re\n\n\nclass Route:\n    def __init__(self, pattern: str, handler, methods: list[str] = None):\n        self.pattern = pattern\n        self.handler = handler\n        self.methods = methods or [\"GET\"]\n        self._regex = None\n        self._param_names = []\n\n    def compile(self):\n        pass\n\n    def match(self, path: str) -> dict | None:\n        pass\n\n\nclass Router:\n    def __init__(self):\n        self.routes = []\n\n    def add(self, pattern: str, handler, methods: list[str] = None):\n        pass\n\n    def resolve(self, method: str, path: str) -> tuple | None:\n        pass\n",
                "middleware.py": "# Middleware Chain\n# TODO: Base middleware class with process_request and process_response\n# TODO: CORSMiddleware -- add CORS headers\n# TODO: LoggerMiddleware -- log requests to stdout\n# TODO: AuthMiddleware -- check for API token\n# TODO: RateLimitMiddleware -- limit requests per IP\n# TODO: Chain middleware execution order\n\nimport time\n\n\nclass Middleware:\n    def process_request(self, request):\n        pass\n\n    def process_response(self, request, response):\n        pass\n\n\nclass LoggerMiddleware(Middleware):\n    def process_request(self, request):\n        request._start_time = time.time()\n\n    def process_response(self, request, response):\n        elapsed = time.time() - request._start_time\n        print(f\"{request.method} {request.path} -> {response.status} ({elapsed:.3f}s)\")\n\n\nclass CORSMiddleware(Middleware):\n    def process_response(self, request, response):\n        response.headers[\"Access-Control-Allow-Origin\"] = \"*\"\n        response.headers[\"Access-Control-Allow-Methods\"] = \"GET, POST, PUT, DELETE, OPTIONS\"\n\n\nclass AuthMiddleware(Middleware):\n    def process_request(self, request):\n        pass\n\n\nclass RateLimitMiddleware(Middleware):\n    def __init__(self, max_requests: int = 100, window: int = 60):\n        self.max_requests = max_requests\n        self.window = window\n        self.requests = {}\n\n    def process_request(self, request):\n        pass\n",
                "responses.py": "# Response Helpers\n# TODO: Response class: status, headers, body\n# TODO: json_response(data, status) -- JSON response\n# TODO: html_response(text, status) -- HTML response\n# TODO: text_response(text, status) -- plain text\n# TODO: error_response(status, message) -- JSON error\n# TODO: redirect_response(location) -- 302 redirect\n\nimport json\n\n\nclass Response:\n    def __init__(self, body: str, status: int = 200, content_type: str = \"text/plain\"):\n        self.status = status\n        self.headers = {\"Content-Type\": content_type}\n        self.body = body\n\n    def to_wsgi(self, start_response) -> list[bytes]:\n        pass\n\n\ndef json_response(data, status: int = 200) -> Response:\n    pass\n\ndef html_response(text: str, status: int = 200) -> Response:\n    pass\n\ndef error_response(status: int, message: str) -> Response:\n    pass\n",
                "request.py": "# Request Object\n# TODO: Parse environ dict from WSGI server\n# TODO: Extract method, path, headers, query string\n# TODO: Parse JSON body for POST/PUT\n# TODO: Parse form-encoded body\n# TODO: Parse cookies from headers\n\nfrom urllib.parse import parse_qs\n\n\nclass Request:\n    def __init__(self, environ: dict):\n        self.environ = environ\n        self.method = \"GET\"\n        self.path = \"/\"\n        self.headers = {}\n        self.query = {}\n        self.body = None\n        self.json = None\n        self.cookies = {}\n\n    def parse(self):\n        pass\n",
                "examples/hello.py": "# Hello World API\nfrom framework import App\n\napp = App()\n\n\n@app.route(\"/\")\ndef home(request):\n    return {\"message\": \"Welcome to the API Framework!\"}\n\n\n@app.route(\"/hello/{name}\")\ndef greet(request, name):\n    return {\"hello\": name}\n\n\nif __name__ == \"__main__\":\n    app.run()\n",
                "examples/todo_api.py": "# Todo API Example\nfrom framework import App\n\napp = App()\ntodos = []\ncounter = 0\n\n\n@app.route(\"/todos\")\ndef list_todos(request):\n    return {\"todos\": todos}\n\n\n@app.route(\"/todos\", methods=[\"POST\"])\ndef create_todo(request):\n    # TODO: parse request.json and add a new todo\n    return {\"message\": \"created\"}, 201\n\n\n@app.route(\"/todos/{id}\")\ndef get_todo(request, id):\n    # TODO: find todo by id and return it\n    pass\n\n\n@app.route(\"/todos/{id}\", methods=[\"DELETE\"])\ndef delete_todo(request, id):\n    # TODO: find and remove todo by id\n    pass\n\n\nif __name__ == \"__main__\":\n    app.run()\n",
                "tests/test_routing.py": "# Router Tests\n# TODO: Test exact path matching\n# TODO: Test parameter extraction from path\n# TODO: Test 404 for unmatched routes\n# TODO: Test method filtering\n\ndef test_exact_match():\n    pass\n\ndef test_path_params():\n    pass\n",
                "tests/test_responses.py": "# Response Tests\n# TODO: Test json_response serialization\n# TODO: Test Response.to_wsgi output format\n# TODO: Test error_response structure\n\ndef test_json_response():\n    pass\n",
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

    def action_projects(self) -> None:
        self.push_screen(ProjectsScreen(self.progress))

    def on_project_selected(self, message: ProjectSelected) -> None:
        self._load_project(message.project)

    def _load_project(self, project) -> None:
        self.current_project = project
        self.current_project_step = 0
        self._project_mode = True
        self.query_one(ContentPanel).load_steps(project.steps, project.title)
        self.query_one(CodePanel).load_project(project)
        self.progress.mark_project_step(project.slug, 0)
        self.query_one(TutorialStatusBar).refresh()
        self._update_nav_hints()

    def on_section_changed(self, message) -> None:
        if self._project_mode and self.current_project:
            idx = message.index
            prev_step = self.current_project_step
            self.current_project_step = idx
            if idx > prev_step:
                self.progress.mark_project_step(self.current_project.slug, idx)
            self.query_one(TutorialStatusBar).refresh()

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
        self._project_mode = False
        self.current_project = None
        self.current_project_step = 0
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
