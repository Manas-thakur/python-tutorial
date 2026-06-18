from python_tutorial.models import ProjectTutorial, Section

TUTORIAL = ProjectTutorial(
    slug="markdown-blog",
    title="Build a Markdown Blog Engine",
    description="A static site generator that converts Markdown to HTML with themes, a dev server, and RSS support.",
    difficulty="intermediate",
    project_dir="markdown-blog",
    prerequisites=["Functions", "File I/O", "Strings", "Classes"],
    steps=[
        Section(
            heading="Step 1: Project Architecture",
            content='''\
## File overview

Here\'s the file layout for our Markdown blog engine:

```text
markdown-blog/
├── build.py          # Site builder — walks content/, parses, renders, writes _site/
├── serve.py          # Dev server with live reload via SSE
├── parser.py         # Frontmatter parsing + Markdown → HTML conversion
├── renderer.py       # Custom template engine (variables, loops, if-blocks, includes)
├── themes/           # HTML templates and CSS
│   ├── default/
│   │   ├── base.html
│   │   ├── post.html
│   │   ├── index.html
│   │   └── style.css
├── content/          # Your Markdown posts
│   ├── hello-world.md
│   └── second-post.md
└── _site/            # Generated static output (git-ignored)
```

## Build pipeline

The entire pipeline follows a clean data flow:

```
.md file → parse frontmatter + markdown → render with template → write to _site/
```

1. Read each `.md` file from `content/`
2. Extract metadata (title, date, tags) from frontmatter
3. Convert Markdown body to HTML
4. Render HTML through a template with the metadata as context
5. Write the result to `_site/` with the correct path

## Why this architecture

Separating parsing, rendering, and building into distinct modules means each piece is testable and swappable. Want to switch from a custom Markdown parser to `mistune`? You only touch `parser.py`. Want to add a new theme? Drop a folder in `themes/` and it just works.

## Dry run — what you\'ll build

A developer writes a post in `content/my-article.md`:

```markdown
---
title: My First Post
date: 2026-01-15
tags: python, web
---
# Hello World

This is **awesome**.
```

Running `python build.py` produces `_site/my-article/index.html` — a complete, styled blog page. No database, no server-side runtime, just static HTML you can host anywhere.
''',
        ),
        Section(
            heading="Step 2: Frontmatter Parsing (parser.py)",
            content='''\
## What is frontmatter?

Frontmatter is metadata placed at the top of a Markdown file, delimited by `---` lines. It lets authors specify title, date, tags, and other metadata alongside the content — no separate database or config file required.

```markdown
---
title: Hello World
date: 2026-01-15
tags: python, web
draft: false
---
# Actual markdown content starts here...
```

## Parsing frontmatter

We\'ll write a function that splits frontmatter from body text and parses the key-value pairs. The format is deliberately simple (YAML-like) so you can build it with just Python\'s `str` methods — no PyYAML dependency needed.

```python
def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
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
    body = "\\n".join(lines[end + 1:])

    metadata = {}
    for line in frontmatter_lines:
        if ":" in line:
            key, _, value = line.partition(":")
            metadata[key.strip()] = value.strip()

    return metadata, body
```

## Dry run

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
body    == "# Hello\\n\\nThis is a post."
```

## Why frontmatter?

Without frontmatter, you\'d need a separate database or a naming convention (like `2026-01-15-hello-world.md`) and a second config file for tags. Frontmatter keeps everything in one file — authors edit one document, and the metadata travels with the content. This is the same approach used by Jekyll, Hugo, and 11ty.
''',
        ),
        Section(
            heading="Step 3: Markdown to HTML (parser.py)",
            content='''\
## Building a custom Markdown parser

We\'ll extend `parser.py` with a function that converts Markdown text into HTML. Instead of reaching for a library like `mistune` or `markdown`, we\'ll write our own — it\'s a fantastic way to learn how parsers work.

```python
def markdown_to_html(md: str) -> str:
    lines = md.splitlines()
    html_lines = []
    in_code_block = False

    for line in lines:
        # Code blocks
        if line.startswith("```"):
            if in_code_block:
                html_lines.append("</code></pre>")
                in_code_block = False
            else:
                html_lines.append("<pre><code>")
                in_code_block = True
            continue

        if in_code_block:
            html_lines.append(escape_html(line))
            continue

        # Headings
        if line.startswith("### "):
            html_lines.append(f"<h3>{line[4:]}</h3>")
        elif line.startswith("## "):
            html_lines.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("# "):
            html_lines.append(f"<h1>{line[2:]}</h1>")

        # Bold and italic
        elif "**" in line:
            # Simple inline parsing (full version handles nesting)
            processed = line.replace("**", "<strong>", 1)
            processed = processed.replace("**", "</strong>", 1)
            html_lines.append(f"<p>{processed}</p>")

        elif line.startswith("- "):
            html_lines.append(f"<li>{line[2:]}</li>")

        elif line.strip() == "":
            html_lines.append("")

        else:
            html_lines.append(f"<p>{line}</p>")

    return "\\n".join(html_lines)
```

## Dry run

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

<li>Item one</li>
<li>Item two</li>
```

## Why build a custom parser?

Using `pip install mistune` is easier, but you learn nothing about how parsers work. Writing your own teaches you:
- **State machines** — tracking whether you\'re inside a code block, a list, or a paragraph
- **String processing** — splitting, searching, replacing in a single pass
- **Error handling** — what happens when a Markdown file has an unclosed code fence?

The full version of our parser handles inline formatting (`` `code` ``, `[links](url)`, `*italic*`), ordered lists, blockquotes, and nested emphasis. Start simple and add features as you need them.
''',
        ),
        Section(
            heading="Step 4: Template Engine (renderer.py)",
            content='''\
## Variable substitution

The simplest template operation — replacing `{{ variable }}` placeholders with actual values.

```python
import re

def render_template(template: str, context: dict) -> str:
    result = template

    # Variable substitution: {{ var_name }}
    for key, value in context.items():
        result = result.replace("{{ " + key + " }}", str(value))
        result = result.replace("{{" + key + "}}", str(value))

    return result
```

## Adding control flow

A real template engine needs more than variable interpolation. We\'ll add `{% for %}` loops and `{% if %}` blocks.

```python
def render_for_block(match, context):
    # match.group(1) = "post in posts"
    loop_var, _, iterable_name = match.group(1).partition(" in ")
    items = context.get(iterable_name.strip(), [])
    block_content = match.group(2)
    parts = []
    for item in items:
        local_context = {**context, loop_var.strip(): item}
        parts.append(render_template(block_content, local_context))
    return "".join(parts)

def render_template(template: str, context: dict) -> str:
    # Process {% for %}...{% endfor %} blocks first
    for_pattern = r"\\{% for (.+?) %\\}(.*?)\\{\\% endfor %\\}"
    template = re.sub(for_pattern, lambda m: render_for_block(m, context), template, flags=re.DOTALL)

    # Then variable substitution
    for key, value in context.items():
        template = template.replace("{{ " + key + " }}", str(value))
        template = template.replace("{{" + key + "}}", str(value))

    return template
```

## Template inheritance

Base templates define a layout with `{% block content %}` placeholders that child templates fill in:

```html
<!-- themes/default/base.html -->
<!DOCTYPE html>
<html>
<head>
  <title>{{ title }}</title>
  <link rel="stylesheet" href="/style.css">
</head>
<body>
  <header><h1>{{ site_name }}</h1></header>
  <main>{% block content %}{% endblock %}</main>
  <footer>&copy; 2026</footer>
</body>
</html>
```

## Dry run

Template file `post.html`:

```html
{% extends "base.html" %}
{% block content %}
<article>
  <h1>{{ title }}</h1>
  <div class="date">{{ date }}</div>
  <div>{{ body }}</div>
</article>
{% endblock %}
```

Rendered with `context = {"title": "Hello", "date": "2026-01-15", "body": "<p>Hi</p>"}` produces a full HTML page with the blog post embedded in the base layout.

## Why a custom template engine?

It demystifies tools like Jinja2 and Django Templates. You\'ll understand:
- **Sandboxing** — why template engines restrict arbitrary Python execution
- **Inheritance** — how `{% extends %}` and `{% block %}` compose layouts
- **Caching** — why production engines compile templates to bytecode

Your engine can stay simple — no need to match Jinja2 feature-for-feature. The goal is understanding, not production readiness.
''',
        ),
        Section(
            heading="Step 5: Site Builder (build.py)",
            content='''\
## The build function

`build.py` orchestrates the entire pipeline: walk the `content/` directory, parse each file, render through templates, and write the output to `_site/`.

```python
import os
import shutil
from pathlib import Path
from parser import parse_frontmatter, markdown_to_html
from renderer import render_template

def build_site(content_dir="content", theme_dir="themes/default", output_dir="_site"):
    # Clean output directory
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    posts = []

    for filepath in Path(content_dir).glob("*.md"):
        raw = filepath.read_text(encoding="utf-8")
        metadata, body = parse_frontmatter(raw)
        metadata["body"] = markdown_to_html(body)

        # Create output path: _site/slug/index.html
        slug = filepath.stem
        post_dir = Path(output_dir) / slug
        post_dir.mkdir(parents=True, exist_ok=True)

        template = (Path(theme_dir) / "post.html").read_text(encoding="utf-8")
        html = render_template(template, metadata)
        (post_dir / "index.html").write_text(html, encoding="utf-8")

        posts.append(metadata)

    # Build index page with list of all posts
    index_template = (Path(theme_dir) / "index.html").read_text(encoding="utf-8")
    index_html = render_template(index_template, {"posts": posts, "site_name": "My Blog"})
    (Path(output_dir) / "index.html").write_text(index_html, encoding="utf-8")

    # Copy static assets
    css_src = Path(theme_dir) / "style.css"
    if css_src.exists():
        shutil.copy(css_src, Path(output_dir) / "style.css")

    print(f"Built {len(posts)} posts to {output_dir}/")

if __name__ == "__main__":
    build_site()
```

## Dry run

With two posts in `content/`:

```text
content/
├── hello-world.md   (title: Hello World, date: 2026-01-15)
└── second-post.md   (title: Second Post, date: 2026-01-20)
```

Running `python build.py` generates:

```text
_site/
├── index.html        # Lists both posts with titles and dates
├── style.css         # Copied from theme
├── hello-world/
│   └── index.html    # Full blog post page
└── second-post/
    └── index.html    # Full blog post page
```

## Tag pages

Extend the builder to collect tags and generate tag archive pages:

```python
tag_pages = {}
for post in posts:
    tags = [t.strip() for t in post.get("tags", "").split(",") if t.strip()]
    for tag in tags:
        tag_pages.setdefault(tag, []).append(post)

os.makedirs(f"{output_dir}/tags", exist_ok=True)
for tag, tagged_posts in tag_pages.items():
    html = render_template(tag_template, {"tag": tag, "posts": tagged_posts})
    Path(f"{output_dir}/tags/{tag}.html").write_text(html)
```

## Why static sites?

Static sites are:
- **Fast** — no database queries, no server-side rendering per request
- **Secure** — no login pages, no SQL injection, no runtime vulnerabilities
- **Cheap** — host on GitHub Pages, Netlify, or S3 for free
- **Version-controllable** — your entire site is a git repo

This is the same architecture powering Jekyll (GitHub Pages), Hugo, and Eleventy.
''',
        ),
        Section(
            heading="Step 6: Dev Server (serve.py)",
            content='''\
## HTTP server basics

The dev server serves the `_site/` directory over HTTP and automatically reloads the browser when files change.

```python
import os
import time
import socket
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler

class LiveReloadHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="_site", **kwargs)

    def end_headers(self):
        # Inject SSE script into HTML pages for live reload
        if self.path.endswith(".html") or self.path == "/":
            sse_script = """
<script>
  const evtSource = new EventSource("/_reload");
  evtSource.onmessage = () => location.reload();
</script>
</body>"""
            # Simplified — full version modifies the response body
        super().end_headers()
```

## Server-Sent Events (SSE) for live reload

When a file changes, the server sends a reload event to all connected browsers:

```python
reload_event = threading.Event()

class SSEHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/_reload":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            while True:
                if reload_event.wait(timeout=1):
                    self.wfile.write(b"data: reload\\n\\n")
                    self.wfile.flush()
                    reload_event.clear()
                # Send keepalive comment every 30s
                self.wfile.write(b": keepalive\\n\\n")
                self.wfile.flush()
        else:
            super().do_GET()

def watch_files(directory="content"):
    last_mtimes = {}
    while True:
        for root, _, files in os.walk(directory):
            for fname in files:
                fpath = os.path.join(root, fname)
                mtime = os.path.getmtime(fpath)
                if fpath in last_mtimes and last_mtimes[fpath] != mtime:
                    reload_event.set()
                last_mtimes[fpath] = mtime
        time.sleep(1)
```

## Dry run

1. Start the server: `python serve.py`
2. Open a browser to `http://localhost:8000`
3. Edit a Markdown file in `content/` and save
4. The browser automatically reloads — you see your changes instantly

The browser connects to `/_reload`, and the server keeps the connection open. When a file changes, the server sends `data: reload`, and the browser\'s JavaScript calls `location.reload()`.

## Why SSE over WebSocket?

| Feature | SSE | WebSocket |
|---------|-----|-----------|
| Direction | Server → client only | Bidirectional |
| Protocol | HTTP | WS |
| Browser support | Everywhere | Everywhere |
| Reconnection | Automatic | Manual |
| Complexity | Minimal | Higher |

For a dev server that only needs to push "reload" events to the browser, SSE is the simple, correct choice. It\'s just HTTP with a special content type — no handshake, no framing protocol.
''',
        ),
        Section(
            heading="Step 7: RSS Feed Generation",
            content='''\
## RSS XML structure

RSS (Really Simple Syndication) lets readers subscribe to your blog using feed readers, email newsletters, or podcast apps.

```python
from datetime import datetime
from xml.sax.saxutils import escape

def generate_rss(posts: list[dict], site_url="http://localhost:8000", site_title="My Blog") -> str:
    items = []
    for post in posts:
        item = f"""  <item>
    <title>{escape(post["title"])}</title>
    <link>{site_url}/{post.get("slug", "")}/</link>
    <description>{escape(post.get("body", ""))}</description>
    <pubDate>{parse_date(post.get("date", ""))}</pubDate>
    <guid>{site_url}/{post.get("slug", "")}/</guid>
  </item>"""
        items.append(item)

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{escape(site_title)}</title>
    <link>{site_url}</link>
    <description>A blog powered by our Markdown engine</description>
    <language>en-us</language>
    {"\\n".join(items)}
  </channel>
</rss>"""
    return rss

def parse_date(date_str: str) -> str:
    # Converts "2026-01-15" → "Thu, 15 Jan 2026 00:00:00 GMT"
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
```

## Integrating with the build step

Add RSS generation to `build.py`:

```python
def build_site():
    # ... parse and render all posts ...

    # Generate RSS feed
    rss_xml = generate_rss(posts)
    (Path(output_dir) / "feed.xml").write_text(rss_xml, encoding="utf-8")
```

## Dry run

With two posts, the generated `_site/feed.xml` looks like:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>My Blog</title>
    <link>http://localhost:8000</link>
    <description>A blog powered by our Markdown engine</description>
    <language>en-us</language>
    <item>
      <title>Hello World</title>
      <link>http://localhost:8000/hello-world/</link>
      <description>&lt;h1&gt;Hello World&lt;/h1&gt;</description>
      <pubDate>Thu, 15 Jan 2026 00:00:00 GMT</pubDate>
      <guid>http://localhost:8000/hello-world/</guid>
    </item>
    <item>
      <title>Second Post</title>
      <link>http://localhost:8000/second-post/</link>
      <description>&lt;h1&gt;Second Post&lt;/h1&gt;</description>
      <pubDate>Mon, 20 Jan 2026 00:00:00 GMT</pubDate>
      <guid>http://localhost:8000/second-post/</guid>
    </item>
  </channel>
</rss>
```

## Why RSS?

RSS is the unsung hero of the open web:
- **Content syndication** — readers subscribe in Feedly, Inoreader, or NetNewsWire
- **Email newsletters** — services like ConvertKit and Mailchimp ingest RSS to send daily digests
- **Podcasting** — the entire podcast ecosystem runs on RSS enclosures
- **Decentralization** — RSS puts users in control of their reading, outside algorithm-driven feeds

Adding RSS to your static site is a one-time effort that unlocks every RSS consumer in existence.
''',
        ),
        Section(
            heading="Step 8: Running and Extensions",
            content='''\
## Running your blog

```bash
# 1. Write some content
echo \'---
title: Hello World
date: 2026-01-15
---
# Hello!\' > content/hello-world.md

# 2. Build the site
python build.py
# Output: Built 1 posts to _site/

# 3. Start the dev server
python serve.py
# Output: Serving at http://localhost:8000
```

Open `http://localhost:8000` in your browser — you\'ll see your blog.

## Extension ideas

### Syntax highlighting in code blocks

Replace `<pre><code>` with highlighted versions using a library like `Pygments`:

```python
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

def highlight_code(code: str, language: str) -> str:
    lexer = get_lexer_by_name(language)
    formatter = HtmlFormatter()
    return highlight(code, lexer, formatter)
```

### Tag pages with counts

Extend the builder to generate a `/tags/` index page showing each tag with the number of posts, linked to individual tag pages.

### Deploy to GitHub Pages

Add a GitHub Actions workflow that runs `python build.py` on every push and deploys `_site/` to GitHub Pages:

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

### Full-text search

Generate a JSON search index during build and use a lightweight client-side search library (or write your own trie-based search in vanilla JS).

## What you\'ve learned

By building this project you\'ve experienced:

| Concept | Where it applied |
|---------|-----------------|
| File I/O | Reading content/, writing _site/ |
| String processing | Frontmatter parsing, Markdown → HTML |
| Recursive algorithms | Template inheritance resolution |
| HTTP protocol | Dev server request handling |
| Event-driven programming | SSE live reload |
| XML generation | RSS feed creation |
| CI/CD | GitHub Pages deployment |

## Next steps

- Add support for nested tags and categories
- Implement pagination for the index page
- Add an `--output` CLI flag to `build.py` using `argparse`
- Create a `--watch` mode that re-builds automatically on file changes
- Write tests for `parser.py` and `renderer.py` with `pytest`
- Package your blog engine with `pyproject.toml` so it\'s installable

The full source code for this tutorial is available in the `markdown-blog/` project directory.
''',
        ),
    ],
)
