"""YAML frontmatter parsing for SKILL.md files."""

import re
from pathlib import Path
from typing import Optional

import strictyaml

from .constants import (
    MAX_ALLOWED_TOOLS_LENGTH,
    MAX_COMPATIBILITY_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    MAX_FRONTMATTER_FIELDS_COUNT,
    MAX_FRONTMATTER_VALUE_LENGTH,
    MAX_LICENSE_LENGTH,
    MAX_METADATA_KEY_LENGTH,
    MAX_METADATA_KEYS_COUNT,
    MAX_METADATA_VALUE_LENGTH,
    MAX_SKILL_NAME_LENGTH,
    MAX_UNTRUSTED_TEXT_LENGTH,
    MAX_FILE_SIZE,
)
from .errors import ParseError, ValidationError
from .models import SkillProperties


def _sanitize_error_text(text: str, max_len: int = MAX_UNTRUSTED_TEXT_LENGTH) -> str:
    """Strip ANSI escape codes and truncate untrusted strings for error messages."""
    # Strip ANSI escape codes
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    text = ansi_escape.sub("", text)
    # Truncate
    if len(text) > max_len:
        return text[:max_len] + "..."
    return text


def _safe_name(name: str) -> str:
    """Convenience wrapper to sanitize a directory or skill name for error messages."""
    return _sanitize_error_text(name, MAX_UNTRUSTED_TEXT_LENGTH)


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
        if isinstance(e, strictyaml.YAMLError):
            err_msg = _sanitize_error_text(str(e), max_len=1000)
            raise ParseError(f"Invalid YAML in frontmatter: {err_msg}")
        else:
            raise ParseError("Invalid YAML in frontmatter: Internal parsing error")

    if not isinstance(metadata, dict):
        raise ParseError("SKILL.md frontmatter must be a YAML mapping")

    if len(metadata) > MAX_FRONTMATTER_FIELDS_COUNT:
        raise ParseError(
            f"Frontmatter exceeds {MAX_FRONTMATTER_FIELDS_COUNT} fields limit"
        )

    for key, value in metadata.items():
        if not isinstance(key, str):
            raise ParseError("Frontmatter keys must be strings")

        display_key = _sanitize_error_text(key, max_len=100)
        if len(key) > MAX_METADATA_KEY_LENGTH:
            raise ParseError(
                f"Frontmatter key '{display_key}' exceeds {MAX_METADATA_KEY_LENGTH} character limit"
            )
        if isinstance(value, str) and len(value) > MAX_FRONTMATTER_VALUE_LENGTH:
            raise ParseError(
                f"Frontmatter value for '{display_key}' exceeds {MAX_FRONTMATTER_VALUE_LENGTH} character limit"
            )

    if "metadata" in metadata and isinstance(metadata["metadata"], dict):
        if len(metadata["metadata"]) > MAX_METADATA_KEYS_COUNT:
            raise ParseError(
                f"Field 'metadata' exceeds {MAX_METADATA_KEYS_COUNT} keys limit"
            )

        clean_metadata = {}
        for k, v in metadata["metadata"].items():
            if isinstance(v, (dict, list)):
                raise ParseError(
                    f"Complex structures not allowed in metadata values: '{k}'"
                )
            clean_metadata[str(k)] = str(v)
        metadata["metadata"] = clean_metadata

    return metadata, body


def _check_string_length(metadata: dict, field_name: str, max_length: int) -> None:
    """Validate string length limits and type of metadata fields parsed from SKILL.md.

    First verifies that the field is a string, then checks its length.
    """
    if field_name not in metadata:
        return
    value = metadata[field_name]
    if value is None:
        return

    if not isinstance(value, str):
        raise ValidationError(f"Field '{field_name}' must be a string")

    if len(value) > max_length:
        raise ValidationError(
            f"Field '{field_name}' exceeds {max_length} character limit"
        )


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
        ValidationError: If required fields (name, description) are missing or exceed length limits
    """
    skill_dir = Path(skill_dir)

    try:
        skill_md = find_skill_md(skill_dir)

        if skill_md is None:
            raise ParseError(f"SKILL.md not found in {_safe_name(skill_dir.name)}")

        with open(skill_md, "r", encoding="utf-8") as f:
            content = f.read(MAX_FILE_SIZE + 1)
            if len(content) > MAX_FILE_SIZE:
                raise ParseError(
                    f"SKILL.md in {_safe_name(skill_dir.name)} exceeds 1MB size limit"
                )
    except OSError as e:
        raise ParseError(
            f"Failed to read SKILL.md in {_safe_name(skill_dir.name)}: {_sanitize_error_text(str(e.strerror))}"
        )
    except UnicodeDecodeError:
        raise ParseError(f"SKILL.md in {_safe_name(skill_dir.name)} is not valid UTF-8")
    except RuntimeError:
        raise ParseError(
            f"Failed to read SKILL.md in {_safe_name(skill_dir.name)}: Symlink loop or unresolvable path"
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
        raise ValidationError(
            f"Field 'name' exceeds {MAX_SKILL_NAME_LENGTH} character limit"
        )

    if not isinstance(description, str) or not description.strip():
        raise ValidationError("Field 'description' must be a non-empty string")
    if len(description) > MAX_DESCRIPTION_LENGTH:
        raise ValidationError(
            f"Field 'description' exceeds {MAX_DESCRIPTION_LENGTH} character limit"
        )

    _check_string_length(metadata, "license", MAX_LICENSE_LENGTH)
    _check_string_length(metadata, "compatibility", MAX_COMPATIBILITY_LENGTH)
    _check_string_length(metadata, "allowed-tools", MAX_ALLOWED_TOOLS_LENGTH)

    license_val = metadata.get("license")
    comp_val = metadata.get("compatibility")
    tools_val = metadata.get("allowed-tools")

    custom_metadata = metadata.get("metadata")
    if custom_metadata is not None:
        if not isinstance(custom_metadata, dict):
            raise ValidationError("Field 'metadata' must be a dictionary")
        if len(custom_metadata) > MAX_METADATA_KEYS_COUNT:
            raise ValidationError(
                f"Field 'metadata' exceeds {MAX_METADATA_KEYS_COUNT} keys limit"
            )
        for k, v in custom_metadata.items():
            if not isinstance(k, str) or len(k) > MAX_METADATA_KEY_LENGTH:
                raise ValidationError(
                    f"Metadata key exceeds {MAX_METADATA_KEY_LENGTH} character limit"
                )
            if not isinstance(v, str) or len(v) > MAX_METADATA_VALUE_LENGTH:
                raise ValidationError(
                    f"Metadata value exceeds {MAX_METADATA_VALUE_LENGTH} character limit"
                )

    return SkillProperties(
        name=name.strip(),
        description=description.strip(),
        license=license_val,
        compatibility=comp_val,
        allowed_tools=tools_val,
        metadata=custom_metadata,
    )
