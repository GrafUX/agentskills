"""Tests for validator module."""

from skills_ref.validator import validate, validate_metadata


def test_valid_skill(tmp_path):
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: my-skill
description: A test skill
---
# My Skill
""")
    errors = validate(skill_dir)
    assert errors == []


def test_nonexistent_path(tmp_path):
    errors = validate(tmp_path / "nonexistent")
    assert len(errors) == 1
    assert "does not exist" in errors[0]


def test_not_a_directory(tmp_path):
    file_path = tmp_path / "file.txt"
    file_path.write_text("test")
    errors = validate(file_path)
    assert len(errors) == 1
    assert "Not a directory" in errors[0]


def test_missing_skill_md(tmp_path):
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    errors = validate(skill_dir)
    assert len(errors) == 1
    assert "Missing required file: SKILL.md" in errors[0]


def test_invalid_name_uppercase(tmp_path):
    skill_dir = tmp_path / "MySkill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: MySkill
description: A test skill
---
Body
""")
    errors = validate(skill_dir)
    assert any("lowercase" in e for e in errors)


def test_name_too_long(tmp_path):
    long_name = "a" * 70  # Exceeds 64 char limit
    skill_dir = tmp_path / long_name
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(f"""---
name: {long_name}
description: A test skill
---
Body
""")
    errors = validate(skill_dir)
    assert any("exceeds" in e and "character limit" in e for e in errors)


def test_name_leading_hyphen(tmp_path):
    skill_dir = tmp_path / "-my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: -my-skill
description: A test skill
---
Body
""")
    errors = validate(skill_dir)
    assert any("cannot start or end with a hyphen" in e for e in errors)


def test_name_consecutive_hyphens(tmp_path):
    skill_dir = tmp_path / "my--skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: my--skill
description: A test skill
---
Body
""")
    errors = validate(skill_dir)
    assert any("consecutive hyphens" in e for e in errors)


def test_name_invalid_characters(tmp_path):
    skill_dir = tmp_path / "my_skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: my_skill
description: A test skill
---
Body
""")
    errors = validate(skill_dir)
    assert any("invalid characters" in e for e in errors)


def test_name_directory_mismatch(tmp_path):
    skill_dir = tmp_path / "wrong-name"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: correct-name
description: A test skill
---
Body
""")
    errors = validate(skill_dir)
    assert any("must match skill name" in e for e in errors)


def test_unexpected_fields(tmp_path):
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: my-skill
description: A test skill
unknown_field: should not be here
---
Body
""")
    errors = validate(skill_dir)
    assert any("Unexpected fields" in e for e in errors)


def test_valid_with_all_fields(tmp_path):
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: my-skill
description: A test skill
license: MIT
metadata:
  author: Test
---
Body
""")
    errors = validate(skill_dir)
    assert errors == []


def test_allowed_tools_accepted(tmp_path):
    """allowed-tools is accepted (experimental feature)."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: my-skill
description: A test skill
allowed-tools: Bash(jq:*) Bash(git:*)
---
Body
""")
    errors = validate(skill_dir)
    assert errors == []


def test_i18n_chinese_name(tmp_path):
    """Chinese characters are allowed in skill names."""
    skill_dir = tmp_path / "技能"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: 技能
description: A skill with Chinese name
---
Body
""")
    errors = validate(skill_dir)
    assert errors == []


def test_i18n_russian_name_with_hyphens(tmp_path):
    """Russian names with hyphens are allowed."""
    skill_dir = tmp_path / "мой-навык"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: мой-навык
description: A skill with Russian name
---
Body
""")
    errors = validate(skill_dir)
    assert errors == []


def test_i18n_russian_lowercase_valid(tmp_path):
    """Russian lowercase names should be accepted."""
    skill_dir = tmp_path / "навык"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: навык
description: A skill with Russian lowercase name
---
Body
""")
    errors = validate(skill_dir)
    assert errors == []


def test_i18n_russian_uppercase_rejected(tmp_path):
    """Russian uppercase names should be rejected."""
    skill_dir = tmp_path / "НАВЫК"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: НАВЫК
description: A skill with Russian uppercase name
---
Body
""")
    errors = validate(skill_dir)
    assert any("lowercase" in e for e in errors)


def test_description_too_long(tmp_path):
    """Description exceeding 1024 chars should fail."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    long_desc = "x" * 1100
    (skill_dir / "SKILL.md").write_text(f"""---
name: my-skill
description: {long_desc}
---
Body
""")
    errors = validate(skill_dir)
    assert any("exceed" in e and "1024" in e for e in errors)


def test_valid_compatibility(tmp_path):
    """Valid compatibility field should be accepted."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: my-skill
