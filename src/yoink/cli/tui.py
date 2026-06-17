import os
import re
import sys
import json
from pathlib import Path
from yoink.core.shield import generate_pseudonym

# ── Windows UTF-8 Bootstrap ──────────────────────────────────────────────────
# Windows terminals often default to cp1252 which cannot render box-drawing
# or emoji characters.  Force UTF-8 on stdout/stderr before any output.
if os.name == "nt":
    os.system("")                          # enable VT100 escape sequences
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def _supports_unicode() -> bool:
    """Return True when the terminal can render box-drawing and emoji."""
    try:
        "╭".encode(sys.stdout.encoding or "ascii")
        return True
    except (UnicodeEncodeError, LookupError):
        return False


_UNICODE = _supports_unicode()

# ── ANSI Styling ──────────────────────────────────────────────────────────────
RESET      = "\033[0m"
BOLD       = "\033[1m"
DIM        = "\033[2m"
UNDERLINE  = "\033[4m"
CYAN       = "\033[36m"
GREEN      = "\033[32m"
YELLOW     = "\033[33m"
RED        = "\033[31m"
MAGENTA    = "\033[35m"
WHITE      = "\033[97m"
BLUE       = "\033[34m"

# ── Box-Drawing Constants (with ASCII fallbacks) ─────────────────────────────
BOX_TL = "╭" if _UNICODE else "+"
BOX_TR = "╮" if _UNICODE else "+"
BOX_BL = "╰" if _UNICODE else "+"
BOX_BR = "╯" if _UNICODE else "+"
BOX_H  = "─" if _UNICODE else "-"
BOX_V  = "│" if _UNICODE else "|"

# Unicode icons — degrade to plain-text labels on limited terminals.
ICON_SHIELD   = "🛡️ " if _UNICODE else "[*]"
ICON_WORD     = "📝" if _UNICODE else "[W]"
ICON_DOMAIN   = "🌐" if _UNICODE else "[D]"
ICON_TOGGLE   = "⚙️ " if _UNICODE else "[~]"
ICON_EXIT     = "👋" if _UNICODE else "[x]"
ICON_ADD      = "➕" if _UNICODE else "[+]"
ICON_REMOVE   = "🗑️ " if _UNICODE else "[-]"
ICON_CHECK    = "✔" if _UNICODE else "v"
ICON_CROSS    = "✖" if _UNICODE else "x"
ICON_ARROW    = "→" if _UNICODE else "->"
ICON_DOT      = "●" if _UNICODE else "*"
ICON_SPARKLE  = "✦" if _UNICODE else ">"


# Layout width for the main box frame.
BOX_WIDTH = 56


# ── Helper Utilities ──────────────────────────────────────────────────────────

def _box_top() -> str:
    """Render the top edge of a box."""
    return f"{CYAN}{BOX_TL}{BOX_H * BOX_WIDTH}{BOX_TR}{RESET}"


def _box_bottom() -> str:
    """Render the bottom edge of a box."""
    return f"{CYAN}{BOX_BL}{BOX_H * BOX_WIDTH}{BOX_BR}{RESET}"


def _box_row(text: str, align: str = "left") -> str:
    """
    Render a single row of content inside a box frame.

    ANSI codes are stripped for width calculation so columns align correctly
    even when the text contains escape sequences.

    :param text: The visible content of this row.
    :param align: 'left' or 'center'.
    """
    visible = re.sub(r"\033\[[0-9;]*m", "", text)
    padding = max(0, BOX_WIDTH - 2 - len(visible))
    if align == "center":
        left = padding // 2
        right = padding - left
        return f"{CYAN}{BOX_V}{RESET} {' ' * left}{text}{' ' * right} {CYAN}{BOX_V}{RESET}"
    return f"{CYAN}{BOX_V}{RESET} {text}{' ' * padding} {CYAN}{BOX_V}{RESET}"


