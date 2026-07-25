from pathlib import Path

import pytest

from skills_ref.errors import SkillError
from skills_ref.parser import (
    ParseError,
    _safe_name,
    _sanitize_error_text,
    parse_frontmatter,
    read_properties,
)
from skills_ref.prompt import to_prompt
from skills_ref.validator import validate, validate_metadata


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


def test_sanitize_error_text_removes_del_and_c1_controls():
    """Test that DEL and C1 control characters are removed."""
    text_with_controls = "prefix\x7fmiddle\x9b[31msuffix"
    sanitized = _sanitize_error_text(text_with_controls)
    assert sanitized == "prefixmiddle[31msuffix"


def test_safe_name_replaces_newlines_and_tabs():
    """Test that safe_name replaces newlines, carriage returns, and tabs with spaces."""
    name_with_whitespaces = "my\nname\rwith\ttabs"
    safe = _safe_name(name_with_whitespaces)
    assert safe == "my name with tabs"


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


def test_validate_unexpected_fields_ansi_and_control_characters_sanitized():
    """Test that validation errors for unexpected fields sanitize/escape newlines, control characters, and ANSI escapes."""
    metadata = {
        "name": "valid-name",
        "description": "valid description",
        "unexpected\nkey\x1b[31mred\x1b[0m": "value",
    }
    errors = validate_metadata(metadata)
    assert len(errors) > 0
    err_str = errors[0]
    assert "Unexpected fields in frontmatter:" in err_str
    assert "\x1b" not in err_str
    assert "\n" not in err_str
    assert "unexpected keyred" in err_str


def test_validate_unexpected_fields_truncation():
    """Test that validation errors for unexpected fields truncate extremely long unexpected field names."""
    long_key = "x" * 150
    metadata = {
        "name": "valid-name",
        "description": "valid description",
        long_key: "value",
    }
    errors = validate_metadata(metadata)
    assert len(errors) > 0
    err_str = errors[0]
    assert "Unexpected fields in frontmatter:" in err_str
    assert "x" * 100 + "..." in err_str


def test_parse_frontmatter_invalid_yaml_ansi():
    """Test that ParseError in parse_frontmatter sanitizes invalid YAML error messages containing ANSI sequences."""
    content = "---\nname: \x1b[31minvalid\x1b[0m\n---\nbody"
    with pytest.raises(ParseError) as exc_info:
        parse_frontmatter(content)

    error_str = str(exc_info.value)
    assert "Invalid YAML in frontmatter:" in error_str
    assert "\x1b" not in error_str
    assert "[31m" not in error_str


def test_parse_frontmatter_key_too_long_ansi(monkeypatch):
    """Test that ParseError in parse_frontmatter sanitizes frontmatter key with ANSI sequence."""
    long_key_with_ansi = "\x1b[31mred\x1b[0m" + "x" * 110

    class MockParsed:
        def __init__(self):
            self.data = {long_key_with_ansi: "value"}

    monkeypatch.setattr("strictyaml.load", lambda *args, **kwargs: MockParsed())

    with pytest.raises(ParseError) as exc_info:
        parse_frontmatter("---\nfoo: bar\n---\nbody")

    error_str = str(exc_info.value)
    assert "Frontmatter key '" in error_str
    assert "\x1b" not in error_str
    assert "..." in error_str
    assert "red" in error_str


def test_validate_name_ansi_sanitized():
    """Test that validate_metadata sanitizes invalid skill name with ANSI sequences."""
    metadata = {
        "name": "Invalid-Name\x1b[31mred\x1b[0m",
        "description": "test description",
    }
    errors = validate_metadata(metadata)
    assert len(errors) > 0
    # Any error message referencing the name should have the ANSI sequence stripped
    for err in errors:
        assert "\x1b" not in err
        assert "red" in err


def test_validate_metadata_key_ansi_sanitized():
    """Test that validate_metadata sanitizes custom metadata keys with ANSI sequences."""
    long_key_with_ansi = "\x1b[31mred\x1b[0m" + "x" * 110
    metadata = {
        "name": "valid-name",
        "description": "test description",
        "metadata": {long_key_with_ansi: "value"},
    }
    errors = validate_metadata(metadata)
    assert len(errors) > 0
    # Any error message referencing the metadata key should have the ANSI sequence stripped
    for err in errors:
        if "Metadata key" in err:
            assert "\x1b" not in err
            assert "red" in err
            assert "..." in err


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
