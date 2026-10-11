"""Tests for the installers: scripts/install.sh, the root install.sh, and the
mahabharat-install Python CLI.

Everything runs by subprocess into temp dirs with HOME and CLAUDE_CONFIG_DIR
pointed at temp paths, so no test can touch a real ~/.claude.

scripts/install.sh installs from `git archive <ref>`, so its tests build a small
throwaway git repo (a copy of the real script plus synthetic agents) and commit
to *that* repo; the real checkout is only read.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
INSTALL_SH = REPO_ROOT / "scripts" / "install.sh"
ROOT_INSTALL_SH = REPO_ROOT / "install.sh"

pytestmark = pytest.mark.skipif(shutil.which("git") is None or shutil.which("bash") is None,
                                reason="needs git and bash")


# --------------------------------------------------------------- helpers ---


def _env(tmp_path: Path, **extra: str) -> dict:
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CONFIG_DIR"}
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    env.update(
        HOME=str(home),
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_NOSYSTEM="1",
        PYTHONPATH=str(REPO_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", ""),
        PYTHONDONTWRITEBYTECODE="1",
    )
    env.update(extra)
    return env


def _run(cmd: list[str], env: dict, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run(cmd, env=env, cwd=cwd, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise AssertionError(
            f"{' '.join(cmd)} exited {proc.returncode}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return proc


def _git(repo: Path, env: dict, *args: str) -> str:
    return _run(
        ["git", "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
         "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false", "-c", "core.hooksPath=/dev/null",
         "-C", str(repo), *args],
        env,
    ).stdout.strip()


def _agent(name: str, rank: str, body: str = "Body.") -> str:
    return (
        "---\n"
        f"name: {name}\n"
        f'description: "Fixture agent {name} for installer tests. Use when testing the installer."\n'
        "tools: Read, Grep, Glob, Skill\n"
        "model: sonnet\n"
        "effort: medium\n"
        "x-mahabharat:\n"
        "  spec: mahabharat.agent/v1\n"
        f"  character: {name}\n"
        "  title: Fixture\n"
        f"  rank: {rank}\n"
        "  reports_to: null\n"
        "---\n"
        f"{body}\n"
    )


FIXTURE_AGENTS = {
    "krishna": ("agents/masters/krishna.md", "god"),
    "bhima": ("agents/masters/bhima.md", "master"),
    "sepoy-backend-1": ("agents/sepoys/examples/backend-dev-1.md", "sepoy"),
}


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def src_repo(tmp_path: Path) -> Path:
    """A throwaway git repo shaped like mahabharat-agents, with the real scripts/install.sh."""
    repo = tmp_path / "src-repo"
    env = _env(tmp_path)
    roster = ["spec: mahabharat.roster/v1", "agents:"]
    for name, (rel, rank) in FIXTURE_AGENTS.items():
        _write(repo / rel, _agent(name, rank))
        roster.append(f"  - {{name: {name}, file: {rel}, rank: {rank}}}")
    _write(repo / "agents" / "roster.yaml", "\n".join(roster) + "\n")
    _write(repo / "templates" / "sepoy-agent.md", _agent("sepoy-template-x", "sepoy"))
    _write(repo / "skills" / "shared" / "hld" / "SKILL.md", "---\nname: hld\ndescription: d\n---\nHLD\n")
    _write(repo / "skills" / "shared" / "hld" / "references" / "notes.md", "notes\n")
    _write(repo / "skills" / "shared" / "zero-bias" / "SKILL.md", "---\nname: zero-bias\ndescription: d\n---\nZB\n")
    _write(repo / "skills" / "role-specific" / "ci-cd" / "SKILL.md", "---\nname: ci-cd\ndescription: d\n---\nCI\n")
    _write(repo / "workflows" / "bug-fix.js", "export const meta = {name: 'bug-fix'};\n")
    (repo / "scripts").mkdir(parents=True)
    shutil.copy2(INSTALL_SH, repo / "scripts" / "install.sh")
    _run(["git", "init", "-q", str(repo)], env)
    _git(repo, env, "add", "-A")
    _git(repo, env, "commit", "-qm", "fixture v1")
    return repo


def _install(repo: Path, tmp_path: Path, *args: str, check: bool = True, **env_extra: str):
    env = _env(tmp_path, **env_extra)
    env.setdefault("CLAUDE_CONFIG_DIR", str(tmp_path / "must-not-be-used"))
    return _run(["bash", str(repo / "scripts" / "install.sh"), *args], env, cwd=tmp_path, check=check)


def _snapshot(root: Path) -> dict[str, bytes]:
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def _assert_flat_agents(claude_dir: Path, expected: set[str]) -> None:
    agents = claude_dir / "agents"
    entries = sorted(agents.iterdir())
    assert all(p.is_file() for p in entries), f"agents/ must be flat, found {[p.name for p in entries]}"
    assert {p.name for p in entries} == {f"{n}.md" for n in expected}


def _assert_no_template(claude_dir: Path) -> None:
    for p in claude_dir.rglob("*"):
        assert "template" not in p.name.lower(), f"template installed: {p}"
        if p.is_file() and p.suffix == ".md":
            assert "sepoy-template-x" not in p.read_text(encoding="utf-8"), f"template content in {p}"


def _assert_manifest(claude_dir: Path, sha: str | None = None, ref: str | None = None) -> dict:
    manifest = json.loads((claude_dir / "mahabharat" / "install-manifest.json").read_text())
    assert set(manifest) == {"ref", "sha", "installed"}
    if sha is not None:
        assert manifest["sha"] == sha
    if ref is not None:
        assert manifest["ref"] == ref
    paths = [e["path"] for e in manifest["installed"]]
    assert len(paths) == len(set(paths))
    for entry in manifest["installed"]:
        f = claude_dir / entry["path"]
        assert f.is_file(), f"manifest lists missing {entry['path']}"
        assert hashlib.sha256(f.read_bytes()).hexdigest() == entry["sha256"], entry["path"]
    return manifest


# ------------------------------------------------------ scripts/install.sh ---


class TestScriptInstall:
    def test_project_install_layout_and_manifest(self, src_repo, tmp_path):
        proj = tmp_path / "proj"
        proj.mkdir()
        _install(src_repo, tmp_path, "--target", str(proj))
        claude = proj / ".claude"
        _assert_flat_agents(claude, set(FIXTURE_AGENTS))
        _assert_no_template(claude)
        assert (claude / "skills" / "hld" / "SKILL.md").is_file()
        assert (claude / "skills" / "hld" / "references" / "notes.md").is_file()
        assert (claude / "skills" / "ci-cd" / "SKILL.md").is_file()
        assert not (claude / "skills" / "zero-bias").exists(), "zero-bias is retired"
        assert (claude / "workflows" / "bug-fix.js").is_file()
        sha = _git(src_repo, _env(tmp_path), "rev-parse", "HEAD")
        manifest = _assert_manifest(claude, sha=sha, ref="HEAD")
        assert {e["path"] for e in manifest["installed"]} == {
            "agents/krishna.md", "agents/bhima.md", "agents/sepoy-backend-1.md",
            "skills/hld/SKILL.md", "skills/hld/references/notes.md", "skills/ci-cd/SKILL.md",
            "workflows/bug-fix.js",
        }
        assert not (claude / "mahabharat" / "backup").exists()

    def test_target_is_required(self, src_repo, tmp_path):
        """A bare run must not change the live user config: --target has no default."""
        env = _env(tmp_path)
        proc = _run(["bash", str(src_repo / "scripts" / "install.sh")], env, cwd=tmp_path, check=False)
        assert proc.returncode != 0 and "--target is required" in proc.stderr
        assert not (Path(env["HOME"]) / ".claude").exists()

    def test_user_target_installs_to_home(self, src_repo, tmp_path):
        env = _env(tmp_path)
        proc = _run(["bash", str(src_repo / "scripts" / "install.sh"), "--target", "user"], env, cwd=tmp_path)
        claude = Path(env["HOME"]) / ".claude"
        _assert_flat_agents(claude, set(FIXTURE_AGENTS))
        _assert_manifest(claude)
        assert "user scope" in proc.stdout

    def test_user_target_honours_claude_config_dir(self, src_repo, tmp_path):
        cfg = tmp_path / "cfg"
        _install(src_repo, tmp_path, "--target", "user", CLAUDE_CONFIG_DIR=str(cfg))
        _assert_flat_agents(cfg, set(FIXTURE_AGENTS))
        assert not (Path(_env(tmp_path)["HOME"]) / ".claude").exists()

    def test_rerun_is_idempotent(self, src_repo, tmp_path):
        proj = tmp_path / "proj"
        proj.mkdir()
        _install(src_repo, tmp_path, "--target", str(proj))
        before = _snapshot(proj)
        mtimes = {p: p.stat().st_mtime_ns for p in proj.rglob("*") if p.is_file()}
        second = _install(src_repo, tmp_path, "--target", str(proj))
        assert _snapshot(proj) == before
        assert {p: p.stat().st_mtime_ns for p in proj.rglob("*") if p.is_file()} == mtimes
        assert "0 file(s) changed" in second.stdout
        assert not (proj / ".claude" / "mahabharat" / "backup").exists()

    def test_dry_run_writes_nothing(self, src_repo, tmp_path):
        proj = tmp_path / "proj"
        proj.mkdir()
        proc = _install(src_repo, tmp_path, "--target", str(proj), "--dry-run")
        assert list(proj.iterdir()) == []
        assert "would install" in proc.stdout and "agents/krishna.md" in proc.stdout

    def test_existing_different_file_is_backed_up_outside_agents(self, src_repo, tmp_path):
        proj = tmp_path / "proj"
        old = proj / ".claude" / "agents" / "bhima.md"
        hand_edited = _agent("bhima", "master", body="old hand-edited bhima")
        _write(old, hand_edited)
        _install(src_repo, tmp_path, "--target", str(proj))
        claude = proj / ".claude"
        sha = _git(src_repo, _env(tmp_path), "rev-parse", "HEAD")
        backup = claude / "mahabharat" / "backup" / sha / "agents" / "bhima.md"
        assert backup.read_text() == hand_edited
        assert old.read_text() == (src_repo / "agents/masters/bhima.md").read_text()
        _assert_flat_agents(claude, set(FIXTURE_AGENTS))  # nothing extra landed in agents/
        # A second run must not create another backup.
        _install(src_repo, tmp_path, "--target", str(proj))
        assert sorted(p.name for p in backup.parent.iterdir()) == ["bhima.md"]

    @pytest.mark.parametrize("link", [".claude", ".claude/agents", ".claude/agents/bhima.md", ".claude/mahabharat"])
    def test_symlinked_destination_is_refused(self, src_repo, tmp_path, link):
        proj = tmp_path / "proj"
        proj.mkdir()
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        (elsewhere / "keep.txt").write_text("keep")
        link_path = proj / link
        link_path.parent.mkdir(parents=True, exist_ok=True)
        if link.endswith(".md"):
            os.symlink(elsewhere / "keep.txt", link_path)
        else:
            os.symlink(elsewhere, link_path)
        before = _snapshot(proj)
        proc = _install(src_repo, tmp_path, "--target", str(proj), check=False)
        assert proc.returncode != 0
        assert "symlink" in proc.stderr
        assert _snapshot(elsewhere) == {"keep.txt": b"keep"}, "nothing may be written through a symlink"
        assert _snapshot(proj) == before

    def test_symlinked_user_config_dir_is_refused(self, src_repo, tmp_path):
        real = tmp_path / "real-cfg"
        real.mkdir()
        cfg = tmp_path / "cfg-link"
        os.symlink(real, cfg)
        proc = _install(src_repo, tmp_path, "--target", "user", check=False, CLAUDE_CONFIG_DIR=str(cfg))
        assert proc.returncode != 0 and "symlink" in proc.stderr
        assert list(real.iterdir()) == []

    def test_dangling_symlink_at_a_numbered_backup_is_refused(self, src_repo, tmp_path):
        """A planted dangling symlink at <backup>/<rel>.N must not be written through."""
        proj = tmp_path / "proj"
        proj.mkdir()
        _install(src_repo, tmp_path, "--target", str(proj))
        claude = proj / ".claude"
        sha = _git(src_repo, _env(tmp_path), "rev-parse", "HEAD")
        bhima = claude / "agents" / "bhima.md"
        bhima.write_text(_agent("bhima", "master", body="hand edit one"))
        _install(src_repo, tmp_path, "--target", str(proj))  # backs up to <sha>/agents/bhima.md
        backup = claude / "mahabharat" / "backup" / sha / "agents" / "bhima.md"
        assert backup.is_file()
        outside = tmp_path / "outside.md"
        os.symlink(outside, backup.parent / "bhima.md.1")  # dangling
        bhima.write_text(_agent("bhima", "master", body="hand edit two"))
        _install(src_repo, tmp_path, "--target", str(proj))
        assert not outside.exists(), "the installer wrote through a dangling symlink"
        assert (backup.parent / "bhima.md.1").is_symlink(), "the planted link is left alone"
        assert "hand edit two" in (backup.parent / "bhima.md.2").read_text()

    def test_installs_the_ref_not_the_working_tree(self, src_repo, tmp_path):
        env = _env(tmp_path)
        _git(src_repo, env, "tag", "v-test")
        tagged_sha = _git(src_repo, env, "rev-parse", "v-test^{commit}")
        bhima = src_repo / "agents/masters/bhima.md"
        bhima.write_text(_agent("bhima", "master", body="Version two."))
        _git(src_repo, env, "commit", "-qam", "v2")
        bhima.write_text(_agent("bhima", "master", body="Uncommitted edit."))

        proj = tmp_path / "proj"
        proj.mkdir()
        _install(src_repo, tmp_path, "--from", "v-test", "--target", str(proj))
        installed = (proj / ".claude/agents/bhima.md").read_text()
        assert "Body." in installed and "Version two." not in installed
        _assert_manifest(proj / ".claude", sha=tagged_sha, ref="v-test")

        _install(src_repo, tmp_path, "--target", str(proj))  # HEAD
        installed = (proj / ".claude/agents/bhima.md").read_text()
        assert "Version two." in installed and "Uncommitted edit." not in installed

    def test_unknown_ref_and_bad_roster_fail_cleanly(self, src_repo, tmp_path):
        proj = tmp_path / "proj"
        proj.mkdir()
        proc = _install(src_repo, tmp_path, "--from", "no-such-ref", "--target", str(proj), check=False)
        assert proc.returncode != 0 and "cannot resolve" in proc.stderr

        env = _env(tmp_path)
        roster = src_repo / "agents" / "roster.yaml"
        roster.write_text(roster.read_text().replace("name: bhima,", "name: bhim,"))
        _git(src_repo, env, "commit", "-qam", "bad roster")
        proc = _install(src_repo, tmp_path, "--target", str(proj), check=False)
        assert proc.returncode != 0 and "frontmatter name is 'bhima', roster says 'bhim'" in proc.stderr
        assert list(proj.iterdir()) == []

    @pytest.mark.parametrize("linked", ["skills/shared", "skills/shared/hld", "workflows", "agents/masters"])
    def test_symlink_in_source_ref_is_refused(self, src_repo, tmp_path, linked):
        """A symlinked directory committed in the ref must not pull files from the installing machine."""
        env = _env(tmp_path)
        outside = tmp_path / "outside"
        original = src_repo / linked
        # Mirror the real directory's contents outside the repo, plus a planted file.
        shutil.copytree(original, outside)
        _write(outside / "secret-skill" / "SKILL.md", "---\nname: secret-skill\ndescription: d\n---\nS\n")
        _write(outside / "secret-skill" / "key.txt", "PRIVATE KEY\n")
        _write(outside / "planted.js", "export const meta = {name: 'planted'};\n")
        shutil.rmtree(original)
        os.symlink(outside, original)
        _git(src_repo, env, "add", "-A")
        _git(src_repo, env, "commit", "-qm", f"symlink {linked}")
        assert "120000" in _git(src_repo, env, "ls-tree", "HEAD", "--", linked)

        proj = tmp_path / "proj"
        proj.mkdir()
        for extra in ([], ["--dry-run"]):
            proc = _install(src_repo, tmp_path, "--target", str(proj), *extra, check=False)
            assert proc.returncode != 0, proc.stdout
            assert "symlink" in proc.stderr and linked in proc.stderr
            assert list(proj.iterdir()) == [], "a refusal must write nothing"

    def test_foreign_skill_with_same_name_is_refused(self, src_repo, tmp_path):
        """Another package's skills/hld/ is never overwritten or mixed with ours."""
        proj = tmp_path / "proj"
        foreign = proj / ".claude" / "skills" / "hld"
        _write(foreign / "SKILL.md", "---\nname: ckm:hld\ndescription: other package\n---\nForeign\n")
        _write(foreign / "references" / "extra.md", "foreign extra\n")
        before = _snapshot(proj)
        proc = _install(src_repo, tmp_path, "--target", str(proj), check=False)
        assert proc.returncode != 0
        assert "skills/hld/" in proc.stderr and "ckm:hld" in proc.stderr
        assert "--skip-skill" in proc.stderr and "--force-replace" in proc.stderr
        assert _snapshot(proj) == before, "a refusal must write nothing"
        dry = _install(src_repo, tmp_path, "--target", str(proj), "--dry-run", check=False)
        assert dry.returncode != 0 and _snapshot(proj) == before

    def test_skip_skill_leaves_a_foreign_skill_alone(self, src_repo, tmp_path):
        proj = tmp_path / "proj"
        foreign = proj / ".claude" / "skills" / "hld" / "SKILL.md"
        _write(foreign, "---\nname: ckm:hld\n---\nForeign\n")
        proc = _install(src_repo, tmp_path, "--target", str(proj), "--skip-skill", "hld")
        claude = proj / ".claude"
        assert foreign.read_text() == "---\nname: ckm:hld\n---\nForeign\n"
        assert "skills/hld (skipped" in proc.stdout
        assert (claude / "skills" / "ci-cd" / "SKILL.md").is_file()
        manifest = _assert_manifest(claude)
        assert not any(e["path"].startswith("skills/hld/") for e in manifest["installed"])

    def test_force_replace_backs_up_a_foreign_skill(self, src_repo, tmp_path):
        proj = tmp_path / "proj"
        claude = proj / ".claude"
        _write(claude / "skills" / "hld" / "SKILL.md", "---\nname: ckm:hld\n---\nForeign\n")
        _write(claude / "skills" / "hld" / "extra.md", "foreign extra\n")
        proc = _install(src_repo, tmp_path, "--target", str(proj), "--force-replace")
        assert "--force-replace" in proc.stderr
        sha = _git(src_repo, _env(tmp_path), "rev-parse", "HEAD")
        backup = claude / "mahabharat" / "backup" / sha / "skills" / "hld" / "SKILL.md"
        assert backup.read_text() == "---\nname: ckm:hld\n---\nForeign\n"
        assert (claude / "skills" / "hld" / "SKILL.md").read_text() == (
            src_repo / "skills/shared/hld/SKILL.md").read_text()

    def test_foreign_agent_file_is_refused(self, src_repo, tmp_path):
        proj = tmp_path / "proj"
        other = proj / ".claude" / "agents" / "bhima.md"
        _write(other, "---\nname: someone-else\n---\nNot ours\n")
        proc = _install(src_repo, tmp_path, "--target", str(proj), check=False)
        assert proc.returncode != 0 and "agents/bhima.md" in proc.stderr
        assert other.read_text() == "---\nname: someone-else\n---\nNot ours\n"

    def test_previously_installed_skill_with_local_edit_is_replaced(self, src_repo, tmp_path):
        """A path in the previous install manifest is ours, even after a local edit."""
        proj = tmp_path / "proj"
        proj.mkdir()
        _install(src_repo, tmp_path, "--target", str(proj))
        skill = proj / ".claude" / "skills" / "hld" / "SKILL.md"
        skill.write_text("---\nname: hld\n---\nlocally edited\n")
        _install(src_repo, tmp_path, "--target", str(proj))
        assert skill.read_text() == (src_repo / "skills/shared/hld/SKILL.md").read_text()
        backups = list((proj / ".claude" / "mahabharat" / "backup").rglob("SKILL.md"))
        assert [b.read_text() for b in backups] == ["---\nname: hld\n---\nlocally edited\n"]

    def test_older_committed_version_is_recognised(self, src_repo, tmp_path):
        """A file identical to an earlier commit of the same repo file is ours (no manifest needed)."""
        env = _env(tmp_path)
        v1 = (src_repo / "skills/shared/hld/SKILL.md").read_text()
        (src_repo / "skills/shared/hld/SKILL.md").write_text(v1 + "Version two.\n")
        _git(src_repo, env, "commit", "-qam", "hld v2")
        proj = tmp_path / "proj"
        _write(proj / ".claude" / "skills" / "hld" / "SKILL.md", v1)
        _install(src_repo, tmp_path, "--target", str(proj))
        assert "Version two." in (proj / ".claude" / "skills" / "hld" / "SKILL.md").read_text()

    def test_target_path_with_brackets(self, src_repo, tmp_path):
        """$BASE is quoted in ${var#pattern}: a '[1]' in the path is literal, not a glob."""
        proj = tmp_path / "proj[1]"
        proj.mkdir()
        first = _install(src_repo, tmp_path, "--target", str(proj))
        assert "duplicate definition" not in first.stderr, first.stderr
        claude = proj / ".claude"
        _assert_flat_agents(claude, set(FIXTURE_AGENTS))
        (claude / "agents" / "bhima.md").write_text(_agent("bhima", "master", body="hand edit"))
        dry = _install(src_repo, tmp_path, "--target", str(proj), "--dry-run")
        assert "would be backed up to mahabharat/backup/" in dry.stdout, dry.stdout
        second = _install(src_repo, tmp_path, "--target", str(proj))
        assert "previous version saved to mahabharat/backup/" in second.stdout, second.stdout
        assert "duplicate definition" not in second.stderr and "old-layout" not in second.stderr, second.stderr
        _assert_manifest(claude)

    def test_old_layout_is_reported(self, src_repo, tmp_path):
        proj = tmp_path / "proj"
        _write(proj / ".claude/agents/sepoys/backend-dev-1.md", _agent("sepoy-backend-1", "sepoy"))
        proc = _install(src_repo, tmp_path, "--target", str(proj))
        assert "old-layout file agents/sepoys/backend-dev-1.md" in proc.stderr

    def test_real_roster_installs_flat(self, tmp_path):
        """The live roster, agents and skills install cleanly (from a throwaway commit of the working tree)."""
        repo = tmp_path / "live-copy"
        env = _env(tmp_path)
        for sub in ("agents", "skills", "workflows", "templates"):
            if (REPO_ROOT / sub).is_dir():
                shutil.copytree(REPO_ROOT / sub, repo / sub)
        (repo / "scripts").mkdir(parents=True)
        shutil.copy2(INSTALL_SH, repo / "scripts" / "install.sh")
        _run(["git", "init", "-q", str(repo)], env)
        _git(repo, env, "add", "-A")
        _git(repo, env, "commit", "-qm", "live copy")
        proj = tmp_path / "proj"
        proj.mkdir()
        _install(repo, tmp_path, "--target", str(proj))
        import yaml

        roster = yaml.safe_load((REPO_ROOT / "agents" / "roster.yaml").read_text())["agents"]
        _assert_flat_agents(proj / ".claude", {e["name"] for e in roster})
        _assert_no_template(proj / ".claude")
        _assert_manifest(proj / ".claude")
        assert not (proj / ".claude" / "skills" / "zero-bias").exists()


