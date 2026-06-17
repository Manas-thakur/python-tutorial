import random

from textual.screen import Screen, ModalScreen
from textual.widgets import Static, Button, Input, ListView, ListItem, Label, RichLog, DataTable
from textual.containers import Container, Vertical, Horizontal
from textual.app import ComposeResult
from textual.binding import Binding

from ..content import discover_phases, get_quiz_questions, search_content
from ..tutor import AdaptiveTutor


class TutorDashboardScreen(Screen):
    """Adaptive tutor dashboard showing mastery map and recommendations."""

    def __init__(self, progress, app_ref=None, **kwargs):
        super().__init__(**kwargs)
        self.progress = progress
        self.app_ref = app_ref
        self.tutor = AdaptiveTutor(progress)
        self.recommendations = []

    def compose(self) -> ComposeResult:
        yield Static("", id="tutor-header")
        yield RichLog(id="tutor-content", highlight=True, markup=True)
        yield Vertical(id="tutor-actions")
        yield Button("Close", id="close-tutor", variant="primary")

    def on_mount(self) -> None:
        self.recommendations = self.tutor.get_next_recommendations(limit=5)
        self._render_dashboard()

    def _render_dashboard(self) -> None:
        header = self.query_one("#tutor-header", Static)
        header.update("[bold cyan]Adaptive Learning Guide[/]")

        log = self.query_one("#tutor-content", RichLog)
        log.clear()

        stats = self.tutor.get_overall_stats()
        log.write(
            f"[bold]Overall Progress[/]\n"
            f"  {stats['completed']}/{stats['total_topics']} topics "
            f"({stats['completion_pct']:.0f}%)\n"
            f"  [green]Strong[/]: {stats['strong']}  [yellow]Weak[/]: {stats['weak']}\n"
            f"  Level {stats['level']} | {stats['xp']} XP | Streak: {stats['streak']}d\n"
        )

        log.write("\n[bold yellow]Recommended Next Actions:[/]\n")
        if self.recommendations:
            for i, rec in enumerate(self.recommendations, 1):
                icon = {
                    "learn": "\U0001f4da",
                    "quiz": "\u2753",
                    "flashcard": "\U0001f3b4",
                    "challenge": "\u26a1",
                    "review": "\U0001f504",
                }.get(rec.action_type, "\u2022")
                log.write(
                    f"  {i}. {icon} [bold]P{rec.phase}.{rec.topic}[/] "
                    f"({rec.action_type}) - {rec.reason}\n"
                )
        else:
            log.write("  No recommendations yet. Keep learning!\n")

        log.write("\n[bold]Phase Mastery Map:[/]\n")
        for phase_num in range(1, 8):
            summary = self.tutor.get_phase_summary(phase_num)
            if not summary:
                continue
            lock_icon = "" if summary["unlocked"] else " [red]\U0001f512[/]"
            bar = self._make_progress_bar(
                summary["completed"], summary["total"], 15
            )
            log.write(
                f"  {summary['title']}{lock_icon}\n"
                f"    {bar} {summary['completed']}/{summary['total']}\n"
            )

        actions = self.query_one("#tutor-actions", Vertical)
        actions.remove_children()
        if self.recommendations:
            rec = self.recommendations[0]
            actions.mount(
                Button(
                    f"Go to P{rec.phase}.{rec.topic}",
                    id="tutor-go-recommended",
                    variant="primary",
                )
            )

    def _make_progress_bar(self, completed: int, total: int, width: int = 15) -> str:
        if total == 0:
            filled = width
        else:
            filled = int((completed / total) * width)
        empty = width - filled
        return f"[green]{'█' * filled}[/][dim]{'░' * empty}[/]"

    def on_button_pressed(self, event) -> None:
        if event.button.id == "close-tutor":
            self.app.pop_screen()
        elif event.button.id == "tutor-go-recommended" and self.recommendations:
            rec = self.recommendations[0]
            self.app.pop_screen()


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
            if self.cards:
                phase, topic, _, _ = self.cards[0]
                self.progress.record_quiz_attempt(phase, topic, self.correct, total)
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
    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("enter", "next", "Next"),
        Binding("1", "answer_1", "A"),
        Binding("2", "answer_2", "B"),
        Binding("3", "answer_3", "C"),
        Binding("4", "answer_4", "D"),
    ]

    def __init__(self, progress, phase, **kwargs):
        super().__init__(**kwargs)
        self.progress = progress
        self.phase = phase
        self.questions = []
        self.current_index = 0
        self.correct = 0
        self._answered = False
        self._advancing = False

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
        self._answered = False
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

    def _show_next_button(self) -> None:
        opts = self.query_one("#quiz-options", Vertical)
        opts.remove_children()
        opts.mount(Button("Next Question", id="qopt-next", variant="primary"))

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
            self.progress.record_quiz_attempt(self.phase.number, 0, self.correct, total)
        self.query_one("#quiz-progress", Static).update("")

    def action_close(self) -> None:
        self.app.pop_screen()

    def action_next(self) -> None:
        if self._advancing:
            return
        self._advancing = True
        if self.current_index < len(self.questions):
            self.current_index += 1
            self._show_question()
        self._advancing = False

    def action_answer_1(self) -> None:
        self._select_answer(0)

    def action_answer_2(self) -> None:
        self._select_answer(1)

    def action_answer_3(self) -> None:
        self._select_answer(2)

    def action_answer_4(self) -> None:
        self._select_answer(3)

    def _select_answer(self, idx: int) -> None:
        if self._answered:
            return
        self._answered = True
        if not self.questions or self.current_index >= len(self.questions):
            return
        q = self.questions[self.current_index]
        if not q.is_mcq:
            return
        fb = self.query_one("#quiz-feedback", RichLog)
        if idx == q.answer_index:
            fb.write("[bold green]Correct![/]")
            self.correct += 1
        else:
            fb.write(f"[bold red]Incorrect.[/] Answer: {q.answer}")
        self._show_next_button()

    def on_button_pressed(self, event) -> None:
        if event.button.id == "close-quiz":
            self.action_close()
            return

        if not self.questions or self.current_index >= len(self.questions):
            return

        q = self.questions[self.current_index]

        if event.button.id == "qopt-reveal":
            if self._answered:
                return
            self._answered = True
            fb = self.query_one("#quiz-feedback", RichLog)
            fb.write(f"[bold]Answer:[/] {q.answer}")
            opts = self.query_one("#quiz-options", Vertical)
            opts.remove_children()
            opts.mount(Button("Yes - got it right", id="qa-yes", variant="success"))
            opts.mount(Button("No - got it wrong", id="qa-no", variant="error"))

        elif event.button.id and event.button.id.startswith("qopt-"):
            if self._answered:
                return
            self._answered = True
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
            self._show_next_button()

        elif event.button.id == "qa-yes":
            if self._advancing:
                return
            self._advancing = True
            self.correct += 1
            self.current_index += 1
            self._show_question()
            self._advancing = False
        elif event.button.id == "qa-no":
            if self._advancing:
                return
            self._advancing = True
            self.current_index += 1
            self._show_question()
            self._advancing = False
        elif event.button.id == "qopt-next":
            if self._advancing:
                return
            self._advancing = True
            self.current_index += 1
            self._show_question()
            self._advancing = False


