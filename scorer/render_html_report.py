#!/usr/bin/env python3
"""Render a Markdown evaluation report as a standalone HTML document."""

import argparse
import html
from pathlib import Path

try:
    import markdown
except ImportError:
    raise SystemExit(
        "Missing dependency: Markdown\n"
        "Install it with: python3 -m pip install Markdown"
    )


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Database evaluation benchmark report">
<title>{title}</title>
<style>
:root {{
  color-scheme: light;
  --bg: #f5f7fb;
  --surface: #ffffff;
  --text: #182230;
  --muted: #667085;
  --border: #e4e7ec;
  --accent: #2563eb;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  line-height: 1.7;
}}
header {{
  background: #101828;
  color: white;
  padding: 42px 24px;
}}
header .inner, main {{
  width: min(1100px, calc(100% - 32px));
  margin: auto;
}}
header p {{ color: #d0d5dd; margin-bottom: 0; }}
main {{
  background: var(--surface);
  margin: 32px auto;
  padding: clamp(20px, 5vw, 56px);
  border: 1px solid var(--border);
  border-radius: 14px;
  box-shadow: 0 8px 30px rgba(16,24,40,.05);
}}
h1, h2, h3, h4 {{ line-height: 1.3; }}
h2 {{
  margin-top: 2.4em;
  padding-bottom: .45em;
  border-bottom: 1px solid var(--border);
}}
a {{ color: var(--accent); }}
table {{
  width: 100%;
  border-collapse: collapse;
  display: block;
  overflow-x: auto;
  margin: 24px 0;
  font-size: .94rem;
}}
th, td {{
  border: 1px solid var(--border);
  padding: 10px 13px;
  text-align: left;
}}
th {{ background: #f2f4f7; }}
tr:nth-child(even) td {{ background: #fafbfc; }}
code {{
  background: #f2f4f7;
  padding: 2px 5px;
  border-radius: 4px;
  font-size: .9em;
}}
pre {{
  overflow-x: auto;
  background: #101828;
  color: #f2f4f7;
  padding: 18px;
  border-radius: 9px;
}}
pre code {{ background: transparent; color: inherit; padding: 0; }}
blockquote {{
  margin-left: 0;
  padding: 12px 20px;
  border-left: 4px solid var(--accent);
  background: #eff6ff;
}}
img {{ max-width: 100%; height: auto; }}
.mermaid {{ overflow-x: auto; }}
footer {{
  text-align: center;
  color: var(--muted);
  padding: 20px;
  font-size: .85rem;
}}
@media print {{
  body {{ background: white; }}
  main {{ width: 100%; margin: 0; border: 0; box-shadow: none; }}
  header {{ background: white; color: black; padding: 15px 0; }}
  header p {{ color: #444; }}
  a {{ color: inherit; text-decoration: none; }}
}}
</style>
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<script>
document.addEventListener("DOMContentLoaded", function () {{
  document.querySelectorAll("pre code.language-mermaid").forEach(function (code) {{
    const container = document.createElement("div");
    container.className = "mermaid";
    container.textContent = code.textContent;
    code.parentElement.replaceWith(container);
  }});
  if (window.mermaid) {{
    mermaid.initialize({{ startOnLoad: true, theme: "default" }});
  }}
}});
</script>
<script>
window.MathJax = {{
  tex: {{ inlineMath: [['\\\\\\\\(', '\\\\\\\\)'], ['$', '$']] }}
}};
</script>
<script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
</head>
<body>
<header>
  <div class="inner">
    <h1>{title}</h1>
    <p>Database Evaluation Benchmark Report</p>
  </div>
</header>
<main>
{content}
</main>
<footer>Generated from Markdown by dbeval</footer>
</body>
</html>
"""


def render_report(source: Path, output: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(f"Input report not found: {source}")

    markdown_text = source.read_text(encoding="utf-8")
    content = markdown.markdown(
        markdown_text,
        extensions=["tables", "fenced_code", "toc", "sane_lists"],
        output_format="html5",
    )

    first_heading = next(
        (line.lstrip("# ").strip() for line in markdown_text.splitlines()
         if line.startswith("# ")),
        source.stem.replace("_", " ").title(),
    )

    document = HTML_TEMPLATE.format(
        title=html.escape(first_heading),
        content=content,
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert a Markdown evaluation report into HTML."
    )
    parser.add_argument("input", type=Path, help="Markdown report path")
    parser.add_argument(
        "--output", "-o", type=Path, required=True,
        help="Destination HTML file"
    )
    args = parser.parse_args()

    try:
        render_report(args.input, args.output)
    except (FileNotFoundError, OSError) as error:
        parser.error(str(error))

    print(f"[PASS] HTML report generated: {args.output}")


if __name__ == "__main__":
    main()
