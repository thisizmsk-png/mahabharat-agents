# Itihasa — Historical Record (L2 Context)

> Retrieved on demand. Past decisions, archived artifacts, research findings.
> Named after the Itihasa texts (Mahabharata, Ramayana) — historical epics
> that preserve wisdom across generations.

## What Goes Here

This directory contains long-term historical context retrieved when agents
need deep background:

- **Archived architectural decisions (ADRs)**
- **Past postmortem reports**
- **Historical research findings**
- **Completed feature specs**
- **Performance benchmarks over time**
- **Security audit histories**

## How to Use

1. Agents do NOT load this directory at session start (too large)
2. Agents retrieve specific files when they need historical context
3. Files here are append-only — never modify historical records
4. Use semantic naming so agents can find relevant history

## File Naming Convention

```
{date}-{category}-{topic}.md
```

Example: `2026-03-15-adr-event-driven-signal-bus.md`,
`2026-03-10-postmortem-api-outage.md`

## Retrieval Pattern

When an agent needs historical context:
1. Search Itihasa by category and keyword
2. Load only the relevant files (not the entire directory)
3. Extract the specific insight needed
4. Reference the source in their reasoning

## Template

```markdown
# [Category]: [Topic] — [Date]

## Summary
[1-2 sentence overview]

## Content
[Full historical record]

## Tags
[Keywords for retrieval: architecture, security, performance, etc.]

## Referenced By
[Which agents/decisions have used this record]
```
