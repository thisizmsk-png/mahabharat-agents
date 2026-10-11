"""Assertions for scripts/smoke.sh (Stage 0 smoke test). Stdlib only; run with `python3 -I`.

Usage: python3 -I smoke_check.py <spec.json>
       python3 -I smoke_check.py --preflight-settings <settings.json>...

spec.json (written by smoke.sh):
  {
    "roster": [{"name": ..., "file": ...}, ...],   # expected agents (agents/roster.yaml)
    "agent_dirs": ["<scope>/.claude/agents", ...],  # every agents dir Claude scans in this scope
    "manifest": "<scope>/mahabharat/install-manifest.json" or null,
    "runs": [{"label": "base"|"agent:<name>", "agent": null|"<name>",
              "stream": "<file.jsonl>", "debug": "<file.log>", "stderr": "<file>"}]
  }

Agent files whose frontmatter defines a key twice (scripts/frontmatter_loader.py) fail
for roster agents and warn otherwise: YAML loaders silently keep the last value.

A run passes the auth check only if its final result message says "Not logged in"
and shows no sign of an API request: zero input/output tokens, zero API time, at most
one turn, and no "API Error" / "Connection error" / "Invalid API key" text (any of
those means credentials were present and a request was attempted: exit 3).

--preflight-settings checks settings files Claude Code would load for the run and
exits 1 if one sets apiKeyHelper, awsAuthRefresh, awsCredentialExport, gcpAuthRefresh
or otelHeadersHelper, or an env variable that carries credentials or switches the
provider, endpoint or proxy.

Exit codes: 0 pass, 1 assertion failures, 3 a run reached a model, attempted an API
request, or had credentials.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import sys
from pathlib import Path


def _load_frontmatter_loader():
    """Import scripts/frontmatter_loader.py by path (``python3 -I`` puts no script dir on sys.path)."""
    path = Path(__file__).resolve().parent / "frontmatter_loader.py"
    spec = importlib.util.spec_from_file_location("mahabharat_frontmatter_loader", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fm_loader = _load_frontmatter_loader()

# The only acceptable end of a run: Claude Code's own "Not logged in · Please run /login".
NOT_LOGGED_IN = re.compile(r"^\s*Not logged in\b")
# Result text that means a request was attempted (so credentials were present).
API_ATTEMPT = re.compile(
    r"api error|connection error|invalid api key|econnrefused|fetch failed|overloaded|"
    r"rate limit|credit balance|unauthorized|forbidden|status code \d{3}",
    re.I,
)
# Settings keys that run a credential helper or command.
HELPER_KEYS = ("apiKeyHelper", "awsAuthRefresh", "awsCredentialExport", "gcpAuthRefresh", "otelHeadersHelper")
# env variables (in a settings file) that carry credentials or switch provider/endpoint/proxy.
RISKY_ENV = re.compile(
    r"^(ANTHROPIC_|CLAUDE|AWS_|GOOGLE_|GCLOUD_|CLOUDSDK_|AZURE_|VERTEX_|BEDROCK_|NODE_OPTIONS$|NODE_EXTRA_CA_CERTS$)"
    r"|PROXY|KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|BASE_URL",
    re.I,
)
# Claude Code 2.1.295 reports the Agent tool as "Task", and when Bash is granted it folds
# Grep/Glob into Bash's embedded search, so init.tools omits them.
SEARCH_TOOLS = {"Grep", "Glob"}

failures: list[str] = []
warnings: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def frontmatter(path: Path) -> dict | None:
    """Minimal frontmatter reader.

    Returns {'name': str|None, 'tools': [str]|None, 'duplicates': [str]}; 'duplicates'
    lists keys the frontmatter defines twice (see scripts/frontmatter_loader.py)."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    fm_text, _body = fm_loader.split_frontmatter(text)
    if fm_text is None:
        return None
    lines = fm_text.splitlines()
    out: dict = {"name": None, "tools": None, "duplicates": fm_loader.duplicate_keys(fm_text)}
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^(name|tools):\s*(.*?)\s*$", line)
        if m:
            key, val = m.group(1), m.group(2)
            if key == "name":
                out["name"] = val.strip("'\"") or None
            elif val.startswith("["):
                out["tools"] = split_tools(val.strip("[]"))
            elif val:
                out["tools"] = split_tools(val.strip("'\""))
            else:
                items = []
                while i + 1 < len(lines) and re.match(r"^\s+-\s+", lines[i + 1]):
                    i += 1
                    items.append(re.sub(r"^\s+-\s+", "", lines[i]).strip("'\""))
                out["tools"] = items
        i += 1
    return out


def split_tools(value: str) -> list[str]:
    items, depth, cur = [], 0, ""
    for ch in value:
        depth += (ch == "(") - (ch == ")")
        if ch == "," and depth == 0:
            items.append(cur.strip().strip("'\""))
            cur = ""
        else:
            cur += ch
    if cur.strip():
        items.append(cur.strip().strip("'\""))
    return [t for t in items if t]


