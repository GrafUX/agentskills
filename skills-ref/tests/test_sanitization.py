from skills_ref.parser import _sanitize_error_text, _safe_name


def test_sanitize_error_text_strips_ansi():
    ansi_text = "\x1b[31mError:\x1b[0m something went wrong"
    sanitized = _sanitize_error_text(ansi_text)
    assert sanitized == "Error: something went wrong"


def test_sanitize_error_text_truncates():
    long_text = "a" * 100
    sanitized = _sanitize_error_text(long_text, max_len=10)
    assert sanitized == "a" * 10 + "..."


def test_sanitize_error_text_strips_and_truncates():
    text = "\x1b[31m" + "a" * 50 + "\x1b[0m" + "b" * 50
    sanitized = _sanitize_error_text(text, max_len=10)
    assert sanitized == "a" * 10 + "..."


def test_safe_name_truncates():
    long_name = "a" * 100
    sanitized = _safe_name(long_name)
    assert len(sanitized) == 67  # 64 + 3 for "..."
    assert sanitized.endswith("...")


def test_sanitize_error_text_no_change():
    text = "Simple error message"
    assert _sanitize_error_text(text) == text
