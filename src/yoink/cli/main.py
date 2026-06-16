import sys
import json
import argparse
from pathlib import Path
from yoink.core.scanner import get_files_to_process
from yoink.core.packer import pack_codebase

def load_config(config_path: Path | None) -> dict:
    """Load configuration from a JSON file."""
    if not config_path:
        return {}
    if not config_path.exists():
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load config from {config_path}: {e}", file=sys.stderr)
        return {}

def main():
    parser = argparse.ArgumentParser(
        description="Yoink: Pack your codebase into a single markdown file for LLM context."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to the directory or file to pack (default: current directory)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file path (default: yoink_output.md or '-' for stdout)"
    )
    parser.add_argument(
        "--exclude-tests",
        action="store_true",
        help="Exclude test files and directories from packing"
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Pack raw file contents directly, disabling all comment/whitespace/secret/compliance/tree modifications"
    )
    parser.add_argument(
        "-c", "--config",
        help="Path to config file (default: .yoinkconfig.json in target directory)"
    )
    
    args = parser.parse_args()
    
    target_path = Path(args.path).resolve()
    if not target_path.exists():
        print(f"Error: Target path '{target_path}' does not exist.", file=sys.stderr)
        sys.exit(1)
        
    # Find config file
    config_file = None
    if args.config:
        config_file = Path(args.config)
    else:
        test_cfg = target_path / ".yoinkconfig.json" if target_path.is_dir() else Path(".yoinkconfig.json")
        if test_cfg.exists():
            config_file = test_cfg
            
    config = load_config(config_file)
    
    # ponytail: consolidated micro-knob cleaning parameters into a single --raw override.
    # Why: Exposing every cleaning option as a CLI parameter leads to user confusion. Using --raw as a single
    # global bypass allows users to easily choose raw output, while specific adjustments remain in the config.
    if args.raw:
        strip_comments = False
        strip_whitespace = False
        mask_secrets_enabled = False
        secret_patterns = None
        compliance_patterns = None
        visualize = False
    else:
        strip_comments = config.get("strip_comments", True)
        strip_whitespace = config.get("strip_whitespace", True)
        mask_secrets_enabled = config.get("mask_secrets", True)
        visualize = config.get("visualize", True)
        secret_patterns = config.get("secret_patterns", None)
        compliance_patterns = config.get("compliance_patterns", None)

    exclude_patterns = config.get("exclude_patterns") or []
    if args.exclude_tests:
        exclude_patterns.extend(["**/tests/**", "**/test_*", "**/*_test.*"])
        
    include_extensions = config.get("include_extensions", None)
    
    # Scan files
    files = get_files_to_process(target_path, exclude_patterns, include_extensions)
    if not files:
        print("No matching files found.", file=sys.stderr)
        sys.exit(0)
        
    print(f"Yoinking {len(files)} files...", file=sys.stderr)
    
    # Pack codebase
    packed_md = pack_codebase(
        root_dir=target_path if target_path.is_dir() else target_path.parent,
        files=files,
        strip_comments=strip_comments,
        strip_whitespace=strip_whitespace,
        mask_sensitive=mask_secrets_enabled,
        custom_secrets=secret_patterns,
        compliance_patterns=compliance_patterns,
        visualize=visualize
    )
    
    # Determine output
    output_path = args.output or config.get("output_file") or "yoink_output.md"
    
    if output_path == "-":
        sys.stdout.write(packed_md + "\n")
    else:
        out_file = Path(output_path)
        try:
            out_file.parent.mkdir(parents=True, exist_ok=True)
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(packed_md)
            print(f"Successfully yoinked codebase into: {out_file}", file=sys.stderr)
        except Exception as e:
            print(f"Error writing output file: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
