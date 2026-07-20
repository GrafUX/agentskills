"""Tests for models module."""

from skills_ref.models import SkillProperties


def test_skill_properties_to_dict_minimal():
    """Test that to_dict() only includes name and description when other fields are empty/None."""
    props = SkillProperties(
        name="test-skill",
        description="A minimal test skill",
    )
    result = props.to_dict()
    assert result == {
        "name": "test-skill",
        "description": "A minimal test skill",
    }


def test_skill_properties_to_dict_full():
    """Test that to_dict() includes all fields when they are fully populated."""
    props = SkillProperties(
        name="test-skill",
        description="A full test skill",
        license="MIT",
        compatibility=">=1.0.0",
        allowed_tools="Bash(git:*)",
        metadata={"author": "Jules", "version": "1.2.3"},
    )
    result = props.to_dict()
    assert result == {
        "name": "test-skill",
        "description": "A full test skill",
        "license": "MIT",
        "compatibility": ">=1.0.0",
        "allowed-tools": "Bash(git:*)",
        "metadata": {"author": "Jules", "version": "1.2.3"},
    }


def test_skill_properties_to_dict_partial():
    """Test that to_dict() only includes the populated optional fields."""
    props1 = SkillProperties(
        name="test-skill-1",
        description="Partial test skill 1",
        license="Apache-2.0",
    )
    assert props1.to_dict() == {
        "name": "test-skill-1",
        "description": "Partial test skill 1",
        "license": "Apache-2.0",
    }

    props2 = SkillProperties(
        name="test-skill-2",
        description="Partial test skill 2",
        compatibility="any",
    )
    assert props2.to_dict() == {
        "name": "test-skill-2",
        "description": "Partial test skill 2",
        "compatibility": "any",
    }

    props3 = SkillProperties(
        name="test-skill-3",
        description="Partial test skill 3",
        allowed_tools="test-tool",
    )
    assert props3.to_dict() == {
        "name": "test-skill-3",
        "description": "Partial test skill 3",
        "allowed-tools": "test-tool",
    }

    props4 = SkillProperties(
        name="test-skill-4",
        description="Partial test skill 4",
        metadata={"key": "val"},
    )
    assert props4.to_dict() == {
        "name": "test-skill-4",
        "description": "Partial test skill 4",
        "metadata": {"key": "val"},
    }
