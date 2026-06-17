import os
import re


def strip_license_header(code: str) -> str:
    """Strip license headers/copyright blocks from the top of the file."""
    stripped_code = code.lstrip()
    
    # 1. Handle C-style block comments at the start (/* ... */)
    if stripped_code.startswith("/*"):
        end_idx = stripped_code.find("*/")
        if end_idx != -1:
            block = stripped_code[:end_idx + 2]
            block_lower = block.lower()
            if any(k in block_lower for k in ("copyright", "license", "author", "gpl", "mit", "apache")):
                # Strip and recurse to catch any consecutive blocks
                return strip_license_header(stripped_code[end_idx + 2:])

    # 2. Handle line comments (# or //) at the start
    lines = code.splitlines()
    header_lines = []
    license_found = False
    
    for line in lines:
        line_strip = line.strip()
        if line_strip.startswith("#") or line_strip.startswith("//"):
            header_lines.append(line)
            if any(k in line_strip.lower() for k in ("copyright", "license", "author", "gpl", "mit", "apache")):
                license_found = True
        elif not line_strip:
            # Collect empty lines within the header block
            header_lines.append(line)
        else:
            break
            
    if license_found and header_lines:
        num_header_lines = len(header_lines)
        return "\n".join(lines[num_header_lines:])
        
    return code


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


def strip_hash_comments(code: str) -> str:
    """Strip # line comments from shell scripts and configuration files, preserving strings."""
    # Matches double-quotes, single-quotes, and line comments
    pattern = r'("(?:\\.|[^"\\])*")|(\'(?:\\.|[^\'\\])*\')|(#.*)'
    return re.sub(pattern, lambda m: m.group(1) or m.group(2) or "", code)


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
    filename_or_ext: str,
    strip_comments: bool = True,
    strip_whitespace: bool = True,
) -> str:
    """Apply language-specific comment and whitespace stripping rules."""
    if strip_comments:
        code = strip_license_header(code)

    if not strip_comments:
        if strip_whitespace:
            return strip_excess_whitespace(code)
        return code

    name_or_ext = filename_or_ext.lower()
    
    # Check exact filenames
    if name_or_ext in ("dockerfile", ".dockerignore", "requirements.txt", ".gitignore"):
        code = strip_hash_comments(code)
    else:
        # ponytail: standard splitext handles extension extraction cleanly with original fallback
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
