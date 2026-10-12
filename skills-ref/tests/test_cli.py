"""Tests for the cli module."""

import pytest
from pathlib import Path
from unittest.mock import patch

from skills_ref.cli import _is_skill_md_file

def test_is_skill_md_file_happy_path(tmp_path):
    """Test that _is_skill_md_file returns True for SKILL.md and skill.md."""
    # Create SKILL.md
    skill_md = tmp_path / "SKILL.md"
    skill_md.touch()
    assert _is_skill_md_file(skill_md) is True

    # Create skill.md
    skill_md_lower = tmp_path / "skill.md"
    skill_md_lower.touch()
    assert _is_skill_md_file(skill_md_lower) is True

def test_is_skill_md_file_directory(tmp_path):
    """Test that _is_skill_md_file returns False for a directory named SKILL.md."""
    skill_md_dir = tmp_path / "SKILL.md"
    skill_md_dir.mkdir()
    assert _is_skill_md_file(skill_md_dir) is False

def test_is_skill_md_file_wrong_name(tmp_path):
    """Test that _is_skill_md_file returns False for other files."""
    readme_md = tmp_path / "README.md"
    readme_md.touch()
    assert _is_skill_md_file(readme_md) is False

def test_is_skill_md_file_oserror():
    """Test that _is_skill_md_file catches OSError."""
    path = Path("fake/path")
    with patch.object(Path, 'is_file', side_effect=OSError):
        assert _is_skill_md_file(path) is False

def test_is_skill_md_file_runtimeerror():
    """Test that _is_skill_md_file catches RuntimeError."""
    path = Path("fake/path")
    with patch.object(Path, 'is_file', side_effect=RuntimeError):
        assert _is_skill_md_file(path) is False
