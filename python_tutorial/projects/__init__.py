from ..models import ProjectTutorial
from .tui_text_editor import TUTORIAL as tui_text_editor
from .expense_tracker import TUTORIAL as expense_tracker
from .markdown_blog import TUTORIAL as markdown_blog
from .chat_server import TUTORIAL as chat_server
from .task_scheduler import TUTORIAL as task_scheduler
from .pixel_editor import TUTORIAL as pixel_editor
from .api_framework import TUTORIAL as api_framework

_ALL_PROJECTS: dict[str, ProjectTutorial] = {
    tui_text_editor.slug: tui_text_editor,
    expense_tracker.slug: expense_tracker,
    markdown_blog.slug: markdown_blog,
    chat_server.slug: chat_server,
    task_scheduler.slug: task_scheduler,
    pixel_editor.slug: pixel_editor,
    api_framework.slug: api_framework,
}


def load_all() -> list[ProjectTutorial]:
    return list(_ALL_PROJECTS.values())


def get(slug: str) -> ProjectTutorial | None:
    return _ALL_PROJECTS.get(slug)
