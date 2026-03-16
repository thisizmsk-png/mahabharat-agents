# Feedback Loop — Continuous Agent Improvement

> Every agent gets better every iteration. Like a real corporate performance
> review system, but faster and data-driven.

## The Feedback Cycle

```
    ┌─────────────────────────────────────────┐
    │                                         │
    ▼                                         │
 EXECUTE ──▶ OBSERVE ──▶ REVIEW ──▶ IMPROVE ──┘
 (do work)   (collect    (peer      (update
              metrics)    feedback)   agent def)
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

After each review cycle, Krishna (CEO) updates agent definitions:

### 1. Karma Updates
If an agent's goals are misaligned with their performance, update the Karma
section to refine what they should focus on.

### 2. Guardrail Additions
If an agent repeatedly makes the same type of error, add a specific guardrail
to their definition. Example: "I NEVER estimate without checking historical data"
(added after repeated over-optimistic estimates).

### 3. Skill Reassignment
If an agent is underperforming with a skill, reassign it to a more capable agent.
If an agent excels with a skill, consider making it their primary.

### 4. Authority Adjustments
- **Promotion:** Sepoy → Master (if consistently performing at master level)
- **Expanded authority:** Agent earns more "I Own" items
- **Reduced authority:** Agent loses decision rights (moved to "I Escalate")

### 5. Trait Refinement
Add new leadership principles or remove ones that aren't serving the agent.

## Review Cadence

| Review Type | Frequency | Participants |
|-------------|-----------|-------------|
| Quick retro | After each workflow completion | Participating agents |
| Sprint review | Weekly | All active agents |
| Full 360 review | Monthly | All agents including sepoys |
| Strategic review | Quarterly | Krishna + C-suite (Yudhishthira, Draupadi) |

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
