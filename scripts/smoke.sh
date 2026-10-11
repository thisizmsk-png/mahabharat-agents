#!/usr/bin/env bash
# scripts/smoke.sh — Stage 0 smoke test: costs $0 and needs no auth.
#
# Usage: scripts/smoke.sh [--project <dir> | --user] [--from <git-ref> | --worktree] [--keep] [--print-env]
#
#   (default)          build a temp fixture project, install this repo into it with
#                      `scripts/install.sh --from <ref> --target <fixture>`, and check it
#   --project <dir>    check an existing project install (<dir>/.claude)
#   --user             check the user install (${CLAUDE_CONFIG_DIR:-$HOME/.claude}), read-only
#   --from <git-ref>   ref to install in the default fixture mode (default: HEAD)
#   --worktree         fixture mode, but install a throwaway commit of the working tree
#                      (tracked + untracked, not ignored) to check work before it is committed
#   --keep             keep the temp dir with logs (it is always kept on failure)
#   --print-env        print the isolated environment every run gets, then exit 0
#                      (runs nothing; used by tests/test_smoke_check.py)
#
#   CLAUDE_BIN         Claude Code binary to test (default: claude); must be >= 2.1.295
#
# How it stays at $0: every run uses a fresh empty CLAUDE_CONFIG_DIR (so no stored login),
# strips ANTHROPIC_*/CLAUDE* and cloud-provider credential variables (AWS_*, GOOGLE_*,
# AZURE_*, ...) from the environment, points ANTHROPIC_BASE_URL at a dead local port as a
# backstop (in the environment and again in a --settings file, which outranks project
# settings), and reads stdin from /dev/null. Claude Code emits system/init and its
# agent-parse debug lines before authenticating, then stops with "Not logged in". If a run
# ever reaches a model, attempts an API request, or sees credentials, this script fails
# loudly (exit 3).
#
# Settings files can bring credentials or code back, so every run also passes
# `--settings <file>` with disableAllHooks (no settings hook runs) and
# `--strict-mcp-config` (no MCP server starts). Before any run, the settings files Claude
# Code would still load (the project's .claude/settings.json and settings.local.json, and
# managed settings, managed-settings.d/*.json drop-ins and macOS MDM preferences) are
# checked; the script refuses if one sets apiKeyHelper,
# awsAuthRefresh, awsCredentialExport, gcpAuthRefresh or otelHeadersHelper, or an env
# variable that carries credentials or switches the provider, endpoint or proxy.
#
# In --user mode the temp config dir gets symlinks to the real agents/, skills/ and
# workflows/ (read only; nothing is written there) and nothing else: your settings.json,
# hooks, MCP servers and credentials are not used.
#
# Checks: init.agents ⊇ roster; per agent, init.tools == the declared `tools` (Agent may
# show as Task, Agent(...) as Agent/Task; Grep/Glob fold into Bash when Bash is granted);
# no "Failed to parse agent" line for a roster file and no "invalid effort" line; no agent
# name defined twice across agents/**/*.md in scope; no frontmatter key defined twice in a
# roster agent (scripts/frontmatter_loader.py); init.skills ⊇ installed skills; the
# install manifest's sha256s match the files on disk.
set -euo pipefail

MIN_VERSION="2.1.295"
PROG="scripts/smoke.sh"

usage() { sed -n '4,17p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; }
die() { printf '%s: error: %s\n' "$PROG" "$*" >&2; exit 1; }

MODE="fixture"
PROJECT=""
FROM="HEAD"
FROM_SET=0
WORKTREE=0
KEEP=0
PRINT_ENV=0
while [ $# -gt 0 ]; do
    case "$1" in
        --project)
            [ $# -ge 2 ] || die "--project needs a directory"
            MODE="project"; PROJECT="$2"; shift 2 ;;
        --project=*)
            MODE="project"; PROJECT="${1#--project=}"; shift ;;
        --user)
            MODE="user"; shift ;;
        --from)
            [ $# -ge 2 ] || die "--from needs a git ref"
            FROM="$2"; FROM_SET=1; shift 2 ;;
        --from=*)
            FROM="${1#--from=}"; FROM_SET=1; shift ;;
        --worktree)
            WORKTREE=1; shift ;;
        --keep)
            KEEP=1; shift ;;
        --print-env)
            PRINT_ENV=1; shift ;;
        -h|--help)
            usage; exit 0 ;;
        *)
            usage >&2; die "unknown argument: $1" ;;
    esac
