"""Tests for scripts/smoke_check.py, the assertions behind scripts/smoke.sh.

Each test writes a synthetic spec.json plus the stream/debug/stderr files a smoke run
would leave, then runs smoke_check.py on it. No Claude Code binary is needed.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SMOKE_CHECK = REPO_ROOT / "scripts" / "smoke_check.py"

NOT_LOGGED_IN = "Not logged in · Please run /login"
ZERO_USAGE = {"input_tokens": 0, "output_tokens": 0, "cache_creation_input_tokens": 0,
              "cache_read_input_tokens": 0}


def _result(text: str = NOT_LOGGED_IN, **overrides) -> dict:
    msg = {"type": "result", "subtype": "success", "is_error": True, "result": text,
           "num_turns": 1, "duration_api_ms": 0, "total_cost_usd": 0, "usage": dict(ZERO_USAGE)}
    msg.update(overrides)
    return msg


def _spec(tmp_path: Path, result: dict, stderr: str = "", api_key_source: str = "none") -> Path:
    agents = tmp_path / "agents"
    agents.mkdir()
    (agents / "solo.md").write_text("---\nname: solo\ndescription: d\ntools: Read\n---\nBody\n")
    init = {"type": "system", "subtype": "init", "apiKeySource": api_key_source,
            "agents": ["solo"], "skills": [], "slash_commands": [], "tools": ["Read"]}
    stream = tmp_path / "base.jsonl"
    stream.write_text("\n".join(json.dumps(m) for m in (init, result)) + "\n")
    (tmp_path / "base.debug.log").write_text("debug\n")
    (tmp_path / "base.stderr").write_text(stderr)
    spec = {
        "roster": [{"name": "solo"}],
        "agent_dirs": [str(agents)],
        "manifest": None,
        "runs": [{"label": "base", "agent": None, "stream": str(stream),
                  "debug": str(tmp_path / "base.debug.log"), "stderr": str(tmp_path / "base.stderr")}],
    }
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(spec))
    return path


def _check(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-I", str(SMOKE_CHECK), *args],
                          capture_output=True, text=True)


def test_clean_auth_stop_passes(tmp_path):
    proc = _check(str(_spec(tmp_path, _result())))
    assert proc.returncode == 0, proc.stdout
    assert "PASS" in proc.stdout


def test_api_error_is_a_credential_leak_even_if_stderr_mentions_oauth(tmp_path):
    """The case the old loose regex let through: an attempted request at the dead port."""
    spec = _spec(tmp_path, _result("API Error: Connection error."), stderr="[DEBUG] Refreshing OAuth token\n")
    proc = _check(str(spec))
    assert proc.returncode == 3, proc.stdout
    assert "attempted an API request" in proc.stdout


@pytest.mark.parametrize(
    "overrides",
    [
        {"usage": {**ZERO_USAGE, "input_tokens": 12}},
        {"duration_api_ms": 840},
        {"num_turns": 2},
    ],
)
def test_any_api_activity_is_exit_3(tmp_path, overrides):
    proc = _check(str(_spec(tmp_path, _result(**overrides))))
    assert proc.returncode == 3, proc.stdout


@pytest.mark.parametrize("text", ["Invalid API key · Please run /login", "Credit balance is too low"])
def test_credential_errors_are_exit_3(tmp_path, text):
    assert _check(str(_spec(tmp_path, _result(text)))).returncode == 3


def test_other_endings_fail_instead_of_passing(tmp_path):
    """Only Claude Code's own 'Not logged in' passes; stderr text no longer counts."""
    spec = _spec(tmp_path, _result("Something else happened"), stderr="please log in; oauth; credential\n")
    proc = _check(str(spec))
    assert proc.returncode == 1, proc.stdout
    assert "did not end at 'Not logged in'" in proc.stdout


def test_visible_api_key_is_exit_3(tmp_path):
    assert _check(str(_spec(tmp_path, _result(), api_key_source="ANTHROPIC_API_KEY"))).returncode == 3


# --------------------------------------------------------- settings preflight ---


def _settings(tmp_path: Path, name: str, data) -> Path:
    path = tmp_path / name
    path.write_text(data if isinstance(data, str) else json.dumps(data))
    return path


