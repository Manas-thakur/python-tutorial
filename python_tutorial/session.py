import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

STATE_DIR = Path.home() / ".local" / "state" / "python-tutorial"
STATE_FILE = STATE_DIR / "session.json"


@dataclass
class SessionState:
    phase: Optional[int] = None
    topic: Optional[int] = None
    sidebar_collapsed: bool = False
    content_collapsed: bool = False

    def is_valid(self) -> bool:
        return self.phase is not None and self.topic is not None


def _ensure_dir():
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def save_session(state: SessionState) -> None:
    _ensure_dir()
    try:
        STATE_FILE.write_text(json.dumps({
            "phase": state.phase,
            "topic": state.topic,
            "sidebar_collapsed": state.sidebar_collapsed,
            "content_collapsed": state.content_collapsed,
        }))
    except OSError:
        pass


def load_session() -> SessionState:
    if not STATE_FILE.exists():
        return SessionState()
    try:
        data = json.loads(STATE_FILE.read_text())
        return SessionState(
            phase=data.get("phase"),
            topic=data.get("topic"),
            sidebar_collapsed=data.get("sidebar_collapsed", False),
            content_collapsed=data.get("content_collapsed", False),
        )
    except (json.JSONDecodeError, OSError, KeyError):
        return SessionState()


