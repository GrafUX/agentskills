from click.testing import CliRunner

import skills_ref.cli
from skills_ref.cli import main


def test_validate_cmd_unexpected_error(tmp_path, monkeypatch):
    """Test that unexpected errors during validation are handled gracefully."""
    runner = CliRunner()

    # Mock validate to raise a generic exception
    def mock_validate(path):
        raise Exception("Unexpected error")

    monkeypatch.setattr(skills_ref.cli, "validate", mock_validate)

    # Create a dummy skill dir
    skill_dir = tmp_path / "dummy_skill"
    skill_dir.mkdir()

    result = runner.invoke(main, ["validate", str(skill_dir)])

    assert result.exit_code == 1
    assert "An unexpected error occurred validating dummy_skill" in result.output


def test_read_properties_cmd_unexpected_error(tmp_path, monkeypatch):
    """Test that unexpected errors during reading properties are handled gracefully."""
    runner = CliRunner()

    # Mock read_properties to raise a generic exception
    def mock_read_properties(path):
        raise Exception("Unexpected error")

    monkeypatch.setattr(skills_ref.cli, "read_properties", mock_read_properties)

    # Create a dummy skill dir
    skill_dir = tmp_path / "dummy_skill"
    skill_dir.mkdir()

    result = runner.invoke(main, ["read-properties", str(skill_dir)])

    assert result.exit_code == 1
    assert (
        "An unexpected error occurred reading properties for dummy_skill"
        in result.output
    )
