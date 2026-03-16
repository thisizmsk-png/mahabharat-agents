# Escalation Rules — When to Escalate and to Whom

## Automatic Escalation Triggers

| Trigger | Escalate To | Reason |
|---------|-------------|--------|
| Decision outside authority matrix | `reports_to` agent | Authority boundary |
| Disagreement between same-level agents | Shared superior | Conflict resolution |
| Security concern (any severity) | Bhishma | Security is always escalated |
| Production incident (SEV1/SEV2) | Ashwatthama → Hanuman → Yudhishthira | Incident chain |
| Deadlock after 3 rounds | Krishna | CEO tiebreak |
| Sepoy stuck > 30 minutes | Master agent | Mentorship and unblocking |
| Adversarial finding (HIGH+) | Krishna + relevant domain owner | Risk acceptance |
| Budget or resource request | Krishna | Resource allocation |
| Cross-module/cross-team change | Arjuna (technical) or Draupadi (product) | Coordination |
| User data at risk | Bhishma → Krishna | Compliance and legal |

## Escalation Protocol

### Step 1: Identify
- What is the issue?
- Why can't I resolve it within my authority?
- What have I tried?

### Step 2: Prepare
- Document the issue clearly
- State the options you've considered
- Provide your recommendation (if you have one)
- Estimate the urgency (blocking vs. can-wait)

### Step 3: Escalate
- Contact the correct agent per the trigger table above
- Provide the prepared documentation
- If urgent (blocking work), mark as URGENT in the artifact

### Step 4: Follow Up
- Track the escalation until resolved
- Implement the decision once made
- Log the decision in the audit trail

## Escalation Anti-Patterns (DO NOT)

- **Don't escalate without trying first** — Attempt to resolve within your authority
- **Don't skip levels** — Go to your `reports_to` first, not directly to Krishna
- **Don't escalate opinions as facts** — Clearly separate your recommendation from the situation
- **Don't escalate repeatedly** — If Krishna decides, accept and commit (disagree and commit)
- **Don't avoid escalation** — Under-escalation is as bad as over-escalation

## Emergency Override

In genuine emergencies (data loss, security breach, service down):
- ANY agent can escalate directly to Krishna
- Normal hierarchy is suspended during SEV1 incidents
- Ashwatthama has authority to rollback without approval during active incidents
- All emergency actions are logged and reviewed in postmortem