def _pill(text: str, color: str) -> str:
    """Wrap text in a colored bracket-pill for inline status badges."""
    return f"{color}[{text}]{RESET}"


# ── Core Display Functions ────────────────────────────────────────────────────

def print_header():
    """
    Print a styled box-art header banner for the interactive TUI.

    Uses box-drawing characters and centered text for a polished terminal feel.
    """
    print()
    print(_box_top())
    print(_box_row("", "center"))
    print(_box_row(f"{BOLD}{WHITE}{ICON_SHIELD}  YOINK CENSOR WIZARD{RESET}", "center"))
    print(_box_row(f"{DIM}Active Masking & Shielding Configuration{RESET}", "center"))
    print(_box_row("", "center"))
    print(_box_bottom())
    print()


def print_status(config):
    """
    Display current active censorship configuration in a formatted panel.

    :param config: The configuration dictionary.
    """
    words = config.get("censor_words", [])
    domains = config.get("censor_domains", [])
    pseudo = config.get("pseudonym_masking", True)

    # Status badge
    if pseudo:
        badge = _pill(f"{ICON_CHECK} Pseudonym", GREEN)
    else:
        badge = _pill(f"{ICON_CROSS} Redacted", YELLOW)

    print(f"  {BOLD}{WHITE}Status{RESET}  {badge}")
    print()

    # Words
    if words:
        print(f"  {ICON_WORD}  {BOLD}Censored Words{RESET} {DIM}({len(words)}){RESET}")
        for w in words:
            replacement = generate_pseudonym(w) if pseudo else "[REDACTED]"
            print(f"     {DIM}{ICON_DOT}{RESET} {w} {DIM}{ICON_ARROW}{RESET} {GREEN}{replacement}{RESET}")
    else:
        print(f"  {ICON_WORD}  {BOLD}Censored Words{RESET}  {DIM}(none){RESET}")

    print()

    # Domains
    if domains:
        print(f"  {ICON_DOMAIN}  {BOLD}Censored Domains{RESET} {DIM}({len(domains)}){RESET}")
        for d in domains:
            if pseudo:
                replacement = generate_pseudonym(d).lower() + ".local"
            else:
                replacement = "[REDACTED_DOMAIN]"
            print(f"     {DIM}{ICON_DOT}{RESET} {d} {DIM}{ICON_ARROW}{RESET} {GREEN}{replacement}{RESET}")
    else:
        print(f"  {ICON_DOMAIN}  {BOLD}Censored Domains{RESET}  {DIM}(none){RESET}")

    print()
    print(f"  {DIM}{'─' * 48}{RESET}")
    print()


def print_menu():
    """Print the main action menu with numbered, icon-annotated options."""
    print(f"  {BOLD}{WHITE}Actions{RESET}")
    print()
    print(f"    {BOLD}{CYAN}1{RESET} {DIM}│{RESET} {ICON_ADD}  Add words to censor")
    print(f"    {BOLD}{CYAN}2{RESET} {DIM}│{RESET} {ICON_ADD}  Add domains to censor")
    print(f"    {BOLD}{CYAN}3{RESET} {DIM}│{RESET} {ICON_REMOVE}  Remove a word or domain")
    print(f"    {BOLD}{CYAN}4{RESET} {DIM}│{RESET} {ICON_TOGGLE}  Toggle pseudonym masking")
    print()
    print(f"    {BOLD}{CYAN}0{RESET} {DIM}│{RESET} {ICON_EXIT}  Save & exit")
    print()


def _success(msg: str):
    """Print a green success message."""
    print(f"\n  {GREEN}{ICON_CHECK} {msg}{RESET}\n")


def _warn(msg: str):
    """Print a yellow warning message."""
    print(f"\n  {YELLOW}⚠  {msg}{RESET}\n")


def _error(msg: str):
    """Print a red error message."""
    print(f"\n  {RED}{ICON_CROSS} {msg}{RESET}\n")