@pytest.mark.parametrize(
    "data",
    [
        {"env": {"ANTHROPIC_BASE_URL": "https://example.invalid"}},
        {"env": {"ANTHROPIC_API_KEY": "sk-fixture"}},
        {"env": {"CLAUDE_CODE_USE_BEDROCK": "1"}},
        {"env": {"AWS_PROFILE": "prod"}},
        {"env": {"HTTPS_PROXY": "http://proxy.invalid"}},
        {"apiKeyHelper": "/bin/echo fixture"},
        {"awsCredentialExport": "/bin/true"},
        "{ not json",
    ],
)
def test_preflight_refuses_credential_settings(tmp_path, data):
    path = _settings(tmp_path, "settings.json", data)
    proc = _check("--preflight-settings", str(path))
    assert proc.returncode == 1, proc.stdout
    assert "REFUSE" in proc.stdout


def test_preflight_allows_harmless_settings(tmp_path):
    path = _settings(tmp_path, "settings.json", {
        "env": {"NODE_ENV": "test"},
        "hooks": {"UserPromptSubmit": [{"hooks": [{"type": "command", "command": "true"}]}]},
        "permissions": {"deny": ["Read(~/.ssh/**)"]},
    })
    proc = _check("--preflight-settings", str(path), str(tmp_path / "missing.json"))
    assert proc.returncode == 0, proc.stdout
    assert "WARN" in proc.stdout and "disableAllHooks" in proc.stdout


def test_smoke_sh_isolates_settings():
    """smoke.sh never copies the user's settings.json and passes the isolating flags."""
    text = (REPO_ROOT / "scripts" / "smoke.sh").read_text()
    assert 'cp "$SCOPE/settings.json"' not in text
    assert "--strict-mcp-config" in text and '--settings "$SMOKE_SETTINGS"' in text
    assert '"disableAllHooks": true' in text
    assert "--preflight-settings" in text
    for prefix in ("AWS_*", "GOOGLE_*", "AZURE_*"):
        assert prefix in text


def test_smoke_sh_preflights_managed_drop_ins_and_mdm():
    """Managed settings outrank --settings, so every managed source must be preflighted."""
    text = (REPO_ROOT / "scripts" / "smoke.sh").read_text()
    assert "managed-settings.d" in text and '"$d"/*.json' in text
    assert "com.anthropic.claudecode.plist" in text and "plutil -convert json" in text


# ------------------------------------------------- full-spec assertions ---
# A base run plus per-agent runs, agent dirs and an install manifest, so the checks that
# make the smoke test worth running (tools, duplicates, drift, debug lines, init lists)
# are exercised, not just the auth stop.


def _agent_md(name: str, tools: str) -> str:
    return f"---\nname: {name}\ndescription: d\ntools: {tools}\n---\nBody\n"


def _write_run(tmp_path: Path, label: str, agent: str | None, init: dict, debug: str = "debug\n") -> dict:
    slug = label.replace(":", "_")
    stream = tmp_path / f"{slug}.jsonl"
    base_init = {"type": "system", "subtype": "init", "apiKeySource": "none",
                 "agents": [], "skills": [], "slash_commands": [], "tools": []}
    base_init.update(init)
    stream.write_text("\n".join(json.dumps(m) for m in (base_init, _result())) + "\n")
    (tmp_path / f"{slug}.debug.log").write_text(debug)
    (tmp_path / f"{slug}.stderr").write_text("")
    return {"label": label, "agent": agent, "stream": str(stream),
            "debug": str(tmp_path / f"{slug}.debug.log"), "stderr": str(tmp_path / f"{slug}.stderr")}


