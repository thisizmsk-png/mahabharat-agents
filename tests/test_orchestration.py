"""Tests for orchestration topology and workflow YAML files."""

import pytest
import yaml
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


@pytest.fixture
def topology_files():
    """Find all .yaml files in orchestration/topologies/."""
    topo_dir = REPO_ROOT / "orchestration" / "topologies"
    files = sorted(topo_dir.glob("*.yaml"))
    assert len(files) > 0, f"No .yaml files found in {topo_dir}"
    return files


@pytest.fixture
def workflow_files():
    """Find all .yaml files in orchestration/workflows/."""
    wf_dir = REPO_ROOT / "orchestration" / "workflows"
    files = sorted(wf_dir.glob("*.yaml"))
    assert len(files) > 0, f"No .yaml files found in {wf_dir}"
    return files


class TestTopologies:
    def test_at_least_5_topologies(self, topology_files):
        assert len(topology_files) >= 5, (
            f"Expected at least 5 topologies, found {len(topology_files)}"
        )

    def test_topologies_parse_without_errors(self, topology_files):
        for path in topology_files:
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
            except yaml.YAMLError as exc:
                pytest.fail(f"YAML parse error in {path.name}: {exc}")
            assert data is not None, f"{path.name} is empty"


class TestWorkflows:
    def test_at_least_5_workflows(self, workflow_files):
        assert len(workflow_files) >= 5, (
            f"Expected at least 5 workflows, found {len(workflow_files)}"
        )

    def test_workflows_parse_without_errors(self, workflow_files):
        for path in workflow_files:
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
            except yaml.YAMLError as exc:
                pytest.fail(f"YAML parse error in {path.name}: {exc}")
            assert data is not None, f"{path.name} is empty"
