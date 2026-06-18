import sys
sys.path.insert(0, "..")

from parser import markdown_to_html, parse_frontmatter


def test_heading_h1():
    html = markdown_to_html("# Hello")
    assert "<h1>Hello</h1>" in html, f"Expected <h1>, got: {html}"


def test_heading_h2():
    html = markdown_to_html("## Subtitle")
    assert "<h2>Subtitle</h2>" in html


def test_heading_h3():
    html = markdown_to_html("### Section")
    assert "<h3>Section</h3>" in html


def test_heading_h4():
    html = markdown_to_html("#### Subsection")
    assert "<h4>Subsection</h4>" in html


def test_heading_h5():
    html = markdown_to_html("##### Deep")
    assert "<h5>Deep</h5>" in html


def test_heading_h6():
    html = markdown_to_html("###### Deepest")
    assert "<h6>Deepest</h6>" in html


def test_bold():
    html = markdown_to_html("This is **bold** text.")
    assert "<strong>bold</strong>" in html
    assert "<p>" in html


def test_italic():
    html = markdown_to_html("This is *italic* text.")
    assert "<em>italic</em>" in html


def test_bold_and_italic():
    html = markdown_to_html("***both***")
    assert "<strong><em>both</em></strong>" in html


def test_inline_code():
    html = markdown_to_html("Use `code` here.")
    assert "<code>code</code>" in html


def test_code_block():
    html = markdown_to_html("```\nprint('hello')\n```")
    assert "<pre><code>" in html
    assert "print('hello')" in html
    assert "</code></pre>" in html


def test_code_block_with_language():
    html = markdown_to_html("```python\nx = 1\n```")
    assert 'class="language-python"' in html
    assert "x = 1" in html


def test_unordered_list():
    html = markdown_to_html("- Item A\n- Item B\n- Item C")
    assert "<ul>" in html
    assert "<li>Item A</li>" in html
    assert "<li>Item B</li>" in html
    assert "<li>Item C</li>" in html
    assert "</ul>" in html


def test_ordered_list():
    html = markdown_to_html("1. First\n2. Second\n3. Third")
    assert "<ol>" in html
    assert "<li>First</li>" in html
    assert "<li>Second</li>" in html
    assert "<li>Third</li>" in html
    assert "</ol>" in html


def test_link():
    html = markdown_to_html("[Click here](https://example.com)")
    assert '<a href="https://example.com">Click here</a>' in html


def test_image():
    html = markdown_to_html("![Alt](image.png)")
    assert '<img src="image.png" alt="Alt">' in html


def test_blockquote():
    html = markdown_to_html("> A wise quote.")
    assert "<blockquote>" in html
    assert "A wise quote." in html


def test_horizontal_rule():
    html = markdown_to_html("---")
    assert "<hr>" in html


def test_paragraph():
    html = markdown_to_html("Just a paragraph.")
    assert "<p>Just a paragraph.</p>" in html


def test_html_escaping():
    html = markdown_to_html("<script>alert('xss')</script>")
    assert "&lt;script&gt;" in html
    assert "<script>" not in html


def test_code_block_html_escaping():
    html = markdown_to_html("```\n<script>alert('xss')</script>\n```")
    assert "&lt;script&gt;" in html
    assert "<script>" not in html, "HTML should be escaped in code blocks"


def test_parse_frontmatter_basic():
    text = """---
title: Test Post
date: 2026-01-15
tags: python, web
---
# Body
content here"""
    metadata, body = parse_frontmatter(text)
    assert metadata["title"] == "Test Post"
    assert metadata["date"] == "2026-01-15"
    assert metadata["tags"] == "python, web"
    assert "Body" in body


def test_parse_frontmatter_no_frontmatter():
    text = "# Just a heading\n\nSome content."
    metadata, body = parse_frontmatter(text)
    assert metadata == {}
    assert body == text


def test_parse_frontmatter_partial():
    text = "---\ntitle: Incomplete\nSome content"
    metadata, body = parse_frontmatter(text)
    assert metadata == {}
    assert body == text


def test_parse_frontmatter_empty():
    metadata, body = parse_frontmatter("")
    assert metadata == {}
    assert body == ""


def test_empty_input():
    html = markdown_to_html("")
    assert html == ""


def test_inline_formatting_in_heading():
    html = markdown_to_html("# **Bold Heading**")
    assert "<h1>" in html
    assert "<strong>Bold Heading</strong>" in html


def test_multiple_paragraphs():
    html = markdown_to_html("Para one.\n\nPara two.")
    assert html.count("<p>") == 2


def test_run_all():
    tests = [
        ("heading_h1", test_heading_h1),
        ("heading_h2", test_heading_h2),
        ("heading_h3", test_heading_h3),
        ("heading_h4", test_heading_h4),
        ("heading_h5", test_heading_h5),
        ("heading_h6", test_heading_h6),
        ("bold", test_bold),
        ("italic", test_italic),
        ("bold_and_italic", test_bold_and_italic),
        ("inline_code", test_inline_code),
        ("code_block", test_code_block),
        ("code_block_with_language", test_code_block_with_language),
        ("unordered_list", test_unordered_list),
        ("ordered_list", test_ordered_list),
        ("link", test_link),
        ("image", test_image),
        ("blockquote", test_blockquote),
        ("horizontal_rule", test_horizontal_rule),
        ("paragraph", test_paragraph),
        ("html_escaping", test_html_escaping),
        ("code_block_html_escaping", test_code_block_html_escaping),
        ("parse_frontmatter_basic", test_parse_frontmatter_basic),
        ("parse_frontmatter_no_frontmatter", test_parse_frontmatter_no_frontmatter),
        ("parse_frontmatter_partial", test_parse_frontmatter_partial),
        ("parse_frontmatter_empty", test_parse_frontmatter_empty),
        ("empty_input", test_empty_input),
        ("inline_formatting_in_heading", test_inline_formatting_in_heading),
        ("multiple_paragraphs", test_multiple_paragraphs),
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
