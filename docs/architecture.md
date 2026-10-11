# Architecture — Mahabharat Agents Package

## Core Concepts

### 1. Roles
FAANG-level job definitions stored in `roles/*.md`. Each role defines:
- Responsibilities, traits, leadership principles
- Authority matrix (owns vs escalates)
- Interaction patterns with other roles

Roles are generic — they work for any software project.

Roles are background reading only. They are not installed, and agents don't link to
them. Their authority lines (for example "Ultimate authority" in `roles/ceo.md`, or
go/no-go in the PM and QA roles) predate v1. In v1 the human owner is the CEO and the
only approver of protected actions (push, PR, deploy, migrations, destructive data
operations, secrets, spend, external messages). Krishna orchestrates and never
approves. Where a role file disagrees, the agent file wins.

### 2. Agents (DKK Format)
Mahabharata-named entities stored in `agents/masters/*.md`. Each agent has:
- **Dharma** (Role & Duty) — What they do, from their role definition
- **Karma** (Goal & Mission) — What they aim to achieve
- **Katha** (Backstory & Persona) — Character traits that influence decisions
- **Traits** — Leadership principles as behavioral constraints
- **Skills** — Composable capabilities they can invoke
- **Authority** — What they own vs. escalate
- **Guardrails** — Behavioral constraints

### 3. Skills (SKILL.md Format)
Claude Code skills stored in `skills/`. Two types:
- **Shared** — Available to multiple roles (HLD, LLD, code-review, testing, research, spec; the old zero-bias skill is retired and not installed)
- **Role-specific** — Tied to specific roles (product-spec, threat-modeling, incident-response, etc.)

### 4. Orchestration Topologies
Five coordination patterns stored in `orchestration/topologies/`:

| Topology | Sanskrit | Pattern |
|----------|----------|---------|
| Sequential | **Vyuha** | Pipeline: A → B → C |
| Debate | **Sabha** | Parallel evaluation → consensus |
| Hierarchical | **Rajya** | Approval chain: bottom-up |
| Graph DAG | **Chakravyuha** | Complex dependencies |
| Fork-Join | **Akshauhini** | Parallel tasks → merge |

Like roles, `orchestration/` (topologies, workflows, guardrails) and `context/` are
design notes in the repo. v1 does not install them: they predate the owner-only
approval model (some name krishna as `approver` or `ceo_override`, or allow
auto-approval and rollback without approval). Where they disagree with an agent file,
the agent file wins. They return, rewritten, with saved workflows.

### 5. Master/Sepoy Hierarchy
- **Masters** — Named Mahabharata characters with full role authority
- **Sepoys** — Supporting agents that inherit master's role but with reduced authority

### 6. Context Tiers (Shruti/Smriti/Itihasa)
Three-tier context management inspired by OpenViking:
- **L0 (Shruti)** — Always loaded: core principles, hierarchy, protocols
- **L1 (Smriti)** — Per session: current tasks, recent decisions, active context
- **L2 (Itihasa)** — On demand: historical records, past decisions, archived research

## Data Flow

```
The human owner (CEO) sets direction and approves protected actions
    ↓
Krishna plans and delegates
    ↓
Orchestration Engine selects topology
    ↓
Agents execute within their authority
    ↓
Artifacts flow through pub-sub bus
    ↓
Validation gates check quality
    ↓
Decision audit log captures everything
```

## Design Principles

1. **Artifact-based communication** — Prevents hallucination cascading (MetaGPT)
2. **Role-Goal-Backstory trinity** — Expressive agent definition (CrewAI → DKK)
3. **Multi-topology orchestration** — Right pattern for right task (Swarms)
4. **Tiered context** — Efficient memory management (OpenViking)
5. **Owner-only approval** — Protected actions are approved only by the human owner, through Claude Code's permission prompt
6. **Authority boundaries** — Agents can't exceed their role
7. **Adversarial review** — Duryodhana challenges everything before shipping
