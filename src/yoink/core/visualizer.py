import ast
import re
from pathlib import Path


def get_python_imports(file_path: Path, root_dir: Path) -> list[str]:
    """Parse a python file and find all imports."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            tree = ast.parse(f.read(), filename=str(file_path))
    except Exception:
        return []

    imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            # level > 0 indicates relative import (e.g. from .core import scanner)
            module_name = node.module or ""
            imports.append(module_name)

    return imports


def get_non_python_imports(file_path: Path) -> list[str]:
    """Extract imports from JS, TS, Go, C/C++ using regexes."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception:
        return []

    imports = []
    suffix = file_path.suffix.lower()

    if suffix in (".js", ".ts", ".jsx", ".tsx"):
        # Match: import ... from '...' or import '...'
        matches = re.findall(
            r"""import\s+(?:.*?\s+from\s+)?['"]([^'"]+)['"]""", content
        )
        imports.extend(matches)
        # Match: require('...')
        matches_req = re.findall(r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)""", content)
        imports.extend(matches_req)
    elif suffix == ".go":
        # Match: import "..."
        matches = re.findall(r"""import\s+['"]([^'"]+)['"]""", content)
        imports.extend(matches)
        # Match: import ( ... )
        multi_line = re.findall(r"""import\s*\((.*?)\)""", content, re.DOTALL)
        for block in multi_line:
            matches_block = re.findall(r"""['"]([^'"]+)['"]""", block)
            imports.extend(matches_block)
    elif suffix in (".c", ".cpp", ".h", ".hpp"):
        # Match: #include "..." (local headers, not <header>)
        matches = re.findall(r"""#include\s+['"]([^'"]+)['"]""", content)
        imports.extend(matches)

    return imports


def resolve_relative_import(
    import_path: str, current_file: Path, files_set: set[Path]
) -> Path | None:
    """Resolve a relative import string to a concrete file in the scanned set."""
    current_dir = current_file.parent
    try:
        resolved = (current_dir / import_path).resolve()
    except Exception:
        return None

    # Check potential suffixes
    for ext in (".js", ".ts", ".jsx", ".tsx", ".h", ".hpp", ".cpp", ".c", ".go"):
        test_file = resolved.with_suffix(ext)
        if test_file in files_set:
            return test_file
        test_index = resolved / f"index{ext}"
        if test_index in files_set:
            return test_index

    if resolved in files_set:
        return resolved

    return None


def build_dependency_graph(files: list[Path], root_dir: Path) -> dict[str, list[str]]:
    """Build a dependency graph mapping files to their list of local dependencies."""
    files_set = set(files)
    graph = {}

    # Pre-map python files to module names for module-level absolute resolution
    module_to_file = {}
    for f in files:
        if f.suffix.lower() == ".py":
            try:
                parts = list(f.with_suffix("").relative_to(root_dir).parts)
                if len(parts) > 1 and parts[0] in ("src", "lib"):
                    parts = parts[1:]
                module_name = ".".join(parts)
                module_to_file[module_name] = f
            except Exception:
                pass

    for f in files:
        try:
            rel_path = f.relative_to(root_dir).as_posix()
        except ValueError:
            rel_path = f.as_posix()

        graph[rel_path] = []
        suffix = f.suffix.lower()

        if suffix == ".py":
            imports = get_python_imports(f, root_dir)
            for imp in imports:
                if not imp:
                    continue
                # 1. Try exact module match
                if imp in module_to_file:
                    target = module_to_file[imp]
                    try:
                        target_rel = target.relative_to(root_dir).as_posix()
                    except ValueError:
                        target_rel = target.as_posix()
                    if target_rel != rel_path and target_rel not in graph[rel_path]:
                        graph[rel_path].append(target_rel)
                    continue
                # 2. Try prefix matches (handles sub-module imports)
                for mod_name, target_file in module_to_file.items():
                    if mod_name.startswith(imp + ".") or imp.startswith(mod_name):
                        try:
                            target_rel = target_file.relative_to(root_dir).as_posix()
                        except ValueError:
                            target_rel = target_file.as_posix()
                        if target_rel != rel_path and target_rel not in graph[rel_path]:
                            graph[rel_path].append(target_rel)
        else:
            imports = get_non_python_imports(f)
            for imp in imports:
                if not imp:
                    continue
                resolved = resolve_relative_import(imp, f, files_set)
                if resolved:
                    try:
                        target_rel = resolved.relative_to(root_dir).as_posix()
                    except ValueError:
                        target_rel = resolved.as_posix()
                    if target_rel != rel_path and target_rel not in graph[rel_path]:
                        graph[rel_path].append(target_rel)

    return graph


def generate_tree_text(graph: dict[str, list[str]]) -> str:
    """Generate a text-based tree representing code relationships."""
    if not graph:
        return "No dependencies found."

    all_nodes = set(graph.keys())
    imported_nodes = set(val for targets in graph.values() for val in targets)
    roots = sorted(list(all_nodes - imported_nodes))

    if not roots:
        roots = sorted(list(all_nodes))

    lines = ["Dependency Tree:"]
    visited = set()

    def print_node(node: str, prefix: str = "", is_last: bool = True):
        if node in visited:
            lines.append(f"{prefix}{'└── ' if is_last else '├── '}{node} (cycle)")
            return

        visited.add(node)
        char = "└── " if is_last else "├── "
        lines.append(f"{prefix}{char}{node}")

        children = sorted(graph.get(node, []))
        new_prefix = prefix + ("    " if is_last else "│   ")

        for i, child in enumerate(children):
            print_node(child, new_prefix, i == len(children) - 1)

        visited.remove(node)

    for i, root in enumerate(roots):
        print_node(root, "", i == len(roots) - 1)

    return "\n".join(lines)


def generate_mermaid_flowchart(graph: dict[str, list[str]]) -> str:
    """Generate a Mermaid diagram schema of code dependencies."""
    if not graph:
        return ""

    # Check if there are any connections
    has_edges = any(targets for targets in graph.values())
    if not has_edges:
        return ""

    lines = ["```mermaid", "graph TD"]
    node_ids = {}
    id_counter = 0

    def get_id(path: str) -> str:
        nonlocal id_counter
        if path not in node_ids:
            node_ids[path] = f"N{id_counter}"
            id_counter += 1
        return node_ids[path]

    for source, targets in graph.items():
        if not targets:
            continue
        source_id = get_id(source)
        lines.append(f'    {source_id}["{source}"]')
        for target in targets:
            target_id = get_id(target)
            lines.append(f'    {target_id}["{target}"]')
            lines.append(f"    {source_id} --> {target_id}")

    lines.append("```")
    return "\n".join(lines)
