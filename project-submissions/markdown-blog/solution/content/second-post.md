---
title: Second Post
date: 2026-01-20
tags: general, meta
---

This is the **second post** on this blog. Here I'll talk about how the blog engine works.

## Architecture

The blog engine has four main components:

1. **Parser** (`parser.py`) — converts Markdown to HTML and extracts frontmatter
2. **Renderer** (`renderer.py`) — renders HTML templates with variables and control flow
3. **Builder** (`build.py`) — orchestrates the build pipeline
4. **Server** (`serve.py`) — development server with live reload

## Example Ordered List

1. Write content in Markdown
2. Run `python build.py`
3. Deploy `_site/` to any static host

## Inline Code

Use `parser.parse_frontmatter()` to extract metadata and `parser.markdown_to_html()` to convert content.

## More Blockquotes

> Static sites are fast, secure, and cheap to host.
> — Every static site advocate ever
