"""Tests for cli module."""

from unittest.mock import patch
from click.testing import CliRunner
from skills_ref.cli import main


def test_validate_cmd_success(tmp_path):
    """Test that validating a valid skill path succeeds."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: my-skill
description: A test skill
---
# My Skill
""")
    runner = CliRunner()
    result = runner.invoke(main, ["validate", str(skill_dir)])
    assert result.exit_code == 0
    assert "Valid skill: my-skill" in result.output


def test_validate_cmd_failure(tmp_path):
    """Test that validating an invalid skill path fails."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    # No SKILL.md -> validation fails
    runner = CliRunner()
    result = runner.invoke(main, ["validate", str(skill_dir)])
    assert result.exit_code == 1
    assert "Validation failed for my-skill" in result.output
    assert "Missing required file: SKILL.md" in result.output


def test_validate_cmd_unexpected_exception(tmp_path):
    """Test that validate_cmd handles unexpected exceptions gracefully."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: my-skill
description: A test skill
---
# My Skill
""")

    runner = CliRunner()
    with patch(
        "skills_ref.cli.validate", side_effect=Exception("Unexpected breakdown")
    ):
        result = runner.invoke(main, ["validate", str(skill_dir)])
        assert result.exit_code == 1
        assert "An unexpected error occurred validating my-skill" in result.output