def _full_spec(
    tmp_path: Path,
    *,
    agent_tools: dict[str, str] | None = None,
    init_tools: dict[str, list[str]] | None = None,
    base_agents: list[str] | None = None,
    base_skills: list[str] | None = None,
    debug: dict[str, str] | None = None,
    extra_dir_agents: dict[str, str] | None = None,
    tamper_manifest: bool = False,
) -> Path:
    """Scope with agents alpha (Read, Grep) and beta (Read, Bash) and one installed skill."""
    agent_tools = agent_tools or {"alpha": "Read, Grep", "beta": "Read, Bash"}
    init_tools = init_tools or {"alpha": ["Read", "Grep"], "beta": ["Read", "Bash"]}
    debug = debug or {}
    scope = tmp_path / "scope"
    agents = scope / "agents"
    agents.mkdir(parents=True)
    for name, tools in agent_tools.items():
        (agents / f"{name}.md").write_text(_agent_md(name, tools))
    skill = scope / "skills" / "hld" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("---\nname: hld\ndescription: d\n---\nHLD\n")
    installed = [f"agents/{n}.md" for n in agent_tools] + ["skills/hld/SKILL.md"]
    entries = [{"path": p, "sha256": hashlib.sha256((scope / p).read_bytes()).hexdigest()} for p in installed]
    if tamper_manifest:
        (agents / "alpha.md").write_text(_agent_md("alpha", agent_tools["alpha"]) + "local edit\n")
    manifest = scope / "mahabharat" / "install-manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"ref": "HEAD", "sha": "0" * 40, "installed": entries}))

    dirs = [str(agents)]
    if extra_dir_agents:
        other = tmp_path / "project-agents"
        other.mkdir()
        for name, tools in extra_dir_agents.items():
            (other / f"{name}.md").write_text(_agent_md(name, tools))
        dirs.append(str(other))

    runs = [_write_run(tmp_path, "base", None,
                       {"agents": base_agents if base_agents is not None else list(agent_tools),
                        "skills": base_skills if base_skills is not None else ["hld"]},
                       debug.get("base", "debug\n"))]
    for name in agent_tools:
        runs.append(_write_run(tmp_path, f"agent:{name}", name, {"tools": init_tools[name]},
                               debug.get(name, "debug\n")))
    spec = {"roster": [{"name": n} for n in agent_tools], "agent_dirs": dirs,
            "manifest": str(manifest), "runs": runs}
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(spec))
    return path


def test_full_spec_passes(tmp_path):
    proc = _check(str(_full_spec(tmp_path)))
    assert proc.returncode == 0, proc.stdout
    assert "PASS  2 roster agents" in proc.stdout


def test_bash_agent_may_omit_grep_and_glob(tmp_path):
    spec = _full_spec(tmp_path, agent_tools={"alpha": "Read, Grep", "beta": "Read, Grep, Glob, Bash"},
                      init_tools={"alpha": ["Read", "Grep"], "beta": ["Read", "Bash"]})
    proc = _check(str(spec))
    assert proc.returncode == 0, proc.stdout


def test_extra_tool_in_init_fails(tmp_path):
    spec = _full_spec(tmp_path, init_tools={"alpha": ["Read", "Grep", "Write"], "beta": ["Read", "Bash"]})
    proc = _check(str(spec))
    assert proc.returncode == 1, proc.stdout
    assert "init.tools != declared tools for alpha" in proc.stdout and "extra ['Write']" in proc.stdout


def test_missing_tool_in_init_fails(tmp_path):
    spec = _full_spec(tmp_path, init_tools={"alpha": ["Read"], "beta": ["Read", "Bash"]})
    proc = _check(str(spec))
    assert proc.returncode == 1, proc.stdout
    assert "missing ['Grep']" in proc.stdout


def test_agent_defined_twice_fails(tmp_path):
    spec = _full_spec(tmp_path, extra_dir_agents={"alpha": "Read"})
    proc = _check(str(spec))
    assert proc.returncode == 1, proc.stdout
    assert "agent 'alpha' is defined 2 times" in proc.stdout


def test_manifest_drift_fails(tmp_path):
    proc = _check(str(_full_spec(tmp_path, tamper_manifest=True)))
    assert proc.returncode == 1, proc.stdout
    assert "drift: agents/alpha.md" in proc.stdout


def test_invalid_effort_debug_line_fails(tmp_path):
    spec = _full_spec(tmp_path, debug={"beta": "[DEBUG] Agent beta: invalid effort 'turbo', ignoring\n"})
    proc = _check(str(spec))
    assert proc.returncode == 1, proc.stdout
    assert "invalid effort" in proc.stdout


def test_parse_failure_of_roster_file_fails(tmp_path):
    roster_file = tmp_path / "scope" / "agents" / "alpha.md"
    spec = _full_spec(tmp_path, debug={"base": f"[DEBUG] Failed to parse agent from {roster_file}: bad\n"})
    proc = _check(str(spec))
    assert proc.returncode == 1, proc.stdout
    assert "FAIL" in proc.stdout and "Failed to parse agent" in proc.stdout


def test_parse_failure_of_unrelated_file_only_warns(tmp_path):
    spec = _full_spec(tmp_path, debug={"base": "[DEBUG] Failed to parse agent from /else/where/zzz.md: bad\n"})
    proc = _check(str(spec))
    assert proc.returncode == 0, proc.stdout
    assert "WARN" in proc.stdout and "Failed to parse agent" in proc.stdout


def test_init_agents_missing_roster_name_fails(tmp_path):
    proc = _check(str(_full_spec(tmp_path, base_agents=["alpha"])))
    assert proc.returncode == 1, proc.stdout
    assert "init.agents is missing roster agents: ['beta']" in proc.stdout


