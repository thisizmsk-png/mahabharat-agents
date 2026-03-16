# Getting Started with Mahabharat Agents

## Prerequisites

- [Claude Code](https://claude.com/claude-code) installed and configured
- A project directory with `.claude/` support

## Installation

```bash
git clone https://github.com/saikrishnamadavarapu/mahabharat-agents.git
cd mahabharat-agents
bash install.sh /path/to/your/project
```

## Your First Command

After installation, open Claude Code in your project:

```
# Ask a specific agent
"Ask Arjuna to review the architecture of the auth module"

# Invoke a skill
/hld for the new payment integration

# Run a workflow
"Run the feature-development workflow for the user dashboard"
```

## Understanding the Hierarchy

You are **Krishna** — the CEO/God. You direct the agents:

- **Strategic decisions** → You make them (or Yudhishthira advises)
- **Technical architecture** → Arjuna and Yudhishthira handle it
- **Product decisions** → Draupadi drives the roadmap
- **Implementation** → Bhima (backend), Nakula (frontend), Sepoys (supporting)
- **Quality** → Vidura tests, Bhishma secures, Duryodhana stress-tests

## Adding Agents

### New Master Agent
1. Copy any existing master from `agents/masters/`
2. Modify the DKK (Dharma-Karma-Katha) sections
3. Update frontmatter (name, role, reports_to)
4. Re-run `install.sh`

### New Sepoy
1. Copy `agents/sepoys/_template.md`
2. Set the `master` field to an existing master agent
3. Add any specialization in the Delta section
4. Re-run `install.sh`

## Next Steps

- [Creating Agents](creating-agents.md)
- [Creating Roles](creating-roles.md)
- [Creating Skills](creating-skills.md)
- [Orchestration Guide](orchestration-guide.md)
