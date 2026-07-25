import pytest
from skills_ref.parser import parse_frontmatter
from skills_ref.errors import ParseError


def test_metadata_complex_structure():
    yaml_str = """---
name: test
description: test
metadata:
  k:
    - 1
    - 2
---"""
    with pytest.raises(ParseError, match="cannot be a complex structure"):
        parse_frontmatter(yaml_str)


def test_specific_fields_not_string():
    for field in ("license", "allowed-tools", "compatibility"):
        yaml_str = f"""---
name: test
description: test
{field}:
  - complex
---"""
        with pytest.raises(ParseError, match=f"Field '{field}' must be a string"):
            parse_frontmatter(yaml_str)
