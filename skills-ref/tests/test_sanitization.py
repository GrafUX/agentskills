from skills_ref.sanitization import sanitize_error_text, safe_name


def test_sanitize_error_text_strips_ansi():
    ansi_text = "\x1b[31mError:\x1b[0m something went wrong"
    sanitized = sanitize_error_text(ansi_text)
    assert sanitized == "Error: something went wrong"


def test_sanitize_error_text_truncates():
    long_text = "a" * 100
    sanitized = sanitize_error_text(long_text, max_len=10)
    assert sanitized == "a" * 10 + "..."


def test_sanitize_error_text_strips_and_truncates():
    text = "\x1b[31m" + "a" * 50 + "\x1b[0m" + "b" * 50
    sanitized = sanitize_error_text(text, max_len=10)
    assert sanitized == "a" * 10 + "..."


def test_safe_name_truncates():
    long_name = "a" * 100
    sanitized = safe_name(long_name)
    assert len(sanitized) == 67  # 64 + 3 for "..."
    assert sanitized.endswith("...")


def test_sanitize_error_text_no_change():
    text = "Simple error message"
    assert sanitize_error_text(text) == text
