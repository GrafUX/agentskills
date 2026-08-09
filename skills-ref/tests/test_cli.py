import json
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from skills_ref.cli import main
from skills_ref.errors import SkillError


@pytest.fixture
def runner():
    return CliRunner()


@patch("skills_ref.cli.validate")
def test_validate_cmd_success(mock_validate, runner, tmp_path):
    # Setup
    mock_validate.return_value = []
    skill_dir = tmp_path / "my_skill"
    skill_dir.mkdir()

    # Execute
    result = runner.invoke(main, ["validate", str(skill_dir)])

    # Assert
    assert result.exit_code == 0
    assert "Valid skill: my_skill" in result.output
    mock_validate.assert_called_once_with(skill_dir)


@patch("skills_ref.cli.validate")
def test_validate_cmd_with_skill_md_path(mock_validate, runner, tmp_path):
    # Setup
    mock_validate.return_value = []
    skill_dir = tmp_path / "my_skill"
    skill_dir.mkdir()
    skill_md = skill_dir / "SKILL.md"
    skill_md.touch()

    # Execute
    result = runner.invoke(main, ["validate", str(skill_md)])

    # Assert
    assert result.exit_code == 0
    assert "Valid skill: my_skill" in result.output
    mock_validate.assert_called_once_with(skill_dir)


@patch("skills_ref.cli.validate")
def test_validate_cmd_errors(mock_validate, runner, tmp_path):
    # Setup
    mock_validate.return_value = ["Missing title", "Invalid tools"]
    skill_dir = tmp_path / "my_skill"
    skill_dir.mkdir()

    # Execute
    result = runner.invoke(main, ["validate", str(skill_dir)])

    # Assert
    assert result.exit_code == 1
    assert "Validation failed for my_skill:" in result.output
    assert "- Missing title" in result.output
    assert "- Invalid tools" in result.output


@patch("skills_ref.cli.validate")
def test_validate_cmd_unexpected_error(mock_validate, runner, tmp_path):
    # Setup
    mock_validate.side_effect = Exception("Boom!")
    skill_dir = tmp_path / "my_skill"
    skill_dir.mkdir()

    # Execute
    result = runner.invoke(main, ["validate", str(skill_dir)])

    # Assert
    assert result.exit_code == 1
    assert "An unexpected error occurred validating my_skill" in result.output


@patch("skills_ref.cli.read_properties")
def test_read_properties_cmd_success(mock_read_properties, runner, tmp_path):
    # Setup
    mock_props = MagicMock()
    mock_props.to_dict.return_value = {"title": "My Skill", "tools": "my_tool"}
    mock_read_properties.return_value = mock_props

    skill_dir = tmp_path / "my_skill"
    skill_dir.mkdir()

    # Execute
    result = runner.invoke(main, ["read-properties", str(skill_dir)])

    # Assert
    assert result.exit_code == 0
    output_json = json.loads(result.output)
    assert output_json == {"title": "My Skill", "tools": "my_tool"}
    mock_read_properties.assert_called_once_with(skill_dir)


@patch("skills_ref.cli.read_properties")
def test_read_properties_cmd_skill_error(mock_read_properties, runner, tmp_path):
    # Setup
    mock_read_properties.side_effect = SkillError("Invalid YAML")
    skill_dir = tmp_path / "my_skill"
    skill_dir.mkdir()

    # Execute
    result = runner.invoke(main, ["read-properties", str(skill_dir)])

    # Assert
    assert result.exit_code == 1
    assert "Error: Invalid YAML" in result.output


@patch("skills_ref.cli.read_properties")
def test_read_properties_cmd_unexpected_error(mock_read_properties, runner, tmp_path):
    # Setup
    mock_read_properties.side_effect = Exception("Boom!")
    skill_dir = tmp_path / "my_skill"
    skill_dir.mkdir()

    # Execute
    result = runner.invoke(main, ["read-properties", str(skill_dir)])

    # Assert
    assert result.exit_code == 1
    assert (
        "An unexpected error occurred reading properties for my_skill" in result.output
    )


@patch("skills_ref.cli.to_prompt")
def test_to_prompt_cmd_success(mock_to_prompt, runner, tmp_path):
    # Setup
    mock_to_prompt.return_value = "<available_skills>...</available_skills>"

    skill_dir1 = tmp_path / "skill1"
    skill_dir1.mkdir()
    skill_dir2 = tmp_path / "skill2"
    skill_dir2.mkdir()

    # Execute
    result = runner.invoke(main, ["to-prompt", str(skill_dir1), str(skill_dir2)])

    # Assert
    assert result.exit_code == 0
    assert "<available_skills>...</available_skills>" in result.output
    mock_to_prompt.assert_called_once_with([skill_dir1, skill_dir2])


@patch("skills_ref.cli.to_prompt")
def test_to_prompt_cmd_skill_error(mock_to_prompt, runner, tmp_path):
    # Setup
    mock_to_prompt.side_effect = SkillError("Missing properties")
    skill_dir = tmp_path / "my_skill"
    skill_dir.mkdir()

    # Execute
    result = runner.invoke(main, ["to-prompt", str(skill_dir)])

    # Assert
    assert result.exit_code == 1
    assert "Error: Missing properties" in result.output


@patch("skills_ref.cli.to_prompt")
def test_to_prompt_cmd_unexpected_error(mock_to_prompt, runner, tmp_path):
    # Setup
    mock_to_prompt.side_effect = Exception("Boom!")
    skill_dir = tmp_path / "my_skill"
    skill_dir.mkdir()

    # Execute
    result = runner.invoke(main, ["to-prompt", str(skill_dir)])

    # Assert
    assert result.exit_code == 1
    assert "An unexpected error occurred generating prompts" in result.output
