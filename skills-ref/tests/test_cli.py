import json
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from skills_ref.cli import _is_skill_md_file, main
from skills_ref.errors import SkillError
from skills_ref.models import SkillProperties


def test_is_skill_md_file_valid_uppercase(tmp_path):
    skill_file = tmp_path / "SKILL.md"
    skill_file.touch()
    assert _is_skill_md_file(skill_file) is True


def test_is_skill_md_file_valid_lowercase(tmp_path):
    skill_file = tmp_path / "skill.md"
    skill_file.touch()
    assert _is_skill_md_file(skill_file) is True


def test_is_skill_md_file_invalid_name(tmp_path):
    skill_file = tmp_path / "other.md"
    skill_file.touch()
    assert _is_skill_md_file(skill_file) is False


def test_is_skill_md_file_directory(tmp_path):
    skill_dir = tmp_path / "skill.md"
    skill_dir.mkdir()
    assert _is_skill_md_file(skill_dir) is False


def test_is_skill_md_file_oserror(monkeypatch, tmp_path):
    def mock_is_file(*args, **kwargs):
        raise OSError("Permission denied")

    monkeypatch.setattr(Path, "is_file", mock_is_file)
    assert _is_skill_md_file(tmp_path / "SKILL.md") is False


def test_is_skill_md_file_runtime_error(monkeypatch, tmp_path):
    def mock_is_file(*args, **kwargs):
        raise RuntimeError("Symlink loop")

    monkeypatch.setattr(Path, "is_file", mock_is_file)
    assert _is_skill_md_file(tmp_path / "SKILL.md") is False


# validate command tests


def test_validate_cmd_success(tmp_path):
    runner = CliRunner()
    skill_dir = tmp_path / "my_skill"
    skill_dir.mkdir()

    with patch("skills_ref.cli.validate") as mock_validate:
        mock_validate.return_value = []
        result = runner.invoke(main, ["validate", str(skill_dir)])

        assert result.exit_code == 0
        assert "Valid skill: my_skill" in result.output


def test_validate_cmd_with_skill_md_file(tmp_path):
    runner = CliRunner()
    skill_dir = tmp_path / "my_skill"
    skill_dir.mkdir()
    skill_file = skill_dir / "SKILL.md"
    skill_file.touch()

    with patch("skills_ref.cli.validate") as mock_validate:
        mock_validate.return_value = []
        result = runner.invoke(main, ["validate", str(skill_file)])

        assert result.exit_code == 0
        assert "Valid skill: my_skill" in result.output
        mock_validate.assert_called_once_with(skill_dir)


def test_validate_cmd_failure(tmp_path):
    runner = CliRunner()
    skill_dir = tmp_path / "my_skill"
    skill_dir.mkdir()

    with patch("skills_ref.cli.validate") as mock_validate:
        mock_validate.return_value = ["Missing name", "Invalid license"]
        result = runner.invoke(main, ["validate", str(skill_dir)])

        assert result.exit_code == 1
        assert "Validation failed for my_skill:" in result.output
        assert "  - Missing name" in result.output
        assert "  - Invalid license" in result.output


def test_validate_cmd_exception(tmp_path):
    runner = CliRunner()
    skill_dir = tmp_path / "my_skill"
    skill_dir.mkdir()

    with patch("skills_ref.cli.validate") as mock_validate:
        mock_validate.side_effect = Exception("Unexpected")
        result = runner.invoke(main, ["validate", str(skill_dir)])

        assert result.exit_code == 1
        assert "An unexpected error occurred validating my_skill" in result.output


# read-properties command tests


def test_read_properties_cmd_success(tmp_path):
    runner = CliRunner()
    skill_dir = tmp_path / "my_skill"
    skill_dir.mkdir()

    mock_props = SkillProperties(name="my_skill", description="desc", license="MIT")

    with patch("skills_ref.cli.read_properties") as mock_read:
        mock_read.return_value = mock_props
        result = runner.invoke(main, ["read-properties", str(skill_dir)])

        assert result.exit_code == 0
        output_json = json.loads(result.output)
        assert output_json["name"] == "my_skill"
        assert output_json["description"] == "desc"
        assert output_json["license"] == "MIT"


