"""Tests for prompt module."""

import sys
import pytest
from skills_ref.prompt import to_prompt


def test_empty_list():
    result = to_prompt([])
    assert result == "<available_skills>\n</available_skills>"


def test_single_skill(tmp_path):
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: my-skill
description: A test skill
---
Body
""")
    result = to_prompt([skill_dir])
    assert "<available_skills>" in result
    assert "</available_skills>" in result
    assert "<name>\nmy-skill\n</name>" in result
    assert "<description>\nA test skill\n</description>" in result
    assert "<location>" in result
    assert "SKILL.md" in result


def test_multiple_skills(tmp_path):
    skill_a = tmp_path / "skill-a"
    skill_a.mkdir()
    (skill_a / "SKILL.md").write_text("""---
name: skill-a
description: First skill
---
Body
""")

    skill_b = tmp_path / "skill-b"
    skill_b.mkdir()
    (skill_b / "SKILL.md").write_text("""---
name: skill-b
description: Second skill
---
Body
""")

    result = to_prompt([skill_a, skill_b])
    assert result.count("<skill>") == 2
    assert result.count("</skill>") == 2
    assert "skill-a" in result
    assert "skill-b" in result


def test_special_characters_escaped(tmp_path):
    """XML special characters in description are escaped."""
    skill_dir = tmp_path / "special-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: special-skill
description: Use <foo> & <bar> tags
---
Body
""")
    result = to_prompt([skill_dir])
    assert "&lt;foo&gt;" in result
    assert "&amp;" in result
    assert "&lt;bar&gt;" in result
    assert "<foo>" not in result
    assert "<bar>" not in result


def test_deduplication(tmp_path):
    """Duplicate skill directories are de-duplicated."""
    skill_dir = tmp_path / "dedup-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: dedup-skill
description: A test skill
---
Body
""")
    # Same directory provided twice
    paths = [skill_dir, skill_dir]

    result = to_prompt(paths)
    assert result.count("<skill>") == 1


def test_max_skills_limit(tmp_path, monkeypatch):
    """Providing too many skills raises SkillError."""
    from skills_ref.constants import MAX_SKILLS_PER_PROMPT
    from skills_ref.errors import SkillError

    # We don't actually need to create many directories, we can mock the input
    # or just use many copies of the same if we didn't have dedup,
    # but we DO have dedup, so we need unique paths.
    skill_dirs = []
    for i in range(MAX_SKILLS_PER_PROMPT + 1):
        d = tmp_path / f"skill-{i}"
        d.mkdir()
        (d / "SKILL.md").write_text(f"---\nname: skill-{i}\ndescription: desc\n---\n")
        skill_dirs.append(d)

    with pytest.raises(SkillError) as excinfo:
        to_prompt(skill_dirs)
    assert f"exceeds maximum limit of {MAX_SKILLS_PER_PROMPT}" in str(excinfo.value)


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows does not support < or > in paths"
)
def test_special_characters_escaped_in_location(tmp_path):
    """XML special characters in location path are escaped."""
    skill_dir = tmp_path / "special-location-&-<>"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: special-location
description: Test skill with special characters in path
---
Body
""")
    result = to_prompt([skill_dir])
    assert "&amp;" in result
    assert "&lt;" in result
    assert "&gt;" in result
    assert "special-location-&-<>" not in result
