from rich.style import Style
from rich.color import Color
from textual.widgets._text_area import TextAreaTheme


def _c(hex_str: str) -> Color:
    return Color.parse(hex_str)


def make_tokyo_night_theme() -> TextAreaTheme:
    return TextAreaTheme(
        name="tokyo-night",
        base_style=Style.from_color(_c("#a9b1d6"), _c("#1a1b26")),
        gutter_style=Style.from_color(_c("#565f89"), _c("#1a1b26")),
        cursor_style=Style.from_color(_c("#1a1b26"), _c("#a9b1d6")),
        cursor_line_style=Style(bgcolor=_c("#1f2335")),
        cursor_line_gutter_style=Style.from_color(_c("#7dcfff"), _c("#1f2335")),
        bracket_matching_style=Style(bgcolor=_c("#28344a"), bold=True),
        selection_style=Style(bgcolor=_c("#28344a")),
        syntax_styles={
            "string": Style(color=_c("#9ece6a")),
            "string.documentation": Style(color=_c("#9ece6a")),
            "comment": Style(color=_c("#565f89")),
            "heading.marker": Style(color=_c("#565f89")),
            "keyword": Style(color=_c("#bb9af7")),
            "operator": Style(color=_c("#89ddff")),
            "repeat": Style(color=_c("#bb9af7")),
            "exception": Style(color=_c("#f7768e")),
            "include": Style(color=_c("#bb9af7")),
            "keyword.function": Style(color=_c("#bb9af7")),
            "keyword.return": Style(color=_c("#bb9af7")),
            "keyword.operator": Style(color=_c("#bb9af7")),
            "conditional": Style(color=_c("#bb9af7")),
            "number": Style(color=_c("#ff9e64")),
            "float": Style(color=_c("#ff9e64")),
            "class": Style(color=_c("#ff9e64")),
            "type": Style(color=_c("#ff9e64")),
            "type.class": Style(color=_c("#ff9e64")),
            "type.builtin": Style(color=_c("#f7768e")),
            "variable.builtin": Style(color=_c("#a9b1d6")),
            "function": Style(color=_c("#7aa2f7")),
            "function.call": Style(color=_c("#7aa2f7")),
            "method": Style(color=_c("#7aa2f7")),
            "method.call": Style(color=_c("#7aa2f7")),
            "boolean": Style(color=_c("#ff9e64"), italic=True),
            "constant.builtin": Style(color=_c("#f7768e")),
            "json.null": Style(color=_c("#ff9e64"), italic=True),
            "regex.punctuation.bracket": Style(color=_c("#bb9af7")),
            "regex.operator": Style(color=_c("#bb9af7")),
            "tag": Style(color=_c("#f7768e")),
            "yaml.field": Style(color=_c("#f7768e"), bold=True),
            "json.label": Style(color=_c("#f7768e"), bold=True),
            "toml.type": Style(color=_c("#f7768e")),
            "toml.datetime": Style(color=_c("#ff9e64")),
            "css.property": Style(color=_c("#ff9e64")),
            "heading": Style(color=_c("#f7768e"), bold=True),
            "bold": Style(bold=True),
            "italic": Style(italic=True),
            "strikethrough": Style(strike=True),
            "link.label": Style(color=_c("#f7768e")),
            "link.uri": Style(color=_c("#7dcfff"), underline=True),
            "list.marker": Style(color=_c("#565f89")),
            "inline_code": Style(color=_c("#9ece6a")),
            "punctuation.bracket": Style(color=_c("#a9b1d6")),
            "punctuation.delimiter": Style(color=_c("#a9b1d6")),
            "punctuation.special": Style(color=_c("#a9b1d6")),
            "html.end_tag_error": Style(color=_c("#f7768e"), underline=True),
        },
    )
