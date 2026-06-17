from yoink.core.shield import mask_secrets, strip_compliance, generate_pseudonym, censor_content


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


def test_generate_pseudonym():
    p1 = generate_pseudonym("Google")
    p2 = generate_pseudonym("google")
    p3 = generate_pseudonym("Amazon")

    assert p1 == p2
    assert p1 != p3
    assert len(p1) > 0
    
    # Must start with a phonetic alphabet word followed by a number
    letters_part = "".join(c for c in p1 if c.isalpha())
    digits_part = "".join(c for c in p1 if c.isdigit())
    
    from yoink.core.shield import PHONETIC_ALPHABET
    assert letters_part in PHONETIC_ALPHABET
    assert digits_part.isdigit()
    assert int(digits_part) >= 1


def test_censor_content_words():
    google_pseudo = generate_pseudonym("Google")
    
    # Standalone
    res1 = censor_content("Welcome to Google.", censor_words=["Google"])
    assert google_pseudo in res1
    assert "Google" not in res1

    # CamelCase
    res2 = censor_content("class GoogleClient:", censor_words=["Google"])
    assert f"class {google_pseudo}Client:" in res2

    # snake_case
    res3 = censor_content("def query_google_api():", censor_words=["Google"])
    assert f"def query_{google_pseudo}_api():" in res3

    # Inside standard words (should not match)
    res4 = censor_content("We love apple and mapper.", censor_words=["app"])
    assert "apple" in res4
    assert "mapper" in res4


def test_censor_content_domains():
    domain_pseudo = generate_pseudonym("internal.net").lower()
    
    res1 = censor_content("Connect to staging.db.internal.net", censor_domains=["internal.net"])
    assert f"staging.db.{domain_pseudo}.local" in res1

    res2 = censor_content("Root: internal.net", censor_domains=["internal.net"])
    assert f"Root: {domain_pseudo}.local" in res2


def test_censor_content_redacted():
    res1 = censor_content(
        "Welcome to Google at internal.net",
        censor_words=["Google"],
        censor_domains=["internal.net"],
        pseudonym_masking=False
    )
    assert "[REDACTED]" in res1
    assert "[REDACTED_DOMAIN]" in res1
    assert "Google" not in res1
    assert "internal.net" not in res1
