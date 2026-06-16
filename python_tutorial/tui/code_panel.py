from textual.widgets import TextArea, Button, RichLog, Static
from textual.widget import Widget
from textual.containers import Vertical

from ..sandbox import run_code
from ..explainer import explain_error


class CodePanel(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._topic = None

    def compose(self):
        yield Static("[bold]Code Editor[/]", id="code-heading")
        yield TextArea(
            "# Write Python code here\n",
            id="code-editor",
            language="python",
            theme="monokai",
        )
        yield Button("Run (F5)", id="run-btn", variant="primary")
        yield Static("[bold]Output:[/]", id="output-heading")
        yield RichLog(id="output-log", highlight=True, markup=True, max_lines=100)

    def load_topic(self, topic) -> None:
        self._topic = topic
        self.query_one("#code-editor", TextArea).text = "# Write Python code here\n"

    def run_code(self) -> None:
        editor = self.query_one("#code-editor", TextArea)
        log = self.query_one("#output-log", RichLog)
        log.clear()

        code = editor.text.strip()
        if not code:
            log.write("[dim]No code to run[/]")
            return

        log.write("[dim]Running...[/]")
        result = run_code(code)

        if result["stdout"]:
            log.write("[bold]stdout:[/]")
            log.write(result["stdout"].rstrip())

        if result["stderr"]:
            log.write("[bold red]stderr:[/]")
            log.write(result["stderr"].rstrip())
            expl = explain_error(result["stderr"], result["stderr"])
            log.write(f"\n[bold yellow]Explanation: {expl['title']}[/]")
            log.write(expl["explanation"])
            if expl["common_causes"]:
                log.write("\n[bold]Common causes:[/]")
                for c in expl["common_causes"]:
                    log.write(f"  - {c}")
            if expl["fixes"]:
                log.write("\n[bold]How to fix:[/]")
                for f in expl["fixes"]:
                    log.write(f"  - {f}")
        elif result["success"]:
            log.write("[green]Code ran successfully[/]")

    def on_button_pressed(self, event) -> None:
        if event.button.id == "run-btn":
            self.run_code()
