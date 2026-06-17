from pygments.style import Style
from pygments.token import (Keyword, Name, Comment, String, Number,
                             Operator, Generic, Punctuation, Error, Text)


class TokyoNightStyle(Style):
    background_color = "#1a1b26"
    highlight_color = "#28344a"
    line_number_color = "#565f89"
    line_number_background_color = "#1a1b26"

    styles = {
        Text: "#a9b1d6",
        Comment: "#565f89",
        Comment.Single: "#565f89",
        Comment.Multiline: "#565f89",
        Comment.Special: "#565f89 italic",
        Keyword: "#bb9af7",
        Keyword.Constant: "#f7768e",
        Keyword.Declaration: "#bb9af7",
        Keyword.Namespace: "#bb9af7",
        Keyword.Pseudo: "#bb9af7",
        Keyword.Reserved: "#bb9af7",
        Keyword.Type: "#bb9af7",
        Name: "#a9b1d6",
        Name.Attribute: "#7aa2f7",
        Name.Builtin: "#f7768e",
        Name.Builtin.Pseudo: "#a9b1d6",
        Name.Class: "#ff9e64",
        Name.Constant: "#f7768e",
        Name.Decorator: "#7aa2f7",
        Name.Entity: "#7dcfff",
        Name.Exception: "#f7768e",
        Name.Function: "#7aa2f7",
        Name.Label: "#7aa2f7",
        Name.Namespace: "#ff9e64",
        Name.Property: "#7aa2f7",
        Name.Tag: "#f7768e",
        Name.Variable: "#a9b1d6",
        String: "#9ece6a",
        String.Backtick: "#9ece6a",
        String.Char: "#9ece6a",
        String.Doc: "#9ece6a",
        String.Double: "#9ece6a",
        String.Escape: "#bb9af7",
        String.Heredoc: "#9ece6a",
        String.Interpol: "#bb9af7",
        String.Other: "#9ece6a",
        String.Regex: "#89ddff",
        String.Single: "#9ece6a",
        String.Symbol: "#9ece6a",
        Number: "#ff9e64",
        Number.Float: "#ff9e64",
        Number.Hex: "#ff9e64",
        Number.Integer: "#ff9e64",
        Number.Oct: "#ff9e64",
        Operator: "#89ddff",
        Operator.Word: "#bb9af7",
        Punctuation: "#a9b1d6",
        Generic.Heading: "#f7768e bold",
        Generic.Subheading: "#f7768e bold",
        Generic.Deleted: "#f7768e",
        Generic.Inserted: "#9ece6a",
        Generic.Error: "#f7768e",
        Generic.Emph: "italic",
        Generic.Strong: "bold",
        Generic.Prompt: "#565f89",
        Generic.Output: "#a9b1d6",
        Generic.Traceback: "#f7768e",
        Error: "#f7768e",
    }

    name = "tokyo-night"
    aliases = ["tokyo-night"]
