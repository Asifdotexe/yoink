import re

DEFAULT_PATTERNS = {
    "ip_address": r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b",
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "private_key": r"-----BEGIN[ A-Z0-9_-]+PRIVATE KEY-----[^-]+-----END[ A-Z0-9_-]+PRIVATE KEY-----",
    "aws_access_key": r"\b(AKIA|ASCA|ASIA)[0-9A-Z]{16}\b",
    "generic_api_key": r"\b(key|api|secret|token|password|passwd|auth)_?(key|api|secret|token|password|passwd|auth)?\s*[:=]\s*['\"]([a-zA-Z0-9_\-]{16,})['\"]",
}

# We pre-compile default regex patterns at the module level to avoid the
# CPU overhead of compiling patterns repeatedly on every scanned file.
_COMPILED_DEFAULT_PATTERNS = {
    "ip_address": re.compile(DEFAULT_PATTERNS["ip_address"], re.IGNORECASE),
    "email": re.compile(DEFAULT_PATTERNS["email"], re.IGNORECASE),
    "private_key": re.compile(
        DEFAULT_PATTERNS["private_key"], re.IGNORECASE | re.MULTILINE | re.DOTALL
    ),
    "aws_access_key": re.compile(DEFAULT_PATTERNS["aws_access_key"], re.IGNORECASE),
    "generic_api_key": re.compile(DEFAULT_PATTERNS["generic_api_key"], re.IGNORECASE),
}


def mask_secrets(content: str, custom_patterns: dict[str, str] = None) -> str:
    """
    Mask sensitive keys, certificates, email addresses, and IPs.

    Applies pre-compiled default patterns and compiles any additional custom
    patterns on the fly. Wraps custom compiles in a try-catch block to prevent
    malformed user-provided regular expressions from crashing the packer.

    :param content: Raw text content of the file.
    :param custom_patterns: Dictionary mapping custom labels to regex strings.
    :return: Sanitized content with sensitive information masked.
    """
    patterns = _COMPILED_DEFAULT_PATTERNS.copy()
    if custom_patterns:
        for label, pattern_str in custom_patterns.items():
            try:
                flags = re.IGNORECASE
                if "private_key" in label:
                    flags |= re.MULTILINE | re.DOTALL
                patterns[label] = re.compile(pattern_str, flags)
            except Exception:
                pass

    masked_content = content

    for label, regex in patterns.items():
        try:
            if not isinstance(regex, re.Pattern):
                continue

            if label == "generic_api_key":
                # We target and replace only the secret value match group
                # (group 3) instead of replacing the entire matched string.
                # This preserves surrounding code structure (e.g. `api_key = `).
                masked_content = regex.sub(
                    lambda m: m.group(0).replace(m.group(3), f"<{label.upper()}>"),
                    masked_content,
                )
            elif label == "private_key":
                # Replaces full private keys with standard header blocks
                # to keep formatting uniform.
                masked_content = regex.sub(
                    lambda m: (
                        f"-----BEGIN PRIVATE KEY-----\n<{label.upper()}>\n-----END PRIVATE KEY-----"
                    ),
                    masked_content,
                )
            else:
                masked_content = regex.sub(
                    lambda m: f"<{label.upper()}>", masked_content
                )
        except Exception:
            pass

    return masked_content


def strip_compliance(content: str, compliance_patterns: dict[str, str] = None) -> str:
    """
    Scrub corporate and compliance identifiers.

    Matches IP rules, trademarks, legal entities, or internal domains
    and replaces them with custom labels. Executed in a try-catch block
    to prevent invalid configuration patterns from crashing the run.

    :param content: Raw text content of the file.
    :param compliance_patterns: Mapping of regex target pattern to replacement.
    :return: Cleaned text content.
    """
    for target_pattern, replacement_descriptor in (compliance_patterns or {}).items():
        try:
            content = re.sub(
                target_pattern, replacement_descriptor, content, flags=re.IGNORECASE
            )
        except Exception:
            pass
    return content
