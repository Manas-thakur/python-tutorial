---
title: Build a Markdown Blog Engine
author: Codédex Community
uid: markdown-blog
datePublished: 2026-06-18
description: Build a static site generator that converts Markdown to HTML with custom themes, a live-reload dev server, tag pages, and RSS feed generation — all in pure Python.
published: false
readTime: 120
prerequisites: Python, HTML basics
versions: Python 3.10+
tags:
  - intermediate
  - python
  - web
---

## Introduction

Static site generators power thousands of blogs across the web — from personal sites to documentation hubs. Jekyll, Hugo, Eleventy, and Next.js all do the same fundamental thing: take Markdown input and produce HTML output. In this project, we'll build our own from scratch.

Here's what you'll learn:

- **Markdown parsing** — convert Markdown to HTML with headings, bold, italic, code blocks, lists, links, and images
- **Frontmatter** — extract metadata (title, date, tags) embedded in Markdown files
- **Template engine** — render HTML templates with variable substitution, for loops, if blocks, includes, and inheritance
- **Static site building** — walk a content directory, process each file, and write a complete site to disk
- **Dev server with live reload** — serve the site locally and auto-reload the browser on file changes
- **RSS feed generation** — produce XML feed for content syndication
- **Tag taxonomy** — automatically group posts by tags with dedicated pages

Let's build it!

## Setting Up

First, create a new directory for the project:

```bash
mkdir markdown-blog
cd markdown-blog
```

