"""Tests for error classes in errors.py."""

from skills_ref.errors import ParseError, SkillError, ValidationError


def test_skill_error():
    """Test that SkillError inherits from Exception and is instantiated correctly."""
    err = SkillError("Skill error occurred")
    assert isinstance(err, Exception)
    assert str(err) == "Skill error occurred"


def test_parse_error():
    """Test that ParseError inherits from SkillError and is instantiated correctly."""
    err = ParseError("Parsing failed")
    assert isinstance(err, SkillError)
    assert str(err) == "Parsing failed"


def test_validation_error_default_errors():
    """Test ValidationError initialization with default errors list."""
    err = ValidationError("Validation failed")
    assert isinstance(err, SkillError)
    assert str(err) == "Validation failed"
    assert err.errors == ["Validation failed"]


def test_validation_error_custom_errors():
    """Test ValidationError initialization with custom errors list."""
    custom_errors = ["Error 1", "Error 2"]
    err = ValidationError("Validation failed", errors=custom_errors)
    assert isinstance(err, SkillError)
    assert str(err) == "Validation failed"
    assert err.errors == custom_errors
