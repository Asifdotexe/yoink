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
    max_file_size_kb: int = 100,
) -> str:
    """Pack the selected files into a single structured markdown document."""
    root_path = Path(root_dir).resolve()

    # 1. Document Header
    lines = [
        "# YP",
        f"- Gen: {datetime.now().isoformat()}",
        f"- Dir: {root_path.as_posix()}",
        f"- Files: {len(files)}",
        "- Tokens: {{TOKEN_COUNT}}",
        "",
        "[Legend: YP=Yoink Pack, FL=File List, DT=Dependency Tree, VG=Visual Graph, SF=Start File, EF=End File]",
        "",
    ]

    lines.append("## FL")
    for f in files:
        try:
            rel = f.relative_to(root_path).as_posix()
        except ValueError:
            rel = f.as_posix()
        lines.append(f"- `{rel}`")
    lines.append("")

    # 2. Dependency Visualization
    if visualize:
        lines.append("## DT")
        graph = build_dependency_graph(files, root_path)
        tree_text = generate_tree_text(graph)
        mermaid_text = generate_mermaid_flowchart(graph)

        lines.append("```")
        lines.append(tree_text)
        lines.append("```")
        lines.append("")

        if mermaid_text:
            lines.append("## VG")
            lines.append(mermaid_text)
            lines.append("")

    # 3. File Contents
    for f in files:
        try:
            rel = f.relative_to(root_path).as_posix()
        except ValueError:
            rel = f.as_posix()

        # Check file size before reading
        try:
            file_size_kb = f.stat().st_size / 1024
            if file_size_kb > max_file_size_kb:
                lines.append(f"#SF:{rel}")
                lines.append(f"*File skipped: size ({file_size_kb:.1f} KB) exceeds limit ({max_file_size_kb} KB)*")
                lines.append(f"#EF:{rel}")
                lines.append("")
                continue
        except Exception:
            pass

        suffix = f.suffix.lower()
        lang = suffix.lstrip(".")
        if lang == "py":
            lang = "python"
        elif lang in ("js", "ts", "jsx", "tsx"):
            lang = "javascript" if lang in ("js", "jsx") else "typescript"
        elif not lang:
            lang = "text"

        lines.append(f"#SF:{rel}")

        try:
            with open(f, "r", encoding="utf-8", errors="replace") as file_io:
                content = file_io.read()

            content = shred_code(content, f.name, strip_comments, strip_whitespace)
            if mask_sensitive:
                content = mask_secrets(content, custom_secrets)
            if compliance_patterns:
                content = strip_compliance(content, compliance_patterns)

            lines.append(f"```{lang}")
            lines.append(content)
            lines.append("```")
        except Exception as e:
            lines.append(f"*Error reading file: {str(e)}*")

        lines.append(f"#EF:{rel}")
        lines.append("")

    draft = "\n".join(lines)
    token_count = count_tokens(draft)
    return draft.replace("{{TOKEN_COUNT}}", f"{token_count:,}")

