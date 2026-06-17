from yoink.core.shield import mask_secrets, strip_compliance


def test_ip_masking():
    content = "Connecting to database at 192.168.1.50 and backup at 10.0.0.1"
    masked = mask_secrets(content)
    assert "192.168.1.50" not in masked
    assert "10.0.0.1" not in masked
    assert "<IP_ADDRESS>" in masked


def test_generic_api_key_masking():
    content = 'api_key = "abc123xyz7890123456"'
    masked = mask_secrets(content)
    assert "abc123xyz7890123456" not in masked
    assert 'api_key = "<GENERIC_API_KEY>"' in masked


def test_strip_compliance():
    content = "Welcome to YoinkCorp. Connect at db.internal.net."
    compliance = {
        r"\bYoinkCorp\b": "[COMPANY]",
        r"\b[a-zA-Z0-9.-]+\.internal\.net\b": "[PROPRIETARY_ENDPOINT]",
    }
    stripped = strip_compliance(content, compliance)
    assert "YoinkCorp" not in stripped
    assert "db.internal.net" not in stripped
    assert "Welcome to [COMPANY]. Connect at [PROPRIETARY_ENDPOINT]." in stripped
