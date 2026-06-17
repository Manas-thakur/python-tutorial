import pytest

from python_tutorial.content import discover_phases


@pytest.fixture
def phases():
    return discover_phases()


@pytest.fixture
def progress():
    from python_tutorial.progress import ProgressTracker
    tracker = ProgressTracker()
    tracker.reset()
    return tracker
