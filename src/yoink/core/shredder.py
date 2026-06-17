import os
import re


def strip_license_header(code: str) -> str:
    """
    Strip license headers and copyright blocks from the top of the file.

    Recursively checks for block comments and loops over line comments
    containing license-related keywords until code logic begins.

    :param code: Raw source code string.
    :return: Source code with leading license headers removed.
    """
    stripped_code = code.lstrip()

    # 1. Handle C-style block comments at the start (/* ... */)
    # We strip and recurse to catch any consecutive blocks.
    if stripped_code.startswith("/*"):
        end_idx = stripped_code.find("*/")
        if end_idx != -1:
            block = stripped_code[: end_idx + 2]
            block_lower = block.lower()
            if any(
                k in block_lower
                for k in ("copyright", "license", "author", "gpl", "mit", "apache")
            ):
                return strip_license_header(stripped_code[end_idx + 2 :])

    # 2. Handle consecutive line comments (# or //) at the start
    lines = code.splitlines()
    header_lines = []
    license_found = False

    for line in lines:
        line_strip = line.strip()
        if line_strip.startswith("#") or line_strip.startswith("//"):
            header_lines.append(line)
            if any(
                k in line_strip.lower()
                for k in ("copyright", "license", "author", "gpl", "mit", "apache")
            ):
                license_found = True
        elif not line_strip:
            # We collect empty lines nested within the header block to avoid
            # leaving orphan blank lines at the top of the file.
            header_lines.append(line)
        else:
            break

    if license_found and header_lines:
        num_header_lines = len(header_lines)
        return "\n".join(lines[num_header_lines:])

    return code


# We pre-compile regex patterns at the module level to eliminate inline
# compilation overhead during bulk file parsing runs.
_PYTHON_COMMENTS_RE = re.compile(
    r'("""[\s\S]*?""")|(\'\'\'[\s\S]*?\'\'\')|("(?:\\.|[^"\\])*")|(\'(?:\\.|[^\'\\])*\')|(#.*)'
)
_C_STYLE_COMMENTS_RE = re.compile(
    r'("(?:\\.|[^"\\])*")|(\'(?:\\.|[^\'\\])*\')|(`(?:\\.|[^`\\])*`)|(/\*[\s\S]*?\*/)|(//.*)'
)
_HASH_COMMENTS_RE = re.compile(r'("(?:\\.|[^"\\])*")|(\'(?:\\.|[^\'\\])*\')|(#.*)')
_HTML_XML_COMMENTS_RE = re.compile(r"(<!--[\s\S]*?-->)")


def strip_python_comments_regex(code: str) -> str:
    """
    Strip line comments and triple-quoted docstrings from Python code.

    Preserves code syntax by ignoring comments embedded within quotes.

    :param code: Raw Python source code.
    :return: Python source code without docstrings and comments.
    """
    return _PYTHON_COMMENTS_RE.sub(lambda m: m.group(3) or m.group(4) or "", code)


def strip_c_style_comments(code: str) -> str:
    """
    Strip block and line comments from C-style source files.

    Applies to Go, JavaScript, TypeScript, C, C++, Java, Rust, Kotlin, etc.
    Ensures inline block comment spaces are preserved to prevent syntax joins.

    :param code: Raw C-style source code.
    :return: Cleaned source code.
    """
    return _C_STYLE_COMMENTS_RE.sub(
        lambda m: m.group(1) or m.group(2) or m.group(3) or (" " if m.group(4) else ""),
        code,
    )


def strip_hash_comments(code: str) -> str:
    """
    Strip hash line comments from shell scripts and configuration files.

    Guarantees that strings enclosing hash characters are not corrupted.

    :param code: Raw script or config content.
    :return: Cleaned content.
    """
    return _HASH_COMMENTS_RE.sub(lambda m: m.group(1) or m.group(2) or "", code)


def strip_html_xml_comments(code: str) -> str:
    """
    Strip HTML and XML comment blocks.

    :param code: Raw HTML/XML content.
    :return: Content without comment tags.
    """
    return _HTML_XML_COMMENTS_RE.sub("", code)


def strip_excess_whitespace(code: str) -> str:
    """
    Strip trailing spaces and discard empty lines to optimize tokens.

    :param code: Source code content.
    :return: Densely formatted code without blank lines.
    """
    return "\n".join(
        line for line in (char.rstrip() for char in code.splitlines()) if line
    )


def shred_code(
    code: str,
    filename_or_ext: str,
    strip_comments: bool = True,
    strip_whitespace: bool = True,
) -> str:
    """
    Route source code through language-specific cleaning and pruning.

    :param code: Raw file content.
    :param filename_or_ext: Name of the file or its file extension.
    :param strip_comments: Whether to prune comments/docstrings.
    :param strip_whitespace: Whether to minify empty lines and spaces.
    :return: Cleaned code content.
    """
    if strip_comments:
        code = strip_license_header(code)

    if not strip_comments:
        if strip_whitespace:
            return strip_excess_whitespace(code)
        return code

    name_or_ext = filename_or_ext.lower()

    # 1. Process exact filenames that do not have traditional extensions
    if name_or_ext in ("dockerfile", ".dockerignore", "requirements.txt", ".gitignore"):
        code = strip_hash_comments(code)
    else:
        # standard splitext extracts suffix, falling back to name if no dot exists.
        ext = os.path.splitext(name_or_ext)[1] or name_or_ext

        if ext == ".py":
            code = strip_python_comments_regex(code)
        elif ext in (
            ".yaml",
            ".yml",
            ".toml",
            ".sh",
            ".bash",
            ".zsh",
            ".ini",
            ".cfg",
            ".conf",
            ".properties",
        ):
            code = strip_hash_comments(code)
        elif ext in (
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
            ".css",
        ):
            code = strip_c_style_comments(code)
        elif ext in (".html", ".xml", ".xhtml", ".svg"):
            code = strip_html_xml_comments(code)

    if strip_whitespace:
        code = strip_excess_whitespace(code)

    return code
