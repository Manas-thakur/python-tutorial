from textual.screen import Screen
from textual.widgets import Static, Button, Input, RichLog
from textual.containers import Container, Vertical, Horizontal
from textual.app import ComposeResult

from ..content import discover_phases, get_quiz_questions, search_content


class QuizScreen(Screen):
    def __init__(self, progress, phase, **kwargs):
        super().__init__(**kwargs)
        self.progress = progress
        self.phase = phase
        self.questions = []
        self.current_index = 0
        self.correct = 0

    def compose(self) -> ComposeResult:
        yield Static("", id="quiz-header")
        yield Static("", id="quiz-question")
        yield Vertical(id="quiz-options")
        yield RichLog(id="quiz-feedback", highlight=True, markup=True)
        yield Static("", id="quiz-progress")
        yield Button("Close", id="close-quiz", variant="primary")

    def on_mount(self) -> None:
        for topic in self.phase.topics:
            self.questions.extend(get_quiz_questions(topic))
        if not self.questions:
            self.query_one("#quiz-header", Static).update("No quiz questions found")
            return
        self._show_question()

    def _show_question(self) -> None:
        if self.current_index >= len(self.questions):
            self._show_results()
            return

        q = self.questions[self.current_index]
        self.query_one("#quiz-header", Static).update(
            f"[bold cyan]Question {self.current_index + 1}/{len(self.questions)}[/]"
        )
        self.query_one("#quiz-question", Static).update(f"[bold yellow]{q.question}[/]")
        self.query_one("#quiz-progress", Static).update(
            f"Score: {self.correct}/{self.current_index}"
        )

        opts = self.query_one("#quiz-options", Vertical)
        opts.remove_children()

        if q.is_mcq:
            for i, opt in enumerate(q.options):
                opts.mount(Button(f"  {chr(65+i)}) {opt}", id=f"qopt-{i}"))
        else:
            opts.mount(Button("Reveal Answer", id="qopt-reveal", variant="default"))

        self.query_one("#quiz-feedback", RichLog).clear()

    def _show_results(self) -> None:
        self.query_one("#quiz-header", Static).update("[bold green]Quiz Complete![/]")
        self.query_one("#quiz-question", Static).update("")
        self.query_one("#quiz-options", Vertical).remove_children()
        fb = self.query_one("#quiz-feedback", RichLog)
        fb.clear()
        total = len(self.questions)
        fb.write(f"[bold]Final Score: {self.correct}/{total}[/]")
        if total > 0:
            pct = (self.correct / total) * 100
            fb.write(f"[bold]{pct:.0f}%[/]")
        self.query_one("#quiz-progress", Static).update("")

    def on_button_pressed(self, event) -> None:
        if event.button.id == "close-quiz":
            self.app.pop_screen()
            return

        if not self.questions or self.current_index >= len(self.questions):
            return

        q = self.questions[self.current_index]

        if event.button.id == "qopt-reveal":
            fb = self.query_one("#quiz-feedback", RichLog)
            fb.write(f"[bold]Answer:[/] {q.answer}")
            opts = self.query_one("#quiz-options", Vertical)
            opts.remove_children()
            opts.mount(Button("Yes - got it right", id="qa-yes", variant="success"))
            opts.mount(Button("No - got it wrong", id="qa-no", variant="error"))

        elif event.button.id and event.button.id.startswith("qopt-"):
            try:
                choice = int(event.button.id.split("-")[1])
            except (ValueError, IndexError):
                return
            fb = self.query_one("#quiz-feedback", RichLog)
            if choice == q.answer_index:
                fb.write("[bold green]Correct![/]")
                self.correct += 1
            else:
                fb.write(f"[bold red]Incorrect.[/] Answer: {q.answer}")
            opts = self.query_one("#quiz-options", Vertical)
            opts.remove_children()
            opts.mount(Button("Next Question", id="qopt-next", variant="primary"))

        elif event.button.id == "qa-yes":
            self.correct += 1
            self.current_index += 1
            self._show_question()
        elif event.button.id == "qa-no":
            self.current_index += 1
            self._show_question()
        elif event.button.id == "qopt-next":
            self.current_index += 1
            self._show_question()


class SearchScreen(Screen):
    def __init__(self, progress, **kwargs):
        super().__init__(**kwargs)
        self.progress = progress

    def compose(self) -> ComposeResult:
        yield Static("[bold cyan]Search[/]", id="search-title")
        yield Input(placeholder="Type search term...", id="search-input")
        yield RichLog(id="search-results", highlight=True, markup=True)
        yield Button("Close", id="close-search", variant="primary")

    def on_input_submitted(self, event) -> None:
        query = event.value.strip()
        if not query:
            return
        log = self.query_one("#search-results", RichLog)
        log.clear()
        phases = discover_phases()
        results = search_content(query, phases)
        if not results:
            log.write(f"[yellow]No results for '{query}'[/]")
            return
        log.write(f"[bold]{len(results)} topics found:[/]\n")
        for r in results[:15]:
            log.write(f"\n[bold yellow]P{r['phase']}.{r['topic']}[/] {r['title']}")
            for line_no, text in r["matches"][:3]:
                truncated = text[:120] + "..." if len(text) > 120 else text
                log.write(f"  [dim]L{line_no}:[/] {truncated}")

    def on_button_pressed(self, event) -> None:
        if event.button.id == "close-search":
            self.app.pop_screen()
