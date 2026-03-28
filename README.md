<p align="center">
  <h1 align="center">Mahabharat Agents</h1>
  <p align="center">
    <strong>One person. One AI company. Infinite leverage.</strong>
  </p>
</p>

<p align="center">
  <a href="https://pypi.org/project/mahabharat-agents/"><img src="https://img.shields.io/pypi/v/mahabharat-agents.svg" alt="PyPI version"></a>
  <a href="https://github.com/thisizmsk-png/mahabharat-agents/actions"><img src="https://github.com/thisizmsk-png/mahabharat-agents/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://github.com/thisizmsk-png/mahabharat-agents/stargazers"><img src="https://img.shields.io/github/stars/thisizmsk-png/mahabharat-agents?style=social" alt="GitHub Stars"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10%2B-blue.svg" alt="Python 3.10+"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
</p>

<p align="center">
  <a href="#install">Install</a> &bull;
  <a href="#the-agents">Agents</a> &bull;
  <a href="#how-it-compares">Compare</a> &bull;
  <a href="#usage">Usage</a> &bull;
  <a href="CONTRIBUTING.md">Contributing</a> &bull;
  <a href="CHANGELOG.md">Changelog</a> &bull;
  <a href="#roadmap">Roadmap</a>
</p>

---

Deploy **17 FAANG-level AI agents** into any project with a single command. Each agent is named after a Mahabharata character and embodies a specialized engineering role. They work inside **Claude Code natively** — no API keys, no runtime dependencies, no Python framework code. Just markdown files that Claude picks up from your `.claude/` directory.

## Install

```bash
pip install mahabharat-agents
mahabharat-install .
```

That's it. Agents, skills, orchestration configs, and context tiers are copied into your `.claude/` directory. Claude Code picks them up automatically.

> **macOS Homebrew users:** If you get `externally-managed-environment`, use `pipx`:
> ```bash
> brew install pipx
> pipx install mahabharat-agents
> mahabharat-install .
> ```

<details>
<summary>Other install methods</summary>

**Shell script:**
```bash
git clone https://github.com/thisizmsk-png/mahabharat-agents.git
cd mahabharat-agents
bash install.sh /path/to/your/project
```

**Manual:** Copy `agents/`, `skills/`, `orchestration/`, and `context/` into your project's `.claude/` folder.
</details>

## What Gets Installed

```
your-project/.claude/
├── agents/              17 master agents + sepoy templates
├── skills/              13 composable skills (research, code-review, testing, etc.)
├── orchestration/       5 topologies + 6 workflows + 4 guardrails
└── context/             3-tier context system (Shruti/Smriti/Itihasa)
```

## How It Compares

| Feature | Mahabharat Agents | MetaGPT | CrewAI | AutoGen | ChatDev |
|---------|:-:|:-:|:-:|:-:|:-:|
| **Zero code required** | Yes | No | No | No | No |
| **Zero API keys needed** | Yes | No | No | No | No |
| **Claude Code native** | Yes | No | No | No | No |
| **Agent personality system** | DKK format | SOP roles | Role/Goal/Backstory | Conversable | Phase roles |
| **Built-in adversarial review** | Yes (Duryodhana) | No | No | No | No |
| **Cognitive bias prevention** | Yes (all agents) | No | No | No | No |
| **Orchestration topologies** | 5 (Sanskrit-named) | 1 (SOP) | 1 (Sequential) | 2 | 1 (Phase) |
| **pip install and done** | Yes | Partial | Partial | Partial | No |

**The difference:** MetaGPT, CrewAI, and AutoGen require you to write Python and make API calls. Mahabharat Agents requires zero code — agents are markdown files that Claude Code loads from the `.claude/` directory.

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
"Ask Arjuna to review this pull request"
"Have Bhishma do a security audit of the auth module"
"Run the feature-development workflow for the new payments system"
"Ask Vidura to write tests for the user service"
"Tell Duryodhana to red-team the API design"
"Have Yudhishthira design the system architecture for search"
```

### Selective install

```bash
mahabharat-install . --agents-only    # only agent definitions
mahabharat-install . --skills-only    # only skills
```

## Orchestration Topologies

Five battle formations, each mapped to a software orchestration pattern:

| Topology | Sanskrit | Pattern | Use Case |
|----------|----------|---------|----------|
| Sequential | **Vyuha** | Pipeline | Feature development flow |
| Debate | **Sabha** | Mixture of Agents | Consensus decisions |
| Governance | **Rajya** | Hierarchical | Approval chains |
| Complex | **Chakravyuha** | Graph DAG | Multi-dependency workflows |
| Parallel | **Akshauhini** | Fork-Join | Independent parallel tasks |

## Why Narrative Priming Works

Each agent has a **Katha** (backstory) drawn from the Mahabharata. This is not cosmetic naming. Giving an LLM a mythological character with specific traits produces measurably different reasoning than a generic role description.

Telling Claude *"you are Bhishma who swore an absolute vow to protect"* activates different reasoning patterns than *"you are a security engineer."* The vow framing makes the agent more thorough, more reluctant to approve shortcuts, and more likely to flag edge cases.

## Core Principles

Non-negotiable for all 17 agents:

1. **Zero Cognitive Bias Protocol** — No anchoring, confirmation, availability, survivorship, authority, or sunk cost bias. Question assumptions. Seek disconfirming evidence.

2. **5-Question Research Framework** — For every non-trivial decision: Domain Understanding, Business Rules, Industry Standards, Data Requirements, Edge Cases.

## Continuous Improvement

Every agent improves through structured feedback loops:

```
EXECUTE -> OBSERVE -> REVIEW -> IMPROVE -> repeat
```

```
"Run the performance-review workflow for this sprint"
```

## Creating Your Own Agents

```bash
# Add a new agent
cp .claude/agents/sepoys/_template.md .claude/agents/my-agent.md

# Add a workflow
cp .claude/orchestration/workflows/feature-development.yaml \
   .claude/orchestration/workflows/my-workflow.yaml
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide.

## Roadmap

- [ ] Kurukshetra Dashboard — real-time agent activity visualization
- [ ] Agent memory persistence across sessions
- [ ] Custom agent builder CLI (`mahabharat create-agent`)
- [ ] VS Code extension for agent status panel
- [ ] Prompt-to-workflow generator
- [ ] Community agent marketplace
- [ ] Benchmark suite for agent quality evaluation
- [ ] Support for additional LLM backends beyond Claude

## Star History

<a href="https://star-history.com/#thisizmsk-png/mahabharat-agents&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=thisizmsk-png/mahabharat-agents&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=thisizmsk-png/mahabharat-agents&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=thisizmsk-png/mahabharat-agents&type=Date" />
 </picture>
</a>

## License

MIT License. See [LICENSE](LICENSE).

## Credits

Built on ideas from MetaGPT, CrewAI, ChatDev, Swarms, AutoGen, CAMEL, and OpenHands. Full attribution in [CREDITS.md](CREDITS.md).

---

*"Yada yada hi dharmasya glanir bhavati bharata..."*
*Whenever dharma declines, Krishna appears to restore order.*

Built by [Sai Krishna Madavarapu](https://github.com/thisizmsk-png) with Claude Code.
