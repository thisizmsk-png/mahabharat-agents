# Mahabharat Agents

[![PyPI version](https://img.shields.io/pypi/v/mahabharat-agents.svg)](https://pypi.org/project/mahabharat-agents/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> One person. One AI company. Infinite leverage.

Deploy 17 FAANG-level AI agents into any project with a single command. Each agent is named after a Mahabharata character and embodies a specialized engineering role — from CTO to Security Engineer to Incident Response.

## Install

```bash
pip install mahabharat-agents
mahabharat-install .
```

That's it. This copies all agents, skills, orchestration configs, and context tiers into your project's `.claude/` directory. Claude Code picks them up automatically.

> **macOS Homebrew users:** If you get `externally-managed-environment`, use `pipx`:
> ```bash
> brew install pipx
> pipx install mahabharat-agents
> mahabharat-install .
> ```

### Other install methods

<details>
<summary>Shell script</summary>

```bash
git clone https://github.com/thisizmsk-png/mahabharat-agents.git
cd mahabharat-agents
bash install.sh /path/to/your/project
```
</details>

<details>
<summary>Manual</summary>

Copy `agents/`, `skills/`, `orchestration/`, and `context/` directories into your project's `.claude/` folder.
</details>

## What gets installed

```
your-project/.claude/
├── agents/              17 master agents + sepoy templates
├── skills/              13 composable skills (research, code-review, testing, etc.)
├── orchestration/       5 topologies + 6 workflows + 4 guardrails
└── context/             3-tier context system (Shruti/Smriti/Itihasa)
```

## The Agents

You are **Krishna** — the CEO, the orchestrator. Your agents are your Pandavas:

| Agent | Role | Superpower |
|-------|------|------------|
| **Krishna** | CEO / Strategist | Sees all outcomes; empowers without doing |
| **Yudhishthira** | CTO | Long-term architecture; answers the unanswerable |
| **Arjuna** | Principal SDE | Fish-eye precision; cross-realm mastery |
| **Bhima** | Senior Backend SDE | Raw throughput; highest ship count |
| **Nakula** | Senior Frontend | Aesthetic excellence; pixel-perfect craft |
| **Sahadeva** | Data Scientist | Predictive insight; pattern recognition |
| **Draupadi** | Product Manager | Manages 5 teams; drives the roadmap |
| **Karna** | Quant Engineer | Mathematical genius from first principles |
| **Drona** | Product Owner | Sets acceptance criteria; evaluates completion |
| **Bhishma** | Security Engineer | Knows all attacks/defenses; eternal watchman |
| **Vidura** | QA Engineer | Sees every flaw; warns before crisis |
| **Hanuman** | DevOps / SRE | Bridges systems; immortal uptime |
| **Duryodhana** | Red Team Lead | Stress-tests everything; the necessary antagonist |
| **Shakuni** | Offensive Security | Game theory; social engineering; exploit crafting |
| **Abhimanyu** | Junior Engineer | Learns fast; growth track with mentorship |
| **Ashwatthama** | Incident Response | Never stops; carries scars of every incident |
| **Dhrishtadyumna** | Program Manager | Born to ship; coordinates all forces |

## Usage

Invoke agents by name in Claude Code:

```
"Ask Arjuna to review this architecture"
"Have Bhishma do a security audit of the auth module"
"Run the feature-development workflow for the new payments system"
"Ask Vidura to write tests for the API layer"
```

### Selective install

```bash
mahabharat-install . --agents-only    # only agent definitions
mahabharat-install . --skills-only    # only skills
```

## Orchestration Topologies

| Topology | Sanskrit | Pattern | Use Case |
|----------|----------|---------|----------|
| Sequential | **Vyuha** | Pipeline | Feature development flow |
| Debate | **Sabha** | Mixture of Agents | Consensus decisions |
| Governance | **Rajya** | Hierarchical | Approval chains |
| Complex | **Chakravyuha** | Graph DAG | Multi-dependency workflows |
| Parallel | **Akshauhini** | Fork-Join | Independent parallel tasks |

## Core Principles (non-negotiable for all agents)

1. **Zero Cognitive Bias Protocol** — No anchoring, confirmation, availability, survivorship, authority, or sunk cost bias. Question assumptions. Seek disconfirming evidence.

2. **5-Question Research Framework** — For every non-trivial decision: Domain Understanding, Business Rules, Industry Standards, Data Requirements, Edge Cases.

## Continuous Improvement

Every agent improves through structured feedback loops:

```
EXECUTE → OBSERVE → REVIEW → IMPROVE → repeat
```

Run performance reviews weekly or after milestones:
```
"Run the performance-review workflow for this sprint"
```

## Creating Your Own Agents

```bash
# Add a new agent
cp .claude/agents/sepoys/_template.md .claude/agents/my-agent.md

# Add a workflow
cp .claude/orchestration/workflows/feature-development.yaml .claude/orchestration/workflows/my-workflow.yaml
```

## License

MIT License. See [LICENSE](LICENSE).

## Credits

Built on ideas from MetaGPT, CrewAI, ChatDev, Swarms, AutoGen, CAMEL, and OpenHands. Full attribution in [CREDITS.md](CREDITS.md).

---

*"Yada yada hi dharmasya glanir bhavati bharata..."*
*Whenever dharma declines, Krishna appears to restore order.*

Built by [Sai Krishna Madavarapu](https://github.com/thisizmsk-png) with Claude Code.
