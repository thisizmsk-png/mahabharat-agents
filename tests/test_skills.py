"""Tests for skill definition files."""

import pytest
import yaml
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

REQUIRED_FIELDS = {"name", "description"}


@pytest.fixture
def skill_files():
    """Find all SKILL.md files recursively under skills/."""
    skills_dir = REPO_ROOT / "skills"
    files = sorted(skills_dir.rglob("SKILL.md"))
    assert len(files) > 0, f"No SKILL.md files found in {skills_dir}"
    return files


def _extract_frontmatter(path: Path) -> dict:
    """Extract YAML frontmatter between --- delimiters."""
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3:
        pytest.fail(f"No YAML frontmatter found in {path}")
    return yaml.safe_load(parts[1])


class TestSkills:
    def test_at_least_10_skills(self, skill_files):
        assert len(skill_files) >= 10, (
            f"Expected at least 10 skills, found {len(skill_files)}"
        )

    def test_required_fields_present(self, skill_files):
        for path in skill_files:
            fm = _extract_frontmatter(path)
            missing = REQUIRED_FIELDS - set(fm.keys())
            assert not missing, (
                f"{path.relative_to(REPO_ROOT)} missing required fields: {missing}"
            )