# ---------------------------------------------------- Python CLI (pip path) ---


def _roster_names() -> set[str]:
    import yaml

    return {e["name"] for e in yaml.safe_load((REPO_ROOT / "agents" / "roster.yaml").read_text())["agents"]}


def _cli(tmp_path: Path, *args: str, check: bool = True):
    env = _env(tmp_path, CLAUDE_CONFIG_DIR=str(tmp_path / "must-not-be-used"))
    return _run([sys.executable, "-m", "mahabharat_agents.cli", *args], env, cwd=tmp_path, check=check)


class TestPythonCli:
    def test_import_cli(self):
        import mahabharat_agents.cli  # noqa: F401

    def test_install_layout_and_manifest(self, tmp_path):
        proj = tmp_path / "proj"
        proj.mkdir()
        _cli(tmp_path, str(proj))
        claude = proj / ".claude"
        _assert_flat_agents(claude, _roster_names())
        _assert_no_template(claude)
        assert (claude / "skills" / "hld" / "SKILL.md").is_file()
        assert not (claude / "skills" / "zero-bias").exists()
        for sub in ("orchestration", "context"):
            # pre-v1 docs that still name krishna as approver are never installed
            assert not (claude / sub).exists(), f"{sub}/ must not be installed"
        _assert_manifest(claude)
        assert not (claude / "mahabharat" / "backup").exists()

    def test_rerun_is_idempotent(self, tmp_path):
        proj = tmp_path / "proj"
        proj.mkdir()
        _cli(tmp_path, str(proj))
        before = _snapshot(proj)
        mtimes = {p: p.stat().st_mtime_ns for p in proj.rglob("*") if p.is_file()}
        second = _cli(tmp_path, str(proj))
        assert _snapshot(proj) == before
        assert {p: p.stat().st_mtime_ns for p in proj.rglob("*") if p.is_file()} == mtimes
        assert "0 file(s) changed" in second.stdout

    def test_dry_run_writes_nothing(self, tmp_path):
        proj = tmp_path / "proj"
        proj.mkdir()
        _cli(tmp_path, str(proj), "--dry-run")
        assert list(proj.iterdir()) == []

    def test_agents_only(self, tmp_path):
        proj = tmp_path / "proj"
        proj.mkdir()
        _cli(tmp_path, str(proj), "--agents-only")
        claude = proj / ".claude"
        _assert_flat_agents(claude, _roster_names())
        assert not (claude / "skills").exists()

    @pytest.mark.parametrize("link", [".claude", ".claude/agents", ".claude/agents/arjuna.md"])
    def test_symlinked_destination_is_refused(self, tmp_path, link):
        proj = tmp_path / "proj"
        proj.mkdir()
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        (elsewhere / "keep.txt").write_text("keep")
        link_path = proj / link
        link_path.parent.mkdir(parents=True, exist_ok=True)
        os.symlink(elsewhere / "keep.txt" if link.endswith(".md") else elsewhere, link_path)
        proc = _cli(tmp_path, str(proj), check=False)
        assert proc.returncode != 0 and "symlink" in proc.stderr
        assert _snapshot(elsewhere) == {"keep.txt": b"keep"}

    def test_existing_different_file_is_backed_up_outside_agents(self, tmp_path):
        proj = tmp_path / "proj"
        old = proj / ".claude" / "agents" / "arjuna.md"
        hand_edited = _agent("arjuna", "master", body="old arjuna")
        _write(old, hand_edited)
        _cli(tmp_path, str(proj))
        claude = proj / ".claude"
        backups = list((claude / "mahabharat" / "backup").rglob("arjuna.md"))
        assert len(backups) == 1 and backups[0].read_text() == hand_edited
        assert backups[0].relative_to(claude).parts[:2] == ("mahabharat", "backup")
        _assert_flat_agents(claude, _roster_names())

    def test_foreign_skill_and_agent_are_refused(self, tmp_path):
        proj = tmp_path / "proj"
        claude = proj / ".claude"
        _write(claude / "skills" / "hld" / "SKILL.md", "---\nname: ckm:hld\n---\nForeign\n")
        _write(claude / "agents" / "arjuna.md", "not an agent\n")
        before = _snapshot(proj)
        proc = _cli(tmp_path, str(proj), check=False)
        assert proc.returncode != 0
        assert "skills/hld/" in proc.stderr and "ckm:hld" in proc.stderr and "agents/arjuna.md" in proc.stderr
        assert _snapshot(proj) == before

        _cli(tmp_path, str(proj), "--skip-skill", "hld", "--force-replace")
        assert (claude / "skills" / "hld" / "SKILL.md").read_text() == "---\nname: ckm:hld\n---\nForeign\n"
        assert list((claude / "mahabharat" / "backup").rglob("arjuna.md"))
        _assert_flat_agents(claude, _roster_names())


