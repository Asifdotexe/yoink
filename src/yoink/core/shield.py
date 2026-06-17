import hashlib
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


PHONETIC_ALPHABET = [
    "Alpha",
    "Bravo",
    "Char",
    "Delta",
    "Echo",
    "Fox",
    "Golf",
    "Hotel",
    "India",
    "Jay",
    "Kilo",
    "Lima",
    "Mike",
    "Nova",
    "Oscar",
    "Papa",
    "Queen",
    "Romeo",
    "Star",
    "Tango",
    "Unit",
    "Volt",
    "West",
    "Xray",
    "Yoink",
    "Zulu",
]


_PSEUDONYM_CACHE = {}
_CENSOR_REGEX_CACHE = {}
_DOMAIN_REGEX_CACHE = {}


def generate_pseudonym(word: str) -> str:
    """
    Generate a deterministic token-efficient pseudonym based on an input word.

    Combines a NATO phonetic alphabet word and a number (1-99) by hashing the
    lowercase input value to ensure process-independent consistency.

    :param word: The raw word string to obfuscate.
    :return: A CamelCase pseudonym string (e.g. "Alpha1").
    """
    normalized = word.lower().strip()
    if not normalized:
        return "Codenamed0"
    if normalized not in _PSEUDONYM_CACHE:
        h_bytes = hashlib.sha256(normalized.encode("utf-8")).digest()
        alphabet_idx = int.from_bytes(h_bytes[:4], "big") % len(PHONETIC_ALPHABET)
        num = (int.from_bytes(h_bytes[4:8], "big") % 99) + 1
        _PSEUDONYM_CACHE[normalized] = f"{PHONETIC_ALPHABET[alphabet_idx]}{num}"
    return _PSEUDONYM_CACHE[normalized]


def _get_censor_regex(word: str) -> re.Pattern:
    """
    Pre-compile or retrieve cached regex pattern for censor word matching.

    :param word: The word to match.
    :return: Compiled regex pattern.
    """
    if word not in _CENSOR_REGEX_CACHE:
        _CENSOR_REGEX_CACHE[word] = re.compile(re.escape(word), re.IGNORECASE)
    return _CENSOR_REGEX_CACHE[word]


def _get_domain_regex(domain: str) -> re.Pattern:
    """
    Pre-compile or retrieve cached regex pattern for censor domain matching.

    :param domain: The domain to match.
    :return: Compiled regex pattern.
    """
    if domain not in _DOMAIN_REGEX_CACHE:
        _DOMAIN_REGEX_CACHE[domain] = re.compile(
            r"\b([a-zA-Z0-9.-]+\.)?" + re.escape(domain) + r"\b", re.IGNORECASE
        )
    return _DOMAIN_REGEX_CACHE[domain]


def censor_content(
    content: str,
    censor_words: list[str] = None,
    censor_domains: list[str] = None,
    pseudonym_masking: bool = True,
) -> str:
    """
    Scrub specified words and domains using list-based configurations.

    Applies boundary-aware word replacement (including snake_case and CamelCase)
    and subdomain-preserving domain obfuscation.

    :param content: Raw text content.
    :param censor_words: List of specific words/identifiers to replace.
    :param censor_domains: List of domain names to replace.
    :param pseudonym_masking: True to use CamelCase pseudonyms; False to use [REDACTED].
    :return: Sanitized content.
    """
    # 1. Censor specific words/identifiers
    for word in censor_words or []:
        if not word.strip():
            continue

        replacement = generate_pseudonym(word) if pseudonym_masking else "[REDACTED]"
        pattern = _get_censor_regex(word)

        def replace_callback(match):
            matched_str = match.group(0)
            start_idx = match.start()
            end_idx = match.end()

            pre_char = content[start_idx - 1] if start_idx > 0 else None
            post_char = content[end_idx] if end_idx < len(content) else None

            prefix_ok = False
            if pre_char is None or not pre_char.isalnum():
                prefix_ok = True
            elif pre_char.islower() and matched_str[0].isupper():
                prefix_ok = True

            suffix_ok = False
            if post_char is None or not post_char.isalnum():
                suffix_ok = True
            elif matched_str[-1].islower() and post_char.isupper():
                suffix_ok = True

            if prefix_ok and suffix_ok:
                return replacement
            return matched_str

        content = pattern.sub(replace_callback, content)

    # 2. Censor domains (preserving subdomains if using pseudonyms)
    for domain in censor_domains or []:
        if not domain.strip():
            continue

        pattern = _get_domain_regex(domain)
        if pseudonym_masking:
            pseudonym = generate_pseudonym(domain)
            replacement = r"\g<1>" + pseudonym.lower() + ".local"
        else:
            replacement = "[REDACTED_DOMAIN]"

        content = pattern.sub(replacement, content)

    return content
