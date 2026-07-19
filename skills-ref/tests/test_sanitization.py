import pytest
from pathlib import Path
from skills_ref.parser import (
    _sanitize_error_text,
    _safe_name,
    read_properties,
    ParseError,
)
from skills_ref.validator import validate
from skills_ref.prompt import to_prompt
from skills_ref.errors import SkillError


def test_sanitize_error_text_ansi_escape():
    """Test that ANSI escape sequences are completely stripped."""
    text_with_ansi = "\x1b[31mError:\x1b[0m Something went \x1b[1mwrong\x1b[0m"
    sanitized = _sanitize_error_text(text_with_ansi)
    assert "Error: Something went wrong" == sanitized


def test_sanitize_error_text_control_characters():
    """Test that unprintable control characters are removed, but standard whitespace is preserved."""
    text_with_control = "Line 1\nLine 2\r\t\x00\x08secret"
    sanitized = _sanitize_error_text(text_with_control)
    assert "Line 1\nLine 2\r\tsecret" == sanitized


def test_safe_name_truncation():
    """Test that safe_name truncates strings longer than max_len."""
    long_name = "a" * 100
    safe = _safe_name(long_name)
    assert len(safe) == 67  # 64 + len("...")
    assert safe.endswith("...")
    assert safe == "a" * 64 + "..."


def test_safe_name_custom_truncation_limit():
    """Test safe_name with custom truncation limit."""
    long_name = "a" * 100
    safe = _safe_name(long_name, max_len=10)
    assert len(safe) == 13  # 10 + len("...")
    assert safe == "a" * 10 + "..."


def test_safe_name_ansi_and_truncation():
    """Test safe_name strips ANSI escapes first, then truncates."""
    long_name_with_ansi = "\x1b[32m" + "a" * 100 + "\x1b[0m"
    safe = _safe_name(long_name_with_ansi, max_len=50)
    assert len(safe) == 53  # 50 + len("...")
    assert "\x1b" not in safe
    assert safe == "a" * 50 + "..."


def test_parser_error_uses_safe_name(tmp_path):
    """Test that ParseError in read_properties reflects a sanitized/truncated directory name."""
    long_dir_name = "a" * 100 + "\x1b[31mred\x1b[0m"
    skill_dir = tmp_path / long_dir_name
    skill_dir.mkdir()

    # SKILL.md is missing, which triggers ParseError
    with pytest.raises(ParseError) as exc_info:
        read_properties(skill_dir)

    error_str = str(exc_info.value)
    assert "SKILL.md not found in" in error_str
    # Verify the directory name is sanitized and truncated in the error
    assert "\x1b" not in error_str
    assert "..." in error_str
    assert "a" * 64 in error_str


def test_frontmatter_key_reflection_is_sanitized_and_truncated():
    """Test that frontmatter keys reflected in ParseError are sanitized and truncated."""
    from skills_ref.parser import parse_frontmatter
    from skills_ref.constants import MAX_FRONTMATTER_VALUE_LENGTH

    # Test key exceeds limit with clean but long key
    over_limit_key = "a" * 120
    content_key_over = f"""---
{over_limit_key}: short_value
---
Body
"""
    with pytest.raises(ParseError) as exc_info:
        parse_frontmatter(content_key_over)

    error_str = str(exc_info.value)
    assert "Frontmatter key '" in error_str
    assert "exceeds" in error_str
    assert "..." in error_str
    # Truncation limit in _safe_name should be 100 for display_key, so 100 'a's + "..."
    assert "a" * 100 in error_str
    assert "a" * 101 not in error_str

    # Test value exceeds limit with normal key
    key = "my_key"
    over_limit_value = "v" * (MAX_FRONTMATTER_VALUE_LENGTH + 1)
    content_val_over = f"""---
{key}: {over_limit_value}
---
Body
"""
    with pytest.raises(ParseError) as exc_info:
        parse_frontmatter(content_val_over)

    error_str = str(exc_info.value)
    assert "Frontmatter value for 'my_key' exceeds" in error_str


def test_validator_error_uses_safe_name(tmp_path):
    """Test that validation errors in validate() reflect a sanitized/truncated directory name."""
    long_dir_name = "a" * 100 + "\x1b[31mred\x1b[0m"
    skill_dir = tmp_path / long_dir_name

    # Path does not exist, triggers validation error
    errors = validate(skill_dir)
    assert len(errors) == 1
    error_str = errors[0]
    assert "Path does not exist:" in error_str
    assert "\x1b" not in error_str
    assert "..." in error_str
    assert "a" * 64 in error_str


def test_prompt_error_uses_safe_name(tmp_path, monkeypatch):
    """Test that prompt exceptions in to_prompt() reflect a sanitized/truncated directory name when resolve fails."""
    long_dir_name = "a" * 100 + "\x1b[31mred\x1b[0m"
    skill_dir = tmp_path / long_dir_name

    # Mock Path.resolve to raise OSError
    original_resolve = Path.resolve

    def mock_resolve(self, *args, **kwargs):
        if self.name == long_dir_name:
            raise OSError("Permission denied")
        return original_resolve(self, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", mock_resolve)

    with pytest.raises(SkillError) as exc_info:
        to_prompt([skill_dir])

    error_str = str(exc_info.value)
    assert "Failed to process skill directory" in error_str
    assert "\x1b" not in error_str
    assert "..." in error_str
    assert "a" * 64 in error_str
