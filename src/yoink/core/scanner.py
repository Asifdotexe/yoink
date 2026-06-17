import os
from pathlib import Path

import pathspec

# Default extensions of target files we wish to scan. Excludes binary assets,
# images, audio, video, pdfs, and other formats that cannot be read as text.
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
    """
    Load .gitignore rules from target directory.

    Combines standard ignores (.git, virtual environments, node_modules)
    with any user-defined patterns inside the repository's .gitignore.

    :param root_dir: Target directory root.
    :return: A pathspec instance containing active ignore patterns.
    """
    gitignore_path = root_dir / ".gitignore"
    patterns = []

    # Always ignore development infrastructure, build assets, and dependency directories
    # to protect context token capacity and prevent scanning huge assets.
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
    """
    Recursively scan a directory for valid files.

    Respects gitignore rules, custom config exclude lists, and maps files to
    approved text extensions.

    :param root_dir: Target directory path.
    :param config_exclude: Optional list of glob patterns to exclude.
    :param include_exts: Optional whitelist of extensions to scan.
    :return: Sorted list of resolved file Paths.
    """
    root_path = Path(root_dir).resolve()
    spec = load_gitignore_spec(root_path)

    custom_spec = None
    if config_exclude:
        custom_spec = pathspec.PathSpec.from_lines("gitignore", config_exclude)

    extensions = set(include_exts) if include_exts else DEFAULT_TEXT_EXTENSIONS
    matched_files = []

    for dirpath, dirnames, filenames in os.walk(root_path):
        path_dirpath = Path(dirpath)

        # We filter the sub-directories in-place during the walk loop.
        # This prevents os.walk from entering ignored directories entirely,
        # resulting in massive speedups on large repos with node_modules or venv.
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

            if spec.match_file(rel_path):
                continue
            if custom_spec and custom_spec.match_file(rel_path):
                continue

            if full_f_path.suffix not in extensions:
                continue

            matched_files.append(full_f_path)

    return sorted(matched_files)


def get_files_to_process(
    target_path: Path, config_exclude: list[str] = None, include_exts: list[str] = None
) -> list[Path]:
    """
    Resolve a user target path into a list of file paths to pack.

    Supports resolving a direct single file or recursively scanning a directory.

    :param target_path: Target directory or file path.
    :param config_exclude: Optional list of glob patterns to exclude.
    :param include_exts: Optional list of whitelisted extensions.
    :return: A list of resolved file paths.
    """
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
