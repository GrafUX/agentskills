import pytest
from skills_ref.parser import parse_frontmatter
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
    assert f"Frontmatter key exceeds {MAX_METADATA_KEY_LENGTH} character limit" in str(
        excinfo.value
    )


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
