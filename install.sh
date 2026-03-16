#!/bin/bash
# Mahabharat Agents Package — Installer
# Installs agents, skills, and context into a target project's .claude/ directory

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${1:-.}"

# Resolve to absolute path
TARGET_DIR="$(cd "$TARGET_DIR" && pwd)"

echo "======================================"
echo "  Mahabharat Agents Package Installer"
echo "======================================"
echo ""
echo "Source:  $SCRIPT_DIR"
echo "Target:  $TARGET_DIR"
echo ""

# Verify target is a valid project directory
if [ ! -d "$TARGET_DIR" ]; then
    echo "Error: Target directory '$TARGET_DIR' does not exist."
    echo "Usage: bash install.sh /path/to/your/project"
    exit 1
fi

# Create .claude directories if they don't exist
echo "Creating .claude directories..."
mkdir -p "$TARGET_DIR/.claude/agents"
mkdir -p "$TARGET_DIR/.claude/skills"

# Install master agents
echo "Installing master agents (17)..."
for agent_file in "$SCRIPT_DIR/agents/masters/"*.md; do
    if [ -f "$agent_file" ]; then
        agent_name=$(basename "$agent_file")
        cp "$agent_file" "$TARGET_DIR/.claude/agents/$agent_name"
        echo "  + $agent_name"
    fi
done

# Install sepoy examples (optional)
if [ -d "$SCRIPT_DIR/agents/sepoys/examples" ]; then
    echo "Installing sepoy examples..."
    mkdir -p "$TARGET_DIR/.claude/agents/sepoys"
    cp "$SCRIPT_DIR/agents/sepoys/_template.md" "$TARGET_DIR/.claude/agents/sepoys/"
    for sepoy_file in "$SCRIPT_DIR/agents/sepoys/examples/"*.md; do
        if [ -f "$sepoy_file" ]; then
            sepoy_name=$(basename "$sepoy_file")
            cp "$sepoy_file" "$TARGET_DIR/.claude/agents/sepoys/$sepoy_name"
            echo "  + sepoys/$sepoy_name"
        fi
    done
fi

# Install shared skills
echo "Installing shared skills (7)..."
for skill_dir in "$SCRIPT_DIR/skills/shared/"*/; do
    if [ -d "$skill_dir" ]; then
        skill_name=$(basename "$skill_dir")
        mkdir -p "$TARGET_DIR/.claude/skills/$skill_name"
        cp "$skill_dir/SKILL.md" "$TARGET_DIR/.claude/skills/$skill_name/"
        echo "  + $skill_name"
    fi
done

# Install role-specific skills
echo "Installing role-specific skills (6)..."
for skill_dir in "$SCRIPT_DIR/skills/role-specific/"*/; do
    if [ -d "$skill_dir" ]; then
        skill_name=$(basename "$skill_dir")
        mkdir -p "$TARGET_DIR/.claude/skills/$skill_name"
        cp "$skill_dir/SKILL.md" "$TARGET_DIR/.claude/skills/$skill_name/"
        echo "  + $skill_name"
    fi
done

# Install context (Shruti only — L0 always loaded)
echo "Installing core context (Shruti — L0)..."
mkdir -p "$TARGET_DIR/.claude/context/shruti"
mkdir -p "$TARGET_DIR/.claude/context/smriti"
mkdir -p "$TARGET_DIR/.claude/context/itihasa"
cp "$SCRIPT_DIR/context/shruti/core-principles.md" "$TARGET_DIR/.claude/context/shruti/"
cp "$SCRIPT_DIR/context/smriti/README.md" "$TARGET_DIR/.claude/context/smriti/"
cp "$SCRIPT_DIR/context/itihasa/README.md" "$TARGET_DIR/.claude/context/itihasa/"
echo "  + shruti/core-principles.md"

# Install orchestration configs
echo "Installing orchestration configs..."
mkdir -p "$TARGET_DIR/.claude/orchestration/topologies"
mkdir -p "$TARGET_DIR/.claude/orchestration/workflows"
mkdir -p "$TARGET_DIR/.claude/orchestration/guardrails"

for topo_file in "$SCRIPT_DIR/orchestration/topologies/"*.yaml; do
    if [ -f "$topo_file" ]; then
        cp "$topo_file" "$TARGET_DIR/.claude/orchestration/topologies/"
        echo "  + topologies/$(basename "$topo_file")"
    fi
done

for workflow_file in "$SCRIPT_DIR/orchestration/workflows/"*.yaml; do
    if [ -f "$workflow_file" ]; then
        cp "$workflow_file" "$TARGET_DIR/.claude/orchestration/workflows/"
        echo "  + workflows/$(basename "$workflow_file")"
    fi
done

for guardrail_file in "$SCRIPT_DIR/orchestration/guardrails/"*.md; do
    if [ -f "$guardrail_file" ]; then
        cp "$guardrail_file" "$TARGET_DIR/.claude/orchestration/guardrails/"
        echo "  + guardrails/$(basename "$guardrail_file")"
    fi
done

echo ""
echo "======================================"
echo "  Installation Complete!"
echo "======================================"
echo ""
echo "Installed:"
echo "  - 17 master agents (Mahabharata characters)"
echo "  - 3 sepoy examples + template"
echo "  - 13 skills (7 shared + 6 role-specific)"
echo "  - 5 orchestration topologies (Vyuha, Sabha, Rajya, Chakravyuha, Akshauhini)"
echo "  - 5 workflow templates"
echo "  - 3 guardrail documents"
echo "  - 3-tier context system (Shruti/Smriti/Itihasa)"
echo ""
echo "Next steps:"
echo "  1. Agents are now available in Claude Code via .claude/agents/"
echo "  2. Skills are available via .claude/skills/"
echo "  3. Reference agents by name: 'Ask Arjuna to review this architecture'"
echo "  4. Run workflows: 'Run the feature-development workflow'"
echo "  5. Add sepoys: cp .claude/agents/sepoys/_template.md .claude/agents/sepoys/my-sepoy.md"
echo ""
echo "Jai Shri Krishna! Your AI software company is ready."
