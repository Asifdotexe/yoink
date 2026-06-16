import re

DEFAULT_PATTERNS = {
    "ip_address": r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b",
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "private_key": r"-----BEGIN[ A-Z0-9_-]+PRIVATE KEY-----[^-]+-----END[ A-Z0-9_-]+PRIVATE KEY-----",
    "aws_access_key": r"\b(AKIA|ASCA|ASIA)[0-9A-Z]{16}\b",
    "generic_api_key": r"\b(key|api|secret|token|password|passwd|auth)_?(key|api|secret|token|password|passwd|auth)?\s*[:=]\s*['\"]([a-zA-Z0-9_\-]{16,})['\"]",
}


def mask_secrets(content: str, custom_patterns: dict[str, str] = None) -> str:
    """Mask sensitive keys, private certificates, emails, and IP addresses using regex."""
    patterns = DEFAULT_PATTERNS.copy()
    if custom_patterns:
        patterns.update(custom_patterns)

    masked_content = content

    for label, pattern_str in patterns.items():
        try:
            # Multi-line mode and case insensitivity depends on the target
            flags = re.IGNORECASE
            if "private_key" in label:
                flags |= re.MULTILINE | re.DOTALL

            regex = re.compile(pattern_str, flags)

            if label == "generic_api_key":
                # Only mask the value group to avoid destroying structural syntax (e.g. `api_key = <MASKED>`)
                masked_content = regex.sub(
                    lambda m: m.group(0).replace(m.group(3), f"<{label.upper()}>"),
                    masked_content,
                )
            elif label == "private_key":
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
    """Scrub compliance/IP information (internal domain endpoints, legal entities, trademarks)."""
    # Why: We execute re.sub inline and catch exceptions to prevent malformed or invalid user-defined
    # regex patterns in the config file from halting/crashing the entire codebase packing execution.
    for target_pattern, replacement_descriptor in (compliance_patterns or {}).items():
        try:
            content = re.sub(
                target_pattern, replacement_descriptor, content, flags=re.IGNORECASE
            )
        except Exception:
            pass
    return content
