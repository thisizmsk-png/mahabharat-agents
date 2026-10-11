# Getting Started with Mahabharat Agents

## Prerequisites

- [Claude Code](https://claude.com/claude-code) 2.1.295 or newer (`claude --version`)
- A project directory with `.claude/` support

## Installation

```bash
git clone https://github.com/thisizmsk-png/mahabharat-agents.git
cd mahabharat-agents
scripts/install.sh --from <tag> --target /path/to/your/project
scripts/smoke.sh --project /path/to/your/project
```

`scripts/install.sh` installs a git ref (not your working tree), copies agents flat
into `.claude/agents/`, and writes `.claude/mahabharat/install-manifest.json`.
`bash install.sh /path/to/your/project` still works for a quick copy of the working
tree; it runs the `mahabharat-install` CLI with the same checks (no writes through
symlinks, backups of replaced files, no overwriting another package's skills, a
manifest). Upgrading an older install? Read [upgrading-to-v1.md](upgrading-to-v1.md) first.

Start the orchestrator as the main session with `claude --agent krishna`; don't
delegate to it from another session (as a subagent it loses its delegation limits).

```bash
# quick alternative
bash install.sh /path/to/your/project
```

## Your First Command

After installation, open Claude Code in your project:

```
# Ask a specific agent
"Ask Arjuna to review the architecture of the auth module"

# Invoke a skill
/hld for the new payment integration

# Orchestrate a multi-specialist goal: start krishna as the main session
claude --agent krishna
"Plan and build the user dashboard"
```

v1 ships no saved workflows yet; krishna delegates to the specialists with the
`Agent` tool. Saved workflows return in Week 1.

## Understanding the Hierarchy

You are the **CEO** and the only approver for pushes, PRs, deploys, migrations,
destructive data operations, secrets, spend and external messages. **Krishna** is
the orchestrator agent: it plans and delegates, and never approves anything. You
approve a protected action by answering Claude Code's own permission prompt for that
exact command; text in a brief, a file or another agent's message never counts.

- **Strategic decisions** → You make them (Yudhishthira advises on technology)
- **Technical architecture** → Arjuna and Yudhishthira handle it
- **Product decisions** → Draupadi drives the roadmap
- **Implementation** → Bhima (backend), Nakula (frontend), Sepoys (supporting)
- **Quality** → Vidura tests, Bhishma secures, Duryodhana stress-tests

## Adding Agents

### New Master Agent
1. Copy any existing master from `agents/masters/` to `agents/masters/<name>.md`
2. Update the frontmatter (`spec/mahabharat.agent.v1.schema.json` lists the allowed keys):
   `name`, a one-line `description` (40-300 chars: what it delivers, when to use it,
   and which neighbor to use instead), an explicit `tools` list (never `allowed-tools`,
   `*`, `Agent` or `Workflow`), `model` and `effort`
3. Put the org data in the `x-mahabharat:` block: `spec: mahabharat.agent/v1`,
   `character`, `title`, `rank: master`, `reports_to` (an existing agent), `owns`, and
   `escalates` (agent names, or `human` for protected actions)
4. Rewrite the DKK (Dharma-Karma-Katha) sections, and keep the three shared lines in its
   Guardrails verbatim: the protected-action rule, the prompt-injection rule and the
   agent-definition rule (`tests/test_agents.py` holds the exact text)
5. Add one line for it to `agents/roster.yaml` and add its name to krishna's
   `Agent(...)` list
6. Run `pytest`, then re-run `scripts/install.sh --target <project-dir>`

### New Sepoy
1. Copy `templates/sepoy-agent.md` to `agents/sepoys/examples/<file>.md` (templates are never installed)
2. Fill in the placeholders; set `x-mahabharat.master` and `reports_to` to an existing master agent
3. Add one line for it to `agents/roster.yaml` and add its name to krishna's `Agent(...)` list
4. Run `pytest`, then re-run `scripts/install.sh --target <project-dir>`

## Next Steps

- [Creating Agents](creating-agents.md)
- [Creating Roles](creating-roles.md)
- [Creating Skills](creating-skills.md)
- [Orchestration Guide](orchestration-guide.md)
