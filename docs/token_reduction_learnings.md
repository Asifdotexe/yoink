# Tokenization & Codebase Token Reduction Reference

When feeding full repositories into Large Language Models (LLMs) or autonomous AI coding agents, token optimization is critical. Large prompts consume context window slots, slow down model response times (latency), and increase API inference costs.

This document synthesizes our core learnings about how LLM tokenizers process source code and outlines the most effective strategies to reduce codebase token size without sacrificing prompt quality.

---

## 1. Byte-Pair Encoding (BPE) & `tiktoken`

Most modern LLMs (including GPT-4, Llama, and Gemini) use **Byte-Pair Encoding (BPE)** at the byte level. Understanding BPE is key to optimizing token counts:

### Key Characteristics of BPE
* **No Out-of-Vocabulary (OOV) Errors:** Text is first converted into UTF-8 bytes. Since the vocabulary starts with all 256 basic byte tokens, BPE can tokenize any character (including emojis, non-English scripts, or unusual syntax) by breaking it down into individual bytes if needed.
* **Whitespace Runs are Compressed:** Unlike older tokenizers, modern BPE vocabularies (like OpenAI's `cl100k_base` or `o200k_base`) contain specific tokens for consecutive spaces. 
  
  > [!NOTE]
  > Our measurements showed that **1, 2, 4, 8, and 12 spaces all consume exactly 1 token**. 
  > This means converting spaces to tabs (`\t`) **does not** reduce token counts for modern models, as the tokenizer already compresses space indents into single tokens.

### Heuristics vs. Real Tokenizers
Many tools approximate token counts using a character-based heuristic (e.g., `characters / 4`). While lightweight, this approach has severe limitations:
* **Code is denser than prose:** Repeated indentation, brackets, and syntax structure mean the actual token count is often different from the simple 4-char proxy.
* **Script dependency:** For non-Latin scripts (like Chinese, Japanese, or Devanagari), UTF-8 characters require 3–4 bytes and are often split into multiple tokens. The `char / 4` heuristic will underestimate the token count by up to **8x** for non-English comments.

---

## 2. Advanced Token Reduction Strategies

To beat standard dumps (like GitIngest or raw exports) and maximize context efficiency, several optimizations can be applied:

### Strategy A: Ultra-Condensed Markup Layout
When code is packed into Markdown, the surrounding metadata and file delimiters consume unnecessary tokens. Moving from verbose, human-readable labels to a **Symbolic Legend** saves significant space.

| Old Delimiter Format | Optimized Condensed Format | Character Savings |
| :--- | :--- | :--- |
| `### File: 'path/to/file.py'` | `#SF:path/to/file.py` | ~11 chars |
| `<!-- START_FILE: path/to/file.py -->` | *(Removed entirely)* | ~38 chars |
| `<!-- END_FILE: path/to/file.py -->` | `#EF:path/to/file.py` | ~10 chars |

By defining a small **Legend** at the top of the file, the LLM maintains 100% understanding of the file boundaries:
```markdown
[Legend: YP=Yoink Pack, FL=File List, DT=Dependency Tree, VG=Visual Graph, SF=Start File, EF=End File]
```
> [!TIP]
> This simple change saves roughly **59 characters (~15 tokens) per file**. For a 100-file repository, this yields a free **1,500 token reduction** simply by removing formatting noise.

---

### Strategy B: License & Copyright Header Stripping
Most source files in open-source or enterprise codebases begin with a boilerplate copyright block (10–30 lines). When repeated across 100 files, this wastes a massive number of tokens on legal jargon that the LLM does not need to see to understand the code logic.

* **Method:** Collect comment lines (starting with `#`, `//`, or `/* ... */`) at the very top of the file. If they contain license keywords (`copyright`, `license`, `gpl`, `mit`, `apache`, `author`), strip that block entirely.
* **Impact:** Can reduce the overall token count of corporate repositories by **10% to 20%** with zero impact on code reasoning.

---

### Strategy C: Max File Size Filtering
Accidentally packing a database dump, log file, build asset, or heavy lock file (like `package-lock.json` or `uv.lock`) can instantly exhaust your context window.

* **Method:** Enforce a strict file size limit (e.g., `100 KB`). If a file exceeds this limit, skip packing its raw content and replace it with a metadata boundary placeholder:
  ```markdown
  #SF:config/data.json
  *File skipped: size (1.2 MB) exceeds limit (100 KB)*
  #EF:config/data.json
  ```
* **Impact:** Acts as a fail-safe, preventing massive token spikes while keeping the LLM aware of the file's presence in the project architecture.

---

### Strategy D: Structural whitespace & comment stripping (Token Shredder)
* **Whitespace:** Strip trailing spaces and remove empty lines.
* **Comments:** Safely strip block/line comments and docstrings.
* **Syntax-safe regex:** Ensure regex comment strippers ignore comment characters inside string literals (e.g., `#` in `url = "https://example.com/#hash"`).

---

## 3. Optimization Summary Matrix

| Optimization | Target Files | Token Savings | Prompt Quality Impact |
| :--- | :--- | :--- | :--- |
| **Comments & Docstrings** | Source Code (`.py`, `.js`, `.go`, etc.) | **30% – 50%** | Minimal (if comments are just explanation, though docstrings sometimes contain useful type info). |
| **License Headers** | All Source Files | **5% – 25%** | **Zero** (LLMs do not need legal headers). |
| **Max File Size Limits** | Data, Logs, Lock Files | **Up to 95%** on heavy repos | **Zero** (prevents garbage-in/garbage-out context pollution). |
| **Whitespace Stripping** | All files | **10% – 20%** | **Zero** (LLMs read code indentation perfectly without extra empty lines). |
| **Condensed Tags + Legend** | Document Structure | **1% – 5%** | **Zero** (the legend teaches the LLM how to parse the boundaries). |
