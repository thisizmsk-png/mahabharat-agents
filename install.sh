#!/usr/bin/env bash
# Mahabharat Agents — quick project installer (copies from this working tree).
#
# Usage: bash install.sh [/path/to/your/project] [--dry-run] [--skip-skill <name>]... [--force-replace]
#
# NOTE: prefer scripts/install.sh. It installs a reviewed git ref (`--from <tag>`)
# instead of whatever is in the working tree, supports user scope, and writes the
# sha256 install manifest that scripts/smoke.sh checks:
#
#   scripts/install.sh --from <tag> --target /path/to/your/project
#   scripts/smoke.sh --project /path/to/your/project
#
# This script is a thin wrapper around the mahabharat-install Python CLI
# (src/mahabharat_agents/cli.py), run against this checkout, so it gets the same
# safety checks: it refuses a symlink anywhere on a destination path, backs up every
# file it replaces to .claude/mahabharat/backup/ (never under agents/), replaces only
# files it owns (another package's same-named skill is refused), and writes
# .claude/mahabharat/install-manifest.json. It installs into <project>/.claude/:
#   agents/<name>.md   every agent listed in agents/roster.yaml, flat (sepoys included;
#                      templates/sepoy-agent.md is never installed)
#   skills/<name>/     shared + role-specific skills (the retired zero-bias skill excluded)
# orchestration/ and context/ are not installed: those pre-v1 docs still predate the
# owner-only approval model.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

TARGET_ARG="."
PASS=()
while [ $# -gt 0 ]; do
    case "$1" in
        --dry-run|--force-replace)
            PASS+=("$1"); shift ;;
        --skip-skill)
            [ $# -ge 2 ] || { echo "Error: --skip-skill needs a skill name" >&2; exit 1; }
            PASS+=("$1" "$2"); shift 2 ;;
        --skip-skill=*)
            PASS+=("$1"); shift ;;
        -h|--help)
            sed -n '4p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
        -*)
            echo "Error: unknown option $1" >&2
            echo "Usage: bash install.sh /path/to/your/project [--dry-run] [--skip-skill <name>]... [--force-replace]" >&2
            exit 1 ;;
        *)
            TARGET_ARG="$1"; shift ;;
    esac
done

if [ ! -d "$TARGET_ARG" ]; then
    echo "Error: Target directory '$TARGET_ARG' does not exist." >&2
    echo "Usage: bash install.sh /path/to/your/project" >&2
    exit 1
fi
if [ -L "$TARGET_ARG" ]; then
    echo "Error: target '$TARGET_ARG' is a symlink; pass the real path." >&2
    exit 1
fi
TARGET_DIR="$(cd -P "$TARGET_ARG" && pwd)"

PY="$(command -v python3 || true)"
if [ -z "$PY" ]; then
    echo "Error: python3 is required (it runs the installer's safety checks)." >&2
    exit 1
fi

echo "======================================"
echo "  Mahabharat Agents Package Installer"
echo "======================================"
echo ""
echo "Source:  $SCRIPT_DIR (working tree; see scripts/install.sh for tagged installs)"
echo "Target:  $TARGET_DIR/.claude"

# -I: ignore PYTHON* variables, the user site dir and the current directory; -B: write no
# bytecode into the checkout. The CLI
# is imported from this checkout's src/ only.
"$PY" -I -B -c '
import sys
sys.path.insert(0, sys.argv[1])
from mahabharat_agents.cli import install
install(sys.argv[2:])
' "$SCRIPT_DIR/src" --source "$SCRIPT_DIR" "$TARGET_DIR" ${PASS[@]+"${PASS[@]}"}

masters=0
sepoys=0
while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in
        *"rank: sepoy"*) sepoys=$((sepoys + 1)) ;;
        *"{name:"*) masters=$((masters + 1)) ;;
    esac
done < "$SCRIPT_DIR/agents/roster.yaml"

DONE="Installation Complete!"
case " ${PASS[*]-} " in *" --dry-run "*) DONE="Dry run complete (nothing was written)" ;; esac
echo "======================================"
echo "  $DONE"
echo "======================================"
echo ""
echo "Agents and skills in scope:"
echo "  - $masters master agents (incl. krishna, the orchestrator)"
echo "  - $sepoys sepoy agents"
echo "  - shared and role-specific skills"
echo ""
echo "Next steps:"
echo "  1. Agents are available in Claude Code from .claude/agents/"
echo "  2. Skills are available from .claude/skills/"
echo "  3. Start the orchestrator as the main session: claude --agent krishna"
echo "  4. Add a sepoy: copy templates/sepoy-agent.md into agents/, list it in agents/roster.yaml, re-run"
echo "  5. Verify: scripts/smoke.sh --project $TARGET_DIR"
echo ""
