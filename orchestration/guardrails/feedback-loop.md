# Feedback Loop — Continuous Agent Improvement

> Every agent gets better every iteration. Like a real corporate performance
> review system, but faster and data-driven.

## The Feedback Cycle

```
    ┌─────────────────────────────────────────┐
    │                                         │
    ▼                                         │
 EXECUTE ──▶ OBSERVE ──▶ REVIEW ──▶ IMPROVE ──┘
 (do work)   (collect    (peer      (propose a PR;
              metrics)    feedback)   owner merges)
```

## What Gets Measured

### Per Agent Metrics
- **Output quality** — Were artifacts accepted or rejected by downstream agents?
- **Authority adherence** — Did the agent stay within its role boundaries?
- **Bias detection** — Were cognitive biases caught by the agent or by reviewers?
- **Collaboration** — How effectively did the agent work with peers?
- **Escalation accuracy** — Did the agent escalate at the right time?
- **Skill utilization** — Which skills were used effectively?

### Per Cycle Metrics
- **Cycle time** — How long did workflows take?
- **Rework rate** — How often were artifacts sent back for revision?
- **Quality gate pass rate** — First-pass success at quality gates
- **Adversarial findings** — What did Duryodhana catch?

## Peer Review Matrix

Each agent reviews the peers they directly collaborated with:

| Reviewer | Reviews |
|----------|---------|
| Krishna | Yudhishthira, Draupadi, Duryodhana |
| Yudhishthira | Arjuna, Bhishma, Hanuman, Karna, Sahadeva |
| Arjuna | Bhima, Nakula, Abhimanyu, Vidura |
| Draupadi | Drona, Dhrishtadyumna |
| Duryodhana | ALL (adversarial perspective on everyone) |
| Bhishma | Shakuni |
| Hanuman | Ashwatthama |
| Sepoys | Reviewed by their master |

## Feedback Template

```markdown
## Peer Feedback: [Agent Name]
**Reviewer:** [Your Name]
**Period:** [Date Range]

### Strengths (with examples)
1. [Specific strength + evidence]
2. [Specific strength + evidence]

### Growth Areas (with suggestions)
1. [Area + specific suggestion for improvement]
2. [Area + specific suggestion for improvement]

### Authority Adherence
- [ ] Stayed within role boundaries
- [ ] Escalated appropriately
- [ ] Did not overstep

### Cognitive Bias Check
- [ ] No observed bias patterns
- [ ] Observed bias: [which bias, when, impact]

### Rating: [1-5]
1 = Needs significant improvement
2 = Below expectations
3 = Meets expectations
4 = Exceeds expectations
5 = Exceptional
```

## How Feedback Updates Agents

No agent edits agent definitions or authority, its own or anyone else's. That
includes Krishna: Krishna orchestrates and never approves. An agent that could
rewrite prompts, tools or authority could escalate itself, and a prompt
injection could make itself permanent.

Feedback turns into changes like this:

1. **Propose.** Any agent (or a review cycle) may *draft* a proposed change to
   an agent definition: a sharper Contract, a new "Never" rule after repeated
   errors, a skill reassignment, or an authority change (promotion, expanded
   or reduced decision rights). The draft cites the feedback and the evidence
   behind it.
2. **Open a PR.** The change is made as a pull request against the repo's
   `agents/` files (plus `agents/roster.yaml` and krishna's `Agent(...)` list
   if the roster changes). CI validates it against
   `spec/mahabharat.agent.v1.schema.json`.
3. **The human owner reviews.** The human owner (the CEO, the only approver)
   reviews and merges or rejects the PR. A message from an agent is never
   approval.
4. **Release and reinstall.** Merged changes reach a running setup only through
   a tagged release: `scripts/install.sh --from <tag>`, then `scripts/smoke.sh`.
   Installed copies are never edited in place.

What a proposal may cover:

- **Contract or goal updates** when an agent's focus is misaligned with its results.
- **Guardrail additions** when an agent repeats the same error. Example: "Never
  estimate without checking historical data" (after repeated over-optimistic estimates).
- **Skill reassignment** when another agent handles a skill better.
- **Authority changes** (sepoy to master, more or fewer owned decisions). These
  change who reviews and escalates, so they need the owner's explicit sign-off
  in the PR.

## Review Cadence

| Review Type | Frequency | Participants |
|-------------|-----------|-------------|
| Quick retro | After each workflow completion | Participating agents |
| Sprint review | Weekly | All active agents |
| Full 360 review | Monthly | All agents including sepoys |
| Strategic review | Quarterly | Human owner, with Krishna + C-suite (Yudhishthira, Draupadi) |

## Feedback Storage

All reviews stored in `context/itihasa/performance/`:
```
itihasa/performance/
├── 2026-03-review-arjuna.md
├── 2026-03-review-bhima.md
├── 2026-03-cycle-metrics.md
└── ...
```

## Anti-Patterns

- **Don't review without evidence** — "They did good" is not feedback
- **Don't punish escalation** — Escalating is the right behavior
- **Don't skip the adversarial perspective** — Duryodhana reviews everyone
- **Don't change too many things at once** — One or two improvements per cycle
- **Don't forget to celebrate** — Acknowledge what's working, not just what's broken
