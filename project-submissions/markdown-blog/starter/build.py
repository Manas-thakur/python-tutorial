# Site Builder
#
# TODO: Walk content/ directory for .md files
# TODO: Parse frontmatter (title, date, tags)
# TODO: Convert Markdown body to HTML
# TODO: Render through theme templates
# TODO: Write output to _site/ directory with pretty URLs (slug/index.html)
# TODO: Generate index page listing all posts
# TODO: Generate tag pages
# TODO: Generate RSS feed (feed.xml)
# TODO: Copy static assets (CSS, images)
# TODO: Skip draft posts (draft: true in frontmatter)

import os
from pathlib import Path

CONTENT_DIR = Path("content")
OUTPUT_DIR = Path("_site")
THEME_DIR = Path("themes/default")


def build_site(
    content_dir="content",
    theme_dir="themes/default",
    output_dir="_site",
    site_url="http://localhost:8000",
    site_name="My Blog",
):
    pass


if __name__ == "__main__":
    build_site()
