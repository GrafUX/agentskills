"""Tests for models module."""

from skills_ref.models import SkillProperties


def test_skill_properties_minimal_init():
    """Test SkillProperties instantiation with only required parameters."""
    props = SkillProperties(name="test-skill", description="A test skill description")
    assert props.name == "test-skill"
    assert props.description == "A test skill description"
    assert props.license is None
    assert props.compatibility is None
    assert props.allowed_tools is None
    assert props.metadata == {}


def test_skill_properties_full_init():
    """Test SkillProperties instantiation with all parameters."""
    props = SkillProperties(
        name="test-skill",
        description="A test skill description",
        license="MIT",
        compatibility=">=1.0.0",
        allowed_tools="Bash(git:*)",
        metadata={"key": "value"},
    )
    assert props.name == "test-skill"
    assert props.description == "A test skill description"
    assert props.license == "MIT"
    assert props.compatibility == ">=1.0.0"
    assert props.allowed_tools == "Bash(git:*)"
    assert props.metadata == {"key": "value"}


def test_to_dict_minimal():
    """Test to_dict with minimal parameters (only required)."""
    props = SkillProperties(name="test-skill", description="A test skill description")
    expected = {
        "name": "test-skill",
        "description": "A test skill description",
    }
    assert props.to_dict() == expected


def test_to_dict_full():
    """Test to_dict with all parameters populated."""
    props = SkillProperties(
        name="test-skill",
        description="A test skill description",
        license="MIT",
        compatibility=">=1.0.0",
        allowed_tools="Bash(git:*)",
        metadata={"key": "value"},
    )
    expected = {
        "name": "test-skill",
        "description": "A test skill description",
        "license": "MIT",
        "compatibility": ">=1.0.0",
        "allowed-tools": "Bash(git:*)",
        "metadata": {"key": "value"},
    }
    assert props.to_dict() == expected


def test_to_dict_some_optional():
    """Test to_dict with some optional parameters but not all."""
    props = SkillProperties(
        name="test-skill",
        description="A test skill description",
        license="MIT",
    )
    expected = {
        "name": "test-skill",
        "description": "A test skill description",
        "license": "MIT",
    }
    assert props.to_dict() == expected
