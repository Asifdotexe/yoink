import argparse
import json
import sys
from pathlib import Path

from yoink.core.packer import pack_codebase
from yoink.core.scanner import get_files_to_process
from yoink.core.tokenizer import count_tokens


def load_config(config_path: Path | None) -> dict:
    """
    Load project configuration from a JSON file.

    Handles config missing or invalid JSON formatting gracefully, falling back
    to an empty dictionary structure.

    :param config_path: Absolute or relative path to the config file.
    :return: Loaded configuration settings.
    """
    if not config_path:
        return {}
    if not config_path.exists():
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(
            f"Warning: Failed to load config from {config_path}: {e}", file=sys.stderr
        )
        return {}


def main():
    """
    Execute the Yoink command-line interface entry point.

    Parses CLI parameters, aggregates overrides, loads active JSON configuration,
    scans target directories, and writes the packed markdown output.
    """
    # Handle 'censor' subcommands: init / show / tui
    if len(sys.argv) > 1 and sys.argv[1] == "censor":
        subcommand = sys.argv[2] if len(sys.argv) > 2 else ""
        if subcommand not in ("init", "show", "tui"):
            print("Error: Unknown censor command. Available: 'init', 'show', 'tui'", file=sys.stderr)
            sys.exit(1)

        config_file = Path(".yoinkconfig.json")
        if subcommand == "init":
            from yoink.cli.tui import run_censor_init
            run_censor_init(config_file)
            sys.exit(0)
        elif subcommand == "show":
            from yoink.cli.tui import run_censor_show
            run_censor_show(config_file)
            sys.exit(0)
        elif subcommand == "tui":
            from yoink.cli.tui import run_censor_tui
            run_censor_tui(config_file, Path("."))
            sys.exit(0)

    parser = argparse.ArgumentParser(
        description="Yoink: Pack your codebase into a single markdown file for LLM context."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to the directory or file to pack (default: current directory)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output file path (default: yoink_output.md or '-' for stdout)",
    )
    parser.add_argument(
        "--exclude-tests",
        action="store_true",
        help="Exclude test files and directories from packing",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Pack raw file contents directly, disabling all comment/whitespace/secret/compliance/tree modifications",
    )
    parser.add_argument(
        "-c",
        "--config",
        help="Path to config file (default: .yoinkconfig.json in target directory)",
    )
    parser.add_argument(
        "--max-size",
        type=int,
        help="Maximum file size in KB to pack (default: 100)",
    )
    parser.add_argument(
        "--no-visualize",
        "--no-visualise",
        action="store_true",
        dest="no_visualize",
        help="Disable dependency tree and graph visualization",
    )

    args = parser.parse_args()

    target_path = Path(args.path).resolve()
    if not target_path.exists():
        print(f"Error: Target path '{target_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    # Locates configuration file: command line parameter overrides,
    # falling back to target folder JSON or workspace root.
    config_file = None
    if args.config:
        config_file = Path(args.config)
    else:
        test_cfg = (
            target_path / ".yoinkconfig.json"
            if target_path.is_dir()
            else Path(".yoinkconfig.json")
        )
        if test_cfg.exists():
            config_file = test_cfg
        else:
            config_file = test_cfg


    config = load_config(config_file)

    # We consolidate multiple fine-grained formatting rules into a single
    # --raw bypass. Exposing dozens of micro-parameters directly as flags
    # clutters CLI output and leads to developer confusion, so specific
    # rules remain inside the JSON config.
    if args.raw:
        strip_comments = False
        strip_whitespace = False
        mask_secrets_enabled = False
        secret_patterns = None
        compliance_patterns = None
        censor_words = None
        censor_domains = None
        pseudonym_masking = True
        visualize = False
    else:
        strip_comments = config.get("strip_comments", True)
        strip_whitespace = config.get("strip_whitespace", True)
        mask_secrets_enabled = config.get("mask_secrets", True)
        # Fallback to checking both spellings in the configuration structure.
        visualize = False if args.no_visualize else config.get("visualize", config.get("visualise", True))
        secret_patterns = config.get("secret_patterns", None)
        compliance_patterns = config.get("compliance_patterns", None)
        censor_words = config.get("censor_words", None)
        censor_domains = config.get("censor_domains", None)
        pseudonym_masking = config.get("pseudonym_masking", True)


    exclude_patterns = config.get("exclude_patterns") or []
    if args.exclude_tests:
        exclude_patterns.extend(["**/tests/**", "**/test_*", "**/*_test.*"])

    include_extensions = config.get("include_extensions", None)

    # Scan and process target files.
    files = get_files_to_process(target_path, exclude_patterns, include_extensions)
    if not files:
        print("No matching files found.", file=sys.stderr)
        sys.exit(0)

    print(f"Yoinking {len(files)} files...", file=sys.stderr)

    max_file_size_kb = args.max_size or config.get("max_file_size_kb", 100)

    # Pack codebase
    packed_md = pack_codebase(
        root_dir=target_path if target_path.is_dir() else target_path.parent,
        files=files,
        strip_comments=strip_comments,
        strip_whitespace=strip_whitespace,
        mask_sensitive=mask_secrets_enabled,
        custom_secrets=secret_patterns,
        compliance_patterns=compliance_patterns,
        censor_words=censor_words,
        censor_domains=censor_domains,
        pseudonym_masking=pseudonym_masking,
        visualize=visualize,
        max_file_size_kb=max_file_size_kb,
    )

    # Determine final output destination.
    output_path = args.output or config.get("output_file") or "yoink_output.md"

    if output_path == "-":
        sys.stdout.write(packed_md + "\n")
    else:
        out_file = Path(output_path)
        try:
            out_file.parent.mkdir(parents=True, exist_ok=True)
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(packed_md)
            token_count = count_tokens(packed_md)
            print(
                f"Successfully yoinked codebase into: {out_file} (Est. Tokens: {token_count:,})",
                file=sys.stderr,
            )
        except Exception as e:
            print(f"Error writing output file: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
