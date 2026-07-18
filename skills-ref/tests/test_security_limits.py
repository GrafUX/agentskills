import pytest
from skills_ref.parser import parse_frontmatter
from skills_ref.errors import ParseError
from skills_ref.constants import (
    MAX_FRONTMATTER_FIELDS_COUNT,
    MAX_METADATA_KEY_LENGTH,
    MAX_FRONTMATTER_VALUE_LENGTH,
    MAX_SKILLS_PER_PROMPT,
)
from skills_ref.prompt import to_prompt
from skills_ref.errors import SkillError


def test_parse_frontmatter_too_many_fields():
    # Create frontmatter with more than MAX_FRONTMATTER_FIELDS_COUNT fields
    fields = {f"field{i}": "value" for i in range(MAX_FRONTMATTER_FIELDS_COUNT + 1)}
    yaml_lines = ["---"]
    for k, v in fields.items():
        yaml_lines.append(f"{k}: {v}")
    yaml_lines.append("---")
    yaml_lines.append("body")
    content = "\n".join(yaml_lines)

    with pytest.raises(ParseError) as excinfo:
        parse_frontmatter(content)
    assert f"Frontmatter exceeds {MAX_FRONTMATTER_FIELDS_COUNT} fields limit" in str(
        excinfo.value
    )


def test_parse_frontmatter_key_too_long():
    # Create frontmatter with a key longer than MAX_METADATA_KEY_LENGTH
    long_key = "a" * (MAX_METADATA_KEY_LENGTH + 1)
    content = f"---\n{long_key}: value\n---\nbody"

    with pytest.raises(ParseError) as excinfo:
        parse_frontmatter(content)
    assert "character limit" in str(excinfo.value)
    assert "Frontmatter key" in str(excinfo.value)


def test_parse_frontmatter_value_too_long():
    # Create frontmatter with a value longer than MAX_FRONTMATTER_VALUE_LENGTH
    long_value = "a" * (MAX_FRONTMATTER_VALUE_LENGTH + 1)
    content = f"---\nname: {long_value}\n---\nbody"

    with pytest.raises(ParseError) as excinfo:
        parse_frontmatter(content)
    assert (
        f"Frontmatter value for 'name' exceeds {MAX_FRONTMATTER_VALUE_LENGTH} character limit"
        in str(excinfo.value)
    )


def test_parse_frontmatter_non_string_key():
    # We want to test that non-string keys raise a ParseError
    # However, strictyaml often parses keys as strings anyway.
    # To definitely test this, we would need a way to force a non-string key.
    # If strictyaml converts it to string "1", then our current code won't catch it as non-string.
    # But if it DOES return it as int, our code SHOULD raise ParseError.

    content = "---\n1: value\n---\nbody"
    try:
        metadata, body = parse_frontmatter(content)
        # If it succeeded, it means strictyaml converted it to string "1"
        assert isinstance(list(metadata.keys())[0], str)
    except ParseError as e:
        # If it failed, it should be because it's not a string
        assert "Frontmatter keys must be strings" in str(e)


def test_to_prompt_limit_exceeded(tmp_path):
    # Create more than MAX_SKILLS_PER_PROMPT unique skill directories
    skill_dirs = []
    for i in range(MAX_SKILLS_PER_PROMPT + 1):
        skill_dir = tmp_path / f"skill-{i}"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: skill-{i}\ndescription: desc\n---\n"
        )
        skill_dirs.append(skill_dir)

    with pytest.raises(SkillError) as excinfo:
        to_prompt(skill_dirs)
    assert f"Number of skills exceeds the limit of {MAX_SKILLS_PER_PROMPT}" in str(
        excinfo.value
    )


def test_to_prompt_deduplication(tmp_path):
    # Create one skill directory
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: skill\ndescription: desc\n---\n")

    # Pass the same skill directory multiple times, should not raise error
    skill_dirs = [skill_dir] * (MAX_SKILLS_PER_PROMPT + 1)
    result = to_prompt(skill_dirs)
    assert result.count("<skill>") == 1


def test_error_message_sanitization(tmp_path):
    # Test ANSI stripping and truncation in error messages
    evil_name = "evil_\x1b[31mHACKED\x1b[0m_" + "A" * 200
    evil_dir = tmp_path / evil_name
    evil_dir.mkdir()
    # Missing SKILL.md will trigger ParseError in read_properties

    from skills_ref.parser import read_properties

    with pytest.raises(ParseError) as excinfo:
        read_properties(evil_dir)

    err_msg = str(excinfo.value)
    # Check for truncation (default 64 + "...")
    assert len(err_msg) < 150
    assert "..." in err_msg
    # Check for ANSI stripping
    assert "\x1b[31m" not in err_msg
    assert "HACKED" in err_msg


def test_metadata_key_sanitization():
    # Test sanitization of metadata keys in ParseError.
    # parse_frontmatter uses sanitize_error_text(key, max_len=100) for display;
    # use a key longer than 100 chars to ensure truncation with "..." is triggered.
    from skills_ref.constants import MAX_METADATA_KEY_LENGTH

    long_key = "K" * (MAX_METADATA_KEY_LENGTH + 101)
    content = f"---\nname: skill\ndescription: desc\n{long_key}: value\n---\nbody"

    with pytest.raises(ParseError) as excinfo:
        parse_frontmatter(content)

    err_msg = str(excinfo.value)
    assert len(err_msg) < 200
    assert "..." in err_msg
    assert long_key[:100] in err_msg
