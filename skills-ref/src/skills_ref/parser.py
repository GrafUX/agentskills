"""YAML frontmatter parsing for SKILL.md files."""

import re
from pathlib import Path

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
)
from .errors import ParseError, ValidationError
from .models import SkillProperties

ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]")

_WHITESPACE_MAP = str.maketrans("\n\r\t", "   ")


def _sanitize_error_text(text: str) -> str:
    """Strip ANSI escape codes and other potentially dangerous control characters from error messages."""
    if not isinstance(text, str):
        return ""
    text = ANSI_ESCAPE.sub("", text)
    # Filter out dangerous non-printable control characters, keeping safe whitespace like \n, \r, \t
    text = "".join(c for c in text if c in "\n\r\t" or c.isprintable())
    return text


def _safe_name(name: str, max_len: int = 64) -> str:
    """Sanitize and truncate untrusted strings (like directory names or inputs) reflected in error messages."""
    if not name:
        return ""
    sanitized = _sanitize_error_text(name).strip()
    # Replace newline, carriage return, and tab characters with spaces to prevent log/terminal injection
    sanitized = sanitized.translate(_WHITESPACE_MAP)
    if len(sanitized) > max_len:
        return sanitized[:max_len] + "..."
    return sanitized


def find_skill_md(skill_dir: Path) -> Path | None:
    """Find the SKILL.md file in a skill directory.

    Prefers SKILL.md (uppercase) but accepts skill.md (lowercase).

    Args:
        skill_dir: Path to the skill directory

    Returns:
        Path to the SKILL.md file, or None if not found
    """
    try:
        if not skill_dir.is_dir():
            return None
        for name in ("SKILL.md", "skill.md"):
            path = skill_dir / name
            if path.is_file():
                resolved_dir = skill_dir.resolve()
                resolved_path = path.resolve()
                if resolved_dir not in resolved_path.parents:
                    return None
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
    except Exception as e:  # noqa: BLE001
        # Catch all exceptions because strictyaml can raise non-YAMLError exceptions
        # on certain invalid inputs (e.g. AttributeError on unprintable characters)
        if isinstance(e, strictyaml.YAMLError):
            err_msg = _sanitize_error_text(str(e)).translate(_WHITESPACE_MAP)
            if len(err_msg) > 1000:
                err_msg = err_msg[:1000] + "..."
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

        len_key = len(key)
        if len_key > MAX_METADATA_KEY_LENGTH:
            display_key = _safe_name(key, max_len=100)
            raise ParseError(
                f"Frontmatter key '{display_key}' exceeds {MAX_METADATA_KEY_LENGTH} character limit"
            )
        if key != "metadata" and isinstance(value, (dict, list)):
            display_key = _safe_name(key, max_len=100)
            raise ParseError(
                f"Complex structures (dict/list) are not allowed in frontmatter field '{display_key}'"
            )
        if isinstance(value, str) and len(value) > MAX_FRONTMATTER_VALUE_LENGTH:
            display_key = _safe_name(key, max_len=100)
            raise ParseError(
                f"Frontmatter value for '{display_key}' exceeds {MAX_FRONTMATTER_VALUE_LENGTH} character limit"
            )

    if "metadata" in metadata and isinstance(metadata["metadata"], dict):
        if len(metadata["metadata"]) > MAX_METADATA_KEYS_COUNT:
            raise ParseError(
                f"Field 'metadata' exceeds {MAX_METADATA_KEYS_COUNT} keys limit"
            )
        sanitized_metadata = {}
        for k, v in metadata["metadata"].items():
            if isinstance(v, (dict, list)):
                raise ParseError(
                    "Complex structures (dict/list) are not allowed in 'metadata' values"
                )
            sanitized_metadata[str(k)] = str(v)
        metadata["metadata"] = sanitized_metadata

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
        ValidationError: If required fields (name, description) are missing or exceed length limits
    """
    skill_dir = Path(skill_dir)

    try:
        skill_md = find_skill_md(skill_dir)

        if skill_md is None:
            raise ParseError(f"SKILL.md not found in {_safe_name(skill_dir.name)}")

        with open(skill_md, "r", encoding="utf-8") as f:
            content = f.read(1024 * 1024 + 1)
            if len(content) > 1024 * 1024:
                raise ParseError(
                    f"SKILL.md in {_safe_name(skill_dir.name)} exceeds 1MB size limit"
                )
    except OSError as e:
        raise ParseError(
            f"Failed to read SKILL.md in {_safe_name(skill_dir.name)}: {e.strerror}"
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

    license_val = metadata.get("license")
    if license_val is not None:
        if not isinstance(license_val, str):
            raise ValidationError("Field 'license' must be a string")
        if len(license_val) > MAX_LICENSE_LENGTH:
            raise ValidationError(
                f"Field 'license' exceeds {MAX_LICENSE_LENGTH} character limit"
            )

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
        skill_md_path=skill_md,
    )
