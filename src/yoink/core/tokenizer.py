import tiktoken

# We pre-cache the encoding instance globally at the module level to avoid
# the overhead of querying the C++ registry cache of tiktoken on every
# token count call during the scan.
_ENCODING = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """
    Count the number of tokens in the given text using BPE tokenization.

    Uses the cl100k_base (GPT-4) vocabulary to calculate approximate token consumption
    for the final LLM prompt payload.

    :param text: The text content to tokenize and count.
    :return: The total number of tokens in the text.
    """
    return len(_ENCODING.encode(text, disallowed_special=()))
