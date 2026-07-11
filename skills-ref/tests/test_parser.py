"""Tests for parser module."""

import pytest

from skills_ref.parser import (
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


def test_parse_frontmatter_metadata_limit():
    """parse_frontmatter should enforce metadata keys limit."""
    from skills_ref.constants import MAX_METADATA_KEYS_COUNT

    metadata_block = "\n".join(
        [f"  key{i}: value{i}" for i in range(MAX_METADATA_KEYS_COUNT + 1)]
    )
    content = f"""---
name: my-skill
description: desc
metadata:
{metadata_block}
---
Body
"""
    with pytest.raises(
        ParseError, match=rf"exceeds {MAX_METADATA_KEYS_COUNT} keys limit"
    ):
        parse_frontmatter(content)


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


def test_parse_frontmatter_generic_exception():
    """YAML with unprintable control characters raises a generic exception during strictyaml.load."""
    content = "---\nname: 'test\033[31mred\033[0m'\ndescription: desc\n---\nbody"
    with pytest.raises(ParseError) as exc_info:
        parse_frontmatter(content)

    assert "Invalid YAML in frontmatter: Internal parsing error" in str(exc_info.value)


def test_parse_frontmatter_strictyaml_generic_exception(monkeypatch):
    """An unhandled generic Exception during strictyaml.load raises ParseError."""
    import skills_ref.parser as parser_module

    monkeypatch.setattr(
        parser_module.strictyaml,
        "load",
        lambda *a, **kw: (_ for _ in ()).throw(
            RuntimeError("An unhandled runtime error occurred")
        ),
    )

    content = "---\nname: my-skill\n---\nbody"
    with pytest.raises(ParseError) as exc_info:
        parse_frontmatter(content)

    assert "Invalid YAML in frontmatter: Internal parsing error" in str(exc_info.value)
    assert "An unhandled runtime error occurred" not in str(exc_info.value)


def test_parse_frontmatter_long_yaml_error(monkeypatch):
    """Test that extremely long YAML error messages are truncated to 1000 characters."""
    import strictyaml
    import skills_ref.parser as parser_module

    long_err_msg = "x" * 1200
    monkeypatch.setattr(
        parser_module.strictyaml,
        "load",
        lambda *a, **kw: (_ for _ in ()).throw(strictyaml.YAMLError(long_err_msg)),
    )

    content = "---\nname: my-skill\n---\nbody"
    with pytest.raises(ParseError) as exc_info:
        parse_frontmatter(content)

    assert len(str(exc_info.value)) <= 1050  # 1000 chars + prefix and trailing dots
    assert str(exc_info.value).endswith("...")
