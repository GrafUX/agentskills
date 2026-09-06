import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from skills_ref.cli import main, _is_skill_md_file
from skills_ref.errors import SkillError


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def temp_skill_dir(tmp_path):
    skill_dir = tmp_path / "test_skill"
    skill_dir.mkdir()
    skill_md = skill_dir / "SKILL.md"
    skill_md.touch()
    return skill_dir


def test_main_group(runner):
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Reference library for Agent Skills" in result.output


def test_main_version(runner):
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "version" in result.output.lower()


def test_is_skill_md_file_exceptions():
    with patch("pathlib.Path.is_file", side_effect=OSError("Test OS Error")):
        assert not _is_skill_md_file(Path("some/path/SKILL.md"))

    with patch("pathlib.Path.is_file", side_effect=RuntimeError("Test Runtime Error")):
        assert not _is_skill_md_file(Path("some/path/SKILL.md"))


@patch("skills_ref.cli.validate")
def test_validate_success(mock_validate, runner, temp_skill_dir):
    mock_validate.return_value = []

    result = runner.invoke(main, ["validate", str(temp_skill_dir)])

    assert result.exit_code == 0
    assert "Valid skill:" in result.output
    mock_validate.assert_called_once_with(temp_skill_dir)


@patch("skills_ref.cli.validate")
def test_validate_success_with_skill_md(mock_validate, runner, temp_skill_dir):
    mock_validate.return_value = []

    skill_md_path = temp_skill_dir / "SKILL.md"
    result = runner.invoke(main, ["validate", str(skill_md_path)])

    assert result.exit_code == 0
    assert "Valid skill:" in result.output
    mock_validate.assert_called_once_with(temp_skill_dir)


@patch("skills_ref.cli.validate")
def test_validate_errors_found(mock_validate, runner, temp_skill_dir):
    mock_validate.return_value = ["Missing metadata", "Invalid name"]

    result = runner.invoke(main, ["validate", str(temp_skill_dir)])

    assert result.exit_code == 1
    assert "Validation failed for" in result.output
    assert "- Missing metadata" in result.output
    assert "- Invalid name" in result.output


@patch("skills_ref.cli.validate")
def test_validate_unexpected_exception(mock_validate, runner, temp_skill_dir):
    mock_validate.side_effect = Exception("Boom!")

    result = runner.invoke(main, ["validate", str(temp_skill_dir)])

    assert result.exit_code == 1
    assert "An unexpected error occurred validating" in result.output


@patch("skills_ref.cli.read_properties")
def test_read_properties_success(mock_read_props, runner, temp_skill_dir):
    props_mock = MagicMock()
    props_mock.to_dict.return_value = {"name": "test-skill", "description": "Test"}
    mock_read_props.return_value = props_mock

    result = runner.invoke(main, ["read-properties", str(temp_skill_dir)])

    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["name"] == "test-skill"
    mock_read_props.assert_called_once_with(temp_skill_dir)


@patch("skills_ref.cli.read_properties")
def test_read_properties_success_with_skill_md(mock_read_props, runner, temp_skill_dir):
    props_mock = MagicMock()
    props_mock.to_dict.return_value = {"name": "test-skill"}
    mock_read_props.return_value = props_mock

    skill_md_path = temp_skill_dir / "SKILL.md"
    result = runner.invoke(main, ["read-properties", str(skill_md_path)])

    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["name"] == "test-skill"
    mock_read_props.assert_called_once_with(temp_skill_dir)


@patch("skills_ref.cli.read_properties")
def test_read_properties_skill_error(mock_read_props, runner, temp_skill_dir):
    mock_read_props.side_effect = SkillError("Parse issue")

    result = runner.invoke(main, ["read-properties", str(temp_skill_dir)])

    assert result.exit_code == 1
    assert "Error: Parse issue" in result.output


@patch("skills_ref.cli.read_properties")
def test_read_properties_unexpected_exception(mock_read_props, runner, temp_skill_dir):
    mock_read_props.side_effect = Exception("Unexpected")

    result = runner.invoke(main, ["read-properties", str(temp_skill_dir)])

    assert result.exit_code == 1
    assert "An unexpected error occurred reading properties for" in result.output


@patch("skills_ref.cli.to_prompt")
def test_to_prompt_success(mock_to_prompt, runner, temp_skill_dir):
    mock_to_prompt.return_value = "<available_skills>\nTest output\n</available_skills>"

    result = runner.invoke(main, ["to-prompt", str(temp_skill_dir)])

    assert result.exit_code == 0
    assert "Test output" in result.output
    mock_to_prompt.assert_called_once_with([temp_skill_dir])


@patch("skills_ref.cli.to_prompt")
def test_to_prompt_success_with_skill_md(mock_to_prompt, runner, temp_skill_dir):
    mock_to_prompt.return_value = "<available_skills>\nTest output\n</available_skills>"

    skill_md_path = temp_skill_dir / "SKILL.md"
    result = runner.invoke(main, ["to-prompt", str(temp_skill_dir), str(skill_md_path)])

    assert result.exit_code == 0
    assert "Test output" in result.output
    # skill_md_path should be resolved to temp_skill_dir
    mock_to_prompt.assert_called_once_with([temp_skill_dir, temp_skill_dir])


@patch("skills_ref.cli.to_prompt")
def test_to_prompt_skill_error(mock_to_prompt, runner, temp_skill_dir):
    mock_to_prompt.side_effect = SkillError("Prompt issue")

    result = runner.invoke(main, ["to-prompt", str(temp_skill_dir)])

    assert result.exit_code == 1
    assert "Error: Prompt issue" in result.output


@patch("skills_ref.cli.to_prompt")
def test_to_prompt_unexpected_exception(mock_to_prompt, runner, temp_skill_dir):
    mock_to_prompt.side_effect = Exception("Unexpected")

    result = runner.invoke(main, ["to-prompt", str(temp_skill_dir)])

    assert result.exit_code == 1
    assert "An unexpected error occurred generating prompts" in result.output
