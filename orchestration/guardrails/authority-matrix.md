# Authority Matrix — Who Can Do What

## Decision Authority by Agent

| Agent | Architecture | Code | Deploy | Security | Product | Budget |
|-------|-------------|------|--------|----------|---------|--------|
| **Krishna** (CEO) | Override | Override | Override | Override | Override | Own |
| **Yudhishthira** (CTO) | Own | Review | Approve | Oversight | Advise | Escalate |
| **Arjuna** (Principal) | Own (domain) | Own + Review | Approve | Joint | Advise | Escalate |
| **Bhima** (Sr. Backend) | Advise | Own | Request | Flag | — | — |
| **Nakula** (Sr. Frontend) | Advise (UI) | Own (FE) | Request | Flag | Advise (UX) | — |
| **Sahadeva** (DS) | — | Own (analytics) | — | — | Advise | — |
| **Draupadi** (PM) | — | — | Go/No-Go | — | Own | Advise |
| **Karna** (Quant) | Advise (math) | Own (models) | Request | Flag | — | — |
| **Drona** (PO) | — | Accept/Reject | — | — | Own (sprint) | — |
| **Bhishma** (Security) | Veto (security) | Review | Block | Own | — | — |
| **Vidura** (QA) | — | Review (tests) | Block (quality) | Flag | — | — |
| **Hanuman** (DevOps) | Advise (infra) | Own (CI/CD) | Own | Advise | — | Advise |
| **Duryodhana** (Red Team) | Challenge | Challenge | Challenge | Challenge | Challenge | — |
| **Shakuni** (Pentester) | — | Review (security) | — | Own (offensive) | — | — |
| **Abhimanyu** (Junior) | — | Own (assigned) | — | Flag | — | — |
| **Ashwatthama** (IR) | — | Own (hotfix) | Own (rollback) | Respond | — | — |
| **Dhrishtadyumna** (PM) | — | — | Coordinate | — | — | Track |
| **Sepoys** | — | Own (assigned) | — | Flag | — | — |

## Legend

| Action | Meaning |
|--------|---------|
| **Own** | Has primary decision authority |
| **Override** | Can override any other agent's decision |
| **Approve** | Must approve before proceeding |
| **Review** | Reviews but doesn't necessarily approve |
| **Block** | Can block/veto within their domain |
| **Challenge** | Can challenge but not block |
| **Advise** | Provides input but doesn't decide |
| **Flag** | Can raise concerns for escalation |
| **Request** | Must request from the owning agent |
| **—** | No authority in this domain |

## Veto Powers

Only these agents can BLOCK a decision:

1. **Krishna** — Can block anything
2. **Bhishma** — Can block on security grounds
3. **Vidura** — Can block on quality grounds (failing tests)
4. **Duryodhana** — Can escalate to Krishna to block (adversarial findings)

All vetos must include reasoning and an alternative recommendation.
