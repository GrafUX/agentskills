"""Tests for CLI module."""

import json
from click.testing import CliRunner

from skills_ref.cli import main, _is_skill_md_file


def test_is_skill_md_file_normal(tmp_path):
    # Test valid SKILL.md file
    skill_file = tmp_path / "SKILL.md"
    skill_file.touch()
    assert _is_skill_md_file(skill_file) is True

    # Test lowercase skill.md file
    skill_file_lower = tmp_path / "skill.md"
    skill_file_lower.touch()
    assert _is_skill_md_file(skill_file_lower) is True

    # Test non-skill.md file
    other_file = tmp_path / "other.txt"
    other_file.touch()
    assert _is_skill_md_file(other_file) is False

    # Test directory with same name
    dir_path = tmp_path / "dir.md"
    dir_path.mkdir()
    assert _is_skill_md_file(dir_path) is False


def test_is_skill_md_file_exceptions(monkeypatch):
    class MockPath:
        def __init__(self, name):
            self.name = name

        def is_file(self):
            raise OSError("OS error")

    assert _is_skill_md_file(MockPath("SKILL.md")) is False

    class MockPathRuntimeError:
        def __init__(self, name):
            self.name = name

        def is_file(self):
            raise RuntimeError("Runtime error")

    assert _is_skill_md_file(MockPathRuntimeError("SKILL.md")) is False


def test_main_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Reference library for Agent Skills" in result.output


def test_main_version():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "version" in result.output


def test_validate_success_dir(tmp_path):
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: test-skill
description: A test skill
---
# Test Skill
""")
    runner = CliRunner()
    result = runner.invoke(main, ["validate", str(skill_dir)])
    assert result.exit_code == 0
    assert "Valid skill: test-skill" in result.output


def test_validate_success_file(tmp_path):
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text("""---
name: test-skill
description: A test skill
---
# Test Skill
""")
    runner = CliRunner()
    result = runner.invoke(main, ["validate", str(skill_file)])
    assert result.exit_code == 0
    assert "Valid skill: test-skill" in result.output


def test_validate_failure(tmp_path):
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: mismatch-name
description: A test skill
---
# Test Skill
""")
    runner = CliRunner()
    result = runner.invoke(main, ["validate", str(skill_dir)])
    assert result.exit_code == 1
    assert "Validation failed for test-skill" in result.output
    assert "must match skill name" in result.output


def test_validate_unexpected_exception(tmp_path, monkeypatch):
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: test-skill
description: A test skill
---
# Test Skill
""")

    import skills_ref.cli as cli_mod

    monkeypatch.setattr(
        cli_mod,
        "validate",
        lambda x: (_ for _ in ()).throw(ValueError("Unexpected error")),
    )

    runner = CliRunner()
    result = runner.invoke(main, ["validate", str(skill_dir)])
    assert result.exit_code == 1
    assert "An unexpected error occurred validating test-skill" in result.output


def test_read_properties_success_dir(tmp_path):
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: test-skill
description: A test skill
license: MIT
---
# Test Skill
""")
    runner = CliRunner()
    result = runner.invoke(main, ["read-properties", str(skill_dir)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["name"] == "test-skill"
    assert data["description"] == "A test skill"
    assert data["license"] == "MIT"


def test_read_properties_success_file(tmp_path):
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text("""---
name: test-skill
description: A test skill
license: MIT
---
# Test Skill
""")
    runner = CliRunner()
    result = runner.invoke(main, ["read-properties", str(skill_file)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["name"] == "test-skill"
    assert data["description"] == "A test skill"
    assert data["license"] == "MIT"


def test_read_properties_expected_error(tmp_path):
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()
    # Missing name/description raises a validation error (SkillError)
    (skill_dir / "SKILL.md").write_text("""---
license: MIT
---
# Test Skill
""")
    runner = CliRunner()
    result = runner.invoke(main, ["read-properties", str(skill_dir)])
    assert result.exit_code == 1
    assert "Error: " in result.output


def test_read_properties_unexpected_exception(tmp_path, monkeypatch):
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: test-skill
description: A test skill
---
# Test Skill
""")
    import skills_ref.cli as cli_mod

    monkeypatch.setattr(
        cli_mod,
        "read_properties",
        lambda x: (_ for _ in ()).throw(ValueError("Unexpected error")),
    )

    runner = CliRunner()
    result = runner.invoke(main, ["read-properties", str(skill_dir)])
    assert result.exit_code == 1
    assert (
        "An unexpected error occurred reading properties for test-skill"
        in result.output
    )


def test_to_prompt_success(tmp_path):
    skill_dir1 = tmp_path / "test-skill-1"
    skill_dir1.mkdir()
    (skill_dir1 / "SKILL.md").write_text("""---
name: test-skill-1
description: A test skill one
---
# Test Skill 1
""")

    skill_dir2 = tmp_path / "test-skill-2"
    skill_dir2.mkdir()
    skill_file2 = skill_dir2 / "SKILL.md"
    skill_file2.write_text("""---
name: test-skill-2
description: A test skill two
---
# Test Skill 2
""")

    runner = CliRunner()
    # Pass directory and file directly
    result = runner.invoke(main, ["to-prompt", str(skill_dir1), str(skill_file2)])
    assert result.exit_code == 0
    assert "<available_skills>" in result.output
    assert "test-skill-1" in result.output
    assert "test-skill-2" in result.output


def test_to_prompt_expected_error(tmp_path):
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()
    # Missing SKILL.md file entirely
    runner = CliRunner()
    result = runner.invoke(main, ["to-prompt", str(skill_dir)])
    assert result.exit_code == 1
    assert "Error: " in result.output


def test_to_prompt_unexpected_exception(tmp_path, monkeypatch):
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: test-skill
description: A test skill
---
# Test Skill
""")
    import skills_ref.cli as cli_mod

    monkeypatch.setattr(
        cli_mod,
        "to_prompt",
        lambda x: (_ for _ in ()).throw(ValueError("Unexpected error")),
    )

    runner = CliRunner()
    result = runner.invoke(main, ["to-prompt", str(skill_dir)])
    assert result.exit_code == 1
    assert "An unexpected error occurred generating prompts" in result.output