# ------------------------------------------- Python CLI: source confinement ---
# The CLI installs from a data root (the bundled data, or --source <checkout>). A symlink
# anywhere under it must not pull files from the installing machine into .claude/.

DATA_DIRS = ("agents", "skills")


def _data_copy(tmp_path: Path) -> Path:
    """A temp copy of the real data root (agents, skills)."""
    data = tmp_path / "data"
    for d in DATA_DIRS:
        shutil.copytree(REPO_ROOT / d, data / d)
    return data


def _symlink_out(data: Path, tmp_path: Path, rel: str) -> Path:
    """Move data/<rel> outside the data root, plant a secret beside it, and link it back."""
    original = data / rel
    outside = tmp_path / "outside" / rel.replace("/", "_")
    outside.parent.mkdir(parents=True, exist_ok=True)
    if original.is_dir():
        shutil.copytree(original, outside)
        shutil.rmtree(original)
        _write(outside / "planted-secret.md", "PRIVATE\n")
    else:
        shutil.copy2(original, outside)
        original.unlink()
    os.symlink(outside, original)
    return outside


class TestPythonCliSourceConfinement:
    def test_clean_copy_installs(self, tmp_path):
        data = _data_copy(tmp_path)
        proj = tmp_path / "proj"
        proj.mkdir()
        _cli(tmp_path, str(proj), "--source", str(data))
        _assert_flat_agents(proj / ".claude", _roster_names())
        _assert_manifest(proj / ".claude")

    def test_symlinked_skill_dir_is_refused(self, tmp_path):
        data = _data_copy(tmp_path)
        _symlink_out(data, tmp_path, "skills/shared/hld")
        proj = tmp_path / "proj"
        proj.mkdir()
        for extra in ([], ["--dry-run"], ["--skills-only"]):
            proc = _cli(tmp_path, str(proj), "--source", str(data), *extra, check=False)
            assert proc.returncode != 0, proc.stdout
            assert "symlink" in proc.stderr and "skills/shared/hld" in proc.stderr, proc.stderr
            assert list(proj.iterdir()) == [], "a refusal must write nothing"

    @pytest.mark.parametrize("rel", [
        "skills",
        "skills/shared",
        "skills/role-specific/ci-cd",
        "skills/shared/hld/SKILL.md",
        "agents/masters",
        "agents/masters/bhima.md",
        "agents/roster.yaml",
    ])
    def test_symlinked_source_is_refused(self, tmp_path, rel):
        data = _data_copy(tmp_path)
        _symlink_out(data, tmp_path, rel)
        proj = tmp_path / "proj"
        proj.mkdir()
        proc = _cli(tmp_path, str(proj), "--source", str(data), check=False)
        assert proc.returncode != 0, proc.stdout
        assert "symlink" in proc.stderr, proc.stderr
        assert list(proj.iterdir()) == []

    def test_symlink_nested_inside_a_skill_is_refused(self, tmp_path):
        """A symlinked subdirectory of a skill used to be skipped silently; now it is refused."""
        data = _data_copy(tmp_path)
        secret = tmp_path / "secret-dir"
        _write(secret / "key.txt", "PRIVATE KEY\n")
        os.symlink(secret, data / "skills" / "shared" / "hld" / "references")
        proj = tmp_path / "proj"
        proj.mkdir()
        proc = _cli(tmp_path, str(proj), "--source", str(data), check=False)
        assert proc.returncode != 0 and "symlink" in proc.stderr, proc.stderr
        assert "hld/references" in proc.stderr
        assert list(proj.iterdir()) == []

    def test_roster_path_outside_the_data_root_is_refused(self, tmp_path):
        data = _data_copy(tmp_path)
        _write(tmp_path / "evil.md", _agent("bhima", "master", body="not from the package"))
        roster = data / "agents" / "roster.yaml"
        text = roster.read_text()
        old = next(line for line in text.splitlines() if "name: bhima," in line)
        roster.write_text(text.replace(old, "  - {name: bhima, file: agents/../../evil.md, rank: master}"))
        proj = tmp_path / "proj"
        proj.mkdir()
        proc = _cli(tmp_path, str(proj), "--source", str(data), check=False)
        assert proc.returncode != 0 and "unsafe source path" in proc.stderr, proc.stderr
        assert list(proj.iterdir()) == []

    def test_planted_temp_file_symlink_is_not_written_through(self, tmp_path):
        """Writes go through mkstemp temp files, never a predictable name a symlink can claim."""
        proj = tmp_path / "proj"
        agents = proj / ".claude" / "agents"
        agents.mkdir(parents=True)
        out = tmp_path / "out"
        out.mkdir()
        target = out / "victim.txt"
        target.write_text("PRECIOUS")
        for pid_guess in range(0, 64):  # the old name was <dest>.mahabharat-tmp.<pid>
            os.symlink(target, agents / f"arjuna.md.mahabharat-tmp.{pid_guess}")
        _cli(tmp_path, str(proj), "--agents-only")
        assert target.read_text() == "PRECIOUS"

    def test_root_install_sh_refuses_a_symlinked_skill_dir(self, tmp_path):
        """install.sh wraps the CLI with --source <its checkout>, so it gets the same check."""
        checkout = tmp_path / "checkout"
        for d in DATA_DIRS:
            shutil.copytree(REPO_ROOT / d, checkout / d)
        shutil.copytree(REPO_ROOT / "src", checkout / "src",
                        ignore=shutil.ignore_patterns("__pycache__", "*.egg-info"))
        shutil.copy2(ROOT_INSTALL_SH, checkout / "install.sh")
        _symlink_out(checkout, tmp_path, "skills/shared/hld")
        proj = tmp_path / "proj"
        proj.mkdir()
        env = _env(tmp_path, CLAUDE_CONFIG_DIR=str(tmp_path / "must-not-be-used"))
        proc = _run(["bash", str(checkout / "install.sh"), str(proj)], env, cwd=tmp_path, check=False)
        assert proc.returncode != 0, proc.stdout
        assert "symlink" in proc.stderr and "skills/shared/hld" in proc.stderr, proc.stderr
        assert list(proj.iterdir()) == []


