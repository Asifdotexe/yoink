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
    censor_words: list[str] = None,
    censor_domains: list[str] = None,
    pseudonym_masking: bool = True,
    visualize: bool = True,
    max_file_size_kb: int = 100,
) -> str:
    """
    Pack selected project files into a single structured Markdown document.

    Applies comment/whitespace stripping, sensitive information masking, compliance
    scrubbing, and structural visualizations (dependency trees and graphs).

    :param root_dir: Root directory of the scanned project.
    :param files: List of resolved file paths to be packed.
    :param strip_comments: Whether to prune comments and docstrings.
    :param strip_whitespace: Whether to minify empty lines and spaces.
    :param mask_sensitive: Whether to mask sensitive keys/secrets.
    :param custom_secrets: User-defined secret patterns to match and mask.
    :param compliance_patterns: User-defined compliance scrub mapping.
    :param visualize: Whether to include dependency tree and flowchart.
    :param max_file_size_kb: Size limit in KB; larger files are skipped.
    :return: The packed codebase as a formatted Markdown string.
    """
    root_path = Path(root_dir).resolve()

    # 1. Document Header
    # We utilize short labels (# YP, Gen, Dir, Files, Tokens) instead of verbose
    # strings to minimize token consumption of the pack header layout.
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

    # File List (FL) is always appended to serve as a reliable, predictable master
    # index of all scanned files (including non-code files like README or configs).
    lines.append("## FL")
    for f in files:
        try:
            rel = f.relative_to(root_path).as_posix()
        except ValueError:
            rel = f.as_posix()
        lines.append(f"- `{rel}`")
    lines.append("")

    # 2. Dependency Visualization
    # When enabled, appends a text-based dependency tree (DT) and a Mermaid flowchart (VG)
    # to provide the LLM with immediate architectural structure.
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
    # Appends each file's processed source code within clear start/end tag bounds.
    for f in files:
        try:
            rel = f.relative_to(root_path).as_posix()
        except ValueError:
            rel = f.as_posix()

        # Check file size prior to reading to avoid loading large datasets,
        # binaries, or lockfiles that consume massive token budgets.
        try:
            file_size_kb = f.stat().st_size / 1024
            if file_size_kb > max_file_size_kb:
                lines.append(f"#SF:{rel}")
                lines.append(
                    f"*File skipped: size ({file_size_kb:.1f} KB) exceeds limit ({max_file_size_kb} KB)*"
                )
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

        # #SF: (Start File) and #EF: (End File) boundaries serve as clear,
        # token-efficient delimiters for the LLM context.
        lines.append(f"#SF:{rel}")

        try:
            with open(f, "r", encoding="utf-8", errors="replace") as file_io:
                content = file_io.read()

            content = shred_code(content, f.name, strip_comments, strip_whitespace)
            if mask_sensitive:
                content = mask_secrets(content, custom_secrets)
            if censor_words or censor_domains:
                from yoink.core.shield import censor_content
                content = censor_content(
                    content,
                    censor_words=censor_words,
                    censor_domains=censor_domains,
                    pseudonym_masking=pseudonym_masking,
                )
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