Grab the starter template from our repo at [https://github.com/Manas-thakur/python-tutorial](https://github.com/Manas-thakur/python-tutorial) (path: `project-submissions/markdown-blog/starter/`).

Your project will end up with this structure:

```
markdown-blog/
├── build.py          # Site builder — walks content/, renders, writes _site/
├── serve.py          # Dev server with live reload via SSE
├── parser.py         # Frontmatter parsing + Markdown → HTML conversion
├── renderer.py       # Custom template engine
├── themes/default/   # HTML templates and CSS
│   ├── base.html
│   ├── index.html
│   ├── post.html
│   ├── tag.html
│   └── style.css
├── content/          # Your Markdown posts
│   ├── hello-world.md
│   └── second-post.md
└── _site/            # Generated static output (git-ignored)
```

**Python version:** You'll need Python 3.10+ for the `str | None` union syntax in type hints. If you're on an older version, use `Optional[str]` instead.

There are no external dependencies. Everything uses Python's standard library.

## Step 1: Frontmatter Parsing

Frontmatter is metadata placed at the top of a Markdown file, delimited by `---` lines. It lets authors specify title, date, tags, and other metadata alongside the content — no separate database or config file required.

Create `parser.py` and start with the function that splits frontmatter from body text:

```python
def parse_frontmatter(text: str) -> tuple[dict, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text

    end = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break

    if end == -1:
        return {}, text

    frontmatter_lines = lines[1:end]
    body = "\n".join(lines[end + 1:])

    metadata = {}
    for line in frontmatter_lines:
        if ":" in line:
            key, _, value = line.partition(":")
            metadata[key.strip()] = value.strip()

    return metadata, body
```

**Dry run:**

Input:
```python
text = """---
title: Hello World
date: 2026-01-15
tags: python, web
---
# Hello

This is a post.
"""

metadata, body = parse_frontmatter(text)
```

Result:
```python
metadata == {"title": "Hello World", "date": "2026-01-15", "tags": "python, web"}
body    == "# Hello\n\nThis is a post."
```

Without frontmatter, you'd need a separate database or naming conventions (like `2026-01-15-hello-world.md`) and a second config file for tags. Frontmatter keeps everything in one document. This is the same approach used by Jekyll, Hugo, and 11ty.

## Step 2: Markdown to HTML

Now extend `parser.py` with a function that converts Markdown text into HTML. Instead of reaching for `mistune` or `markdown` from PyPI, we'll write our own — it's the best way to understand how parsers work.

Add an HTML escaping helper:

```python
def escape_html(text: str) -> str:
    html_escape_table = {
        "&": "&amp;",
        '"': "&quot;",
        "<": "&lt;",
        ">": "&gt;",
    }
    return "".join(html_escape_table.get(c, c) for c in text)
```

Now the inline parser for bold, italic, links, and code:

```python
import re

def parse_inline(text: str) -> str:
    text = escape_html(text)

    # Images: ![alt](url)
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1">', text)

    # Links: [text](url)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)

    # Inline code: `code` (must process before bold/italic)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)

    # Bold+italic: ***text***
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
    text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)

    return text
```

And the block-level parser:

```python
def markdown_to_html(md: str) -> str:
    lines = md.splitlines()
    html_lines = []
    in_code_block = False

    i = 0
    while i < len(lines):
        line = lines[i]

        # Code blocks
        if line.startswith("```"):
            if in_code_block:
                html_lines.append("</code></pre>")
                in_code_block = False
            else:
                lang = line[3:].strip()
                if lang:
                    html_lines.append(f'<pre><code class="language-{lang}">')
                else:
                    html_lines.append("<pre><code>")
                in_code_block = True
            i += 1
            continue

        if in_code_block:
            html_lines.append(escape_html(line))
            i += 1
            continue

        # Horizontal rules
        if re.match(r'^(-|\*|_){3,}$', line.strip()):
            html_lines.append("<hr>")
            i += 1
            continue

        # Headings
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if heading_match:
            level = len(heading_match.group(1))
            content = parse_inline(heading_match.group(2))
            html_lines.append(f"<h{level}>{content}</h{level}>")
            i += 1
            continue

        # Blockquotes
        if line.startswith("> "):
            quote_lines = []
            while i < len(lines) and lines[i].startswith("> "):
                quote_lines.append(parse_inline(lines[i][2:]))
                i += 1
            html_lines.append(
                f"<blockquote><p>{'<br>'.join(quote_lines)}</p></blockquote>"
            )
            continue

        # Unordered lists
        if line.startswith("- ") or line.startswith("* "):
            items = []
            while i < len(lines) and (
                lines[i].startswith("- ") or lines[i].startswith("* ")
            ):
                items.append(parse_inline(lines[i][2:]))
                i += 1
            html_lines.append("<ul>")
            for item in items:
                html_lines.append(f"<li>{item}</li>")
            html_lines.append("</ul>")
            continue

        # Ordered lists
        ol_match = re.match(r'^(\d+)\.\s+(.+)$', line)
        if ol_match:
            items = []
            while i < len(lines):
                m = re.match(r'^(\d+)\.\s+(.+)$', lines[i])
                if not m:
                    break
                items.append(parse_inline(m.group(2)))
                i += 1
            html_lines.append("<ol>")
            for item in items:
                html_lines.append(f"<li>{item}</li>")
            html_lines.append("</ol>")
            continue

        # Paragraphs (catch-all for plain text)
        if line.strip() == "":
            html_lines.append("")
            i += 1
            continue

        para_lines = []
        while i < len(lines):
            l = lines[i]
            if (
                l.strip() == ""
                or l.startswith("#")
                or l.startswith("```")
                or l.startswith("> ")
                or l.startswith("- ")
                or l.startswith("* ")
                or re.match(r'^(\d+)\.\s+', l)
                or re.match(r'^(-|\*|_){3,}$', l.strip())
            ):
                break
            para_lines.append(parse_inline(l))
            i += 1
        if para_lines:
            html_lines.append(f"<p>{' '.join(para_lines)}</p>")
            continue

        i += 1

    return "\n".join(html_lines)
```

**Dry run:**

```python
md = """# Hello World

This is **bold** text.

- Item one
- Item two
"""

html = markdown_to_html(md)
```

Produces:

```html
<h1>Hello World</h1>

<p>This is <strong>bold</strong> text.</p>

<ul>
<li>Item one</li>
<li>Item two</li>
</ul>
```

**Why build a custom parser?** Using `pip install mistune` is easier, but building your own teaches you:
- **State machines** — tracking whether you're inside a code block, a list, or a paragraph
- **String processing** — splitting, searching, replacing in a single pass
- **Edge cases** — what happens when unclosed code fences or nested emphasis appear?

Start simple and add features as you need them.

## Step 3: Template Engine

Create `renderer.py`. This is the heart of the blog engine — it takes HTML templates with special tags and replaces them with actual content.

### Variable substitution

The simplest operation — replacing `{{ variable }}` placeholders:

```python
def render_template(template: str, context: dict, template_dir: str = ".") -> str:
    result = template
    for key, value in context.items():
        result = result.replace("{{ " + key + " }}", str(value))
        result = result.replace("{{" + key + "}}", str(value))
    return result
```

### Dot notation access

Templates often access nested data like `{{ post.title }}`. We need a resolver:

```python
def resolve_value(context: dict, name: str):
    parts = name.split(".")
    value = context
    for part in parts:
        if isinstance(value, dict):
            value = value.get(part)
        elif hasattr(value, part):
            value = getattr(value, part)
        else:
            return None
    return value
```

### For loops and if blocks

A real template engine needs control flow. The key challenge is handling nested blocks. A simple regex won't work because `{% for %}...{% endfor %}` pairs can nest. We'll use a balanced-pair finder:

```python
import re

def _find_balanced_block(template: str, block_type: str):
    """Find first top-level {% block_type ... %}...{% endblock_type %} pair.
    Returns (header, body, end_pos) or None."""
    open_re = re.compile(r'\{%\s*' + block_type + r'\s+(.+?)\s*%\}')
    close_re = re.compile(r'\{%\s*end' + block_type + r'\s*%\}')

    m = open_re.search(template)
    if not m:
        return None

    depth = 1
    pos = m.end()

    while pos < len(template) and depth > 0:
        next_open = open_re.search(template, pos)
        next_close = close_re.search(template, pos)

        if next_close is None:
            return None

        if next_open is not None and next_open.start() < next_close.start():
            depth += 1
            pos = next_open.end()
        else:
            depth -= 1
            if depth == 0:
                return {
                    "header": m.group(1).strip(),
                    "body": template[m.end():next_close.start()],
                    "end": next_close.end(),
                    "start": m.start(),
                }
            pos = next_close.end()

    return None
```

This counter-based approach correctly handles `{% for row in matrix %}{% for cell in row %}{{ cell }}{% endfor %}{|{% endfor %}` — each `endfor` matches its corresponding `for`.

### Template inheritance

Base templates define a layout with `{% block content %}` placeholders that child templates fill in:

```html
<!-- themes/default/base.html -->
<!DOCTYPE html>
<html>
<head>
  <title>{% block title %}{{ site_name }}{% endblock %}</title>
</head>
<body>
  <main>{% block content %}{% endblock %}</main>
</body>
</html>
```

```html
<!-- themes/default/post.html -->
{% extends "base.html" %}
{% block content %}
<article>
  <h1>{{ title }}</h1>
  <div class="content">{{ body|safe }}</div>
</article>
{% endblock %}
```

The `{% extends %}` tag tells the engine to load the parent template, then replace its blocks with the child's content.

### Includes

The `{% include "header.html" %}` tag loads and renders another template in place. This is useful for reusable components like navigation bars or sidebars.

### Auto-escaping

By default, template variables are HTML-escaped. If a variable contains `&lt;script&gt;`, it renders as `&amp;lt;script&amp;gt;`. The `|safe` filter bypasses escaping for trusted HTML (like the rendered Markdown body).

## Step 4: Site Builder

Create `build.py`. This is the orchestration layer that walks the `content/` directory, parses each file, renders through templates, and writes the output to `_site/`.

```python
import os
import shutil
from pathlib import Path
from parser import parse_frontmatter, markdown_to_html
from renderer import render_template


def build_site(content_dir="content", theme_dir="themes/default", output_dir="_site"):
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    posts = []

    for filepath in Path(content_dir).glob("*.md"):
        raw = filepath.read_text(encoding="utf-8")
        metadata, body = parse_frontmatter(raw)
        metadata["body"] = markdown_to_html(body)
        metadata["slug"] = filepath.stem

        # Skip drafts
        if metadata.get("draft", "").lower() == "true":
            continue

        # Create output path: _site/slug/index.html
        post_dir = Path(output_dir) / metadata["slug"]
        post_dir.mkdir(parents=True, exist_ok=True)

        template_path = Path(theme_dir) / "post.html"
        template = template_path.read_text(encoding="utf-8")
        html = render_template(template, metadata, template_dir=theme_dir)
        (post_dir / "index.html").write_text(html, encoding="utf-8")

        posts.append(metadata)

    # Sort posts by date (newest first)
    posts.sort(key=lambda p: p.get("date", ""), reverse=True)

    # Build index page
    index_template = (Path(theme_dir) / "index.html").read_text(encoding="utf-8")
    index_html = render_template(
        index_template, {"posts": posts, "site_name": "My Blog"},
        template_dir=theme_dir,
    )
    (Path(output_dir) / "index.html").write_text(index_html, encoding="utf-8")

    # Copy static assets
    css_src = Path(theme_dir) / "style.css"
    if css_src.exists():
        shutil.copy(css_src, Path(output_dir) / "style.css")

    print(f"Built {len(posts)} posts to {output_dir}/")
```

### What happens during a build

1. Delete `_site/` (clean build)
2. For each `.md` file in `content/`:
   a. Read the file
   b. Parse frontmatter into a metadata dict
   c. Convert the Markdown body to HTML
   d. Skip if `draft: true`
   e. Create `_site/slug/index.html`
   f. Render the post template with metadata as context
3. Generate `_site/index.html` listing all posts
4. Copy `style.css` to `_site/`

Try it:

```bash
echo '---
title: Hello World
date: 2026-01-15
---
# Hello!' > content/hello-world.md

python build.py
# Output: Built 1 posts to _site/
```

## Step 5: Tag Pages

Tags give readers a way to discover related content. Let's extend `build.py` to group posts by tag and generate tag pages.

After collecting all posts, build a tag index:

```python
# Group posts by tag
tag_groups = {}
for post in posts:
    tags_raw = post.get("tags", "")
    tag_list = [t.strip() for t in tags_raw.split(",") if t.strip()]
    for tag in tag_list:
        tag_groups.setdefault(tag, []).append(post)

# Create tags directory
tags_dir = Path(output_dir) / "tags"
tags_dir.mkdir(parents=True, exist_ok=True)

# Generate a page for each tag
tag_template = (Path(theme_dir) / "tag.html").read_text(encoding="utf-8")
for tag, tagged_posts in sorted(tag_groups.items()):
    tag_html = render_template(
        tag_template,
        {"tag": tag, "posts": tagged_posts, "site_name": "My Blog"},
        template_dir=theme_dir,
    )
    (tags_dir / f"{tag}.html").write_text(tag_html, encoding="utf-8")

# Generate tags index page
# (list all tags with post counts)
```

The tag template extends `base.html` just like other pages, showing a filtered list of posts for each tag. The tags index page shows all tags with their post counts.

## Step 6: RSS Feed

RSS (Really Simple Syndication) lets readers subscribe to your blog using feed readers like Feedly, Inoreader, or NetNewsWire.

Add RSS generation to `build.py`:

```python
from datetime import datetime
from xml.sax.saxutils import escape


def parse_date(date_str: str) -> str:
    """Converts '2026-01-15' → 'Thu, 15 Jan 2026 00:00:00 GMT'"""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%a, %d %b %Y %H:%M:%S GMT")


def generate_rss(posts, site_url, site_title):
    items = []
    for post in posts:
        link = f"{site_url}/{post['slug']}/"
        item = f"""  <item>
    <title>{escape(post['title'])}</title>
    <link>{escape(link)}</link>
    <description>{escape(post['body'])}</description>
    <pubDate>{parse_date(post['date'])}</pubDate>
    <guid>{escape(link)}</guid>
  </item>"""
        items.append(item)

    rss = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{escape(site_title)}</title>
    <link>{escape(site_url)}</link>
    <description>A blog powered by our Markdown engine</description>
    <language>en-us</language>
    {"\\n".join(items)}
  </channel>
</rss>'''
    return rss
```

Then call it at the end of `build_site()`:

```python
rss_xml = generate_rss(posts, site_url, site_name)
(Path(output_dir) / "feed.xml").write_text(rss_xml, encoding="utf-8")
```

Generated `_site/feed.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>My Blog</title>
    <link>http://localhost:8000</link>
    <description>A blog powered by our Markdown engine</description>
    <language>en-us</language>
    <item>
      <title>Second Post</title>
      <link>http://localhost:8000/second-post/</link>
      <description>&lt;h2&gt;Architecture&lt;/h2&gt;...</description>
      <pubDate>Tue, 20 Jan 2026 00:00:00 GMT</pubDate>
      <guid>http://localhost:8000/second-post/</guid>
    </item>
    <item>
      <title>Hello World</title>
      <link>http://localhost:8000/hello-world/</link>
      ...
    </item>
  </channel>
</rss>
```

## Step 7: Dev Server with Live Reload

Create `serve.py`. This serves the `_site/` directory over HTTP and automatically reloads the browser when files change using Server-Sent Events (SSE).

### HTTP server

```python
import os
import sys
import time
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from build import build_site

reload_event = threading.Event()


class LiveReloadHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="_site", **kwargs)

    def do_GET(self):
        if self.path == "/_reload":
            # SSE endpoint: keeps connection open, pushes events
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            while True:
                if reload_event.wait(timeout=1):
                    try:
                        self.wfile.write(b"data: reload\n\n")
                        self.wfile.flush()
                    except BrokenPipeError:
                        break
                    reload_event.clear()
                else:
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
            return

        # Inject SSE script into HTML responses
        if self.path.endswith(".html") or self.path == "/" or self.path.endswith("/"):
            path = self.translate_path(self.path)
            if os.path.isdir(path):
                path = os.path.join(path, "index.html")
            if os.path.isfile(path):
                with open(path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()

                sse_script = (
                    b"<script>\n"
                    b"(function() {\n"
                    b'  var es = new EventSource("/_reload");\n'
                    b"  es.onmessage = function() { location.reload(); };\n"
                    b"})();\n"
                    b"</script>\n</body>"
                )
                content = content.replace(b"</body>", sse_script)
                self.wfile.write(content)
                return

        super().do_GET()
```

### File watcher

A background thread polls the content and theme directories for changes:

```python
def watch_files(content_dir="content", theme_dir="themes/default"):
    last_mtimes = {}
    while True:
        for directory in [content_dir, theme_dir]:
            if not os.path.exists(directory):
                continue
            for root, _, files in os.walk(directory):
                for fname in files:
                    fpath = os.path.join(root, fname)
                    try:
                        mtime = os.path.getmtime(fpath)
                    except OSError:
                        continue
                    if fpath in last_mtimes and last_mtimes[fpath] != mtime:
                        build_site(content_dir=content_dir, theme_dir=theme_dir)
                        reload_event.set()
                        break
                    last_mtimes[fpath] = mtime
        time.sleep(1)
```

### Putting it together

```python
def serve(port=8000, content_dir="content", theme_dir="themes/default"):
    if not os.path.exists("_site"):
        build_site(content_dir=content_dir, theme_dir=theme_dir)

    watcher = threading.Thread(
        target=watch_files, args=(content_dir, theme_dir), daemon=True,
    )
    watcher.start()

    server = HTTPServer(("0.0.0.0", port), LiveReloadHandler)
    print(f"Serving at http://localhost:{port}")
    print("Press Ctrl+C to stop.")
    server.serve_forever()
```

**Dry run:**

1. Start the server: `python serve.py`
2. Open a browser to `http://localhost:8000`
3. Edit a Markdown file in `content/` and save
4. The browser automatically reloads — you see changes instantly

**Why SSE over WebSocket?**

| Feature | SSE | WebSocket |
|---------|-----|-----------|
| Direction | Server → client only | Bidirectional |
| Protocol | HTTP | WS |
| Reconnection | Automatic | Manual |
| Complexity | Minimal | Higher |

For a dev server that only needs to push "reload" events to the browser, SSE is the simple, correct choice.

## Step 8: Running and Extending

You're done! Fire it up:

```bash
# 1. Write some content
echo '---
title: Hello World
date: 2026-01-15
---
# Hello!' > content/hello-world.md

# 2. Build the site
python build.py
# Output: Built 1 posts to _site/

# 3. Start the dev server
python serve.py
# Output: Serving at http://localhost:8000
```

Open `http://localhost:8000` in your browser — you'll see your blog.

### Extension Ideas

**Syntax highlighting in code blocks.** Replace `<pre><code>` with highlighted versions using Pygments:

```python
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

def highlight_code(code: str, language: str) -> str:
    lexer = get_lexer_by_name(language)
    formatter = HtmlFormatter()
    return highlight(code, lexer, formatter)
```

**Full-text search.** Generate a JSON search index during build and use client-side JavaScript to search through posts:

```python
import json
search_index = [
    {"title": p["title"], "slug": p["slug"], "date": p["date"], "tags": p.get("tags", "")}
    for p in posts
]
(Path(output_dir) / "search.json").write_text(json.dumps(search_index))
```

**Deploy to GitHub Pages.** Add a GitHub Actions workflow that runs `python build.py` on every push and deploys `_site/`:

```yaml
# .github/workflows/deploy.yml
name: Deploy to GitHub Pages
on:
  push:
    branches: [main]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: python build.py
      - uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./_site
```

**Pagination.** On the index page, split posts into pages of 5 or 10 and generate `page/2/index.html` etc.

**Post excerpts.** Use the first paragraph of each post as an excerpt on the index page instead of the full body.

**Custom 404 page.** Generate a `404.html` that your static host will serve for missing URLs.

**CLI flags.** Already implemented in the solution: `--output`, `--theme-dir`, `--content-dir`, `--site-url`, `--site-name`.

### What You've Learned

| Concept | Where it applied |
|---------|-----------------|
| File I/O | Reading content/, writing _site/ |
| String processing | Frontmatter parsing, Markdown → HTML |
| Recursive algorithms | Template inheritance resolution |
| Balanced delimiters | Nested for/if block matching |
| HTTP protocol | Dev server request handling |
| Event-driven programming | SSE live reload |
| XML generation | RSS feed creation |
| Threading | File watcher background thread |
| CI/CD | GitHub Pages deployment |

## Conclusion

You built a fully functional static site generator from scratch — one that converts Markdown to HTML, renders through a custom template engine with inheritance and control flow, generates tag pages and RSS feeds, and includes a live-reload dev server.

Here's what you accomplished:

- Parsed frontmatter metadata from Markdown files
- Built a custom Markdown-to-HTML converter supporting headings, bold, italic, code blocks, lists, links, images, and blockquotes
- Implemented a template engine with variable substitution, for loops, if blocks, template inheritance, includes, and auto-escaping
- Created a site builder that walks content files, renders them through themes, and writes a complete static site
- Generated tag pages that group posts by topic
- Produced an RSS feed for content syndication
- Built a dev server with live browser reload via Server-Sent Events
- Added draft post filtering and CLI configuration

### Next Steps

- Add nested tag support and tag hierarchies
- Implement build caching (only rebuild changed files)
- Add draft post preview support in the dev server
- Write additional themes and make themes configurable per post
- Add support for custom page types (about, contact, projects)
- Package your blog engine with `pyproject.toml` so it's installable

The full source code for this tutorial is available at [https://github.com/Manas-thakur/python-tutorial](https://github.com/Manas-thakur/python-tutorial) (path: `project-submissions/markdown-blog/solution/`).