def test_read_properties_cmd_with_skill_md_file(tmp_path):
    runner = CliRunner()
    skill_dir = tmp_path / "my_skill"
    skill_dir.mkdir()
    skill_file = skill_dir / "SKILL.md"
    skill_file.touch()

    mock_props = SkillProperties(name="my_skill", description="desc")

    with patch("skills_ref.cli.read_properties") as mock_read:
        mock_read.return_value = mock_props
        result = runner.invoke(main, ["read-properties", str(skill_file)])

        assert result.exit_code == 0
        mock_read.assert_called_once_with(skill_dir)


def test_read_properties_cmd_skill_error(tmp_path):
    runner = CliRunner()
    skill_dir = tmp_path / "my_skill"
    skill_dir.mkdir()

    with patch("skills_ref.cli.read_properties") as mock_read:
        mock_read.side_effect = SkillError("Parse failed")
        result = runner.invoke(main, ["read-properties", str(skill_dir)])

        assert result.exit_code == 1
        assert "Error: Parse failed" in result.output


def test_read_properties_cmd_exception(tmp_path):
    runner = CliRunner()
    skill_dir = tmp_path / "my_skill"
    skill_dir.mkdir()

    with patch("skills_ref.cli.read_properties") as mock_read:
        mock_read.side_effect = Exception("Unexpected")
        result = runner.invoke(main, ["read-properties", str(skill_dir)])

        assert result.exit_code == 1
        assert (
            "An unexpected error occurred reading properties for my_skill"
            in result.output
        )


# to-prompt command tests


def test_to_prompt_cmd_success(tmp_path):
    runner = CliRunner()
    skill_dir1 = tmp_path / "skill1"
    skill_dir1.mkdir()
    skill_dir2 = tmp_path / "skill2"
    skill_dir2.mkdir()

    expected_output = "<available_skills>\n</available_skills>"

    with patch("skills_ref.cli.to_prompt") as mock_to_prompt:
        mock_to_prompt.return_value = expected_output
        result = runner.invoke(main, ["to-prompt", str(skill_dir1), str(skill_dir2)])

        assert result.exit_code == 0
        assert expected_output in result.output
        mock_to_prompt.assert_called_once_with([skill_dir1, skill_dir2])


def test_to_prompt_cmd_with_skill_md_file(tmp_path):
    runner = CliRunner()
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    skill_file = skill_dir / "SKILL.md"
    skill_file.touch()

    expected_output = "<available_skills>\n</available_skills>"

    with patch("skills_ref.cli.to_prompt") as mock_to_prompt:
        mock_to_prompt.return_value = expected_output
        result = runner.invoke(main, ["to-prompt", str(skill_file)])

        assert result.exit_code == 0
        mock_to_prompt.assert_called_once_with([skill_dir])


def test_to_prompt_cmd_skill_error(tmp_path):
    runner = CliRunner()
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()

    with patch("skills_ref.cli.to_prompt") as mock_to_prompt:
        mock_to_prompt.side_effect = SkillError("Prompt failed")
        result = runner.invoke(main, ["to-prompt", str(skill_dir)])

        assert result.exit_code == 1
        assert "Error: Prompt failed" in result.output


def test_to_prompt_cmd_exception(tmp_path):
    runner = CliRunner()
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()

    with patch("skills_ref.cli.to_prompt") as mock_to_prompt:
        mock_to_prompt.side_effect = Exception("Unexpected")
        result = runner.invoke(main, ["to-prompt", str(skill_dir)])

        assert result.exit_code == 1
        assert "An unexpected error occurred generating prompts" in result.output