# ------------------------------------------------------- root install.sh ---


def _root_install(tmp_path: Path, *args: str, check: bool = True):
    env = _env(tmp_path, CLAUDE_CONFIG_DIR=str(tmp_path / "must-not-be-used"))
    return _run(["bash", str(ROOT_INSTALL_SH), *args], env, cwd=tmp_path, check=check)


class TestRootInstallSh:
    @pytest.mark.parametrize("link", [".claude/agents/arjuna.md", ".claude/skills/hld", ".claude"])
    def test_symlinked_destination_is_refused(self, tmp_path, link):
        proj = tmp_path / "proj"
        proj.mkdir()
        out = tmp_path / "out"
        out.mkdir()
        (out / "secret.md").write_text("PRECIOUS")
        link_path = proj / link
        link_path.parent.mkdir(parents=True, exist_ok=True)
        os.symlink(out / "secret.md" if link.endswith(".md") else out, link_path)
        proc = _root_install(tmp_path, str(proj), check=False)
        assert proc.returncode != 0 and "symlink" in proc.stderr
        assert _snapshot(out) == {"secret.md": b"PRECIOUS"}, "nothing may be written through a symlink"

    def test_backs_up_and_writes_manifest(self, tmp_path):
        proj = tmp_path / "proj"
        old = proj / ".claude" / "agents" / "arjuna.md"
        hand_edited = _agent("arjuna", "master", body="hand edits")
        _write(old, hand_edited)
        _root_install(tmp_path, str(proj))
        claude = proj / ".claude"
        backups = list((claude / "mahabharat" / "backup").rglob("arjuna.md"))
        assert [b.read_text() for b in backups] == [hand_edited]
        _assert_manifest(claude)
        second = _root_install(tmp_path, str(proj))
        assert "0 file(s) changed" in second.stdout

    def test_foreign_skill_is_refused(self, tmp_path):
        proj = tmp_path / "proj"
        foreign = proj / ".claude" / "skills" / "hld" / "SKILL.md"
        _write(foreign, "---\nname: ckm:hld\n---\nForeign\n")
        proc = _root_install(tmp_path, str(proj), check=False)
        assert proc.returncode != 0 and "ckm:hld" in proc.stderr
        assert foreign.read_text() == "---\nname: ckm:hld\n---\nForeign\n"
        assert not (proj / ".claude" / "agents").exists()

    def test_flat_and_no_template(self, tmp_path):
        proj = tmp_path / "proj"
        proj.mkdir()
        env = _env(tmp_path, CLAUDE_CONFIG_DIR=str(tmp_path / "must-not-be-used"))
        proc = _run(["bash", str(ROOT_INSTALL_SH), str(proj)], env, cwd=tmp_path)
        claude = proj / ".claude"
        _assert_flat_agents(claude, _roster_names())
        _assert_no_template(claude)
        assert not (claude / "skills" / "zero-bias").exists()
        assert "scripts/install.sh" in ROOT_INSTALL_SH.read_text()
        import yaml

        ranks = [e["rank"] for e in yaml.safe_load((REPO_ROOT / "agents" / "roster.yaml").read_text())["agents"]]
        assert f"{sum(r != 'sepoy' for r in ranks)} master agents" in proc.stdout
        assert f"{ranks.count('sepoy')} sepoy agents" in proc.stdout
