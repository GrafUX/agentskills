"""YAML frontmatter parsing for SKILL.md files."""

from pathlib import Path
from typing import Optional

import strictyaml

from .constants import (
    MAX_ALLOWED_TOOLS_LENGTH,
    MAX_COMPATIBILITY_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    MAX_LICENSE_LENGTH,
    MAX_METADATA_KEY_LENGTH,
    MAX_METADATA_VALUE_LENGTH,
    MAX_SKILL_NAME_LENGTH,
)
from .errors import ParseError, ValidationError
from .models import SkillProperties


def find_skill_md(skill_dir: Path) -> Optional[Path]:
    """Find the SKILL.md file in a skill directory.

    Prefers SKILL.md (uppercase) but accepts skill.md (lowercase).

    Args:
        skill_dir: Path to the skill directory

    Returns:
        Path to the SKILL.md file, or None if not found
    """
    try:
        for name in ("SKILL.md", "skill.md"):
            path = skill_dir / name
            if path.is_file():
                return path
    except OSError:
        pass
    except RuntimeError:
        pass
    return None


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from SKILL.md content.

    Args:
        content: Raw content of SKILL.md file

    Returns:
        Tuple of (metadata dict, markdown body)

    Raises:
        ParseError: If frontmatter is missing or invalid
    """
    if not content.startswith("---"):
        raise ParseError("SKILL.md must start with YAML frontmatter (---)")

    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ParseError("SKILL.md frontmatter not properly closed with ---")

    frontmatter_str = parts[1]
    body = parts[2].strip()

    try:
        parsed = strictyaml.load(frontmatter_str)
        metadata = parsed.data
    except Exception as e:
        # Catch all exceptions because strictyaml can raise non-YAMLError exceptions
        # on certain invalid inputs (e.g. AttributeError on unprintable characters)
        raise ParseError(f"Invalid YAML in frontmatter: {e}")

    if not isinstance(metadata, dict):
        raise ParseError("SKILL.md frontmatter must be a YAML mapping")

    if "metadata" in metadata and isinstance(metadata["metadata"], dict):
        metadata["metadata"] = {str(k): str(v) for k, v in metadata["metadata"].items()}

    return metadata, body


def read_properties(skill_dir: Path) -> SkillProperties:
    """Read skill properties from SKILL.md frontmatter.

    This function parses the frontmatter and returns properties.
    It does NOT perform full validation. Use validate() for that.

    Args:
        skill_dir: Path to the skill directory

    Returns:
        SkillProperties with parsed metadata

    Raises:
        ParseError: If SKILL.md is missing or has invalid YAML
        ValidationError: If required fields (name, description) are missing
    """
    skill_dir = Path(skill_dir)

    try:
        skill_md = find_skill_md(skill_dir)

        if skill_md is None:
            raise ParseError(f"SKILL.md not found in {skill_dir.name}")

        with open(skill_md, "r", encoding="utf-8") as f:
            content = f.read(1024 * 1024 + 1)
            if len(content) > 1024 * 1024:
                raise ParseError(f"SKILL.md in {skill_dir.name} exceeds 1MB size limit")
    except OSError as e:
        raise ParseError(f"Failed to read SKILL.md in {skill_dir.name}: {e.strerror}")
    except UnicodeDecodeError:
        raise ParseError(f"SKILL.md in {skill_dir.name} is not valid UTF-8")
    except RuntimeError:
        raise ParseError(
            f"Failed to read SKILL.md in {skill_dir.name}: Symlink loop or unresolvable path"
        )

    metadata, _ = parse_frontmatter(content)

    if "name" not in metadata:
        raise ValidationError("Missing required field in frontmatter: name")
    if "description" not in metadata:
        raise ValidationError("Missing required field in frontmatter: description")

    name = metadata["name"]
    description = metadata["description"]

    if not isinstance(name, str) or not name.strip():
        raise ValidationError("Field 'name' must be a non-empty string")
    if len(name) > MAX_SKILL_NAME_LENGTH:
        raise ValidationError(f"Field 'name' exceeds {MAX_SKILL_NAME_LENGTH} character limit")

    if not isinstance(description, str) or not description.strip():
        raise ValidationError("Field 'description' must be a non-empty string")
    if len(description) > MAX_DESCRIPTION_LENGTH:
        raise ValidationError(
            f"Field 'description' exceeds {MAX_DESCRIPTION_LENGTH} character limit"
        )

    license_val = metadata.get("license")
    if license_val is not None:
        if not isinstance(license_val, str):
            raise ValidationError("Field 'license' must be a string")
        if len(license_val) > MAX_LICENSE_LENGTH:
            raise ValidationError(f"Field 'license' exceeds {MAX_LICENSE_LENGTH} character limit")

    comp_val = metadata.get("compatibility")
    if comp_val is not None:
        if not isinstance(comp_val, str):
            raise ValidationError("Field 'compatibility' must be a string")
        if len(comp_val) > MAX_COMPATIBILITY_LENGTH:
            raise ValidationError(
                f"Field 'compatibility' exceeds {MAX_COMPATIBILITY_LENGTH} character limit"
            )

    tools_val = metadata.get("allowed-tools")
    if tools_val is not None:
        if not isinstance(tools_val, str):
            raise ValidationError("Field 'allowed-tools' must be a string")
        if len(tools_val) > MAX_ALLOWED_TOOLS_LENGTH:
            raise ValidationError(
                f"Field 'allowed-tools' exceeds {MAX_ALLOWED_TOOLS_LENGTH} character limit"
            )

    custom_metadata = metadata.get("metadata")
    if custom_metadata is not None:
        if not isinstance(custom_metadata, dict):
            raise ValidationError("Field 'metadata' must be a dictionary")

        for k, v in custom_metadata.items():
            if not isinstance(k, str):
                raise ValidationError("Metadata keys must be strings")
            if len(k) > MAX_METADATA_KEY_LENGTH:
                raise ValidationError(
                    f"Metadata key '{k}' exceeds {MAX_METADATA_KEY_LENGTH} character limit"
                )
            if not isinstance(v, str):
                raise ValidationError(f"Metadata value for '{k}' must be a string")
            if len(v) > MAX_METADATA_VALUE_LENGTH:
                raise ValidationError(
                    f"Metadata value for '{k}' exceeds {MAX_METADATA_VALUE_LENGTH} character limit"
                )

    return SkillProperties(
        name=name.strip(),
        description=description.strip(),
        license=license_val,
        compatibility=comp_val,
        allowed_tools=tools_val,
        metadata=custom_metadata,
    )
