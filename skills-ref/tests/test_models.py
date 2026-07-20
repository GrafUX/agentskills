"""Tests for data models."""

from skills_ref.models import SkillProperties


def test_to_dict_minimal():
    """Test to_dict with only required fields (name and description)."""
    props = SkillProperties(name="test-skill", description="A simple test skill")
    expected = {
        "name": "test-skill",
        "description": "A simple test skill",
    }
    assert props.to_dict() == expected


def test_to_dict_partial_optional():
    """Test to_dict with some optional fields populated and some None."""
    props = SkillProperties(
        name="test-skill",
        description="A simple test skill",
        license="MIT",
    )
    expected = {
        "name": "test-skill",
        "description": "A simple test skill",
        "license": "MIT",
    }
    assert props.to_dict() == expected


def test_to_dict_full():
    """Test to_dict with all fields, including metadata and allowed-tools (mapped properly)."""
    props = SkillProperties(
        name="test-skill",
        description="A simple test skill",
        license="MIT",
        compatibility=">=1.0.0",
        allowed_tools="Bash(git:*)",
        metadata={"author": "Jules", "version": "1.0.0"},
    )
    expected = {
        "name": "test-skill",
        "description": "A simple test skill",
        "license": "MIT",
        "compatibility": ">=1.0.0",
        "allowed-tools": "Bash(git:*)",
        "metadata": {"author": "Jules", "version": "1.0.0"},
    }
    assert props.to_dict() == expected


def test_to_dict_empty_metadata():
    """Test to_dict when metadata is explicitly empty dict (should be omitted)."""
    props = SkillProperties(
        name="test-skill",
        description="A simple test skill",
        metadata={},
    )
    expected = {
        "name": "test-skill",
        "description": "A simple test skill",
    }
    assert props.to_dict() == expected
