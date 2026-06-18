from dataclasses import dataclass
from typing import Optional


class GapBuffer:
    def __init__(self, initial: str = ""):
        # TODO: implement this
        pass

    def insert_char(self, c: str):
        # TODO: implement this
        pass

    def delete_char(self):
        # TODO: implement this
        pass

    def move_gap_to(self, pos: int):
        # TODO: implement this
        pass

    def to_string(self) -> str:
        # TODO: implement this
        return ""

    def load(self, text: str):
        # TODO: implement this
        pass

    def __len__(self) -> int:
        # TODO: implement this
        return 0

    def _grow(self):
        # TODO: implement this
        pass


@dataclass
class Cursor:
    row: int = 0
    col: int = 0


class EditorBuffer:
    def __init__(self):
        # TODO: implement this
        pass

    def insert_char(self, c: str):
        # TODO: implement this
        pass

    def delete_char(self):
        # TODO: implement this
        pass

    def move_left(self):
        # TODO: implement this
        pass

    def move_right(self):
        # TODO: implement this
        pass

    def move_up(self):
        # TODO: implement this
        pass

    def move_down(self):
        # TODO: implement this
        pass

    def _row_col_to_index(self, row: int, col: int) -> int:
        # TODO: implement this
        return 0

    def snapshot(self):
        # TODO: implement this
        pass

    def undo(self):
        # TODO: implement this
        pass

    def redo(self):
        # TODO: implement this
        pass

    def find(self, text: str) -> Optional[tuple[int, int]]:
        # TODO: implement this
        return None
