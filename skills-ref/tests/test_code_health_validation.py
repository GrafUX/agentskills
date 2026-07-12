import pytest
from skills_ref.parser import read_properties
from skills_ref.errors import ValidationError


def test_read_properties_license_not_string(tmp_path):
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: name\ndescription: desc\nlicense:\n  key: val\n---\nbody"
    )
    with pytest.raises(ValidationError, match="Field 'license' must be a string"):
        read_properties(skill_dir)


def test_read_properties_license_dos_check(tmp_path):
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    # Ensure massive nested or non-string object stringified doesn't bypass/crash or exceeds limit
    (skill_dir / "SKILL.md").write_text(
        "---\nname: name\ndescription: desc\nlicense:\n  - some_list_item\n  - another_item\n---\nbody"
    )
    with pytest.raises(ValidationError, match="Field 'license'"):
        read_properties(skill_dir)
