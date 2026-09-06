"""Generate <available_skills> XML prompt block for agent system prompts."""

import html
from pathlib import Path

from .constants import MAX_SKILLS_PER_PROMPT
from .errors import SkillError
from .parser import read_properties, _safe_name, _sanitize_error_text


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

    if len(skill_dirs) > MAX_SKILLS_PER_PROMPT:
        raise SkillError(
            f"Number of skill directories exceeds maximum limit of {MAX_SKILLS_PER_PROMPT}"
        )

    lines = ["<available_skills>"]
    seen = set()
    seen_unresolved = set()

    for d in skill_dirs:
        if d in seen_unresolved:
            continue
        seen_unresolved.add(d)

        path = Path(d)
        try:
            skill_dir = path.resolve()
            if skill_dir in seen:
                continue

            props = read_properties(skill_dir)
            seen.add(skill_dir)

            sanitized_name = (
                _sanitize_error_text(props.name)
                .replace("\n", " ")
                .replace("\r", " ")
                .replace("\t", " ")
            )
            sanitized_description = (
                _sanitize_error_text(props.description)
                .replace("\n", " ")
                .replace("\r", " ")
                .replace("\t", " ")
            )
            sanitized_path = (
                _sanitize_error_text(str(props.skill_md_path))
                .replace("\n", " ")
                .replace("\r", " ")
                .replace("\t", " ")
            )

            lines.append("<skill>")
            lines.append("<name>")
            lines.append(html.escape(sanitized_name))
            lines.append("</name>")
            lines.append("<description>")
            lines.append(html.escape(sanitized_description))
            lines.append("</description>")

            lines.append("<location>")
            lines.append(html.escape(sanitized_path))
            lines.append("</location>")

            lines.append("</skill>")
        except (OSError, RuntimeError) as e:
            error_msg = getattr(e, "strerror", None)
            if not error_msg:
                error_msg = "Symlink loop or unresolvable path"
            raise SkillError(
                f"Failed to process skill directory {_safe_name(path.name)}: {error_msg}"
            )

    lines.append("</available_skills>")

    return "\n".join(lines)
