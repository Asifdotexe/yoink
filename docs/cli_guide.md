# Yoink CLI Usage Guide

`yoink` is a command-line interface utility to pack a codebase directory into a single markdown file for LLM context, with options to strip comments/whitespace, mask secrets, filter compliance patterns, and visualize local dependencies.

The package is published on PyPI as `yoinky`, but the command-line interface command remains `yoink`.

Install from PyPI:
```bash
pip install yoinky
```

Or install locally in editable mode:
```bash
pip install -e .
```

## Basic Usage

Run `yoink` in the target directory:

```bash
# Packs the current directory and outputs to yoink_output.md
yoink
```

Specify a custom directory to pack and a custom output file:

```bash
# Packs /path/to/project and outputs to output.md
yoink /path/to/project -o output.md
```

Write directly to standard output:

```bash
yoink /path/to/project -o -
```

## CLI Flags and Options

| Flag | Short | Description |
| :--- | :--- | :--- |
| `path` | | Optional target directory or file to process (default: current directory). |
| `--output` | `-o` | Output file path (or `-` for stdout). |
| `--config` | `-c` | Path to a custom `.yoinkconfig.json` configuration file. |
| `--exclude-tests` | | Exclude test files and directories from the packing output. |
| `--max-size` | | Maximum file size in KB to pack (default: 100). |
| `--no-visualize`, `--no-visualise` | | Disable dependency tree and graph visualization. |
| `--raw` | | Disables all processing (comment, whitespace, secret, compliance, dependency trees) and packs files exactly as they are. |

## Examples

### Default Configuration
Packs the codebase, strips comments/whitespaces, masks secrets/endpoints, and generates dependency visualization:
```bash
yoink .
```

### Raw Code Export
Keeps all comments, whitespace, compliance patterns, and secrets intact:
```bash
yoink . --raw
```

### Custom Configuration file
Loads custom rules from a specified JSON configuration file:
```bash
yoink . -c my_custom_config.json
```

### Exclude Tests
Packs the project but ignores files matching test directories or patterns:
```bash
yoink . --exclude-tests
```
