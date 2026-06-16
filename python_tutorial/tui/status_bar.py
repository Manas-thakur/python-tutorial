from textual.widgets import Static
from textual.widget import Widget


class TutorialStatusBar(Widget):
    def __init__(self, progress, **kwargs):
        super().__init__(**kwargs)
        self.progress = progress

    def compose(self):
        yield Static(id="status-text")

    def on_mount(self):
        self._update()

    def _update(self):
        text = self.query_one("#status-text", Static)
        level = self.progress.get_level()
        xp = self.progress.get_xp()
        info = self.progress.get_level_info()
        completed = self.progress.get_total_completed()
        streak = self.progress.get_streak()

        parts = [
            f"Level {level}",
            f"XP {xp}/{info['xp_needed']}",
            f"Topics {completed}/56",
        ]
        if streak:
            parts.append(f"Streak {streak}d")

        parts.append("Ctrl+P Search | Ctrl+Q Quiz | Ctrl+F Flashcards | F5 Run | Ctrl+B Sidebar | C Contents | Q Quit")

        text.update("  |  ".join(parts))

    def refresh(self, **kwargs):
        self._update()
        super().refresh(**kwargs)
