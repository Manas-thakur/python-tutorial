import re


def escape_html(text: str) -> str:
    html_escape_table = {
        "&": "&amp;",
        '"': "&quot;",
        "<": "&lt;",
        ">": "&gt;",
    }
    return "".join(html_escape_table.get(c, c) for c in text)


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


def parse_inline(text: str) -> str:
    text = escape_html(text)

    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1">', text)

    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)

    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)

    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
    text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)

    return text


def markdown_to_html(md: str) -> str:
    lines = md.splitlines()
    html_lines = []
    in_code_block = False

    i = 0
    while i < len(lines):
        line = lines[i]

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

        if re.match(r'^(-|\*|_){3,}$', line.strip()):
            html_lines.append("<hr>")
            i += 1
            continue

        heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if heading_match:
            level = len(heading_match.group(1))
            content = parse_inline(heading_match.group(2))
            html_lines.append(f"<h{level}>{content}</h{level}>")
            i += 1
            continue

        if line.startswith("> "):
            quote_lines = []
            while i < len(lines) and lines[i].startswith("> "):
                quote_lines.append(parse_inline(lines[i][2:]))
                i += 1
            html_lines.append(f"<blockquote><p>{'<br>'.join(quote_lines)}</p></blockquote>")
            continue

        if line.startswith("- ") or line.startswith("* "):
            items = []
            while i < len(lines) and (lines[i].startswith("- ") or lines[i].startswith("* ")):
                items.append(parse_inline(lines[i][2:]))
                i += 1
            html_lines.append("<ul>")
            for item in items:
                html_lines.append(f"<li>{item}</li>")
            html_lines.append("</ul>")
            continue

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

        if line.strip() == "":
            html_lines.append("")
            i += 1
            continue

        para_lines = []
        while i < len(lines):
            l = lines[i]
            if (l.strip() == ""
                or l.startswith("#")
                or l.startswith("```")
                or l.startswith("> ")
                or l.startswith("- ")
                or l.startswith("* ")
                or re.match(r'^(\d+)\.\s+', l)
                or re.match(r'^(-|\*|_){3,}$', l.strip())):
                break
            para_lines.append(parse_inline(l))
            i += 1
        if para_lines:
            html_lines.append(f"<p>{' '.join(para_lines)}</p>")
            continue

        i += 1

    return "\n".join(html_lines)