def tool_set(tools: list[str]) -> set[str]:
    out = set()
    for t in tools:
        base = t.split("(", 1)[0].strip()
        out.add("Agent" if base == "Task" else base)
    return out


def read_stream(path: Path) -> list[dict]:
    msgs = []
    if not path.is_file():
        return msgs
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            msgs.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return msgs


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preflight_settings(paths: list[str]) -> int:
    """Refuse settings files that could put credentials or a credential helper back."""
    bad = 0
    for raw in paths:
        path = Path(raw)
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            print(f"REFUSE {path}: cannot read it as JSON ({exc}); cannot verify it is safe")
            bad += 1
            continue
        if not isinstance(data, dict):
            print(f"REFUSE {path}: not a JSON object; cannot verify it is safe")
            bad += 1
            continue
        for key in HELPER_KEYS:
            if data.get(key):
                print(f"REFUSE {path}: sets {key!r} (a credential helper that runs a command)")
                bad += 1
        env = data.get("env")
        if env is not None and not isinstance(env, dict):
            print(f"REFUSE {path}: 'env' is not an object; cannot verify it is safe")
            bad += 1
        elif env:
            risky = sorted(k for k in env if RISKY_ENV.search(str(k)))
            if risky:
                print(f"REFUSE {path}: env sets {risky} (credentials, provider, endpoint or proxy)")
                bad += 1
            others = sorted(set(map(str, env)) - set(risky))
            if others:
                print(f"WARN   {path}: env sets {others}; they apply to the smoke runs")
        if data.get("hooks"):
            print(f"WARN   {path}: defines hooks; the smoke runs pass disableAllHooks, "
                  "but managed hooks may still run")
    return 1 if bad else 0


def check_auth_stop(label: str, result: dict | None) -> bool:
    """Fail unless the run ended at 'Not logged in' with no API activity.

    Returns True when the run shows an attempted API request (exit 3)."""
    if result is None:
        fail(f"[{label}] no result message")
        return False
    text = str(result.get("result") or "")
    attempted = []
    if API_ATTEMPT.search(text):
        attempted.append(f"result text {text.strip()[:120]!r}")
    usage = result.get("usage") or {}
    for key in ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"):
        if (usage.get(key) or 0) > 0:
            attempted.append(f"usage.{key}={usage.get(key)}")
    if (result.get("duration_api_ms") or 0) > 0:
        attempted.append(f"duration_api_ms={result.get('duration_api_ms')}")
    if (result.get("num_turns") or 0) > 1:
        attempted.append(f"num_turns={result.get('num_turns')}")
    if attempted:
        fail(f"[{label}] the run attempted an API request ({'; '.join(attempted)}); credentials leaked into the run")
        return True
    if not NOT_LOGGED_IN.search(text):
        fail(f"[{label}] run did not end at 'Not logged in': {text.strip()[:200]!r}")
    return False