description: A test skill
compatibility: Requires Python 3.11+
---
Body
""")
    errors = validate(skill_dir)
    assert errors == []


def test_compatibility_too_long(tmp_path):
    """Compatibility exceeding 500 chars should fail."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    long_compat = "x" * 550
    (skill_dir / "SKILL.md").write_text(f"""---
name: my-skill
description: A test skill
compatibility: {long_compat}
---
Body
""")
    errors = validate(skill_dir)
    assert any("exceeds" in e and "500" in e for e in errors)


def test_nfkc_normalization(tmp_path):
    """Skill names are NFKC normalized before validation.

    The name 'café' can be represented two ways:
    - Precomposed: 'café' (4 chars, 'é' is U+00E9)
    - Decomposed: 'café' (5 chars, 'e' + combining acute U+0301)

    NFKC normalizes both to the precomposed form.
    """
    # Use decomposed form: 'cafe' + combining acute accent (U+0301)
    decomposed_name = "cafe\u0301"  # 'café' with combining accent
    composed_name = "café"  # precomposed form

    # Directory uses composed form, SKILL.md uses decomposed - should match after normalization
    skill_dir = tmp_path / composed_name
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(f"""---
name: {decomposed_name}
description: A test skill
---
Body
""")
    errors = validate(skill_dir)
    assert errors == [], f"Expected no errors, got: {errors}"


def test_validate_exceeds_size_limit(tmp_path):
    """File size exceeding 1MB should return a validation error."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text("x" * (1024 * 1024 + 2))

    errors = validate(skill_dir)
    assert len(errors) == 1
    assert "exceeds 1MB size limit" in errors[0]


def test_validate_unicode_error(tmp_path):
    """Invalid UTF-8 file should return a validation error."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_bytes(b"\xff\xfe\xfd")

    errors = validate(skill_dir)
    assert len(errors) == 1
    assert "is not valid UTF-8" in errors[0]


def test_license_too_long(tmp_path):
    """License exceeding 100 chars should fail."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    long_license = "x" * 150
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
    """Allowed tools exceeding 1024 chars should fail."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    long_tools = "x" * 1100
    (skill_dir / "SKILL.md").write_text(f"""---
name: my-skill
description: A test skill
allowed-tools: {long_tools}
---
Body
""")
    errors = validate(skill_dir)
    assert any("exceed" in e and "1024" in e for e in errors)


def test_metadata_key_too_long(tmp_path):
    """Metadata key exceeding 64 chars should fail."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    long_key = "x" * 70
    (skill_dir / "SKILL.md").write_text(f"""---
name: my-skill
description: A test skill
metadata:
  {long_key}: value
---
Body
""")
    errors = validate(skill_dir)
    assert any("exceeds" in e and "64" in e for e in errors)


def test_metadata_value_too_long(tmp_path):
    """Metadata value exceeding 1024 chars should fail."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    long_value = "x" * 1100
    (skill_dir / "SKILL.md").write_text(f"""---
name: my-skill
description: A test skill
metadata:
  key: {long_value}
---
Body
""")
    errors = validate(skill_dir)
    assert any("exceeds" in e and "1024" in e for e in errors)


def test_metadata_not_dict(tmp_path):
    """Metadata that is not a dict should fail."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: my-skill
description: A test skill
metadata: not a dict
---
Body
""")
    errors = validate(skill_dir)
    assert any("must be a dictionary" in e for e in errors)


def test_metadata_keys_limit(tmp_path):
    """Metadata with too many keys should return a validation error."""
    from skills_ref.constants import MAX_METADATA_KEYS_COUNT

    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()

    metadata_block = "\n".join(
        [f"  key{i}: value{i}" for i in range(MAX_METADATA_KEYS_COUNT + 1)]
    )

    (skill_dir / "SKILL.md").write_text(f"""---
name: my-skill
description: A test skill
metadata:
{metadata_block}
---
Body
""")
    errors = validate(skill_dir)
    assert any(f"exceeds {MAX_METADATA_KEYS_COUNT} keys limit" in e for e in errors)


def test_validate_metadata_happy_path():
    """Test validate_metadata with completely valid input."""
    meta = {
        "name": "my-skill",
        "description": "A very useful test skill",
        "compatibility": "Compatible with GPT-4",
        "license": "MIT",
        "allowed-tools": "Bash(jq:*)",
        "metadata": {"version": "1.0.0", "author": "Jules"},
    }
    errors = validate_metadata(meta)
    assert errors == []