def _section(title: str):
    """Print a section divider with a title."""
    print(f"\n  {BOLD}{CYAN}── {title} {'─' * max(1, 40 - len(title))}{RESET}\n")


# ── Config Persistence ────────────────────────────────────────────────────────

def save_config(config_path: Path, config: dict) -> bool:
    """
    Auto-save the active censorship configuration.

    Merges censor fields into any existing config file to preserve
    unrelated settings (e.g. exclude_patterns, output_file).

    :param config_path: Configuration file path.
    :param config: The configuration dict.
    :return: True if the save succeeded, False otherwise.
    """
    try:
        orig_config = {}
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                orig_config = json.load(f)
        orig_config["censor_words"] = config["censor_words"]
        orig_config["censor_domains"] = config["censor_domains"]
        orig_config["pseudonym_masking"] = config["pseudonym_masking"]
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(orig_config, f, indent=2)
        return True
    except Exception as e:
        _error(f"Auto-save failed: {e}")
        return False


# ── Interactive TUI Loop ──────────────────────────────────────────────────────

def run_censor_tui(config_path: Path, target_path: Path):
    """
    Run the interactive TUI loop.

    Allows developers to manage lists of censored words and domains, and toggle
    pseudonym masking settings with automatic configuration saving.

    :param config_path: Path to the target .yoinkconfig.json configuration file.
    :param target_path: Path to the directory or file being packed.
    """
    # Load configuration
    config = {}
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            _warn(f"Could not load {config_path}: {e}. Using defaults.")

    # Ensure lists exist in config
    if "censor_words" not in config:
        config["censor_words"] = []
    if "censor_domains" not in config:
        config["censor_domains"] = []
    if "pseudonym_masking" not in config:
        config["pseudonym_masking"] = True

    while True:
        print_header()
        print_status(config)
        print_menu()

        try:
            choice = input(f"  {BOLD}{CYAN}{ICON_SPARKLE} Select option (0-4):{RESET} ").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n  {DIM}Interrupted. Goodbye!{RESET}\n")
            sys.exit(0)

        if choice == "1":
            _section("Add Words")
            print("  Enter project names, company names, or IP to censor.")
            word_input = input(f"  {DIM}Words (comma-separated):{RESET} ").strip()
            if word_input:
                new_words = [w.strip() for w in word_input.split(",") if w.strip()]
                added_count = 0
                for w in new_words:
                    if w not in config["censor_words"]:
                        config["censor_words"].append(w)
                        added_count += 1
                        if config["pseudonym_masking"]:
                            pseudo = generate_pseudonym(w)
                            print(f"     {GREEN}{ICON_CHECK}{RESET} {w} {DIM}{ICON_ARROW}{RESET} {GREEN}{pseudo}{RESET}")
                        else:
                            print(f"     {GREEN}{ICON_CHECK}{RESET} {w} {DIM}{ICON_ARROW}{RESET} {YELLOW}[REDACTED]{RESET}")
                if added_count > 0:
                    if save_config(config_path, config):
                        _success(f"Added {added_count} word(s) — auto-saved.")
                else:
                    _warn("All words already exist in the list.")
            else:
                _warn("No input provided.")

        elif choice == "2":
            _section("Add Domains")
            print("  Enter internal domain roots (e.g. internal.net, intranet.corp).")
            domain_input = input(f"  {DIM}Domains (comma-separated):{RESET} ").strip()
            if domain_input:
                new_domains = [d.strip() for d in domain_input.split(",") if d.strip()]
                added_count = 0
                for d in new_domains:
                    if d not in config["censor_domains"]:
                        config["censor_domains"].append(d)
                        added_count += 1
                        if config["pseudonym_masking"]:
                            pseudo = generate_pseudonym(d).lower()
                            print(f"     {GREEN}{ICON_CHECK}{RESET} {d} {DIM}{ICON_ARROW}{RESET} {GREEN}*.{pseudo}.local{RESET}")
                        else:
                            print(f"     {GREEN}{ICON_CHECK}{RESET} {d} {DIM}{ICON_ARROW}{RESET} {YELLOW}[REDACTED_DOMAIN]{RESET}")
                if added_count > 0:
                    if save_config(config_path, config):
                        _success(f"Added {added_count} domain(s) — auto-saved.")
                else:
                    _warn("All domains already exist in the list.")
            else:
                _warn("No input provided.")

        elif choice == "3":
            _section("Remove Entry")
            items = []
            for w in config["censor_words"]:
                items.append(("word", w))
            for d in config["censor_domains"]:
                items.append(("domain", d))

            if not items:
                _warn("No active words or domains to remove.")
                continue

            for idx, (type_, name) in enumerate(items, 1):
                tag = _pill("WORD", MAGENTA) if type_ == "word" else _pill("DOMAIN", BLUE)
                print(f"    {BOLD}{CYAN}{idx}{RESET} {DIM}│{RESET} {tag} {name}")

            print()
            try:
                remove_choice = input(f"  {DIM}Select # to remove (Enter to cancel):{RESET} ").strip()
                if not remove_choice:
                    continue
                remove_idx = int(remove_choice) - 1
                if 0 <= remove_idx < len(items):
                    type_, name = items[remove_idx]
                    if type_ == "word":
                        config["censor_words"].remove(name)
                    else:
                        config["censor_domains"].remove(name)
                    if save_config(config_path, config):
                        _success(f"Removed {type_} '{name}' — auto-saved.")
                else:
                    _error("Invalid selection.")
            except ValueError:
                _error("Please enter a valid number.")

        elif choice == "4":
            config["pseudonym_masking"] = not config["pseudonym_masking"]
            if save_config(config_path, config):
                if config["pseudonym_masking"]:
                    _success("Pseudonym masking ENABLED — names get deterministic aliases.")
                else:
                    _warn("Pseudonym masking DISABLED — names will be [REDACTED].")

        elif choice == "0":
            print(f"\n  {DIM}{ICON_EXIT} Goodbye!{RESET}\n")
            sys.exit(0)

        else:
            _error("Invalid option. Please enter 0-4.")


