from unittest.mock import patch
from click.testing import CliRunner
from skills_ref.cli import validate_cmd


def test_validate_cmd_unexpected_error(tmp_path):
    runner = CliRunner()

    with patch(
        "skills_ref.cli.validate", side_effect=Exception("Something unexpected")
    ):
        result = runner.invoke(validate_cmd, [str(tmp_path)])

    assert result.exit_code == 1
    assert "An unexpected error occurred validating" in result.output
    assert tmp_path.name in result.output
