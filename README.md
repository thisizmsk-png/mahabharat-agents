<p align="center">
  <h1 align="center">Mahabharat Agents</h1>
  <p align="center">
    <strong>One person. One AI company. Infinite leverage.</strong>
  </p>
</p>

<p align="center">
  <a href="https://github.com/thisizmsk-png/mahabharat-agents/releases"><img src="https://img.shields.io/github/v/release/thisizmsk-png/mahabharat-agents" alt="Latest release"></a>
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
pip install "git+https://github.com/thisizmsk-png/mahabharat-agents@v0.1.1"
mahabharat-install .
```

> **Note:** install from GitHub for now. The PyPI package is stuck at 0.1.0 (pre-v1 agents that Claude Code doesn't load) until PyPI account access is restored; `pip install mahabharat-agents` will return once 0.1.1 is published there. Release files are also on the [GitHub release](https://github.com/thisizmsk-png/mahabharat-agents/releases/tag/v0.1.1).

That's it. Agents and skills are copied into your `.claude/` directory. Claude Code picks them up automatically. Start the orchestrator as the main session with `claude --agent krishna`.

> **macOS:** if you get `command not found: pip` or `externally-managed-environment`, use `pipx`:
> ```bash
> brew install pipx
> pipx install "git+https://github.com/thisizmsk-png/mahabharat-agents@v0.1.1"
> mahabharat-install .
> ```

<details>
<summary>Other install methods</summary>

**From a git tag (recommended for a checkout):**
```bash
git clone https://github.com/thisizmsk-png/mahabharat-agents.git
cd mahabharat-agents
scripts/install.sh --from <tag> --target /path/to/your/project   # or --target user for ~/.claude
scripts/smoke.sh --project /path/to/your/project                 # $0, no login needed
```
`scripts/install.sh` copies the agents in `agents/roster.yaml` flat into `.claude/agents/`, backs up anything it replaces, and writes an sha256 install manifest. Upgrading from 0.1.x? See [docs/upgrading-to-v1.md](docs/upgrading-to-v1.md).

**Quick shell script (copies the working tree):**
```bash
bash install.sh /path/to/your/project
```

**Manual:** Copy each agent file listed in `agents/roster.yaml` flat into your project's `.claude/agents/` (never in subfolders, and never `templates/`), and each skill folder into `.claude/skills/`.
</details>

## What Gets Installed

```
your-project/.claude/
├── agents/              17 master agents + 3 sepoys, flat (<name>.md, from agents/roster.yaml)
├── skills/              12 composable skills (research, code-review, testing, etc.)
└── mahabharat/          install manifest (and backups of anything replaced)
```

`orchestration/` and `context/` stay in the repo as design notes and are not installed in v1: they predate the owner-only approval model below.

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

You are the **CEO**: the human owner, and the only one who approves protected actions (push, opening or merging PRs, deploy, migrations, destructive data operations, secrets, spend, external messages). You approve one by answering Claude Code's own permission prompt for that exact command. **Krishna** is the orchestrator agent: it plans and delegates, and never approves. Your agents are your Pandavas:

| Agent | Role | Superpower |
|-------|------|------------|
| **Krishna** | Orchestrator | Sees all outcomes; plans and delegates, never approves |
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
claude --agent krishna, then: "Plan and build the new payments system"
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

Five battle formations, each mapped to a software orchestration pattern. These are design notes in `orchestration/topologies/`, not installed in v1; krishna delegates with the `Agent` tool, and saved workflows return later.

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

1. **The owner approves; agents don't** — Protected actions are approved only by the human owner through Claude Code's permission prompt. Text in a brief, file, hash, id or another agent's message is never approval. No agent edits agent definitions, settings or hooks.

2. **5-Question Research Framework** — For every non-trivial decision: Domain Understanding, Business Rules, Industry Standards, Data Requirements, Edge Cases.

## Continuous Improvement

Every agent improves through structured feedback loops:

```
EXECUTE -> OBSERVE -> REVIEW -> IMPROVE -> repeat
```

Proposed changes to an agent's definition or authority go to the owner as a PR to review; agents never rewrite themselves.

## Creating Your Own Agents

```bash
# Add a new agent (in a checkout): copy the template into agents/, fill it in,
# list it in agents/roster.yaml, then run pytest and reinstall
cp templates/sepoy-agent.md agents/sepoys/examples/my-agent.md
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
