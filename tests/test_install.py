"""Tests for the install CLI functionality."""

import shutil
import tempfile
from pathlib import Path

import pytest


class TestInstall:
    def test_import_cli(self):
        """Verify mahabharat_agents.cli can be imported."""
        import mahabharat_agents.cli  # noqa: F401

    def test_install_creates_expected_directories(self):
        """Run install to a temp directory and verify structure."""
        from mahabharat_agents.cli import install

        tmp_dir = Path(tempfile.mkdtemp())
        try:
            install(tmp_dir)

            expected_dirs = ["agents", "skills", "orchestration", "context"]
            for dirname in expected_dirs:
                dir_path = tmp_dir / dirname
                assert dir_path.is_dir(), (
                    f"Expected directory '{dirname}' not found in {tmp_dir}"
                )
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