def main() -> int:
    if len(sys.argv) >= 2 and sys.argv[1] == "--preflight-settings":
        return preflight_settings(sys.argv[2:])
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    roster = spec["roster"]
    roster_names = [e["name"] for e in roster]

    # ---- every agent definition in scope, parsed from the files (not from init) ----
    defined: dict[str, list[Path]] = {}
    duplicated: dict[Path, list[str]] = {}
    for d in spec["agent_dirs"]:
        root = Path(d)
        if not root.is_dir():
            continue
        for dirpath, _dirs, files in os.walk(root, followlinks=True):
            for f in sorted(files):
                if not f.endswith(".md"):
                    continue
                p = Path(dirpath) / f
                fm = frontmatter(p)
                name = (fm or {}).get("name")
                if not name:
                    warn(f"{p}: no frontmatter name (Claude Code may skip it)")
                    continue
                defined.setdefault(name, []).append(p)
                if fm["duplicates"]:
                    duplicated[p] = fm["duplicates"]
    for name, paths in sorted(defined.items()):
        if len(paths) > 1:
            fail(f"agent '{name}' is defined {len(paths)} times: " + ", ".join(map(str, paths)))
    for name in roster_names:
        if name not in defined:
            fail(f"roster agent '{name}' has no file in scope ({', '.join(spec['agent_dirs'])})")
    roster_files = {str(p.resolve()) for n in roster_names for p in defined.get(n, [])}
    # A duplicated key is silently resolved by YAML loaders (last one wins), so what a
    # reviewer reads and what Claude Code loads can differ. Fatal for a roster agent.
    for p, keys in sorted(duplicated.items()):
        msg = f"{p}: frontmatter defines key(s) more than once: {sorted(set(keys))}"
        (fail if str(p.resolve()) in roster_files else warn)(msg)

    # ---- install manifest: catches drift between the installed copy and the release ----
    manifest_path = spec.get("manifest")
    installed_skills: list[str] = []
    installed_workflows: list[str] = []
    if manifest_path and Path(manifest_path).is_file():
        manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        base = Path(manifest_path).parent.parent
        print(f"manifest: ref {manifest.get('ref')} sha {manifest.get('sha')}, {len(manifest.get('installed', []))} files")
        for entry in manifest.get("installed", []):
            p = base / entry["path"]
            if not p.is_file():
                fail(f"manifest file missing: {entry['path']}")
            elif sha256(p) != entry["sha256"]:
                fail(f"drift: {entry['path']} differs from the installed release (sha256 mismatch)")
            parts = entry["path"].split("/")
            if parts[0] == "skills" and parts[-1] == "SKILL.md" and len(parts) == 3:
                installed_skills.append(parts[1])
            if parts[0] == "workflows" and parts[-1].endswith(".js"):
                installed_workflows.append(parts[-1][:-3])
        manifest_agents = {
            e["path"][len("agents/"):-3] for e in manifest.get("installed", [])
            if e["path"].startswith("agents/")
        }
        for name in sorted(set(roster_names) - manifest_agents):
            fail(f"roster agent '{name}' is not in the install manifest (stale install?)")
    else:
        warn("no install manifest in scope; sha256 drift check skipped")

    # ---- each run ----
    reached_model = False
    for run in spec["runs"]:
        label = run["label"]
        msgs = read_stream(Path(run["stream"]))
        init = next((m for m in msgs if m.get("type") == "system" and m.get("subtype") == "init"), None)
        stderr = Path(run["stderr"]).read_text(encoding="utf-8", errors="replace") if Path(run["stderr"]).is_file() else ""

        for m in msgs:
            if m.get("type") == "assistant":
                model = (m.get("message") or {}).get("model")
                if model != "<synthetic>":
                    reached_model = True
                    fail(f"[{label}] REACHED A MODEL REPLY (model={model!r}); the smoke test must stop before any model call")
            if m.get("type") == "result" and (m.get("total_cost_usd") or 0) > 0:
                reached_model = True
                fail(f"[{label}] REACHED A MODEL: total_cost_usd={m.get('total_cost_usd')}")

        if init is None:
            fail(f"[{label}] no system/init message; stderr: {stderr.strip()[:300]}")
            continue
        if init.get("apiKeySource") not in (None, "none"):
            reached_model = True
            fail(f"[{label}] credentials were visible (apiKeySource={init.get('apiKeySource')!r}); isolation failed")

        result = next((m for m in reversed(msgs) if m.get("type") == "result"), None)
        if check_auth_stop(label, result):
            reached_model = True

        if run["agent"] is None:
            missing = [n for n in roster_names if n not in (init.get("agents") or [])]
            if missing:
                fail(f"[{label}] init.agents is missing roster agents: {missing}")
            init_skills = set(init.get("skills") or [])
            missing_skills = [s for s in installed_skills if s not in init_skills]
            if missing_skills:
                fail(f"[{label}] init.skills is missing installed skills: {missing_skills}")
            commands = set(init.get("slash_commands") or [])
            for wf in installed_workflows:
                if wf not in commands:
                    warn(f"[{label}] workflow '{wf}' not seen in init.slash_commands (unverified naming)")
        else:
            name = run["agent"]
            paths = defined.get(name) or []
            fm = frontmatter(paths[0]) if paths else None
            declared = (fm or {}).get("tools")
            if declared is None:
                fail(f"[{label}] {name}: no 'tools' list declared")
            else:
                want = tool_set(declared)
                got = tool_set(init.get("tools") or [])
                if "Bash" in want:
                    want, got = want - SEARCH_TOOLS, got - SEARCH_TOOLS
                if want != got:
                    fail(
                        f"[{label}] init.tools != declared tools for {name}: "
                        f"missing {sorted(want - got)}, extra {sorted(got - want)}"
                    )

        debug = Path(run["debug"])
        if debug.is_file():
            for line in debug.read_text(encoding="utf-8", errors="replace").splitlines():
                if "invalid effort" in line:
                    fail(f"[{label}] debug: {line.strip()[:300]}")
                elif "Failed to parse agent" in line:
                    hit = [f for f in roster_files if f in line or os.path.basename(f) in line]
                    (fail if hit else warn)(f"[{label}] debug: {line.strip()[:300]}")
        else:
            fail(f"[{label}] no debug log written")

    # de-duplicate repeated debug lines across runs
    def uniq(xs):
        seen, out = set(), []
        for x in xs:
            key = re.sub(r"^\[[^\]]+\] ", "", x)
            key = re.sub(r"\d{4}-\d\d-\d\dT[\d:.]+Z ", "", key)
            if key not in seen:
                seen.add(key)
                out.append(x)
        return out

    for w in uniq(warnings):
        print(f"WARN  {w}")
    for f in uniq(failures):
        print(f"FAIL  {f}")
    if reached_model:
        print("\n" + "!" * 72)
        print("!! SMOKE TEST REACHED A MODEL OR SAW CREDENTIALS. It must cost $0 and stop at auth.")
        print("!! Check the env isolation in scripts/smoke.sh before running it again.")
        print("!" * 72)
        return 3
    if failures:
        return 1
    print(f"PASS  {len(roster_names)} roster agents loaded, tools match, no parse/effort errors, no duplicates, no model call")
    return 0


if __name__ == "__main__":
    sys.exit(main())
