"""Tests for prompt module."""

import sys
from pathlib import Path

import pytest
from skills_ref.constants import MAX_SKILLS_PER_PROMPT
from skills_ref.errors import SkillError
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


def test_deduplicate_skills(tmp_path):
    """Duplicate skill directories are only included once."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: my-skill
description: A test skill
---
Body
""")
    # Pass the same skill directory twice (direct path and relative path that resolves to same)
    result = to_prompt([skill_dir, skill_dir, skill_dir])
    assert result.count("<skill>") == 1
    assert result.count("</skill>") == 1

    import os

    rel_path = os.path.relpath(skill_dir)
    result = to_prompt([skill_dir, rel_path])
    assert result.count("<skill>") == 1


def test_max_skills_limit(tmp_path):
    """Providing too many skills raises SkillError."""
    skill_dirs = []
    for i in range(MAX_SKILLS_PER_PROMPT + 1):
        d = tmp_path / f"skill-{i}"
        d.mkdir()
        (d / "SKILL.md").write_text(f"""---
name: skill-{i}
description: Skill {i}
---
Body
""")
        skill_dirs.append(d)

    with pytest.raises(SkillError) as excinfo:
        to_prompt(skill_dirs)
    assert (
        f"Number of skill directories exceeds maximum limit of {MAX_SKILLS_PER_PROMPT}"
        in str(excinfo.value)
    )


def test_max_skill_directory_inputs_limit(tmp_path):
    """Providing too many duplicate inputs raises SkillError before resolve."""
    skill_dir = tmp_path / "repeated-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: repeated-skill
description: A test skill
---
Body
""")

    with pytest.raises(SkillError) as excinfo:
        to_prompt([skill_dir] * (MAX_SKILLS_PER_PROMPT + 1))
    assert (
        f"Number of skill directories exceeds maximum limit of {MAX_SKILLS_PER_PROMPT}"
        in str(excinfo.value)
    )


def test_duplicate_paths_resolved_once(tmp_path, monkeypatch):
    """Exact duplicate paths only trigger one resolve call."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: my-skill
description: A test skill
---
Body
""")

    resolve_calls = 0
    original_resolve = Path.resolve

    def counting_resolve(self):
        nonlocal resolve_calls
        resolve_calls += 1
        return original_resolve(self)

    monkeypatch.setattr(Path, "resolve", counting_resolve)

    to_prompt([skill_dir, skill_dir, skill_dir])

    assert resolve_calls == 1