done

if [ "$WORKTREE" -eq 1 ]; then
    [ "$MODE" = "fixture" ] || die "--worktree works only in the default fixture mode"
    [ "$FROM_SET" -eq 0 ] || die "--worktree and --from are mutually exclusive"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
INSTALL_REPO="$REPO"
CLAUDE_BIN="${CLAUDE_BIN:-claude}"
PYTHON="$(command -v python3 || true)"
[ -n "$PYTHON" ] || die "python3 is required"

# The real user config dir, captured before the isolated env drops CLAUDE_CONFIG_DIR.
REAL_CONFIG="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"

WORK="$(mktemp -d "${TMPDIR:-/tmp}/mahabharat-smoke.XXXXXX")"
WORK="$(cd -P "$WORK" && pwd)"
STATUS=1
cleanup() {
    if [ "$KEEP" -eq 1 ] || [ "$STATUS" -ne 0 ]; then
        echo "logs kept in $WORK" >&2
    else
        rm -rf "$WORK"
    fi
}
trap cleanup EXIT
mkdir -p "$WORK/config" "$WORK/logs"

# ---------------------------------------------------------- isolation ---
# build_iso_env <config-dir>: fill ISO_ENV with `env` arguments that drop every
# Anthropic/Claude variable (API keys, OAuth tokens, base URLs, provider switches, and
# the parent session's variables when run from inside Claude Code) and set the
# isolating ones. Cloud-provider credentials go too: a settings file could switch on
# Bedrock or Vertex, which would then pick up ambient AWS/Google/Azure credentials.
build_iso_env() {
    local config_dir="$1" v
    ISO_ENV=()
    for v in $(env | sed -n 's/^\([A-Za-z_][A-Za-z0-9_]*\)=.*/\1/p'); do
        case "$v" in
            ANTHROPIC_*|CLAUDE*|AWS_*|GOOGLE_*|GCLOUD_*|CLOUDSDK_*|AZURE_*|VERTEX_*|BEDROCK_*) ISO_ENV+=(-u "$v") ;;
        esac
    done
    ISO_ENV+=(-u ANTHROPIC_API_KEY)
    ISO_ENV+=(
        "CLAUDE_CONFIG_DIR=$config_dir"
        "ANTHROPIC_BASE_URL=http://127.0.0.1:9"
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1"
        "DISABLE_AUTOUPDATER=1"
    )
}
build_iso_env "$WORK/config"

if [ "$PRINT_ENV" -eq 1 ]; then
    # Exactly the environment `env "${ISO_ENV[@]}" "$CLAUDE_BIN" ...` gives each run.
    env "${ISO_ENV[@]}" env
    STATUS=0
    exit 0
fi

# Settings passed on every run. --settings outranks project and local settings, so its
# env value wins over a project's ANTHROPIC_BASE_URL; disableAllHooks stops settings hooks.
SMOKE_SETTINGS="$WORK/smoke-settings.json"
printf '%s\n' '{' '  "disableAllHooks": true,' '  "env": { "ANTHROPIC_BASE_URL": "http://127.0.0.1:9" }' '}' \
    > "$SMOKE_SETTINGS"

# Run with a wall-clock limit, using whatever the platform has.
with_timeout() {
    local secs="$1"; shift
    if command -v timeout >/dev/null 2>&1; then
        timeout "$secs" "$@"
    elif command -v perl >/dev/null 2>&1; then
        perl -e 'alarm shift; exec @ARGV or die "exec: $!"' "$secs" "$@"
    else
        "$@"
    fi
}

# ------------------------------------------------------------ version ---
if ! command -v "$CLAUDE_BIN" >/dev/null 2>&1 && [ ! -x "$CLAUDE_BIN" ]; then
    die "Claude Code binary '$CLAUDE_BIN' not found (set CLAUDE_BIN)"
fi
VERSION_LINE="$(env "${ISO_ENV[@]}" "$CLAUDE_BIN" --version < /dev/null 2>/dev/null | head -n 1 || true)"
VERSION="$(printf '%s\n' "$VERSION_LINE" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -n 1 || true)"
[ -n "$VERSION" ] || die "cannot read a version from '$CLAUDE_BIN --version' (got: $VERSION_LINE)"

