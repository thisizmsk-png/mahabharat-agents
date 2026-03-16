# Smriti — Remembered Wisdom (L1 Context)

> Loaded per session. Current project context, active tasks, recent decisions.
> Named after the Smriti scriptures — remembered wisdom, interpreted per era.

## What Goes Here

This directory contains session-specific context that agents load at the start
of each working session:

- **Current sprint goals and active tasks**
- **Recent architectural decisions (last 2 weeks)**
- **Open pull requests and their status**
- **Active incidents or blockers**
- **Current project CLAUDE.md / AGENTS.md content**

## How to Use

1. At session start, agents read all files in this directory
2. During the session, agents update files as context changes
3. At session end, promote important context to Itihasa (L2) if it has long-term value
4. Purge stale context that is no longer relevant

## File Naming Convention

```
{date}-{topic}.md
```

Example: `2026-03-16-sprint-goals.md`, `2026-03-16-active-incidents.md`

## Template

```markdown
# [Topic] — [Date]

## Status
[Current state]

## Relevant Agents
[Which agents need this context]

## Context
[The actual context information]

## Expiry
[When this context becomes stale: date or condition]
```
