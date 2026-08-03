import pytest
from skills_ref.parser import parse_frontmatter, find_skill_md, read_properties
from skills_ref.errors import ParseError
from skills_ref.constants import (
    MAX_FRONTMATTER_FIELDS_COUNT,
    MAX_METADATA_KEY_LENGTH,
    MAX_FRONTMATTER_VALUE_LENGTH,
)


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
    content = "---\n1: value\n---\nbody"
    try:
        metadata, body = parse_frontmatter(content)
        # If it succeeded, it means strictyaml converted it to string "1"
        assert isinstance(list(metadata.keys())[0], str)
    except ParseError as e:
        # If it failed, it should be because it's not a string
        assert "Frontmatter keys must be strings" in str(e)


def test_symlink_path_traversal_protection(tmp_path):
    # Create a secret file outside the skill directory
    secret_file = tmp_path / "secret.txt"
    secret_file.write_text(
        "---\nname: secret-skill\ndescription: secret data\n---\nsecret content"
    )

    # Create the skill directory
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()

    # Create a symlink named SKILL.md inside skill_dir pointing to the secret file outside
    symlink_path = skill_dir / "SKILL.md"
    try:
        symlink_path.symlink_to(secret_file)
    except OSError:
        pytest.skip("Symlinks are not supported or not permitted on this platform")

    # find_skill_md should return None because the resolved SKILL.md is outside skill_dir
    assert find_skill_md(skill_dir) is None

    # Consequently, read_properties should raise a ParseError
    with pytest.raises(ParseError, match="SKILL.md not found in"):
        read_properties(skill_dir)


def test_skill_md_symlink_inside_dir(tmp_path):
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()

    real_md = skill_dir / "REAL_SKILL.md"
    real_md.write_text("---\nname: my-skill\ndescription: test\n---")

    skill_md = skill_dir / "SKILL.md"
    try:
        skill_md.symlink_to(real_md)
    except OSError:
        pytest.skip("Symlinks are not supported or not permitted on this platform")

    props = read_properties(skill_dir)
    assert props.name == "my-skill"


def test_validate_name_fail_fast_limits(monkeypatch):
    from skills_ref.validator import validate_metadata
    from skills_ref.constants import MAX_SKILL_NAME_LENGTH
    import unicodedata

    normalize_called = False
    original_normalize = unicodedata.normalize

    def mock_normalize(*args, **kwargs):
        nonlocal normalize_called
        normalize_called = True
        return original_normalize(*args, **kwargs)

    monkeypatch.setattr(unicodedata, "normalize", mock_normalize)

    # Long name exceeding MAX_SKILL_NAME_LENGTH
    long_name = "a" * (MAX_SKILL_NAME_LENGTH + 1)
    metadata = {
        "name": long_name,
        "description": "test desc",
    }

    errors = validate_metadata(metadata)
    assert len(errors) > 0
    assert any("exceeds" in err and "character limit" in err for err in errors)
    assert not normalize_called, (
        "unicodedata.normalize was called on an oversized name!"
    )


def test_read_properties_oserror_without_strerror(tmp_path, monkeypatch):
    from skills_ref.parser import read_properties
    from skills_ref.errors import ParseError
    import builtins

    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: test-skill\ndescription: desc\n---")

    def mock_open(*args, **kwargs):
        err = OSError("Something bad happened")
        err.strerror = None
        raise err

    monkeypatch.setattr(builtins, "open", mock_open)

    with pytest.raises(ParseError) as exc_info:
        read_properties(skill_dir)

    assert "Failed to read SKILL.md in test-skill: Unknown OS error" in str(
        exc_info.value
    )


def test_validate_oserror_without_strerror(tmp_path, monkeypatch):
    from skills_ref.validator import validate
    import builtins

    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: test-skill\ndescription: desc\n---")

    def mock_open(*args, **kwargs):
        err = OSError("Something bad happened")
        err.strerror = None
        raise err

    monkeypatch.setattr(builtins, "open", mock_open)

    errors = validate(skill_dir)
    assert len(errors) == 1
    assert "Failed to read SKILL.md in test-skill: Unknown OS error" in errors[0]
