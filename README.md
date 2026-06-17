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

## Why Yoink?

Feeding full source repositories into LLMs or autonomous AI agents is powerful, but it comes with three major headaches:

1.  **[Exorbitant](https://www.merriam-webster.com/dictionary/exorbitant) Token Costs:** AI prompts get bloated with system boilerplate, repetitive docstrings, and comments, wasting up to 50% of your context window on noise.
    *   *How Yoink helps:* The **Token Shredder** strips out comments, docstrings, and excess whitespace, cutting codebase sizes in half and dramatically reducing downstream API fees.
2.  **Accidental Leakage of Secrets:** Pushing raw code to external AI providers risks exposing internal API keys, passwords, database URLs, and private keys.
    *   *How Yoink helps:* The **Secret Shield** programmatically scans and redacts credentials, emails, and IP addresses before any code leaves your local workspace.
3.  **Enterprise Non-Compliance:** Sharing proprietary legal entities, trade secrets, or internal server routing targets (`*.internal.net`) can trigger company policy alerts.
    *   *How Yoink helps:* The **Compliance Stripper** automatically replaces custom trademarks, license headers, and corporate endpoints with generic placeholder descriptors based on config rules.
4.  **Lost Codebase Structure:** LLMs struggle to understand how files interact when code is dumped as unstructured text.
    *   *How Yoink helps:* The **Dependency Tree Visualizer** automatically parses code imports using ASTs to generate clear text diagrams and Mermaid flowcharts at the top of your pack, providing instant architecture maps to the LLM.

---

## Installation

The package is published on PyPI as `yoinky`, but the command-line interface command remains `yoink`.

Install from PyPI:
```bash
pip install yoinky
```

Or install locally in editable mode:
```bash
# Clone the repository
git clone https://github.com/Asifdotexe/yoink.git
cd yoink

# Install the package
pip install -e .

# Or install with test dependencies
pip install -e ".[test]"
```

---

## Usage

### 1. Command Line Interface

Run the `yoink` command in the directory you wish to pack:

```bash
yoink [path] [flags]
```

#### Flags and Arguments

| Flag | Short | Description |
| :--- | :--- | :--- |
| `path` | | Path to the directory or file to pack (default: current directory). |
| `-o`, `--output` | | Output file path (default: `yoink_output.md` or `-` for stdout). |
| `-c`, `--config` | | Path to custom configuration file. |
| `--exclude-tests` | | Exclude test files and test directories from scanning. |
| `--max-size` | | Maximum file size in KB to pack (default: 100). |
| `--no-visualize`, `--no-visualise` | | Disable dependency tree and graph visualization. |
| `--raw` | | Disables all processing (comment, whitespace, secret, compliance, dependency trees) and packs files exactly as they are. |

#### Examples

Pack the current directory with default cleaning settings:
```bash
yoink
```

Pack a project folder and output to standard output:
```bash
yoink /path/to/project -o -
```

Pack raw codebase contents while skipping test folders:
```bash
yoink . --raw --exclude-tests
```

### 💡 Token Optimization Tips
If you need to minimize your prompt token usage to the absolute limit, follow these rules:
1. Exclude test files by running with `--exclude-tests` (unless you need the LLM to write or refactor tests).
2. Turn off dependency visualization by running with `--no-visualize` or `--no-visualise` (or setting `"visualize": false` or `"visualise": false` in `.yoinkconfig.json`) to avoid tree formatting token overhead.
3. Skip large files, lockfiles, or dataset files by running with `--max-size 50` (or lower).
4. Keep default comment and whitespace stripping enabled (do not run with `--raw`) to strip all docstrings, comments, empty lines, and copyright headers.



---

### 2. REST API Web Server

Start the API server using Uvicorn:

```bash
python -m uvicorn yoink.api.main:app --reload
```

Interactive OpenAPI documentation is available at `http://localhost:8000/docs`.

#### Endpoints

*   `POST /api/v1/sanitize`: Cleans and sanitizes a single raw code fragment payload.
*   `POST /api/v1/pack`: Takes a list of file paths and contents directly to assemble them into a packed Markdown payload.
*   `POST /api/v1/pack-zip`: Accepts an uploaded ZIP file of a project and runs the packer remotely, automatically reading any `.yoinkconfig.json` configuration inside the archive.

---

## Configuration (`.yoinkconfig.json`)

To customize cleaning behavior, place a `.yoinkconfig.json` in your project root directory:

```json
{
  "exclude_patterns": [
    "**/__pycache__/**",
    "**/.git/**",
    "**/.venv/**"
  ],
  "include_extensions": [
    ".py",
    ".js",
    ".ts",
    ".go"
  ],
  "secret_patterns": {
    "ip_address": "\\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\b",
    "generic_api_key": "(?:key|api|secret|token|password|passwd|auth)_?(?:key|api|secret|token|password|passwd|auth)?\\s*[:=]\\s*['\"][a-zA-Z0-9_\\-]{16,}['\"]"
  },
  "compliance_patterns": {
    "\\b[a-zA-Z0-9.-]+\\.internal\\.net\\b": "[PROPRIETARY_ENDPOINT]",
    "\\bYoinkCorp\\b": "[COMPANY_NAME]",
    "\\bConfidentialProprietaryLogicID\\b": "[PROPRIETARY_ID]"
  },
  "strip_comments": true,
  "strip_whitespace": true,
  "mask_secrets": true,
  "visualize": true,
  "output_file": "yoink_output.md"
}
```

---

## Running Tests

Verify your installation by running the test suite:

```bash
pytest
```

---

## License

This project is licensed under the GNU AGPLv3 License.
