import os
import tempfile
import codecs


class FileHandler:
    def __init__(self):
        # TODO: implement this
        pass

    def read(self, path: str) -> str:
        # TODO: implement this
        return ""

    def save(self, buffer, path: str | None = None) -> None:
        # TODO: implement this
        pass

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
