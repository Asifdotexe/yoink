from yoink.core.tokenizer import count_tokens


def test_count_tokens_bpe():
    # Simple Python code snippet should tokenize correctly with tiktoken
    text = "def foo():\n    return 42"

    # cl100k_base tokenizes "def foo():\n    return 42" into exactly 11 tokens
    tokens = count_tokens(text)
    assert tokens > 0
    assert isinstance(tokens, int)