# ── Init Wizard ───────────────────────────────────────────────────────────────

def run_censor_init(config_path: Path):
    """
    Interactively initialize censorship settings.

    Guides the developer through setting up initial list-based words
    and domains to censor and saves the configuration to the JSON file.

    :param config_path: Configuration file path.
    """
    print_header()

    print(f"  {DIM}This wizard will guide you through setting up your{RESET}")
    print(f"  {DIM}active masking rules and saving them to .yoinkconfig.json.{RESET}")
    print(f"  {DIM}Press Ctrl+C at any time to quit.{RESET}")
    print()

    censor_words = []
    censor_domains = []
    pseudonym_masking = True

    try:
        # 1. Prompt for words
        _section("Step 1 — Censor Words")
        print("  Proprietary names, internal projects, company names.")
        print(f"  {DIM}Enter one per line. Empty line to continue.{RESET}")
        print()
        idx = 1
        while True:
            word = input(f"  {DIM}Word {idx}:{RESET} ").strip()
            if not word:
                break
            if word not in censor_words:
                censor_words.append(word)
                idx += 1

        # 2. Prompt for domains
        _section("Step 2 — Censor Domains")
        print("  Internal domain roots (e.g. internal.net, intranet.corp).")
        print(f"  {DIM}Enter one per line. Empty line to continue.{RESET}")
        print()
        idx = 1
        while True:
            domain = input(f"  {DIM}Domain {idx}:{RESET} ").strip()
            if not domain:
                break
            if domain not in censor_domains:
                censor_domains.append(domain)
                idx += 1

        # 3. Prompt for pseudonym masking
        _section("Step 3 — Pseudonym Masking")
        print("  When enabled, censored terms get deterministic aliases")
        print("  instead of generic [REDACTED] tags.")
        print()
        pseudo_input = input(f"  {DIM}Enable Pseudonym Masking? (Y/n):{RESET} ").strip().lower()
        if pseudo_input in ("n", "no", "false"):
            pseudonym_masking = False

        # Load existing config to merge/preserve other fields
        config = {}
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            except Exception as e:
                _warn(f"Could not load {config_path}: {e}. Starting fresh.")

        config["censor_words"] = censor_words
        config["censor_domains"] = censor_domains
        config["pseudonym_masking"] = pseudonym_masking

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        # Summary
        print()
        print(f"  {DIM}{'─' * 48}{RESET}")
        print()
        _success(f"Configuration saved to {config_path}")
        print(f"  {DIM}Words:   {len(censor_words)}{RESET}")
        print(f"  {DIM}Domains: {len(censor_domains)}{RESET}")
        print(f"  {DIM}Mode:    {'Pseudonym' if pseudonym_masking else 'Redacted'}{RESET}")
        print()

    except (KeyboardInterrupt, EOFError):
        print(f"\n  {YELLOW}⚠  Initialization aborted.{RESET}\n")
        sys.exit(1)


