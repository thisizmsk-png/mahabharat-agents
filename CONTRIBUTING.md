# Contributing to Mahabharat Agents

Thank you for your interest in contributing to **mahabharat-agents**. This guide covers the conventions and workflow for adding agents, skills, workflows, and other improvements.

---

## Getting Started

### Fork and Clone

```bash
git clone https://github.com/<your-username>/mahabharat-agents.git
cd mahabharat-agents
```

### Development Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

This installs the package in editable mode along with development dependencies (linters, formatters, test runners).

### Verify the Installation

```bash
mahabharat --help
```

---

## How to Add a New Agent

1. Copy the template:

```bash
cp agents/sepoys/_template.md agents/sepoys/<agent-name>.md
```

2. Fill in the **DKK format** (Dharma-Karma-Katha):

| Section | Purpose |
|---------|---------|
| **Dharma** | The agent's role, identity, and guiding principles. What it stands for and the boundaries it respects. |
| **Karma** | The concrete actions, tools, and procedures the agent performs. Input/output contracts and step-by-step workflows. |
| **Katha** | Narrative examples, few-shot demonstrations, and edge-case handling stories that teach the agent by example. |

3. Register the agent in the appropriate tier directory (`agents/masters/` for master agents, `agents/sepoys/` for task-level agents).

4. Add a brief entry in the agent index if one exists.

---

## How to Add a Skill

Skills are composable capabilities that agents can invoke.

1. Create a new directory under `skills/`:

```bash
mkdir -p skills/<skill-name>
```

2. Create a `SKILL.md` file inside it:

```bash
touch skills/<skill-name>/SKILL.md
```

3. Structure the SKILL.md with:
   - **Description** -- what the skill does and when to use it.
   - **Inputs** -- parameters the skill expects.
   - **Outputs** -- what the skill produces.
   - **Procedure** -- step-by-step instructions for execution.
   - **Examples** -- concrete usage examples.

4. If the skill is role-specific, note which agents depend on it. If it is shared, ensure it remains agent-agnostic.

---

## How to Add a Workflow

Workflows are YAML definitions in `orchestration/workflows/`.

1. Create a new YAML file:

```bash
touch orchestration/workflows/<workflow-name>.yaml
```

2. Define the workflow with:
   - `name` -- human-readable workflow name.
   - `topology` -- which orchestration topology to use (Vyuha, Sabha, Rajya, Chakravyuha, or Akshauhini).
   - `agents` -- list of agents involved and their roles.
   - `steps` -- ordered sequence of actions and handoffs.
   - `guardrails` -- references to applicable guardrail documents.

3. Validate the YAML before committing:

```bash
python -m yamllint orchestration/workflows/<workflow-name>.yaml
```

---

## Pull Request Expectations

### Before Submitting

- Run the linter and formatter:

```bash
python -m markdownlint '**/*.md'
python -m yamllint orchestration/ config/
```

- Ensure all existing tests pass.
- Write a clear PR description explaining what you added or changed and why.

### Code Style

- **Markdown**: Follow standard markdown linting rules. Use ATX-style headers (`#`), fenced code blocks with language tags, and consistent list markers.
- **YAML**: 2-space indentation, no trailing whitespace, quoted strings where ambiguity exists.
- **Python**: Follow PEP 8. Use type hints for function signatures.
- **Agent files (DKK)**: All three sections (Dharma, Karma, Katha) are required. Do not leave any section empty.

### Commit Messages

Use conventional commit style:

```
feat: add code-review agent with DKK format
fix: correct topology reference in incident-response workflow
docs: update skill index with new shared skills
```

### Review Process

- All PRs require at least one approving review.
- Maintainers may request changes to ensure consistency with the DKK format and project conventions.
- Large additions (new topologies, new tiers) should be discussed in an issue first.

---

## Reporting Issues

Open a GitHub issue with:

- A clear title describing the problem or request.
- Steps to reproduce (for bugs).
- Expected vs. actual behavior.
- Environment details (Python version, OS).

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
