import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "..")

from renderer import render_template, escape_html


def test_variable_substitution():
    result = render_template("Hello {{ name }}!", {"name": "World"})
    assert result == "Hello World!", f"Expected 'Hello World!', got {result!r}"


def test_multiple_variables():
    result = render_template(
        "{{ a }} and {{ b }}",
        {"a": "foo", "b": "bar"},
    )
    assert result == "foo and bar"


def test_missing_variable():
    result = render_template("Hello {{ name }}!", {})
    assert result == "Hello !"


def test_escaped_variable():
    result = render_template("{{ content }}", {"content": "<script>alert('xss')</script>"})
    assert "&lt;script&gt;" in result
    assert "<script>" not in result


def test_safe_variable():
    result = render_template(
        "{{ content|safe }}",
        {"content": "<strong>bold</strong>"},
    )
    assert "<strong>bold</strong>" in result


def test_for_loop():
    result = render_template(
        "{% for item in items %}<li>{{ item }}</li>{% endfor %}",
        {"items": ["A", "B", "C"]},
    )
    assert result == "<li>A</li><li>B</li><li>C</li>"


def test_for_loop_empty():
    result = render_template(
        "{% for item in items %}<li>{{ item }}</li>{% endfor %}",
        {"items": []},
    )
    assert result == ""


def test_for_loop_missing_variable():
    result = render_template(
        "{% for item in items %}{{ item }}{% endfor %}",
        {},
    )
    assert result == ""


def test_if_block_true():
    result = render_template(
        "{% if show %}{{ message }}{% endif %}",
        {"show": True, "message": "visible"},
    )
    assert result == "visible"


def test_if_block_false():
    result = render_template(
        "{% if show %}visible{% endif %}",
        {"show": False},
    )
    assert result == ""


def test_if_block_with_string():
    result = render_template(
        "{% if name %}Hello {{ name }}{% endif %}",
        {"name": "Alice"},
    )
    assert result == "Hello Alice"


def test_if_block_empty_string():
    result = render_template(
        "{% if name %}visible{% endif %}",
        {"name": ""},
    )
    assert result == ""


def test_template_inheritance():
    with tempfile.TemporaryDirectory() as tmpdir:
        base_html = """<html><head><title>{% block title %}Default{% endblock %}</title></head><body>{% block content %}{% endblock %}</body></html>"""
        child_html = """{% extends "base.html" %}{% block title %}Child{% endblock %}{% block content %}<p>Content</p>{% endblock %}"""

        base_path = Path(tmpdir) / "base.html"
        base_path.write_text(base_html, encoding="utf-8")

        result = render_template(child_html, {"site_name": "Test"}, template_dir=tmpdir)
        assert "<title>Child</title>" in result
        assert "<p>Content</p>" in result


def test_include():
    with tempfile.TemporaryDirectory() as tmpdir:
        header_html = "<header>{{ title }}</header>"
        header_path = Path(tmpdir) / "header.html"
        header_path.write_text(header_html, encoding="utf-8")

        result = render_template(
            "{% include \"header.html\" %}<main>Body</main>",
            {"title": "My Site"},
            template_dir=tmpdir,
        )
        assert "<header>My Site</header>" in result
        assert "<main>Body</main>" in result


def test_escape_html():
    assert escape_html("<") == "&lt;"
    assert escape_html(">") == "&gt;"
    assert escape_html("&") == "&amp;"
    assert escape_html('"') == "&quot;"
    assert escape_html("'") == "'"
    assert escape_html("<script>") == "&lt;script&gt;"


def test_dotted_access():
    result = render_template(
        "{{ post.title }}",
        {"post": {"title": "Hello"}},
    )
    assert result == "Hello"


def test_autoescape_default():
    result = render_template(
        "{{ content }}",
        {"content": "<br>"},
    )
    assert result == "&lt;br&gt;"


def test_nested_for_loop():
    result = render_template(
        "{% for row in matrix %}{% for cell in row %}{{ cell }}{% endfor %}|{% endfor %}",
        {"matrix": [["1", "2"], ["3", "4"]]},
    )
    assert result == "12|34|"


def test_run_all():
    tests = [
        ("variable_substitution", test_variable_substitution),
        ("multiple_variables", test_multiple_variables),
        ("missing_variable", test_missing_variable),
        ("escaped_variable", test_escaped_variable),
        ("safe_variable", test_safe_variable),
        ("for_loop", test_for_loop),
        ("for_loop_empty", test_for_loop_empty),
        ("for_loop_missing_variable", test_for_loop_missing_variable),
        ("if_block_true", test_if_block_true),
        ("if_block_false", test_if_block_false),
        ("if_block_with_string", test_if_block_with_string),
        ("if_block_empty_string", test_if_block_empty_string),
        ("template_inheritance", test_template_inheritance),
        ("include", test_include),
        ("escape_html", test_escape_html),
        ("dotted_access", test_dotted_access),
        ("autoescape_default", test_autoescape_default),
        ("nested_for_loop", test_nested_for_loop),
    ]

    passed = 0
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS  {name}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"  FAIL  {name}: {e}")
            failed += 1

    print(f"\n{passed}/{passed + failed} tests passed")
    return failed == 0


if __name__ == "__main__":
    success = test_run_all()
    sys.exit(0 if success else 1)
