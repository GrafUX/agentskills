"""Tests for the CLI module of skills-ref."""

from unittest.mock import patch
from click.testing import CliRunner
from skills_ref.cli import main


def test_validate_cmd_unexpected_error(tmp_path):
    """Test that validate command handles unexpected errors gracefully."""
    runner = CliRunner()

    # Create a dummy skill directory to satisfy click.Path(exists=True)
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()

    with patch(
        "skills_ref.cli.validate", side_effect=Exception("Simulated unexpected error")
    ):
        result = runner.invoke(main, ["validate", str(skill_dir)])

        assert result.exit_code == 1
        assert "An unexpected error occurred validating" in result.output
        assert "test-skill" in result.output


def test_read_properties_cmd_unexpected_error(tmp_path):
    """Test that read-properties command handles unexpected errors gracefully."""
    runner = CliRunner()

    # Create a dummy skill directory to satisfy click.Path(exists=True)
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()

    with patch(
        "skills_ref.cli.read_properties",
        side_effect=Exception("Simulated unexpected error"),
    ):
        result = runner.invoke(main, ["read-properties", str(skill_dir)])

        assert result.exit_code == 1
        assert "An unexpected error occurred reading properties" in result.output
        assert "test-skill" in result.output


def test_to_prompt_cmd_unexpected_error(tmp_path):
    """Test that to-prompt command handles unexpected errors gracefully."""
    runner = CliRunner()

    # Create dummy skill directories to satisfy click.Path(exists=True)
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()

    with patch(
        "skills_ref.cli.to_prompt", side_effect=Exception("Simulated unexpected error")
    ):
        result = runner.invoke(main, ["to-prompt", str(skill_dir)])

        assert result.exit_code == 1
        assert "An unexpected error occurred generating prompts" in result.output