def test_validate_metadata_not_a_dictionary():
    """Test validate_metadata when input is not a dictionary."""
    errors = validate_metadata("not a dictionary")
    assert len(errors) == 1
    assert "must be a dictionary" in errors[0]

    errors = validate_metadata(None)
    assert len(errors) == 1
    assert "must be a dictionary" in errors[0]

    errors = validate_metadata([1, 2, 3])
    assert len(errors) == 1
    assert "must be a dictionary" in errors[0]


def test_validate_metadata_missing_required_fields():
    """Test validate_metadata when required fields are missing."""
    errors = validate_metadata({})
    assert any("Missing required field in frontmatter: name" in e for e in errors)
    assert any(
        "Missing required field in frontmatter: description" in e for e in errors
    )


def test_validate_metadata_invalid_types():
    """Test validate_metadata when standard fields have invalid types."""
    meta_name_list = {
        "name": ["not", "a", "string"],
        "description": "Valid description",
    }
    errors = validate_metadata(meta_name_list)
    assert any("Field 'name' must be a non-empty string" in e for e in errors)

    meta_desc_int = {"name": "my-skill", "description": 12345}
    errors = validate_metadata(meta_desc_int)
    assert any("Field 'description' must be a non-empty string" in e for e in errors)

    meta_compat_dict = {
        "name": "my-skill",
        "description": "Valid description",
        "compatibility": {"version": 1},
    }
    errors = validate_metadata(meta_compat_dict)
    assert any("Field 'compatibility' must be a string" in e for e in errors)

    meta_license_list = {
        "name": "my-skill",
        "description": "Valid description",
        "license": ["MIT", "Apache"],
    }
    errors = validate_metadata(meta_license_list)
    assert any("Field 'license' must be a string" in e for e in errors)

    meta_tools_bool = {
        "name": "my-skill",
        "description": "Valid description",
        "allowed-tools": True,
    }
    errors = validate_metadata(meta_tools_bool)
    assert any("Field 'allowed-tools' must be a string" in e for e in errors)


def test_validate_metadata_mixed_key_types_security():
    """Test validate_metadata with non-string/mixed key types in the top-level metadata dict.

    This ensures that sorting or set operations on keys do not trigger a TypeError DoS.
    """
    meta = {
        "name": "my-skill",
        "description": "A valid description",
        123: "non-string key",
        None: "another non-string key",
    }
    errors = validate_metadata(meta)
    # The non-string keys are unexpected fields and should be safely reported
    assert len(errors) > 0
    assert any("Unexpected fields in frontmatter" in e for e in errors)
    assert any("123" in e for e in errors)
    assert any("None" in e for e in errors)


def test_validate_metadata_custom_metadata_security():
    """Test nested metadata dict structure and mixed key types in the metadata block."""
    meta = {
        "name": "my-skill",
        "description": "A valid description",
        "metadata": {
            999: "integer key",
            "valid_key": ["not", "a", "string", "value"],
            "another_key": {"nested": "dict"},
        },
    }
    errors = validate_metadata(meta)
    assert len(errors) > 0
    assert any("Metadata keys must be strings" in e for e in errors)
    assert any("Metadata value for 'valid_key' must be a string" in e for e in errors)
    assert any("Metadata value for 'another_key' must be a string" in e for e in errors)


def test_validate_metadata_field_length_limits():
    """Test validate_metadata field length boundary/limits."""
    # Exceed name limit
    meta_name_long = {"name": "x" * 150, "description": "Valid description"}
    errors = validate_metadata(meta_name_long)
    assert any("exceeds" in e and "character limit" in e for e in errors)

    # Exceed description limit
    meta_desc_long = {"name": "my-skill", "description": "x" * 2000}
    errors = validate_metadata(meta_desc_long)
    assert any("exceeds" in e and "character limit" in e for e in errors)

    # Exceed compatibility limit
    meta_compat_long = {
        "name": "my-skill",
        "description": "Valid description",
        "compatibility": "x" * 600,
    }
    errors = validate_metadata(meta_compat_long)
    assert any("exceeds" in e and "character limit" in e for e in errors)

    # Exceed license limit
    meta_license_long = {
        "name": "my-skill",
        "description": "Valid description",
        "license": "x" * 150,
    }
    errors = validate_metadata(meta_license_long)
    assert any("exceeds" in e and "character limit" in e for e in errors)

    # Exceed allowed-tools limit
    meta_tools_long = {
        "name": "my-skill",
        "description": "Valid description",
        "allowed-tools": "x" * 1200,
    }
    errors = validate_metadata(meta_tools_long)
    assert any("exceed" in e and "character limit" in e for e in errors)
