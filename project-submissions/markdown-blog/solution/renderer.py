import os
import re


def escape_html(text: str) -> str:
    html_escape_table = {
        "&": "&amp;",
        '"': "&quot;",
        "<": "&lt;",
        ">": "&gt;",
    }
    return "".join(html_escape_table.get(c, c) for c in text)


def resolve_value(context: dict, name: str):
    parts = name.split(".")
    value = context
    for part in parts:
        if isinstance(value, dict):
            value = value.get(part)
        elif hasattr(value, part):
            value = getattr(value, part)
        else:
            try:
                value = value[int(part)]
            except (IndexError, ValueError, TypeError):
                return None
    return value


def _find_balanced_block(template: str, block_type: str):
    """Find the first top-level {% block_type ... %}...{% endblock_type %} pair.
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


def render_template(template: str, context: dict, template_dir: str = ".") -> str:
    autoescape = True

    autoescape_match = re.search(
        r'\{%\s*autoescape\s+(true|false)\s*%\}', template
    )
    if autoescape_match:
        autoescape = autoescape_match.group(1) == "true"
        template = re.sub(r'\{%\s*autoescape\s+(true|false)\s*%\}', "", template)

    extends_match = re.search(
        r'\{%\s*extends\s+"([^"]+)"\s*%\}', template
    )
    if extends_match:
        base_path = os.path.join(template_dir, extends_match.group(1))
        try:
            with open(base_path, encoding="utf-8") as f:
                base_template = f.read()
        except FileNotFoundError:
            return f"<!-- Template not found: {extends_match.group(1)} -->"

        blocks = {}
        for m in re.finditer(
            r'\{%\s*block\s+(\w+)\s*%\}(.*?)\{%\s*endblock\s*%\}',
            template,
            re.DOTALL,
        ):
            blocks[m.group(1)] = m.group(2)

        def replace_block(m):
            block_name = m.group(1)
            default_content = m.group(2)
            rendered = render_template(
                blocks.get(block_name, default_content),
                context,
                template_dir,
            )
            return rendered

        template = re.sub(
            r'\{%\s*block\s+(\w+)\s*%\}(.*?)\{%\s*endblock\s*%\}',
            replace_block,
            base_template,
            flags=re.DOTALL,
        )

    def replace_include(m):
        path = m.group(1)
        include_path = os.path.join(template_dir, path)
        try:
            with open(include_path, encoding="utf-8") as f:
                content = f.read()
            return render_template(content, context, template_dir)
        except FileNotFoundError:
            return f"<!-- Missing include: {path} -->"

    template = re.sub(
        r'\{%\s*include\s+"([^"]+)"\s*%\}',
        replace_include,
        template,
    )

    result_parts = []
    pos = 0
    while pos < len(template):
        block = _find_balanced_block(template[pos:], "for")
        if block is None:
            block = _find_balanced_block(template[pos:], "if")
        if block is None:
            result_parts.append(template[pos:])
            break

        result_parts.append(template[pos:pos + block["start"]])
        body = block["body"]

        if block["header"] and " in " in block["header"]:
            parts = block["header"].split(" in ", 1)
            loop_var = parts[0].strip()
            iterable_name = parts[1].strip()
            items = resolve_value(context, iterable_name)
            if items is None:
                items = []

            inner_parts = []
            for item in items:
                local_ctx = dict(context)
                local_ctx[loop_var] = item
                inner_parts.append(render_template(body, local_ctx, template_dir))
            result_parts.append("".join(inner_parts))
        else:
            condition = block["header"]
            value = resolve_value(context, condition)
            if value:
                result_parts.append(render_template(body, context, template_dir))

        pos += block["end"]

    template = "".join(result_parts)

    def replace_var(m):
        var_expr = m.group(1).strip()
        if var_expr.endswith("|safe"):
            var_name = var_expr[:-5].strip()
            value = resolve_value(context, var_name)
            return str(value) if value is not None else ""
        value = resolve_value(context, var_expr)
        if value is None:
            return ""
        result = str(value)
        if autoescape:
            result = escape_html(result)
        return result

    template = re.sub(r'\{\{\s*(.+?)\s*\}\}', replace_var, template)

    return template
