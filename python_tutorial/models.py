from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Tuple, Union


@dataclass
class Section:
    heading: str
    content: str


@dataclass
class Topic:
    number: int
    title: str
    filepath: Path
    sections: list[Section] = field(default_factory=list)

    @property
    def label(self) -> str:
        return f"{self.number}. {self.title}"


@dataclass
class Phase:
    number: int
    title: str
    path: Path
    topics: list[Topic] = field(default_factory=list)

    def __rich_repr__(self) -> Iterator[Union[str, Tuple[str, int]]]:
        yield "number", self.number
        yield "title", self.title
        yield "label", self.label
        yield "topic_count", len(self.topics)

    @property
    def label(self) -> str:
        return f"Phase {self.number}: {self.title}"


@dataclass
class QuizQuestion:
    question: str
    answer: str
    options: list[str] = field(default_factory=list)
    answer_index: int = -1

    @property
    def is_mcq(self) -> bool:
        return len(self.options) > 0 and self.answer_index >= 0