# ── Show Command ──────────────────────────────────────────────────────────────

def run_censor_show(config_path: Path):
    """
    Print the active mappings of censored terms to their pseudonyms.

    Loads the configuration from target JSON, resolves deterministic
    pseudonyms for configured terms, and prints them in a formatted table.

    :param config_path: Configuration file path.
    """
    if not config_path.exists():
        _error(f"Configuration file not found at {config_path}.")
        print(f"  {DIM}Run `yoink censor init` first to initialize your settings.{RESET}\n")
        sys.exit(1)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        _error(f"Error loading configuration: {e}")
        sys.exit(1)

    words = config.get("censor_words", [])
    domains = config.get("censor_domains", [])
    pseudo = config.get("pseudonym_masking", True)

    print_header()

    # Status badge
    if pseudo:
        badge = _pill(f"{ICON_CHECK} Pseudonym", GREEN)
    else:
        badge = _pill(f"{ICON_CROSS} Redacted", YELLOW)

    print(f"  {BOLD}{WHITE}Active Masking Rules & Mappings{RESET}  {badge}")
    print(f"  Pseudonym Masking: {GREEN if pseudo else YELLOW}{'Enabled' if pseudo else 'Disabled (Redacted)'}{RESET}")
    print()

    if not words and not domains:
        _warn("No words or domains are currently configured.")
        return

    # Words table
    if words:
        print(f"  {ICON_WORD}  {BOLD}{UNDERLINE}Proprietary Words{RESET}")
        print()
        # Calculate column widths
        max_w = max(len(w) for w in words)
        col_w = max(max_w, 12)
        print(f"    {DIM}{'Original':<{col_w}}   {'Replacement'}{RESET}")
        print(f"    {DIM}{'─' * col_w}   {'─' * 20}{RESET}")
        for w in words:
            replacement = generate_pseudonym(w) if pseudo else "[REDACTED]"
            print(f"    {w:<{col_w}}   {GREEN}{replacement}{RESET}")
        print()

    # Domains table
    if domains:
        print(f"  {ICON_DOMAIN}  {BOLD}{UNDERLINE}Proprietary Domains{RESET}")
        print()
        max_d = max(len(d) for d in domains)
        col_d = max(max_d, 12)
        print(f"    {DIM}{'Original':<{col_d}}   {'Replacement'}{RESET}")
        print(f"    {DIM}{'─' * col_d}   {'─' * 20}{RESET}")
        for d in domains:
            if pseudo:
                replacement = generate_pseudonym(d).lower() + ".local"
            else:
                replacement = "[REDACTED_DOMAIN]"
            print(f"    {d:<{col_d}}   {GREEN}{replacement}{RESET}")
        print()