version_ge() {  # version_ge A B: A >= B (numeric, dotted)
    local IFS=.
    # shellcheck disable=SC2206
    local a=($1) b=($2) i
    for i in 0 1 2; do
        if [ "${a[$i]:-0}" -gt "${b[$i]:-0}" ]; then return 0; fi
        if [ "${a[$i]:-0}" -lt "${b[$i]:-0}" ]; then return 1; fi
    done
    return 0
}
version_ge "$VERSION" "$MIN_VERSION" \
    || die "Claude Code $VERSION is too old; the smoke test needs >= $MIN_VERSION (set CLAUDE_BIN)"

# -------------------------------------------------------------- scope ---
AGENT_DIRS=()
case "$MODE" in
    fixture)
        RUN_CWD="$WORK/project"
        mkdir -p "$RUN_CWD"
        if [ "$WORKTREE" -eq 1 ]; then
            # A throwaway repo holding one commit of the working tree. The real checkout
            # is only read: no git command here changes its state.
            INSTALL_REPO="$WORK/worktree-snapshot"
            mkdir -p "$INSTALL_REPO"
            echo "== snapshotting the working tree into $INSTALL_REPO"
            ( cd "$REPO" && git ls-files -z --cached --others --exclude-standard ) > "$WORK/snapshot-files"
            ( cd "$REPO" && while IFS= read -r -d '' f; do
                  case "$f" in */) continue ;; esac            # a nested repo, not a file
                  if [ -d "$f" ] && [ ! -L "$f" ]; then continue; fi
                  if [ -e "$f" ] || [ -L "$f" ]; then printf '%s\0' "$f"; fi   # skip deleted-but-tracked
              done < "$WORK/snapshot-files" ) > "$WORK/snapshot-present"
            ( cd "$REPO" && tar -cf - --null -T "$WORK/snapshot-present" ) | tar -xf - -C "$INSTALL_REPO"
            snap_git() {
                env GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 git -C "$INSTALL_REPO" \
                    -c user.name=smoke -c user.email=smoke@example.invalid \
                    -c commit.gpgsign=false -c core.hooksPath=/dev/null "$@"
            }
            snap_git init -q
            snap_git add -A
            snap_git commit -qm "smoke: working-tree snapshot" \
                || die "could not commit the working-tree snapshot"
            FROM="HEAD"
        fi
        echo "== installing $FROM into a fixture project"
        if ! "$INSTALL_REPO/scripts/install.sh" --from "$FROM" --target "$RUN_CWD" > "$WORK/logs/install.log" 2>&1; then
            cat "$WORK/logs/install.log" >&2
            [ "$WORKTREE" -eq 1 ] || echo "$PROG: hint: to check uncommitted work, run $PROG --worktree" >&2
            die "scripts/install.sh failed"
        fi
        SCOPE="$RUN_CWD/.claude"
        AGENT_DIRS+=("$SCOPE/agents")
        ROSTER_SRC="git"
        ;;
    project)
        [ -d "$PROJECT" ] || die "project directory '$PROJECT' does not exist"
        RUN_CWD="$(cd -P "$PROJECT" && pwd)"
        SCOPE="$RUN_CWD/.claude"
        [ -d "$SCOPE/agents" ] || die "$SCOPE/agents does not exist; install first (scripts/install.sh --target $PROJECT)"
        AGENT_DIRS+=("$SCOPE/agents")
        ROSTER_SRC="installed"
        ;;
    user)
        [ -d "$REAL_CONFIG" ] || die "user config dir $REAL_CONFIG does not exist"
        SCOPE="$(cd -P "$REAL_CONFIG" && pwd)"
        # Only the definitions are linked. settings.json is NOT copied: its env,
        # apiKeyHelper, hooks and MCP servers could bring credentials back or run code.
        for d in agents skills workflows; do
            if [ -e "$SCOPE/$d" ]; then ln -s "$SCOPE/$d" "$WORK/config/$d"; fi
        done
        RUN_CWD="$WORK/cwd"
        mkdir -p "$RUN_CWD"
        AGENT_DIRS+=("$SCOPE/agents")
        # Also scan the invoking project's agents, where a duplicate name would shadow.
        if [ -d "$PWD/.claude/agents" ] && [ "$(cd -P "$PWD/.claude/agents" && pwd)" != "$SCOPE/agents" ]; then
            AGENT_DIRS+=("$(cd -P "$PWD/.claude/agents" && pwd)")
        fi
        ROSTER_SRC="installed"
        ;;
esac

