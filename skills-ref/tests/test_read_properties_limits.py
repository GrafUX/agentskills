import pytest
from skills_ref.parser import read_properties
from skills_ref.errors import ValidationError, ParseError
from skills_ref.constants import (
    MAX_SKILL_NAME_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    MAX_LICENSE_LENGTH,
    MAX_METADATA_KEY_LENGTH,
    MAX_METADATA_VALUE_LENGTH,
    MAX_METADATA_KEYS_COUNT,
)

def test_read_properties_name_too_long(tmp_path):
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    long_name = "a" * (MAX_SKILL_NAME_LENGTH + 1)
    (skill_dir / "SKILL.md").write_text(f"---\nname: {long_name}\ndescription: desc\n---\nbody")
    with pytest.raises(ValidationError, match="Field 'name' exceeds"):
        read_properties(skill_dir)

def test_read_properties_description_too_long(tmp_path):
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    long_desc = "a" * (MAX_DESCRIPTION_LENGTH + 1)
    (skill_dir / "SKILL.md").write_text(f"---\nname: name\ndescription: {long_desc}\n---\nbody")
    with pytest.raises(ValidationError, match="Field 'description' exceeds"):
        read_properties(skill_dir)

def test_read_properties_license_too_long(tmp_path):
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    long_license = "a" * (MAX_LICENSE_LENGTH + 1)
    (skill_dir / "SKILL.md").write_text(f"---\nname: name\ndescription: desc\nlicense: {long_license}\n---\nbody")
    with pytest.raises(ValidationError, match="Field 'license' exceeds"):
        read_properties(skill_dir)

def test_read_properties_metadata_too_many_keys(tmp_path):
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    metadata = {f"k{i}": "v" for i in range(MAX_METADATA_KEYS_COUNT + 1)}
    yaml_lines = ["---", "name: name", "description: desc", "metadata:"]
    for k, v in metadata.items():
        yaml_lines.append(f"  {k}: {v}")
    yaml_lines.append("---")
    (skill_dir / "SKILL.md").write_text("\n".join(yaml_lines))
    # Note: this raises ParseError because it's caught in parse_frontmatter
    with pytest.raises(ParseError, match="Field 'metadata' exceeds.*keys limit"):
        read_properties(skill_dir)

def test_read_properties_metadata_key_too_long(tmp_path):
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    long_key = "a" * (MAX_METADATA_KEY_LENGTH + 1)
    (skill_dir / "SKILL.md").write_text(f"---\nname: name\ndescription: desc\nmetadata:\n  {long_key}: value\n---\nbody")
    with pytest.raises(ValidationError, match="Metadata key exceeds"):
        read_properties(skill_dir)

def test_read_properties_metadata_value_too_long(tmp_path):
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    long_value = "a" * (MAX_METADATA_VALUE_LENGTH + 1)
    (skill_dir / "SKILL.md").write_text(f"---\nname: name\ndescription: desc\nmetadata:\n  key: {long_value}\n---\nbody")
    with pytest.raises(ValidationError, match="Metadata value exceeds"):
        read_properties(skill_dir)