def test_init_skills_missing_installed_skill_fails(tmp_path):
    proc = _check(str(_full_spec(tmp_path, base_skills=[])))
    assert proc.returncode == 1, proc.stdout
    assert "init.skills is missing installed skills: ['hld']" in proc.stdout


# ------------------------------------------------------ duplicate keys ---


def test_duplicate_frontmatter_key_in_roster_agent_fails(tmp_path):
    """Two `tools:` lines: YAML keeps the last silently, so the smoke check must refuse."""
    spec = _full_spec(tmp_path, agent_tools={"alpha": "Read, Grep\ntools: Read, Grep, Write",
                                             "beta": "Read, Bash"})
    proc = _check(str(spec))
    assert proc.returncode == 1, proc.stdout
    assert "FAIL" in proc.stdout and "alpha.md: frontmatter defines key(s) more than once: ['tools']" in proc.stdout


def test_duplicate_frontmatter_key_outside_roster_only_warns(tmp_path):
    spec = _full_spec(tmp_path, extra_dir_agents={"gamma": "Read\ntools: Write"})
    proc = _check(str(spec))
    assert proc.returncode == 0, proc.stdout
    assert "WARN" in proc.stdout and "gamma.md: frontmatter defines key(s) more than once" in proc.stdout


# ------------------------------------------- smoke.sh behaviour (no Claude) ---

SMOKE_SH = REPO_ROOT / "scripts" / "smoke.sh"
needs_bash_git = pytest.mark.skipif(
    __import__("shutil").which("bash") is None or __import__("shutil").which("git") is None,
    reason="needs bash and git",
)


def _base_env(tmp_path: Path) -> dict:
    import os

    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    tmpdir = tmp_path / "tmp"
    tmpdir.mkdir(exist_ok=True)
    env = {k: v for k, v in os.environ.items()}
    env.update(HOME=str(home), TMPDIR=str(tmpdir), GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    return env


def _parse_env(text: str) -> dict[str, str]:
    import re

    out = {}
    for line in text.splitlines():
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


@needs_bash_git
def test_smoke_sh_print_env_strips_credentials_and_isolates(tmp_path):
    """The environment every smoke run gets, as smoke.sh itself builds it."""
    env = _base_env(tmp_path)
    real_cfg = tmp_path / "real-claude-config"
    env.update({
        "ANTHROPIC_API_KEY": "sk-ant-fixture",
        "ANTHROPIC_AUTH_TOKEN": "fixture",
        "ANTHROPIC_BASE_URL": "https://example.invalid",
        "ANTHROPIC_MODEL": "fixture-model",
        "CLAUDE_CODE_OAUTH_TOKEN": "fixture",
        "CLAUDE_CODE_USE_BEDROCK": "1",
        "CLAUDECODE": "1",
        "CLAUDE_CONFIG_DIR": str(real_cfg),
        "AWS_SECRET_ACCESS_KEY": "fixture",
        "AWS_PROFILE": "prod",
        "GOOGLE_APPLICATION_CREDENTIALS": "/fixture.json",
        "AZURE_CLIENT_SECRET": "fixture",
        "VERTEX_REGION_CLAUDE_X": "us",
        "SMOKE_KEEP_ME": "kept",
    })
    proc = subprocess.run(["bash", str(SMOKE_SH), "--print-env"], env=env, capture_output=True, text=True,
                          stdin=subprocess.DEVNULL)
    assert proc.returncode == 0, proc.stderr
    got = _parse_env(proc.stdout)

    anthropic = {k: v for k, v in got.items() if k.startswith("ANTHROPIC_")}
    assert anthropic == {"ANTHROPIC_BASE_URL": "http://127.0.0.1:9"}
    claude = {k for k in got if k.startswith("CLAUDE")}
    assert claude == {"CLAUDE_CONFIG_DIR", "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"}, claude
    for prefix in ("AWS_", "GOOGLE_", "AZURE_", "VERTEX_"):
        assert not [k for k in got if k.startswith(prefix)], prefix
    assert got["SMOKE_KEEP_ME"] == "kept"

    cfg = Path(got["CLAUDE_CONFIG_DIR"])
    assert cfg != real_cfg
    assert cfg.name == "config" and cfg.parent.name.startswith("mahabharat-smoke.")
    assert cfg.parent.parent == (tmp_path / "tmp").resolve(), "the config dir must be a fresh temp dir"
    assert not cfg.parent.exists(), "the temp dir is removed after a clean exit"
    assert not real_cfg.exists()


def _fake_claude(tmp_path: Path) -> Path:
    """A stand-in binary: reports a supported version and does nothing else."""
    fake = tmp_path / "fake-claude"
    fake.write_text('#!/bin/sh\nif [ "$1" = "--version" ]; then echo "2.1.295 (Claude Code)"; fi\nexit 0\n')
    fake.chmod(0o755)
    return fake


def _smoke_repo(tmp_path: Path, env: dict) -> tuple[Path, str]:
    """A throwaway repo with the real smoke scripts and a one-agent roster (alpha), committed;
    the working tree's roster then lists only zeta (uncommitted)."""
    import shutil

    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    for f in ("smoke.sh", "smoke_check.py", "frontmatter_loader.py"):
        shutil.copy2(REPO_ROOT / "scripts" / f, repo / "scripts" / f)
    roster = repo / "agents" / "roster.yaml"
    roster.parent.mkdir()
    roster.write_text("agents:\n  - {name: alpha, file: agents/alpha.md, rank: master}\n")

    def git(*args):
        return subprocess.run(
            ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "commit.gpgsign=false",
             "-c", "core.hooksPath=/dev/null", "-C", str(repo), *args],
            env=env, capture_output=True, text=True, check=True).stdout.strip()

    git("init", "-q")
    git("add", "-A")
    git("commit", "-qm", "fixture")
    sha = git("rev-parse", "HEAD")
    roster.write_text("agents:\n  - {name: zeta, file: agents/zeta.md, rank: master}\n")
    return repo, sha


