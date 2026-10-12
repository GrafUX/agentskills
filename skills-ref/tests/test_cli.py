"""Tests for CLI module."""

import json
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from skills_ref.cli import main
from skills_ref.errors import SkillError
from skills_ref.models import SkillProperties


@pytest.fixture
def runner():
    return CliRunner()


def test_validate_cmd_success(runner, tmp_path):
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()

    with patch("skills_ref.cli.validate", return_value=[]) as mock_validate:
        result = runner.invoke(main, ["validate", str(skill_dir)])

        assert result.exit_code == 0
        assert "Valid skill: my-skill" in result.output
        mock_validate.assert_called_once_with(skill_dir)


def test_validate_cmd_skill_md_file(runner, tmp_path):
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    skill_file = skill_dir / "SKILL.md"
    skill_file.touch()

    with patch("skills_ref.cli.validate", return_value=[]) as mock_validate:
        result = runner.invoke(main, ["validate", str(skill_file)])

        assert result.exit_code == 0
        assert "Valid skill: my-skill" in result.output
        mock_validate.assert_called_once_with(skill_dir)


def test_validate_cmd_errors(runner, tmp_path):
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()

    with patch(
        "skills_ref.cli.validate",
        return_value=["Name is too long", "Missing required field"],
    ):
        result = runner.invoke(main, ["validate", str(skill_dir)])

        assert result.exit_code == 1
        assert "Validation failed for my-skill" in result.output
        assert "- Name is too long" in result.output
        assert "- Missing required field" in result.output


def test_validate_cmd_unexpected_error(runner, tmp_path):
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()

    with patch("skills_ref.cli.validate", side_effect=RuntimeError("Boom")):
        result = runner.invoke(main, ["validate", str(skill_dir)])

        assert result.exit_code == 1
        assert "An unexpected error occurred validating my-skill" in result.output


def test_read_properties_cmd_success(runner, tmp_path):
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()

    mock_props = SkillProperties(name="my-skill", description="A test skill")

    with patch("skills_ref.cli.read_properties", return_value=mock_props) as mock_read:
        result = runner.invoke(main, ["read-properties", str(skill_dir)])

        assert result.exit_code == 0
        mock_read.assert_called_once_with(skill_dir)
        output_json = json.loads(result.output)
        assert output_json["name"] == "my-skill"
        assert output_json["description"] == "A test skill"


def test_read_properties_cmd_skill_md_file(runner, tmp_path):
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    skill_file = skill_dir / "SKILL.md"
    skill_file.touch()

    mock_props = SkillProperties(name="my-skill", description="A test skill")

    with patch("skills_ref.cli.read_properties", return_value=mock_props) as mock_read:
        result = runner.invoke(main, ["read-properties", str(skill_file)])

        assert result.exit_code == 0
        mock_read.assert_called_once_with(skill_dir)


def test_read_properties_cmd_skill_error(runner, tmp_path):
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()

    with patch(
        "skills_ref.cli.read_properties", side_effect=SkillError("Invalid YAML")
    ):
        result = runner.invoke(main, ["read-properties", str(skill_dir)])

        assert result.exit_code == 1
        assert "Error: Invalid YAML" in result.output


def test_read_properties_cmd_unexpected_error(runner, tmp_path):
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()

    with patch("skills_ref.cli.read_properties", side_effect=RuntimeError("Boom")):
        result = runner.invoke(main, ["read-properties", str(skill_dir)])

        assert result.exit_code == 1
        assert (
            "An unexpected error occurred reading properties for my-skill"
            in result.output
        )


def test_to_prompt_cmd_success(runner, tmp_path):
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()

    with patch(
        "skills_ref.cli.to_prompt", return_value="<xml>test</xml>"
    ) as mock_prompt:
        result = runner.invoke(main, ["to-prompt", str(skill_dir)])

        assert result.exit_code == 0
        assert "<xml>test</xml>" in result.output
        mock_prompt.assert_called_once_with([skill_dir])


def test_to_prompt_cmd_multiple_paths(runner, tmp_path):
    skill_dir1 = tmp_path / "my-skill-1"
    skill_dir1.mkdir()

    skill_dir2 = tmp_path / "my-skill-2"
    skill_dir2.mkdir()
    skill_file2 = skill_dir2 / "SKILL.md"
    skill_file2.touch()

    with patch(
        "skills_ref.cli.to_prompt", return_value="<xml>test</xml>"
    ) as mock_prompt:
        result = runner.invoke(main, ["to-prompt", str(skill_dir1), str(skill_file2)])

        assert result.exit_code == 0
        mock_prompt.assert_called_once_with([skill_dir1, skill_dir2])


def test_to_prompt_cmd_skill_error(runner, tmp_path):
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()

    with patch("skills_ref.cli.to_prompt", side_effect=SkillError("Missing SKILL.md")):
        result = runner.invoke(main, ["to-prompt", str(skill_dir)])

        assert result.exit_code == 1
        assert "Error: Missing SKILL.md" in result.output


def test_to_prompt_cmd_unexpected_error(runner, tmp_path):
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()

    with patch("skills_ref.cli.to_prompt", side_effect=RuntimeError("Boom")):
        result = runner.invoke(main, ["to-prompt", str(skill_dir)])

        assert result.exit_code == 1
        assert "An unexpected error occurred generating prompts" in result.output
