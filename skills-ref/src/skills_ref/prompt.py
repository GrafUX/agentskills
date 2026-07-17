"""Generate <available_skills> XML prompt block for agent system prompts."""

import html
from pathlib import Path

from .constants import MAX_SKILLS_PER_PROMPT
from .errors import SkillError
from .parser import find_skill_md, read_properties
from .sanitization import safe_name, sanitize_error_text


def to_prompt(skill_dirs: list[Path]) -> str:
    """Generate the <available_skills> XML block for inclusion in agent prompts.

    This XML format is what Anthropic uses and recommends for Claude models.
    Skill Clients may format skill information differently to suit their
    models or preferences.

    Args:
        skill_dirs: List of paths to skill directories

    Returns:
        XML string with <available_skills> block containing each skill's
        name, description, and location.

    Example output:
        <available_skills>
        <skill>
        <name>pdf-reader</name>
        <description>Read and extract text from PDF files</description>
        <location>/path/to/pdf-reader/SKILL.md</location>
        </skill>
        </available_skills>
    """
    if not skill_dirs:
        return "<available_skills>\n</available_skills>"

    # Lexically de-duplicate skill directories to prevent redundant resolve() calls
    unique_raw_dirs = []
    seen_raw = set()
    for skill_dir in skill_dirs:
        try:
            norm_path = Path(skill_dir)
            if norm_path not in seen_raw:
                seen_raw.add(norm_path)
                unique_raw_dirs.append(norm_path)
        except Exception:
            unique_raw_dirs.append(skill_dir)

    if len(seen_raw) > MAX_SKILLS_PER_PROMPT:
        raise SkillError(
            f"Number of skills exceeds the limit of {MAX_SKILLS_PER_PROMPT}"
        )

    # De-duplicate resolved skill directories using Path.resolve()
    unique_skill_dirs = []
    seen_paths = set()
    for skill_dir in unique_raw_dirs:
        try:
            resolved_path = Path(skill_dir).resolve()
            if resolved_path not in seen_paths:
                seen_paths.add(resolved_path)
                unique_skill_dirs.append(resolved_path)
        except (OSError, RuntimeError) as e:
            error_msg = (
                sanitize_error_text(str(e.strerror))
                if hasattr(e, "strerror")
                else "Symlink loop or unresolvable path"
            )
            raise SkillError(
                f"Failed to resolve skill directory {safe_name(Path(skill_dir).name)}: {error_msg}"
            )

    if len(unique_skill_dirs) > MAX_SKILLS_PER_PROMPT:
        raise SkillError(
            f"Number of skills exceeds the limit of {MAX_SKILLS_PER_PROMPT}"
        )

    lines = ["<available_skills>"]

    for skill_dir in unique_skill_dirs:
        try:
            props = read_properties(skill_dir)
        except (OSError, RuntimeError) as e:
            error_msg = (
                sanitize_error_text(str(e.strerror))
                if hasattr(e, "strerror")
                else "Symlink loop or unresolvable path"
            )
            raise SkillError(
                f"Failed to read properties for {safe_name(Path(skill_dir).name)}: {error_msg}"
            )

        lines.append("<skill>")
        lines.append("<name>")
        lines.append(html.escape(props.name))
        lines.append("</name>")
        lines.append("<description>")
        lines.append(html.escape(props.description))
        lines.append("</description>")

        skill_md_path = find_skill_md(skill_dir)
        lines.append("<location>")
        lines.append(html.escape(str(skill_md_path)))
        lines.append("</location>")

        lines.append("</skill>")

    lines.append("</available_skills>")

    return "\n".join(lines)
