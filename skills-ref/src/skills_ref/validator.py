"""Validator for Agent Skills spec compliance."""

from pathlib import Path
from typing import Optional

import frontmatter

# Maximum field lengths
MAX_SKILL_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
MAX_COMPATIBILITY_LENGTH = 500
MAX_LICENSE_LENGTH = 100
MAX_ALLOWED_TOOLS_LENGTH = 1000

# Allowed frontmatter fields per Agent Skills Spec
ALLOWED_FIELDS = {
    "name",
    "description",
    "compatibility",
    "license",
    "allowed-tools",
}


def validate(skill_dir: Path) -> list[str]:
    """Validate a skill directory against the Agent Skills spec."""
    errors = []
    skill_path = Path(skill_dir)

    # Check if directory exists
    if not skill_path.is_dir():
        return [f"Skill directory does not exist: {skill_path}"]

    skill_md = skill_path / "SKILL.md"

    # Check if SKILL.md exists
    if not skill_md.is_file():
        return [f"SKILL.md not found in {skill_path}"]

    # Read and parse SKILL.md
    try:
        with open(skill_md, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)
    except UnicodeDecodeError:
        return [f"{skill_md} is not valid UTF-8"]
    except Exception as e:
        return [f"Failed to parse {skill_md}: {e}"]

    metadata = post.metadata

    # Validate metadata
    errors.extend(validate_metadata(metadata, skill_path))

    return errors


def validate_metadata(metadata: dict, skill_dir: Optional[Path] = None) -> list[str]:
    """Validate metadata dictionary against the Agent Skills spec."""
    errors = []

    # Validate required fields
    errors.extend(_validate_required_fields(metadata))

    # Validate field content
    errors.extend(_validate_metadata_fields(metadata))

    # Validate name
    if "name" in metadata:
        errors.extend(_validate_name(metadata["name"]))

    # Validate description
    if "description" in metadata:
        errors.extend(_validate_description(metadata["description"]))

    # Validate compatibility
    if "compatibility" in metadata:
        errors.extend(_validate_compatibility(metadata["compatibility"]))

    # Validate license
    if "license" in metadata:
        errors.extend(_validate_license(metadata["license"]))

    # Validate allowed-tools
    if "allowed-tools" in metadata:
        errors.extend(_validate_allowed_tools(metadata["allowed-tools"]))

    return errors


def _validate_required_fields(metadata: dict) -> list[str]:
    """Validate that required fields are present."""
    errors = []
    required = {"name", "description"}

    for field in required:
        if field not in metadata:
            errors.append(f"Required field '{field}' is missing")
        elif not isinstance(metadata[field], str) or not metadata[field].strip():
            errors.append(f"Required field '{field}' cannot be empty")

    return errors


def _validate_name(name: str) -> list[str]:
    """Validate skill name format."""
    errors = []

    if not isinstance(name, str):
        errors.append("Field 'name' must be a string")
        return errors

    if len(name) > MAX_SKILL_NAME_LENGTH:
        errors.append(
            f"Skill name exceeds {MAX_SKILL_NAME_LENGTH} character limit "
            f"({len(name)} chars)"
        )

    if not name.replace("-", "").replace("_", "").isalnum():
        errors.append(
            "Skill name must contain only alphanumeric characters, hyphens, or underscores"
        )

    return errors


def _validate_description(description: str) -> list[str]:
    """Validate description format."""
    errors = []

    if not isinstance(description, str):
        errors.append("Field 'description' must be a string")
        return errors

    if len(description) > MAX_DESCRIPTION_LENGTH:
        errors.append(
            f"Description exceeds {MAX_DESCRIPTION_LENGTH} character limit "
            f"({len(description)} chars)"
        )

    return errors


def _validate_compatibility(compatibility: str) -> list[str]:
    """Validate compatibility format."""
    errors = []

    if not isinstance(compatibility, str):
        errors.append("Field 'compatibility' must be a string")
        return errors

    if len(compatibility) > MAX_COMPATIBILITY_LENGTH:
        errors.append(
            f"Compatibility exceeds {MAX_COMPATIBILITY_LENGTH} character limit "
            f"({len(compatibility)} chars)"
        )

    return errors


def _validate_license(license_str: str) -> list[str]:
    """Validate license format."""
    errors = []

    if not isinstance(license_str, str):
        errors.append("Field 'license' must be a string")
        return errors

    if len(license_str) > MAX_LICENSE_LENGTH:
        errors.append(
            f"License exceeds {MAX_LICENSE_LENGTH} character limit "
            f"({len(license_str)} chars)"
        )

    return errors


def _validate_allowed_tools(allowed_tools: str) -> list[str]:
    """Validate allowed-tools format."""
    errors = []

    if not isinstance(allowed_tools, str):
        errors.append("Field 'allowed-tools' must be a string")
        return errors

    if len(allowed_tools) > MAX_ALLOWED_TOOLS_LENGTH:
        errors.append(
            f"Allowed-tools exceeds {MAX_ALLOWED_TOOLS_LENGTH} character limit "
            f"({len(allowed_tools)} chars)"
        )

    return errors


def _validate_metadata_fields(metadata: dict) -> list[str]:
    """Validate that only allowed fields are present."""
    errors = []

    for field in metadata:
        if field not in ALLOWED_FIELDS:
            errors.append(f"Unknown field '{field}' in metadata")

    return errors
