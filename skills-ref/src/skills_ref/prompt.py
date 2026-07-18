"""Generate <available_skills> XML prompt block for agent system prompts."""

import html
from pathlib import Path

from .constants import MAX_SKILLS_PER_PROMPT
from .errors import SkillError
from .parser import find_skill_md, read_properties, _safe_name


def _skill_to_xml_lines(skill_dir: Path) -> list[str]:
    """Generate the XML lines for a single skill directory.

    Args:
        skill_dir: Path to the resolved skill directory.

    Returns:
        A list of strings representing the XML lines for the skill.
    """
    props = read_properties(skill_dir)
    skill_md_path = find_skill_md(skill_dir)

    lines = [
        "<skill>",
        "<name>",
        html.escape(props.name),
        "</name>",
        "<description>",
        html.escape(props.description),
        "</description>",
        "<location>",
        html.escape(str(skill_md_path)),
        "</location>",
        "</skill>",
    ]
    return lines


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
    resolved_cache = {}

    for d in skill_dirs:
        path = Path(d)
        try:
            skill_dir = resolved_cache.get(path)
            if skill_dir is None:
                skill_dir = path.resolve()
                resolved_cache[path] = skill_dir

            if skill_dir in seen:
                continue

            skill_xml_lines = _skill_to_xml_lines(skill_dir)
            seen.add(skill_dir)
            lines.extend(skill_xml_lines)
        except (OSError, RuntimeError) as e:
            error_msg = getattr(e, "strerror", None)
            if not error_msg:
                error_msg = "Symlink loop or unresolvable path"
            raise SkillError(
                f"Failed to process skill directory {_safe_name(path.name)}: {error_msg}"
            )

    lines.append("</available_skills>")

    return "\n".join(lines)
