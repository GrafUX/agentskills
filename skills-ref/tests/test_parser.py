"""Tests for parser module."""

import pytest

from skills_ref.parser import (
    _validate_frontmatter,
    ParseError,
    ValidationError,
    find_skill_md,
    parse_frontmatter,
    read_properties,
)


def test_valid_frontmatter():
    content = """---
name: my-skill
description: A test skill
---
# My Skill

Instructions here.
"""
    metadata, body = parse_frontmatter(content)
    assert metadata["name"] == "my-skill"
    assert metadata["description"] == "A test skill"
    assert "# My Skill" in body


def test_missing_frontmatter():
    content = "# No frontmatter here"
    with pytest.raises(ParseError, match="must start with YAML frontmatter"):
        parse_frontmatter(content)


def test_unclosed_frontmatter():
    content = """---
name: my-skill
description: A test skill
"""
    with pytest.raises(ParseError, match="not properly closed"):
        parse_frontmatter(content)


def test_invalid_yaml():
    content = """---
name: [invalid
description: broken
---
Body here
"""
    with pytest.raises(ParseError, match="Invalid YAML"):
        parse_frontmatter(content)


def test_non_dict_frontmatter():
    content = """---
- just
- a
- list
---
Body
"""
    with pytest.raises(ParseError, match="must be a YAML mapping"):
        parse_frontmatter(content)


def test_read_valid_skill(tmp_path):
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: my-skill
description: A test skill
license: MIT
---
# My Skill
""")
    props = read_properties(skill_dir)
    assert props.name == "my-skill"
    assert props.description == "A test skill"
    assert props.license == "MIT"


def test_read_with_metadata(tmp_path):
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: my-skill
description: A test skill
metadata:
  author: Test Author
  version: 1.0
---
Body
""")
    props = read_properties(skill_dir)
    assert props.metadata == {"author": "Test Author", "version": "1.0"}


def test_missing_skill_md(tmp_path):
    with pytest.raises(ParseError, match="SKILL.md not found"):
        read_properties(tmp_path)


def test_missing_name(tmp_path):
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
description: A test skill
---
Body
""")
    with pytest.raises(ValidationError, match="Missing required field.*name"):
        read_properties(skill_dir)


def test_missing_description(tmp_path):
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: my-skill
---
Body
""")
    with pytest.raises(ValidationError, match="Missing required field.*description"):
        read_properties(skill_dir)


def test_find_skill_md_prefers_uppercase(tmp_path):
    """SKILL.md should be preferred over skill.md when both exist."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("uppercase")
    (skill_dir / "skill.md").write_text("lowercase")
    result = find_skill_md(skill_dir)
    assert result is not None
    assert result.name == "SKILL.md"


def test_find_skill_md_accepts_lowercase(tmp_path):
    """skill.md should be accepted when SKILL.md doesn't exist."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "skill.md").write_text("lowercase")
    result = find_skill_md(skill_dir)
    assert result is not None
    # Check case-insensitively since some filesystems are case-insensitive
    assert result.name.lower() == "skill.md"


def test_find_skill_md_returns_none_when_missing(tmp_path):
    """find_skill_md should return None when no skill.md exists."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    result = find_skill_md(skill_dir)
    assert result is None


def test_find_skill_md_not_a_directory(tmp_path):
    """find_skill_md should return None if skill_dir is a file or doesn't exist."""
    file_path = tmp_path / "not_a_dir"
    file_path.write_text("just a file")
    assert find_skill_md(file_path) is None
    assert find_skill_md(tmp_path / "nonexistent_dir") is None


def test_find_skill_md_symlink_escape(tmp_path):
    """find_skill_md should return None if the skill file is a symlink escaping the directory."""
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()

    # Create an external file
    external_file = tmp_path / "secret.md"
    external_file.write_text("secret data")

    # Symlink SKILL.md in the skill directory to the external file
    skill_md = skill_dir / "SKILL.md"
    skill_md.symlink_to(external_file)

    # Since SKILL.md resolves to external_file, which is outside skill_dir, find_skill_md should return None
    assert find_skill_md(skill_dir) is None


def test_read_properties_with_lowercase_skill_md(tmp_path):
    """read_properties should work with lowercase skill.md."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "skill.md").write_text("""---
name: my-skill
description: A test skill
---
# My Skill
""")
    props = read_properties(skill_dir)
    assert props.name == "my-skill"
    assert props.description == "A test skill"


def test_read_with_allowed_tools(tmp_path):
    """allowed-tools should be parsed into SkillProperties."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: my-skill
description: A test skill
allowed-tools: Bash(jq:*) Bash(git:*)
---
Body
""")
    props = read_properties(skill_dir)
    assert props.allowed_tools == "Bash(jq:*) Bash(git:*)"
    # Verify to_dict outputs as "allowed-tools" (hyphenated)
    d = props.to_dict()
    assert d["allowed-tools"] == "Bash(jq:*) Bash(git:*)"


def test_read_properties_exceeds_size_limit(tmp_path):
    """File size exceeding 1MB should raise ParseError."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text("x" * (1024 * 1024 + 2))

    with pytest.raises(ParseError, match="exceeds 1MB size limit"):
        read_properties(skill_dir)


