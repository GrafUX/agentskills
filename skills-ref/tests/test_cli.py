from unittest.mock import patch
from click.testing import CliRunner

from skills_ref.cli import to_prompt_cmd
from skills_ref.errors import SkillError


def test_to_prompt_cmd_success(tmp_path):
    runner = CliRunner()
    skill_dir = tmp_path / "my_skill"
    skill_dir.mkdir()

    with patch("skills_ref.cli.to_prompt") as mock_to_prompt:
        mock_to_prompt.return_value = "<available_skills></available_skills>"

        result = runner.invoke(to_prompt_cmd, [str(skill_dir)])

        assert result.exit_code == 0
        assert "<available_skills></available_skills>" in result.output
        mock_to_prompt.assert_called_once_with([skill_dir])


def test_to_prompt_cmd_skill_error(tmp_path):
    runner = CliRunner()
    skill_dir = tmp_path / "my_skill"
    skill_dir.mkdir()

    with patch("skills_ref.cli.to_prompt") as mock_to_prompt:
        mock_to_prompt.side_effect = SkillError("Custom skill error")

        result = runner.invoke(to_prompt_cmd, [str(skill_dir)])

        assert result.exit_code == 1
        assert "Error: Custom skill error\n" in result.output
        mock_to_prompt.assert_called_once_with([skill_dir])


def test_to_prompt_cmd_unexpected_error(tmp_path):
    runner = CliRunner()
    skill_dir = tmp_path / "my_skill"
    skill_dir.mkdir()

    with patch("skills_ref.cli.to_prompt") as mock_to_prompt:
        mock_to_prompt.side_effect = RuntimeError("Unexpected failure")

        result = runner.invoke(to_prompt_cmd, [str(skill_dir)])

        assert result.exit_code == 1
        assert "An unexpected error occurred generating prompts\n" in result.output
        mock_to_prompt.assert_called_once_with([skill_dir])


def test_to_prompt_cmd_with_skill_md_file(tmp_path):
    runner = CliRunner()
    skill_dir = tmp_path / "my_skill"
    skill_dir.mkdir()
    skill_md = skill_dir / "SKILL.md"
    skill_md.touch()

    with patch("skills_ref.cli.to_prompt") as mock_to_prompt:
        mock_to_prompt.return_value = "output"

        result = runner.invoke(to_prompt_cmd, [str(skill_md)])

        assert result.exit_code == 0
        assert "output\n" in result.output
        # Should resolve to the parent directory
        mock_to_prompt.assert_called_once_with([skill_dir])
