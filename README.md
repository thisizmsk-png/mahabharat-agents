# Mahabharat Agents Package

> One person. One AI company. Infinite leverage.

The Mahabharat Agents Package turns a solo developer into a full software company
by deploying specialized AI agents — each named after a Mahabharata character,
each embodying FAANG-level role expertise, each following strict cognitive
bias prevention protocols.

## The Idea

You are Krishna — the CEO, the God, the orchestrator. You don't fight every battle.
You direct the war. Your agents are your Pandavas, each a master of their domain:

| Agent | Character | Role | Superpower |
|-------|-----------|------|------------|
| Krishna | The Strategist | CEO / God | Sees all outcomes; empowers without doing |
| Yudhishthira | The Principled | CTO | Long-term architecture; answers the unanswerable |
| Arjuna | The Focused | Principal SDE | Fish-eye precision; cross-realm mastery |
| Bhima | The Powerful | Senior Backend SDE | Raw throughput; highest ship count |
| Nakula | The Beautiful | Senior Frontend | Aesthetic excellence; pixel-perfect craft |
| Sahadeva | The Seer | Data Scientist | Predictive insight; pattern recognition |
| Draupadi | The Fierce | Product Manager | Manages 5 teams; drives the roadmap |
| Karna | The Self-Made | Quant Engineer | Mathematical genius from first principles |
| Drona | The Teacher | Product Owner | Sets acceptance criteria; evaluates completion |
| Bhishma | The Guardian | Security Engineer | Knows all attacks/defenses; eternal watchman |
| Vidura | The Wise | QA Engineer | Sees every flaw; warns before crisis |
| Hanuman | The Infinite | DevOps / SRE | Bridges systems; immortal uptime |
| Duryodhana | The Challenger | Red Team Lead | Stress-tests everything; the necessary antagonist |
| Shakuni | The Cunning | Offensive Security | Game theory; social engineering; exploit crafting |
| Abhimanyu | The Brave | Junior Engineer | Learns fast; growth track with mentorship |
| Ashwatthama | The Relentless | Incident Response | Never stops; carries scars of every incident |
| Dhrishtadyumna | The Executor | Program Manager | Born to ship; coordinates all forces |

## Architecture

```
Dharma-Karma-Katha (DKK) Agent Definitions
    + FAANG-Level Role Definitions
    + Composable Skills (Claude Code SKILL.md format)
    + Multi-Topology Orchestration (Vyuha, Sabha, Rajya, Chakravyuha, Akshauhini)
    + Artifact-Based Pub-Sub Communication
    + Tiered Context (Shruti/Smriti/Itihasa)
    + Master/Sepoy Hierarchy
    + Kurukshetra War Room Dashboard
```

### Orchestration Topologies

| Topology | Sanskrit | Pattern | Use Case |
|----------|----------|---------|----------|
| Sequential | Vyuha | Pipeline | Feature development flow |
| Debate | Sabha | MixtureOfAgents | Consensus decisions |
| Governance | Rajya | Hierarchical | Approval chains |
| Complex | Chakravyuha | Graph DAG | Multi-dependency workflows |
| Parallel | Akshauhini | Fork-Join | Independent parallel tasks |

### Core Principles (ALL agents, non-negotiable)

1. **Zero Cognitive Bias Protocol** — No anchoring, confirmation, availability,
   survivorship, authority, or sunk cost bias. Question assumptions. Seek
   disconfirming evidence.

2. **5-Question Research Framework** — For every non-trivial decision:
   Domain Understanding, Business Rules, Industry Standards, Data Requirements,
   Edge Cases.

## Installation

### Option 1: pip install (recommended)
```bash
pip install mahabharat-agents
mahabharat-install /path/to/your/project
```

### Option 2: Shell script
```bash
git clone https://github.com/saikrishnamadavarapu/mahabharat-agents.git
cd mahabharat-agents
bash install.sh /path/to/your/project
```

### Option 3: Manual
Copy `agents/`, `skills/`, `orchestration/`, and `context/` directories
into your project's `.claude/` folder.

## Quick Start

1. Install into your project
2. Agents appear in `.claude/agents/`
3. Skills appear in `.claude/skills/`
4. Invoke any agent by name in Claude Code: "Ask Arjuna to review this architecture"
5. Run workflows: "Run the feature-development workflow for the new auth system"

## Continuous Improvement — Feedback Loop

Every agent gets better over time through structured peer reviews:

```
EXECUTE → OBSERVE → REVIEW → IMPROVE → repeat
```

- **Self-assessment:** Each agent evaluates their own performance
- **Peer feedback:** Agents review collaborators with specific, evidence-based feedback
- **360 synthesis:** Krishna (CEO) consolidates feedback into improvement plans
- **Agent updates:** Agent definitions updated based on review (new guardrails, skill changes, authority adjustments)
- **Promotion/demotion:** High-performing sepoys can be promoted; underperforming agents get coaching

Run `performance-review` workflow weekly or after milestones:
```
"Run the performance-review workflow for this sprint"
```

## Creating Your Own Company

```bash
# Add a new role
cp roles/_template.md roles/my-role.md

# Add a new agent
cp agents/masters/_template.md agents/masters/my-agent.md

# Add sepoys (supporting agents)
cp agents/sepoys/_template.md agents/sepoys/my-sepoy.md

# Add a workflow
cp orchestration/workflows/_template.yaml orchestration/workflows/my-workflow.yaml
```

## License

MIT License. See [LICENSE](LICENSE).

## Credits

This project is built on ideas from MetaGPT, CrewAI, ChatDev, Swarms, MiroFish,
OpenViking, AutoGen, CAMEL, and OpenHands. Full attribution in [CREDITS.md](CREDITS.md).

---

*"Yada yada hi dharmasya glanir bhavati bharata..."*
*Whenever dharma declines, Krishna appears to restore order.*

Built by [Sai Krishna Madavarapu](https://github.com/saikrishnamadavarapu) with Claude Code.