# Roster: what the install under test was supposed to contain, not this checkout's
# working tree (which may be ahead of, or behind, what is installed).
#   fixture mode: the ref that was just installed.
#   --project/--user: the install manifest's commit, when it is a commit in this repo
#     (scripts/install.sh records it); else the agents the manifest lists (the Python
#     CLI's manifest); else, with a warning, this checkout's agents/roster.yaml.
INSTALLED_MANIFEST="$SCOPE/mahabharat/install-manifest.json"
if [ "$ROSTER_SRC" = "git" ]; then
    git -C "$INSTALL_REPO" show "$FROM:agents/roster.yaml" > "$WORK/roster.yaml" \
        || die "ref $FROM has no agents/roster.yaml"
    echo "== roster: from ref $FROM"
else
    ROSTER_FROM=""
    if [ -f "$INSTALLED_MANIFEST" ] && [ ! -L "$INSTALLED_MANIFEST" ]; then
        MANIFEST_SHA="$("$PYTHON" -I -c '
import json, re, sys
try:
    sha = str(json.load(open(sys.argv[1], encoding="utf-8")).get("sha") or "")
except Exception:
    sha = ""
print(sha if re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", sha) else "")
' "$INSTALLED_MANIFEST" 2>/dev/null || true)"
        if [ -n "$MANIFEST_SHA" ] \
            && git -C "$REPO" cat-file -e "$MANIFEST_SHA^{commit}" 2>/dev/null \
            && git -C "$REPO" show "$MANIFEST_SHA:agents/roster.yaml" > "$WORK/roster.yaml" 2>/dev/null; then
            ROSTER_FROM="installed commit $MANIFEST_SHA (from $INSTALLED_MANIFEST)"
        elif "$PYTHON" -I -c '
import json, re, sys
data = json.load(open(sys.argv[1], encoding="utf-8"))
names = []
for e in data.get("installed", []):
    m = re.fullmatch(r"agents/([a-z][a-z0-9-]*)\.md", str((e or {}).get("path", "")))
    if m:
        names.append(m.group(1))
if not names:
    sys.exit(1)
with open(sys.argv[2], "w", encoding="utf-8") as out:
    out.write("agents:\n")
    for n in names:
        out.write(f"  - {{name: {n}, file: agents/{n}.md, rank: master}}\n")
' "$INSTALLED_MANIFEST" "$WORK/roster.yaml" 2>/dev/null; then
            ROSTER_FROM="the agents listed in $INSTALLED_MANIFEST"
        fi
    fi
    if [ -z "$ROSTER_FROM" ]; then
        echo "WARN  no usable install manifest in $SCOPE (or its commit is not in $REPO); expecting this checkout's working-tree agents/roster.yaml, which may not match what is installed" >&2
        cp "$REPO/agents/roster.yaml" "$WORK/roster.yaml"
        ROSTER_FROM="working tree $REPO/agents/roster.yaml"
    fi
    echo "== roster: from $ROSTER_FROM"
fi

# ---------------------------------------------------- settings preflight ---
# Settings files Claude Code still loads despite the isolation: the project's (from the
# run's cwd and its git root) and managed settings. Refuse before any run if one of them
# could inject credentials or a credential helper.
PREFLIGHT=()
for dir in "$RUN_CWD" "$(git -C "$RUN_CWD" rev-parse --show-toplevel 2>/dev/null || true)"; do
    [ -n "$dir" ] || continue
    for f in "$dir/.claude/settings.json" "$dir/.claude/settings.local.json"; do
        if [ -e "$f" ]; then PREFLIGHT+=("$f"); fi
    done
done
for f in "/Library/Application Support/ClaudeCode/managed-settings.json" \
         "/etc/claude-code/managed-settings.json" \
         "$WORK/config/settings.json" "$WORK/config/settings.local.json"; do
    if [ -e "$f" ]; then PREFLIGHT+=("$f"); fi
done
# Managed drop-ins: Claude Code also merges every *.json in managed-settings.d/, and
# managed settings outrank --settings, so a drop-in could undo the dead-port backstop.
for d in "/Library/Application Support/ClaudeCode/managed-settings.d" "/etc/claude-code/managed-settings.d"; do
    [ -d "$d" ] || continue
    for f in "$d"/*.json; do
        if [ -e "$f" ]; then PREFLIGHT+=("$f"); fi
    done
done
# macOS MDM preferences (per-user and device-level). Claude Code reads them with
# `plutil -convert json`; do the same and check the result like any settings file. If the
# conversion fails, preflight gets an unreadable file and refuses.
MDM_USER="$(id -un 2>/dev/null || true)"
mdm_i=0
for f in ${MDM_USER:+"/Library/Managed Preferences/$MDM_USER/com.anthropic.claudecode.plist"} \
         "/Library/Managed Preferences/com.anthropic.claudecode.plist"; do
    [ -e "$f" ] || continue
    mdm_i=$((mdm_i + 1))
    out="$WORK/mdm-preferences-$mdm_i.json"
    echo "WARN  MDM-managed Claude Code preferences found: $f (checking them as settings)" >&2
    if [ -x /usr/bin/plutil ] && /usr/bin/plutil -convert json -o "$out" -- "$f" 2>/dev/null; then
        :
    else
        printf 'not JSON: plutil could not convert %s\n' "$f" > "$out"
    fi
    PREFLIGHT+=("$out")
done
if [ "${#PREFLIGHT[@]}" -gt 0 ]; then
    "$PYTHON" -I "$SCRIPT_DIR/smoke_check.py" --preflight-settings "${PREFLIGHT[@]}" \
        || die "a settings file Claude Code would load can inject credentials or helpers (see above); refusing to run"
fi
ROSTER_NAMES=()
while IFS= read -r line || [ -n "$line" ]; do
    n="$(printf '%s\n' "$line" | sed -nE 's/^[[:space:]]*-[[:space:]]*\{[[:space:]]*name:[[:space:]]*([a-z][a-z0-9-]*)[[:space:]]*,.*$/\1/p')"
    if [ -n "$n" ]; then ROSTER_NAMES+=("$n"); fi
done < "$WORK/roster.yaml"
[ "${#ROSTER_NAMES[@]}" -gt 0 ] || die "no agents parsed from roster"

echo "== Claude Code $VERSION ($CLAUDE_BIN)"
echo "== mode: $MODE; scope: $SCOPE; ${#ROSTER_NAMES[@]} roster agents"

# --------------------------------------------------------------- runs ---
RUN_SPECS=""
run_claude() {  # run_claude <label> <agent-or-empty> [extra args...]
    local label="$1" agent="$2"; shift 2
    local slug="${label//[^A-Za-z0-9_-]/_}"
    local stream="$WORK/logs/$slug.jsonl" debug="$WORK/logs/$slug.debug.log" errf="$WORK/logs/$slug.stderr"
    (
        cd "$RUN_CWD"
        with_timeout 120 env "${ISO_ENV[@]}" "$CLAUDE_BIN" -p x \
            --output-format stream-json --verbose --debug-file "$debug" \
            --settings "$SMOKE_SETTINGS" --strict-mcp-config "$@" \
            < /dev/null > "$stream" 2> "$errf"
    ) || true
    local agent_json="null"
    if [ -n "$agent" ]; then agent_json="\"$agent\""; fi
    RUN_SPECS="$RUN_SPECS${RUN_SPECS:+,}
    {\"label\": \"$label\", \"agent\": $agent_json, \"stream\": \"$stream\", \"debug\": \"$debug\", \"stderr\": \"$errf\"}"
}

echo "== run: base"
run_claude "base" ""
for name in "${ROSTER_NAMES[@]}"; do
    echo "== run: --agent $name"
    run_claude "agent:$name" "$name" --agent "$name"
done

# ------------------------------------------------------------- checks ---
MANIFEST_JSON="null"
[ ! -f "$SCOPE/mahabharat/install-manifest.json" ] || MANIFEST_JSON="\"$SCOPE/mahabharat/install-manifest.json\""
ROSTER_JSON=""
for name in "${ROSTER_NAMES[@]}"; do
    ROSTER_JSON="$ROSTER_JSON${ROSTER_JSON:+, }{\"name\": \"$name\"}"
done
DIRS_JSON=""
for d in "${AGENT_DIRS[@]}"; do
    DIRS_JSON="$DIRS_JSON${DIRS_JSON:+, }\"$d\""
done
cat > "$WORK/spec.json" <<EOF
{
  "roster": [$ROSTER_JSON],
  "agent_dirs": [$DIRS_JSON],
  "manifest": $MANIFEST_JSON,
  "runs": [$RUN_SPECS
  ]
}
EOF

set +e
"$PYTHON" -I "$SCRIPT_DIR/smoke_check.py" "$WORK/spec.json"
STATUS=$?
set -e
exit "$STATUS"