class SearchScreen(Screen):
    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("enter", "open_selected", "Open"),
    ]

    def __init__(self, progress, **kwargs):
        super().__init__(**kwargs)
        self.progress = progress
        self._results = []

    def compose(self) -> ComposeResult:
        yield Static("[bold cyan]Search[/]", id="search-title")
        yield Input(placeholder="Type search term...", id="search-input")
        yield ListView(id="search-results")
        yield Button("Close", id="close-search", variant="primary")

    def on_input_changed(self, event) -> None:
        query = event.value.strip()
        listview = self.query_one("#search-results", ListView)
        listview.clear()
        self._results = []
        if not query:
            return
        phases = discover_phases()
        for p in phases:
            for t in p.topics:
                text = t.filepath.read_text(encoding="utf-8")
                if query.lower() in text.lower() or query.lower() in t.title.lower():
                    item = ListItem(Label(f"  P{p.number}.{t.number}  {t.title}"))
                    item._topic_data = (p, t)
                    listview.append(item)
                    self._results.append((p, t))

    def action_open_selected(self) -> None:
        listview = self.query_one("#search-results", ListView)
        if listview.index is not None and listview.index < len(self._results):
            phase, topic = self._results[listview.index]
            self._go_to_topic(phase, topic)

    def on_list_view_selected(self, event) -> None:
        if event.item and hasattr(event.item, '_topic_data'):
            event.stop()
            phase, topic = event.item._topic_data
            self._go_to_topic(phase, topic)

    def _go_to_topic(self, phase, topic) -> None:
        from .sidebar import TopicSelected
        self.app.post_message(TopicSelected(phase, topic))
        self.app.pop_screen()

    def action_close(self) -> None:
        self.dismiss(None)

    def on_button_pressed(self, event) -> None:
        if event.button.id == "close-search":
            self.action_close()


class HelpScreen(ModalScreen):
    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("q", "close", "Close"),
        Binding("?", "close", "Close"),
    ]

    def compose(self) -> ComposeResult:
        yield Static("[bold cyan]Keyboard Shortcuts[/]", id="help-title")
        yield DataTable(id="help-table")
        yield Button("Close", id="close-help", variant="primary")

    def on_mount(self) -> None:
        table = self.query_one("#help-table", DataTable)
        table.add_columns("Key", "Action")
        table.add_rows([
            ("q", "Quit tutorial"),
            ("?", "Open help"),
            ("Ctrl+B", "Toggle sidebar panel"),
            ("C", "Toggle content panel"),
            ("Ctrl+F", "Search topics"),
            ("Ctrl+Q", "Start quiz"),
            ("Ctrl+Shift+F", "Open flashcards"),
            ("Ctrl+T", "Open tutor dashboard"),
            ("F2", "Open playground (Fresh IDE)"),
            ("F5", "Run code"),
            ("Up / Down", "Previous / Next topic"),
            ("Left / Right", "Previous / Next section"),
            ("Enter", "Confirm / Next question"),
            ("Escape", "Close current screen"),
        ])

    def action_close(self) -> None:
        self.app.pop_screen()

    def on_button_pressed(self, event) -> None:
        if event.button.id == "close-help":
            self.action_close()
