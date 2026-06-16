import re


def strip_python_comments_regex(code: str) -> str:
    """Strip comments and triple-quoted docstrings from Python code using regex."""
    # Pattern matches triple double-quotes, triple single-quotes, double-quotes, single-quotes, and line comments
    pattern = r'("""[\s\S]*?""")|(\'\'\'[\s\S]*?\'\'\')|("(?:\\.|[^"\\])*")|(\'(?:\\.|[^\'\\])*\')|(#.*)'
    return re.sub(pattern, lambda m: m.group(3) or m.group(4) or "", code)


def strip_c_style_comments(code: str) -> str:
    """Strip block and line comments from C-style languages (Go, JS, TS, C, C++, Java, etc.)."""
    pattern = r'("(?:\\.|[^"\\])*")|(\'(?:\\.|[^\'\\])*\')|(`(?:\\.|[^`\\])*`)|(/\*[\s\S]*?\*/)|(//.*)'
    return re.sub(
        pattern,
        lambda m: m.group(1) or m.group(2) or m.group(3) or (" " if m.group(4) else ""),
        code,
    )


def strip_html_xml_comments(code: str) -> str:
    """Strip HTML/XML comment tags (<!-- ... -->)."""
    pattern = r"(<!--[\s\S]*?-->)"
    return re.sub(pattern, "", code)


def strip_excess_whitespace(code: str) -> str:
    """Strip trailing whitespace from each line and remove empty lines."""
    return "\n".join(
        line for line in (char.rstrip() for char in code.splitlines()) if line
    )


def shred_code(
    code: str,
    file_suffix: str,
    strip_comments: bool = True,
    strip_whitespace: bool = True,
) -> str:
    """Apply language-specific comment and whitespace stripping rules."""
    if not strip_comments:
        if strip_whitespace:
            return strip_excess_whitespace(code)
        return code

    suffix = file_suffix.lower()
    if suffix == ".py":
        code = strip_python_comments_regex(code)
    elif suffix in (
        ".js",
        ".ts",
        ".go",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".java",
        ".cs",
        ".scala",
        ".swift",
        ".rs",
        ".kt",
    ):
        code = strip_c_style_comments(code)
    elif suffix in (".html", ".xml", ".xhtml", ".svg"):
        code = strip_html_xml_comments(code)

    if strip_whitespace:
        code = strip_excess_whitespace(code)

    return code
