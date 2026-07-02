"""Tests for validator module."""

import pytest

from skills_ref.validator import validate


def test_validate_skill_missing_dir():
    """Missing skill directory should fail."""
    from pathlib import Path
    errors = validate(Path("/nonexistent/path"))
    assert len(errors) == 1
    assert "does not exist" in errors[0]


def test_validate_skill_missing_skill_md(tmp_path):
    """Missing SKILL.md should fail."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    errors = validate(skill_dir)
    assert len(errors) == 1
    assert "SKILL.md not found" in errors[0]


def test_validate_skill_minimal_valid(tmp_path):
    """Minimal valid skill should pass."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        """---
name: my-skill
description: A test skill
---
Body
"""
    )
    errors = validate(skill_dir)
    assert len(errors) == 0


def test_validate_skill_missing_name(tmp_path):
    """Missing name should fail."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        """---
description: A test skill
---
Body
"""
    )
    errors = validate(skill_dir)
    assert len(errors) == 1
    assert "name" in errors[0].lower()


def test_validate_skill_missing_description(tmp_path):
    """Missing description should fail."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        """---
name: my-skill
---
Body
"""
    )
    errors = validate(skill_dir)
    assert len(errors) == 1
    assert "description" in errors[0].lower()


def test_validate_skill_name_too_long(tmp_path):
    """Name exceeding limit should fail."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    long_name = "a" * 100
    (skill_dir / "SKILL.md").write_text(
        f"""---
name: {long_name}
description: A test skill
---
Body
"""
    )
    errors = validate(skill_dir)
    assert len(errors) == 1
    assert "exceeds" in errors[0]


def test_validate_skill_description_too_long(tmp_path):
    """Description exceeding limit should fail."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    long_desc = "a" * 2000
    (skill_dir / "SKILL.md").write_text(
        f"""---
name: my-skill
description: {long_desc}
---
Body
"""
    )
    errors = validate(skill_dir)
    assert len(errors) == 1
    assert "exceeds" in errors[0]


def test_validate_skill_invalid_name(tmp_path):
    """Invalid name characters should fail."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        """---
name: my@skill!
description: A test skill
---
Body
"""
    )
    errors = validate(skill_dir)
    assert len(errors) == 1
    assert "alphanumeric" in errors[0]


def test_validate_skill_unknown_field(tmp_path):
    """Unknown field should fail."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        """---
name: my-skill
description: A test skill
unknown_field: value
---
Body
"""
    )
    errors = validate(skill_dir)
    assert len(errors) == 1
    assert "Unknown field" in errors[0]


def test_validate_skill_with_compatibility(tmp_path):
    """Valid compatibility field should pass."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        """---
name: my-skill
description: A test skill
compatibility: python>=3.8
---
Body
"""
    )
    errors = validate(skill_dir)
    assert len(errors) == 0


def test_validate_skill_with_license(tmp_path):
    """Valid license field should pass."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        """---
name: my-skill
description: A test skill
license: MIT
---
Body
"""
    )
    errors = validate(skill_dir)
    assert len(errors) == 0


def test_validate_skill_with_allowed_tools(tmp_path):
    """Valid allowed-tools field should pass."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        """---
name: my-skill
description: A test skill
allowed-tools: tool1,tool2,tool3
---
Body
"""
    )
    errors = validate(skill_dir)
    assert len(errors) == 0


def test_validate_skill_compatibility_too_long(tmp_path):
    """Compatibility exceeding limit should fail."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    long_compat = "a" * 1000
    (skill_dir / "SKILL.md").write_text(
        f"""---
name: my-skill
description: A test skill
compatibility: {long_compat}
---
Body
"""
    )
    errors = validate(skill_dir)
    assert len(errors) == 1
    assert "exceeds" in errors[0]


def test_validate_skill_multiple_errors(tmp_path):
    """Multiple validation errors should all be reported."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    long_name = "a" * 100
    long_desc = "b" * 2000
    (skill_dir / "SKILL.md").write_text(
        f"""---
name: {long_name}
description: {long_desc}
unknown_field: value
---
Body
"""
    )
    errors = validate(skill_dir)
    assert len(errors) == 3


def test_validate_skill_empty_name(tmp_path):
    """Empty name should fail."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        """---
name:
description: A test skill
---
Body
"""
    )
    errors = validate(skill_dir)
    assert len(errors) == 1
    assert "empty" in errors[0].lower()


def test_validate_skill_empty_description(tmp_path):
    """Empty description should fail."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        """---
name: my-skill
description:
---
Body
"""
    )
    errors = validate(skill_dir)
    assert len(errors) == 1
    assert "empty" in errors[0].lower()


def test_validate_skill_name_with_underscores(tmp_path):
    """Name with underscores should pass."""
    skill_dir = tmp_path / "my_skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        """---
name: my_skill
description: A test skill
---
Body
"""
    )
    errors = validate(skill_dir)
    assert len(errors) == 0


def test_validate_skill_name_with_hyphens(tmp_path):
    """Name with hyphens should pass."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        """---
name: my-skill
description: A test skill
---
Body
"""
    )
    errors = validate(skill_dir)
    assert len(errors) == 0


def test_validate_unicode_error(tmp_path):
    """Invalid UTF-8 should fail gracefully."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    skill_md = skill_dir / "SKILL.md"
    with open(skill_md, "wb") as f:
        f.write(b"\xff\xfe")
    errors = validate(skill_dir)
    assert len(errors) == 1
    assert "is not valid UTF-8" in errors[0]


def test_license_too_long(tmp_path):
    """License exceeding limit should fail."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    long_license = "x" * 200
    (skill_dir / "SKILL.md").write_text(f"""---
name: my-skill
description: A test skill
license: {long_license}
---
Body
""")
    errors = validate(skill_dir)
    assert any("exceeds" in e and "100" in e for e in errors)


def test_allowed_tools_too_long(tmp_path):
    """Allowed-tools exceeding limit should fail."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    long_tools = "x" * 1500
    (skill_dir / "SKILL.md").write_text(f"""---
name: my-skill
description: A test skill
allowed-tools: {long_tools}
---
Body
""")
    errors = validate(skill_dir)
    assert any("exceeds" in e and "1000" in e for e in errors)
