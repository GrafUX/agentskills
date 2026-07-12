"""Generate <available_skills> XML prompt block for agent system prompts."""

import html
from pathlib import Path

from .constants import MAX_SKILLS_PER_PROMPT
from .errors import SkillError
from .parser import find_skill_md, read_properties


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

    lines = ["<available_skills>"]
    seen = set()

    for d in skill_dirs:
        try:
            skill_dir = Path(d).resolve()
            if skill_dir in seen:
                continue

            if len(seen) >= MAX_SKILLS_PER_PROMPT:
                raise SkillError(
                    f"Number of skills exceeds maximum limit of {MAX_SKILLS_PER_PROMPT}"
                )

            props = read_properties(skill_dir)
            seen.add(skill_dir)

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
        except (OSError, RuntimeError) as e:
            error_msg = (
                str(e.strerror)
                if hasattr(e, "strerror")
                else "Symlink loop or unresolvable path"
            )
            raise SkillError(
                f"Failed to process skill directory {Path(d).name}: {error_msg}"
            )

    lines.append("</available_skills>")

    return "\n".join(lines)
