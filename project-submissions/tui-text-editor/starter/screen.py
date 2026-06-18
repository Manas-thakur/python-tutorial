import os
import sys
import tty
import signal
import shutil
import select

from syntax import tokenize, apply_highlighting


class Screen:
    def __init__(self):
        # TODO: implement this
        pass

    def enter_raw_mode(self):
        # TODO: implement this
        pass

    def exit_raw_mode(self):
        # TODO: implement this
        pass

    def read_key(self) -> str:
        # TODO: implement this
        return ""

    def render(self, buffer, mode="edit", prompt_input="", filepath=None):
        # TODO: implement this
        pass

    def _resize(self):
        # TODO: implement this
        pass
