import os
import tempfile
import codecs


class FileHandler:
    def __init__(self):
        self.current_path: str | None = None
        self.encoding: str = "utf-8"

    def read(self, path: str) -> str:
        self.current_path = path
        with open(path, "rb") as f:
            raw = f.read()
        self.encoding = self._detect_encoding(raw)
        return raw.decode(self.encoding)

    def save(self, buffer, path: str | None = None) -> None:
        if path is not None:
            self.current_path = path
        if not self.current_path:
            return
        text = buffer.gap.to_string()
        fd, tmp_path = tempfile.mkstemp(
            dir=os.path.dirname(self.current_path) or ".",
            prefix=".editor-tmp-",
        )
        try:
            with os.fdopen(fd, "w", encoding=self.encoding) as f:
                f.write(text)
            os.replace(tmp_path, self.current_path)
        except BaseException:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def _detect_encoding(self, raw: bytes) -> str:
        if raw.startswith(codecs.BOM_UTF32_LE) or raw.startswith(codecs.BOM_UTF32_BE):
            return "utf-32"
        if raw.startswith(codecs.BOM_UTF16_LE) or raw.startswith(codecs.BOM_UTF16_BE):
            return "utf-16"
        if raw.startswith(codecs.BOM_UTF8):
            return "utf-8-sig"
        try:
            raw.decode("utf-8")
            return "utf-8"
        except UnicodeDecodeError:
            try:
                raw.decode("latin-1")
                return "latin-1"
            except UnicodeDecodeError:
                return "utf-8"