def test_read_properties_unicode_error(tmp_path):
    """Invalid UTF-8 file should raise ParseError."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_bytes(b"\xff\xfe\xfd")

    with pytest.raises(ParseError, match="is not valid UTF-8"):
        read_properties(skill_dir)


def test_invalid_yaml_characters():
    """YAML with unprintable/invalid characters (like ANSI escapes) should not crash."""
    content = "---\nname: 'test\033[31mred\033[0m'\ndescription: desc\n---\nbody"
    with pytest.raises(ParseError, match="Invalid YAML"):
        parse_frontmatter(content)


def test_description_length_limit(tmp_path):
    """Description exceeding length limit should raise ValidationError."""
    from skills_ref.constants import MAX_DESCRIPTION_LENGTH

    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    over = "a" * (MAX_DESCRIPTION_LENGTH + 1)
    (skill_dir / "SKILL.md").write_text(f"""---
name: my-skill
description: {over}
---
Body
""")
    with pytest.raises(
        ValidationError, match=rf"exceeds {MAX_DESCRIPTION_LENGTH} character limit"
    ):
        read_properties(skill_dir)


def test_name_length_limit(tmp_path):
    """Name exceeding length limit should raise ValidationError."""
    from skills_ref.constants import MAX_SKILL_NAME_LENGTH

    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    over = "a" * (MAX_SKILL_NAME_LENGTH + 1)
    (skill_dir / "SKILL.md").write_text(f"""---
name: {over}
description: desc
---
Body
""")
    with pytest.raises(
        ValidationError, match=rf"exceeds {MAX_SKILL_NAME_LENGTH} character limit"
    ):
        read_properties(skill_dir)


def test_metadata_keys_limit(tmp_path):
    """Metadata with too many keys should raise ValidationError/ParseError."""
    from skills_ref.constants import MAX_METADATA_KEYS_COUNT

    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()

    metadata_block = "\n".join(
        [f"  key{i}: value{i}" for i in range(MAX_METADATA_KEYS_COUNT + 1)]
    )

    (skill_dir / "SKILL.md").write_text(f"""---
name: my-skill
description: desc
metadata:
{metadata_block}
---
Body
""")
    with pytest.raises(
        ParseError, match=rf"exceeds {MAX_METADATA_KEYS_COUNT} keys limit"
    ):
        read_properties(skill_dir)


def test_validate_frontmatter_metadata_limit():
    """_validate_frontmatter should enforce metadata keys limit."""
    from skills_ref.constants import MAX_METADATA_KEYS_COUNT

    metadata = {
        "name": "my-skill",
        "description": "desc",
        "metadata": {
            f"key{i}": f"value{i}" for i in range(MAX_METADATA_KEYS_COUNT + 1)
        },
    }
    with pytest.raises(
        ParseError, match=rf"exceeds {MAX_METADATA_KEYS_COUNT} keys limit"
    ):
        _validate_frontmatter(metadata)


def test_internal_parsing_error_is_sanitized(monkeypatch):
    """Non-YAMLError from strictyaml.load must produce a sanitized message."""
    import skills_ref.parser as parser_module

    monkeypatch.setattr(
        parser_module.strictyaml,
        "load",
        lambda *a, **kw: (_ for _ in ()).throw(
            AttributeError("secret internal detail")
        ),
    )

    content = "---\nname: my-skill\n---\nbody"
    with pytest.raises(ParseError) as exc_info:
        parse_frontmatter(content)

    assert "Internal parsing error" in str(exc_info.value)
    assert "secret internal detail" not in str(exc_info.value)


def test_find_skill_md_handles_oserror(monkeypatch):
    """find_skill_md should return None and handle OSError."""
    from pathlib import Path

    def mock_is_file(self):
        raise OSError("Permission denied")

    monkeypatch.setattr(Path, "is_file", mock_is_file)

    # We pass a Path object, when find_skill_md checks path.is_file(), it raises OSError
    result = find_skill_md(Path("/some/dummy/path"))
    assert result is None


def test_find_skill_md_handles_runtime_error(monkeypatch):
    """find_skill_md should return None and handle RuntimeError."""
    from pathlib import Path

    def mock_is_file(self):
        raise RuntimeError("Symlink loop")

    monkeypatch.setattr(Path, "is_file", mock_is_file)

    result = find_skill_md(Path("/some/dummy/path"))
    assert result is None


def test_validate_frontmatter_rejects_complex_values_for_license():
    """_validate_frontmatter should reject list or dict under 'license' field."""
    metadata = {"name": "my-skill", "description": "desc", "license": ["MIT", "Apache"]}
    with pytest.raises(
        ParseError,
        match="Complex structures \\(dict/list\\) are not allowed in frontmatter field 'license'",
    ):
        _validate_frontmatter(metadata)


def test_validate_frontmatter_rejects_complex_values_for_unexpected_fields():
    """_validate_frontmatter should reject list or dict under unexpected fields."""
    metadata = {
        "name": "my-skill",
        "description": "desc",
        "unexpected_field": {"key": "value"},
    }
    with pytest.raises(
        ParseError,
        match="Complex structures \\(dict/list\\) are not allowed in frontmatter field 'unexpected_field'",
    ):
        _validate_frontmatter(metadata)
