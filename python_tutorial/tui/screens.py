import random

from textual.screen import Screen
from textual.widgets import Static, Button, Input, RichLog
from textual.containers import Container, Vertical, Horizontal
from textual.app import ComposeResult

from ..content import discover_phases, get_quiz_questions, search_content


class FlashcardScreen(Screen):
    def __init__(self, progress, phase=None, **kwargs):
        super().__init__(**kwargs)
        self.progress = progress
        self.phase = phase
        self.cards = []
        self.current_index = 0
        self.correct = 0
        self.revealed = False
        self.ratings = []

    def compose(self) -> ComposeResult:
        yield Static("", id="flashcard-header")
        yield Static("", id="flashcard-question")
        yield Static("", id="flashcard-answer")
        yield Vertical(id="flashcard-actions")
        yield RichLog(id="flashcard-feedback", highlight=True, markup=True)
        yield Static("", id="flashcard-progress")
        yield Button("Close", id="close-flashcards", variant="primary")

    def on_mount(self) -> None:
        phases = [self.phase] if self.phase else discover_phases()
        for p in phases:
            if p is None:
                continue
            for topic in p.topics:
                for question in get_quiz_questions(topic):
                    self.cards.append((p.number, topic.number, question.question, question.answer))

        if not self.cards:
            self.query_one("#flashcard-header", Static).update("No flashcards available")
            return

        random.shuffle(self.cards)
        self._show_card()

    def _reset_actions(self) -> Vertical:
        actions = self.query_one("#flashcard-actions", Vertical)
        actions.remove_children()
        return actions

    def _show_card(self) -> None:
        if self.current_index >= len(self.cards):
            self._show_results()
            return

        phase_num, topic_num, question, answer = self.cards[self.current_index]
        self.revealed = False
        self.query_one("#flashcard-header", Static).update(
            f"[bold cyan]Flashcard {self.current_index + 1}/{len(self.cards)}[/]"
        )
        self.query_one("#flashcard-question", Static).update(
            f"[bold yellow]P{phase_num}.{topic_num}[/] {question}"
        )
        self.query_one("#flashcard-answer", Static).update("")
        self.query_one("#flashcard-progress", Static).update(
            f"Score: {self.correct}/{self.current_index}"
        )

        actions = self._reset_actions()
        actions.mount(Button("Reveal Answer", id="flashcard-reveal", variant="default"))
        self.query_one("#flashcard-feedback", RichLog).clear()

    def _show_results(self) -> None:
        self.query_one("#flashcard-header", Static).update("[bold green]Flashcards Complete![/]")
        self.query_one("#flashcard-question", Static).update("")
        self.query_one("#flashcard-answer", Static).update("")
        self._reset_actions()
        feedback = self.query_one("#flashcard-feedback", RichLog)
        feedback.clear()
        total = len(self.cards)
        feedback.write(f"[bold]Final Score: {self.correct}/{total}[/]")
        if total > 0:
            percentage = (self.correct / total) * 100
            feedback.write(f"[bold]{percentage:.0f}%[/]")
        self.query_one("#flashcard-progress", Static).update("")

    def on_button_pressed(self, event) -> None:
        if event.button.id == "close-flashcards":
            self.app.pop_screen()
            return

        if not self.cards or self.current_index >= len(self.cards):
            return

        if event.button.id == "flashcard-reveal":
            _, _, _, answer = self.cards[self.current_index]
            self.revealed = True
            self.query_one("#flashcard-answer", Static).update(f"[bold green]Answer:[/] {answer}")
            actions = self._reset_actions()
            actions.mount(Button("1 Again", id="flash-rate-1", variant="error"))
            actions.mount(Button("2 Hard", id="flash-rate-2", variant="warning"))
            actions.mount(Button("3 Good", id="flash-rate-3", variant="success"))
            actions.mount(Button("4 Easy", id="flash-rate-4", variant="primary"))
            return

        if event.button.id and event.button.id.startswith("flash-rate-"):
            try:
                rating = int(event.button.id.rsplit("-", 1)[1])
            except (ValueError, IndexError):
                return

            self.ratings.append(rating)
            if rating >= 3:
                self.correct += 1

            feedback = self.query_one("#flashcard-feedback", RichLog)
            feedback.write(f"[bold]Rated:[/] {rating}")
            self.current_index += 1
            self._show_card()


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