def _project(tmp_path: Path, manifest: dict | None) -> Path:
    proj = tmp_path / "proj"
    agents = proj / ".claude" / "agents"
    agents.mkdir(parents=True)
    for name in ("alpha", "beta"):
        (agents / f"{name}.md").write_text(_agent_md(name, "Read"))
    if manifest is not None:
        mpath = proj / ".claude" / "mahabharat" / "install-manifest.json"
        mpath.parent.mkdir(parents=True)
        mpath.write_text(json.dumps(manifest))
    return proj


def _run_smoke_project(tmp_path: Path, manifest_for) -> tuple[subprocess.CompletedProcess, str]:
    env = _base_env(tmp_path)
    repo, sha = _smoke_repo(tmp_path, env)
    proj = _project(tmp_path, manifest_for(sha))
    env["CLAUDE_BIN"] = str(_fake_claude(tmp_path))
    return subprocess.run(["bash", str(repo / "scripts" / "smoke.sh"), "--project", str(proj)],
                          env=env, capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=300), sha


def _entries(*names: str) -> list[dict]:
    return [{"path": f"agents/{n}.md", "sha256": "0" * 64} for n in names]


@needs_bash_git
def test_smoke_project_roster_comes_from_the_installed_commit(tmp_path):
    proc, sha = _run_smoke_project(
        tmp_path, lambda sha: {"ref": "v-test", "sha": sha, "installed": _entries("alpha")})
    assert f"== roster: from installed commit {sha}" in proc.stdout, proc.stdout + proc.stderr
    assert "WARN  no usable install manifest" not in proc.stderr
    if "== run: base" in proc.stdout:  # past the settings preflight
        assert "--agent alpha" in proc.stdout and "--agent zeta" not in proc.stdout


@needs_bash_git
def test_smoke_project_roster_falls_back_to_manifest_agents(tmp_path):
    """The Python CLI's manifest sha is a content digest, not a commit: use its agent list."""
    proc, _ = _run_smoke_project(
        tmp_path, lambda sha: {"ref": "mahabharat-agents 0.1.0 (python cli)", "sha": "f" * 40,
                               "installed": _entries("alpha", "beta")})
    assert "== roster: from the agents listed in" in proc.stdout, proc.stdout + proc.stderr
    if "== run: base" in proc.stdout:
        assert "--agent alpha" in proc.stdout and "--agent beta" in proc.stdout
        assert "--agent zeta" not in proc.stdout


@needs_bash_git
def test_smoke_project_roster_without_manifest_warns_and_uses_working_tree(tmp_path):
    proc, _ = _run_smoke_project(tmp_path, lambda sha: None)
    assert "WARN  no usable install manifest" in proc.stderr, proc.stderr
    assert "== roster: from working tree" in proc.stdout
    if "== run: base" in proc.stdout:
        assert "--agent zeta" in proc.stdout
