import tiktoken


def count_tokens(text: str) -> int:
    """
    Count the number of tokens in the given text using BPE tokenization (tiktoken)
    with the cl100k_base (GPT-4) vocabulary.
    """
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text, disallowed_special=()))
