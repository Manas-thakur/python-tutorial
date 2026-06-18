import os
import shutil
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

from parser import parse_frontmatter, markdown_to_html
from renderer import render_template


def parse_date(date_str: str) -> str:
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
    except ValueError:
        return date_str


def generate_rss(posts, site_url="http://localhost:8000", site_title="My Blog"):
    items = []
    for post in posts:
        link = f"{site_url}/{post.get('slug', '')}/"
        item = f"""  <item>
    <title>{escape(post.get('title', ''))}</title>
    <link>{escape(link)}</link>
    <description>{escape(post.get('body', ''))}</description>
    <pubDate>{parse_date(post.get('date', ''))}</pubDate>
    <guid>{escape(link)}</guid>
  </item>"""
        items.append(item)

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{escape(site_title)}</title>
    <link>{escape(site_url)}</link>
    <description>A blog powered by the Markdown Blog Engine</description>
    <language>en-us</language>
{chr(10).join(items)}
  </channel>
</rss>"""
    return rss


def build_site(
    content_dir="content",
    theme_dir="themes/default",
    output_dir="_site",
    site_url="http://localhost:8000",
    site_name="My Blog",
):
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    posts = []

    theme_path = Path(theme_dir)
    content_path = Path(content_dir)
    output_path = Path(output_dir)

    for filepath in sorted(content_path.glob("*.md")):
        raw = filepath.read_text(encoding="utf-8")
        metadata, body = parse_frontmatter(raw)
        metadata["body"] = markdown_to_html(body)
        metadata["slug"] = filepath.stem

        if metadata.get("draft", "").lower() == "true":
            continue

        slug = filepath.stem
        post_dir = output_path / slug
        post_dir.mkdir(parents=True, exist_ok=True)

        post_template_path = theme_path / "post.html"
        if post_template_path.exists():
            post_template = post_template_path.read_text(encoding="utf-8")
            html = render_template(
                post_template,
                metadata,
                template_dir=str(theme_path),
            )
            (post_dir / "index.html").write_text(html, encoding="utf-8")

        posts.append(metadata)

    posts.sort(key=lambda p: p.get("date", ""), reverse=True)

    index_template_path = theme_path / "index.html"
    if index_template_path.exists():
        index_template = index_template_path.read_text(encoding="utf-8")
        index_html = render_template(
            index_template,
            {"posts": posts, "site_name": site_name},
            template_dir=str(theme_path),
        )
        (output_path / "index.html").write_text(index_html, encoding="utf-8")

    tag_groups = {}
    for post in posts:
        tags_raw = post.get("tags", "")
        tag_list = [t.strip() for t in tags_raw.split(",") if t.strip()]
        for tag in tag_list:
            tag_groups.setdefault(tag, []).append(post)

    tags_dir = output_path / "tags"
    tags_dir.mkdir(parents=True, exist_ok=True)

    tag_template_path = theme_path / "tag.html"
    if tag_template_path.exists():
        tag_template = tag_template_path.read_text(encoding="utf-8")
        for tag, tagged_posts in sorted(tag_groups.items()):
            tag_html = render_template(
                tag_template,
                {"tag": tag, "posts": tagged_posts, "site_name": site_name},
                template_dir=str(theme_path),
            )
            (tags_dir / f"{tag}.html").write_text(tag_html, encoding="utf-8")

    if tag_groups:
        tags_index_html = _render_tags_index(
            tag_groups, tags_dir, theme_path, site_name
        )
        if tags_index_html:
            (tags_dir / "index.html").write_text(tags_index_html, encoding="utf-8")

    rss_xml = generate_rss(posts, site_url, site_name)
    (output_path / "feed.xml").write_text(rss_xml, encoding="utf-8")

    css_src = theme_path / "style.css"
    if css_src.exists():
        shutil.copy(css_src, output_path / "style.css")

    print(f"Built {len(posts)} posts to {output_dir}/")


def _render_tags_index(tag_groups, tags_dir, theme_path, site_name):
    tags_index_path = theme_path / "tags.html"
    if tags_index_path.exists():
        template = tags_index_path.read_text(encoding="utf-8")
        tag_list = [
            {"name": tag, "count": len(posts)}
            for tag, posts in sorted(tag_groups.items())
        ]
        return render_template(
            template,
            {"tags": tag_list, "site_name": site_name},
            template_dir=str(theme_path),
        )

    html_parts = [
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<title>Tags - {site_name}</title>"
        "<link rel='stylesheet' href='/style.css'></head><body>",
        "<h1>Tags</h1><ul>",
    ]
    for tag in sorted(tag_groups.keys()):
        count = len(tag_groups[tag])
        html_parts.append(
            f'<li><a href="/tags/{tag}.html">{tag}</a> ({count})</li>'
        )
    html_parts.append("</ul></body></html>")

    tags_index_html = "\n".join(html_parts)
    return tags_index_html


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build the Markdown blog site.")
    parser.add_argument(
        "--content-dir", default="content", help="Directory with Markdown posts"
    )
    parser.add_argument(
        "--theme-dir",
        default="themes/default",
        help="Directory with theme templates",
    )
    parser.add_argument(
        "--output-dir", default="_site", help="Output directory for generated site"
    )
    parser.add_argument(
        "--site-url",
        default="http://localhost:8000",
        help="Public URL of the site",
    )
    parser.add_argument(
        "--site-name", default="My Blog", help="Name of the blog"
    )
    args = parser.parse_args()
    build_site(
        content_dir=args.content_dir,
        theme_dir=args.theme_dir,
        output_dir=args.output_dir,
        site_url=args.site_url,
        site_name=args.site_name,
    )
