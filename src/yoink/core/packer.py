from datetime import datetime
from pathlib import Path

from yoink.core.shield import mask_secrets, strip_compliance
from yoink.core.shredder import shred_code
from yoink.core.tokenizer import count_tokens
from yoink.core.visualizer import (
    build_dependency_graph,
    generate_mermaid_flowchart,
    generate_tree_text,
)


def pack_codebase(
    root_dir: Path,
    files: list[Path],
    strip_comments: bool = True,
    strip_whitespace: bool = True,
    mask_sensitive: bool = True,
    custom_secrets: dict[str, str] = None,
    compliance_patterns: dict[str, str] = None,
    visualize: bool = True,
) -> str:
    """Pack the selected files into a single structured markdown document."""
    root_path = Path(root_dir).resolve()

    # 1. Document Header
    lines = [
        "# Yoink Codebase Pack",
        f"- **Generated on:** {datetime.now().isoformat()}",
        f"- **Root Directory:** `{root_path.as_posix()}`",
        f"- **Total Files:** {len(files)}",
        "- **Estimated Tokens:** {{TOKEN_COUNT}}",
        "",
        "## Scanned Files List",
    ]

    for f in files:
        try:
            rel = f.relative_to(root_path).as_posix()
        except ValueError:
            rel = f.as_posix()
        lines.append(f"- `{rel}`")

    lines.append("")

    # 2. Dependency Visualization
    if visualize:
        lines.append("## Codebase Dependencies")
        graph = build_dependency_graph(files, root_path)
        tree_text = generate_tree_text(graph)
        mermaid_text = generate_mermaid_flowchart(graph)

        lines.append("### Dependency Tree")
        lines.append("```")
        lines.append(tree_text)
        lines.append("```")
        lines.append("")

        if mermaid_text:
            lines.append("### Visual Graph")
            lines.append(mermaid_text)
            lines.append("")

    # 3. File Contents
    lines.append("## File Contents")
    lines.append("")

    for f in files:
        try:
            rel = f.relative_to(root_path).as_posix()
        except ValueError:
            rel = f.as_posix()

        suffix = f.suffix.lower()
        lang = suffix.lstrip(".")
        if lang == "py":
            lang = "python"
        elif lang in ("js", "ts", "jsx", "tsx"):
            lang = "javascript" if lang in ("js", "jsx") else "typescript"
        elif not lang:
            lang = "text"

        lines.append(f"### File: `{rel}`")
        lines.append(f"<!-- START_FILE: {rel} -->")

        try:
            with open(f, "r", encoding="utf-8", errors="replace") as file_io:
                content = file_io.read()

            content = shred_code(content, suffix, strip_comments, strip_whitespace)
            if mask_sensitive:
                content = mask_secrets(content, custom_secrets)
            if compliance_patterns:
                content = strip_compliance(content, compliance_patterns)

            lines.append(f"```{lang}")
            lines.append(content)
            lines.append("```")
        except Exception as e:
            lines.append(f"*Error reading file: {str(e)}*")

        lines.append(f"<!-- END_FILE: {rel} -->")
        lines.append("")

    draft = "\n".join(lines)
    token_count = count_tokens(draft)
    return draft.replace("{{TOKEN_COUNT}}", f"{token_count:,}")
