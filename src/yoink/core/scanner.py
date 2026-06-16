import os
from pathlib import Path

import pathspec

DEFAULT_TEXT_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".go",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".java",
    ".cs",
    ".html",
    ".css",
    ".json",
    ".md",
    ".txt",
    ".yml",
    ".yaml",
    ".toml",
    ".ini",
    ".sh",
    ".bat",
    ".ps1",
    ".sql",
    ".rs",
    ".kt",
}


def load_gitignore_spec(root_dir: Path) -> pathspec.PathSpec:
    """Load gitignore rules from root_dir and parents or default rules."""
    gitignore_path = root_dir / ".gitignore"
    patterns = []

    # Always ignore some default directories
    patterns.extend(
        [
            ".git/",
            ".venv/",
            "venv/",
            "__pycache__/",
            "node_modules/",
            ".yoinkconfig.json",
            "yoink_output.md",
            "LICENSE",
            "*.pyc",
            "*.pyo",
            "*.pyd",
        ]
    )

    if gitignore_path.exists():
        try:
            with open(gitignore_path, "r", encoding="utf-8") as f:
                patterns.extend(f.readlines())
        except Exception:
            pass

    return pathspec.PathSpec.from_lines("gitignore", patterns)


def scan_directory(
    root_dir: Path, config_exclude: list[str] = None, include_exts: list[str] = None
) -> list[Path]:
    """Scan directory recursively, respecting gitignore and custom patterns/extensions."""
    root_path = Path(root_dir).resolve()
    spec = load_gitignore_spec(root_path)

    # If custom excludes are provided, compile them
    custom_spec = None
    if config_exclude:
        custom_spec = pathspec.PathSpec.from_lines("gitignore", config_exclude)

    # Default extensions if not specified
    extensions = set(include_exts) if include_exts else DEFAULT_TEXT_EXTENSIONS

    matched_files = []

    for dirpath, dirnames, filenames in os.walk(root_path):
        path_dirpath = Path(dirpath)

        # Filter dirnames in-place to prevent scanning ignored subdirectories
        filtered_dirs = []
        for d in dirnames:
            full_d_path = path_dirpath / d
            rel_path = full_d_path.relative_to(root_path).as_posix() + "/"

            if spec.match_file(rel_path):
                continue
            if custom_spec and custom_spec.match_file(rel_path):
                continue
            filtered_dirs.append(d)
        dirnames[:] = filtered_dirs

        for f in filenames:
            full_f_path = path_dirpath / f
            rel_path = full_f_path.relative_to(root_path).as_posix()

            # Check gitignore
            if spec.match_file(rel_path):
                continue
            # Check custom config excludes
            if custom_spec and custom_spec.match_file(rel_path):
                continue

            # Filter by extensions
            if full_f_path.suffix not in extensions:
                continue

            matched_files.append(full_f_path)

    return sorted(matched_files)


def get_files_to_process(
    target_path: Path, config_exclude: list[str] = None, include_exts: list[str] = None
) -> list[Path]:
    """Resolve the target path into a list of file paths to process (files or directories)."""
    target = Path(target_path).resolve()
    extensions = set(include_exts) if include_exts else DEFAULT_TEXT_EXTENSIONS

    if target.is_file():
        if target.suffix not in extensions:
            return []
        return [target]
    elif target.is_dir():
        return scan_directory(target, config_exclude, include_exts)
    else:
        return []
