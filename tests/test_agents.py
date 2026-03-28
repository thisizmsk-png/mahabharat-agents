"""Tests for master agent definition files."""

import pytest
import yaml
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

REQUIRED_FIELDS = {"name", "role", "model", "character", "rank", "reports_to"}


@pytest.fixture
def agent_files():
    """Find all .md files in agents/masters/."""
    masters_dir = REPO_ROOT / "agents" / "masters"
    files = sorted(masters_dir.glob("*.md"))
    assert len(files) > 0, f"No .md files found in {masters_dir}"
    return files


def _extract_frontmatter(path: Path) -> dict:
    """Extract YAML frontmatter between --- delimiters."""
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3:
        pytest.fail(f"No YAML frontmatter found in {path.name}")
    return yaml.safe_load(parts[1])


class TestMasterAgents:
    def test_exactly_17_master_agents(self, agent_files):
        assert len(agent_files) == 17, (
            f"Expected 17 master agents, found {len(agent_files)}: "
            f"{[f.name for f in agent_files]}"
        )

    def test_required_fields_present(self, agent_files):
        for path in agent_files:
            fm = _extract_frontmatter(path)
            missing = REQUIRED_FIELDS - set(fm.keys())
            assert not missing, (
                f"{path.name} missing required fields: {missing}"
            )

    def test_all_names_unique(self, agent_files):
        names = []
        for path in agent_files:
            fm = _extract_frontmatter(path)
            names.append(fm.get("name"))
        duplicates = [n for n in names if names.count(n) > 1]
        assert len(duplicates) == 0, f"Duplicate agent names found: {set(duplicates)}"
