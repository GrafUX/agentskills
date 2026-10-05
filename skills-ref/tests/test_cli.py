"""Tests for CLI module."""

import json
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner
import pytest

from skills_ref.cli import main
from skills_ref.errors import SkillError


@pytest.fixture
def runner():
    """Fixture to provide a Click CliRunner."""
    return CliRunner()


@pytest.fixture
def valid_skill_dir(tmp_path):
    """Fixture to provide a valid skill directory."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: my-skill\n"
        "description: A test skill\n"
        "---\n"
        "# My Skill\n"
    )
    return skill_dir


def test_main_help(runner):
    """Test main entry point help message."""
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Reference library for Agent Skills" in result.output
    assert "validate" in result.output
    assert "read-properties" in result.output
    assert "to-prompt" in result.output


def test_validate_valid_skill(runner, valid_skill_dir):
    """Test validating a valid skill directory."""
    result = runner.invoke(main, ["validate", str(valid_skill_dir)])
    assert result.exit_code == 0
    assert "Valid skill: my-skill" in result.output


def test_validate_valid_skill_file(runner, valid_skill_dir):
    """Test validating passing skill.md file directly."""
    result = runner.invoke(main, ["validate", str(valid_skill_dir / "SKILL.md")])
    assert result.exit_code == 0
    assert "Valid skill: my-skill" in result.output


def test_validate_invalid_skill(runner, tmp_path):
    """Test validating an invalid skill directory."""
    invalid_dir = tmp_path / "invalid-skill"
    invalid_dir.mkdir()
    (invalid_dir / "SKILL.md").write_text(
        "---\n"
        "name: wrong_name\n"  # Invalid name for directory invalid-skill
        "description: A test skill\n"
        "---\n"
        "# My Skill\n"
    )
    result = runner.invoke(main, ["validate", str(invalid_dir)])
    assert result.exit_code == 1
    assert "Validation failed for invalid-skill" in result.output


@patch("skills_ref.cli.validate")
def test_validate_unexpected_exception(mock_validate, runner, valid_skill_dir):
    """Test validate command handling unexpected exception."""
    mock_validate.side_effect = Exception("Boom")
    result = runner.invoke(main, ["validate", str(valid_skill_dir)])
    assert result.exit_code == 1
    assert "An unexpected error occurred validating my-skill" in result.output


def test_read_properties_success(runner, valid_skill_dir):
    """Test read-properties command on a valid skill."""
    result = runner.invoke(main, ["read-properties", str(valid_skill_dir)])
    assert result.exit_code == 0
    props = json.loads(result.output)
    assert props["name"] == "my-skill"
    assert props["description"] == "A test skill"


def test_read_properties_skill_md_file(runner, valid_skill_dir):
    """Test read-properties command passing skill.md file directly."""
    result = runner.invoke(main, ["read-properties", str(valid_skill_dir / "SKILL.md")])
    assert result.exit_code == 0
    props = json.loads(result.output)
    assert props["name"] == "my-skill"
    assert props["description"] == "A test skill"


@patch("skills_ref.cli.read_properties")
def test_read_properties_skill_error(mock_read_properties, runner, valid_skill_dir):
    """Test read-properties handling a SkillError."""
    mock_read_properties.side_effect = SkillError("Custom parse error")
    result = runner.invoke(main, ["read-properties", str(valid_skill_dir)])
    assert result.exit_code == 1
    assert "Error: Custom parse error" in result.output


@patch("skills_ref.cli.read_properties")
def test_read_properties_unexpected_error(mock_read_properties, runner, valid_skill_dir):
    """Test read-properties handling an unexpected exception."""
    mock_read_properties.side_effect = Exception("Boom")
    result = runner.invoke(main, ["read-properties", str(valid_skill_dir)])
    assert result.exit_code == 1
    assert "An unexpected error occurred reading properties for my-skill" in result.output


def test_to_prompt_success(runner, valid_skill_dir):
    """Test to-prompt command on a valid skill."""
    result = runner.invoke(main, ["to-prompt", str(valid_skill_dir)])
    assert result.exit_code == 0
    assert "<available_skills>" in result.output
    assert "<skill>" in result.output
    assert "my-skill" in result.output
    assert "A test skill" in result.output
    assert "</available_skills>" in result.output


def test_to_prompt_multiple_skills_and_files(runner, valid_skill_dir, tmp_path):
    """Test to-prompt passing multiple directories and SKILL.md files."""
    skill2_dir = tmp_path / "skill-two"
    skill2_dir.mkdir()
    (skill2_dir / "SKILL.md").write_text(
        "---\n"
        "name: skill-two\n"
        "description: Another skill\n"
        "---\n"
        "# Skill Two\n"
    )

    result = runner.invoke(
        main, ["to-prompt", str(valid_skill_dir), str(skill2_dir / "SKILL.md")]
    )
    assert result.exit_code == 0
    assert "my-skill" in result.output
    assert "skill-two" in result.output


@patch("skills_ref.cli.to_prompt")
def test_to_prompt_skill_error(mock_to_prompt, runner, valid_skill_dir):
    """Test to-prompt handling a SkillError."""
    mock_to_prompt.side_effect = SkillError("Custom prompt error")
    result = runner.invoke(main, ["to-prompt", str(valid_skill_dir)])
    assert result.exit_code == 1
    assert "Error: Custom prompt error" in result.output


@patch("skills_ref.cli.to_prompt")
def test_to_prompt_unexpected_error(mock_to_prompt, runner, valid_skill_dir):
    """Test to-prompt handling an unexpected exception."""
    mock_to_prompt.side_effect = Exception("Boom")
    result = runner.invoke(main, ["to-prompt", str(valid_skill_dir)])
    assert result.exit_code == 1
    assert "An unexpected error occurred generating prompts" in result.output
