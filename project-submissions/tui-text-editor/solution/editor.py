import sys

from buffer import EditorBuffer
from screen import Screen
from files import FileHandler


class Editor:
    def __init__(self):
        self.buffer = EditorBuffer()
        self.screen = Screen()
        self.files = FileHandler()
        self.running = True
        self.mode = "edit"
        self.prompt_input = ""

    def run(self):
        self.screen.enter_raw_mode()
        try:
            while self.running:
                self.screen.render(
                    self.buffer,
                    mode=self.mode,
                    prompt_input=self.prompt_input,
                    filepath=self.files.current_path,
                )
                key = self.screen.read_key()
                self.handle_key(key)
        finally:
            self.screen.exit_raw_mode()

    def handle_key(self, key):
        if self.mode != "edit":
            self._handle_prompt_key(key)
            return

        if key == "Ctrl-Q":
            self.running = False
        elif key == "Ctrl-S":
            if self.files.current_path:
                self.files.save(self.buffer)
            else:
                self.mode = "save"
                self.prompt_input = ""
        elif key == "Ctrl-O":
            self.mode = "open"
            self.prompt_input = ""
        elif key == "Ctrl-Z":
            self.buffer.undo()
        elif key == "Ctrl-R":
            self.buffer.redo()
        elif key == "Ctrl-F":
            self.mode = "find"
            self.prompt_input = ""
        elif key == "Up":
            self.buffer.move_up()
        elif key == "Down":
            self.buffer.move_down()
        elif key == "Left":
            self.buffer.move_left()
        elif key == "Right":
            self.buffer.move_right()
        elif key == "Backspace":
            self.buffer.delete_char()
        elif key == "Enter":
            self.buffer.insert_char("\n")
        elif key == "Tab":
            self.buffer.insert_char("    ")
        elif key == "Escape":
            pass
        elif key and len(key) == 1:
            self.buffer.insert_char(key)

    def _handle_prompt_key(self, key):
        if key == "Escape":
            self.mode = "edit"
            self.prompt_input = ""
        elif key == "Enter":
            if self.mode == "find":
                pos = self.buffer.find(self.prompt_input)
                if pos is not None:
                    self.buffer.cursor.row, self.buffer.cursor.col = pos
                self.mode = "edit"
            elif self.mode == "open":
                try:
                    content = self.files.read(self.prompt_input)
                    self.buffer = EditorBuffer()
                    self.buffer.gap.load(content)
                except (FileNotFoundError, PermissionError, IsADirectoryError):
                    pass
                self.mode = "edit"
            elif self.mode == "save":
                self.files.save(self.buffer, self.prompt_input)
                self.mode = "edit"
            self.prompt_input = ""
        elif key == "Backspace":
            self.prompt_input = self.prompt_input[:-1]
        elif key == "Tab":
            self.prompt_input += "    "
        elif key and len(key) == 1:
            self.prompt_input += key


def main():
    editor = Editor()
    if len(sys.argv) > 1:
        try:
            content = editor.files.read(sys.argv[1])
            editor.buffer.gap.load(content)
        except (FileNotFoundError, PermissionError):
            pass
    editor.run()


if __name__ == "__main__":
    main()
