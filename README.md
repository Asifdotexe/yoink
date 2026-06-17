<p align="center">
  <img src="https://raw.githubusercontent.com/Asifdotexe/yoink/main/assets/yoink.png" alt="Yoink Logo" width="300" />
</p>

<h1 align="center">Yoink</h1>

<p align="center">
  <a href="https://github.com/Asifdotexe/yoink/actions/workflows/ci.yml"><img src="https://github.com/Asifdotexe/yoink/actions/workflows/ci.yml/badge.svg" alt="Python CI" /></a>
  <a href="https://github.com/Asifdotexe/yoink/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-AGPL_v3-blue.svg" alt="License: AGPL v3" /></a>
</p>

Yoink is a command-line tool and FastAPI backend designed to bundle, sanitize, and visualize codebases for Large Language Model (LLM) contexts. It converts raw project directories into structured Markdown documents, optimizing token consumption and preventing compliance and security leaks.

---

## Features

* **Token Shredder:** Safely strips comments, docstrings, and excess whitespace to reduce prompt size.
* **Secret Shield:** Programmatically redacts credentials, private keys, emails, and IP addresses.
* **Compliance Stripper & Masking:** Redacts proprietary terms and internal domains using deterministic, token-efficient phonetic codenames (e.g. `Delta7`) to keep code syntax compilable. Features an interactive terminal UI (TUI) to configure and live-test rules in a sandbox.
* **Dependency Trees:** Automatically generates AST-based ASCII dependency trees and Mermaid flowcharts.

---

## Installation

Install from PyPI:
```bash
pip install yoinky
```

Or install locally in editable mode:
```bash
git clone https://github.com/Asifdotexe/yoink.git
cd yoink
pip install -e .
```

---

## Quick Start

### 1. Pack a Codebase
Pack the current directory:
```bash
yoink
```

### 2. Configure Censor Lists (CLI / TUI)
* **Initialize rules (like `poetry init`):**
  ```bash
  yoink censor init
  ```
* **Inspect active codename mappings (e.g., `Theseus -> Delta7`):**
  ```bash
  yoink censor show
  ```
* **Launch interactive dashboard & sandbox:**
  ```bash
  yoink --censor-tui
  ```

---

## Documentation

For detailed instructions and references, please refer to the dedicated guides:

* **[CLI Usage Guide](docs/cli_guide.md):** Complete reference of CLI commands, flags (`--raw`, `--max-size`, `--no-visualize`, `--censor`, `--censor-tui`, etc.), and usage examples.
* **[REST API Guide](docs/api_guide.md):** Detailed guide to API endpoints, schema structures, and Render blueprint web service deployment.
* **[Token Reduction Learnings](docs/token_reduction_learnings.md):** Technical reference on how BPE tokenizers handle whitespace, license header stripping, and performance tuning.

---

## Running Tests

Verify your local installation:
```bash
pytest
```

---

## License

This project is licensed under the GNU AGPLv3 License.
