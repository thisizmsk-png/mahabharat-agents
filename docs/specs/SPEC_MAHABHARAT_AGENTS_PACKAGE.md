# Spec: Mahabharat Agents Package

**Version:** 1.0.0 | **Date:** 2026-03-16 | **Status:** Implemented
**Author:** Sai Krishna Madavarapu

---

## 1. Requirements

### 1.1 Problem Statement
Solo developers must be CEO, CTO, PM, designer, engineer, tester, and DevOps simultaneously. Current AI coding assistants lack role-specific expertise, organizational structure, or inter-agent coordination. No framework simulates an entire software company where specialized AI agents collaborate like a real team with FAANG-level best practices.

**Who:** Solo builders/developers who want the output of a 10-person team.
**Cost of inaction:** Quality suffers in areas outside the builder's core competency.
**Why now:** Claude Code skills + agents infrastructure is mature. Existing frameworks (MetaGPT, CrewAI) prove the concept but don't integrate with Claude Code.

### 1.2 User Stories
- US-1: As CEO/God, assign tasks to role-specific AI agents with deep domain expertise
- US-2: As a builder, get FAANG-level code reviews, PM specs, security audits from agents
- US-3: As an orchestrator, agents coordinate following guardrails (PM → Design → Eng → QA → Deploy)
- US-4: As a framework user, compose skills and assign to agents based on role
- US-5: As open-source contributor, generic enough for ANY solo builder
- US-6: As CEO, visualization dashboard to see all agents in action

### 1.3 Scope
**In scope:** 15 roles, 17 named agents, 13 skills, 5 orchestration topologies, 5 workflows, sepoy system, context tiers, guardrails, install script, open-source packaging.
**Out of scope (v1):** LLM-agnostic support, real-time voice, billing per agent, multi-user, mobile, agent marketplace.

### 1.4 Non-Functional Requirements
Performance: <30s per task. Scalability: 5-20 agents. Extensibility: config-based, not code. Observability: full audit trail. Security: authority enforcement. Portability: any project.

---

## 2. Design

### 2.1 Architecture Decisions

**ADR-1: DKK (Dharma-Karma-Katha) Agent Format** — Extended Claude Code agent definition with role, goal, backstory, traits, skills, authority, guardrails. Inspired by CrewAI's Role-Goal-Backstory trinity.

**ADR-2: Master/Sepoy Hierarchy** — Named Mahabharata characters as masters, supporting agents as sepoys with inherited role skills but reduced authority.

**ADR-3: Multi-Topology Orchestration** — Sanskrit-named patterns: Vyuha (sequential), Sabha (debate), Rajya (hierarchical), Chakravyuha (graph DAG), Akshauhini (parallel fork-join).

**ADR-4: Artifact-Based Pub-Sub Communication** — MetaGPT-inspired. Prevents hallucination cascading. Typed artifacts validated at boundaries.

**ADR-5: Tiered Context (Shruti/Smriti/Itihasa)** — L0 always loaded, L1 per session, L2 on demand. Inspired by OpenViking.

**ADR-6: Kurukshetra Dashboard** — Next.js war room for agent monitoring (future implementation).

**ADR-7: Duryodhana as Red Team Lead** — Adversarial agent that challenges every major decision.

### 2.2 Agent Roster (17 Masters + Sepoys)

| # | Character | Role | Reports To |
|---|-----------|------|-----------|
| 1 | Krishna | CEO / God | — |
| 2 | Yudhishthira | CTO | Krishna |
| 3 | Arjuna | Principal SDE | Yudhishthira |
| 4 | Bhima | Sr. Backend Engineer | Arjuna |
| 5 | Nakula | Sr. Frontend Engineer | Arjuna |
| 6 | Sahadeva | Data Scientist | Yudhishthira |
| 7 | Draupadi | Product Manager | Krishna |
| 8 | Karna | Quant Engineer | Yudhishthira |
| 9 | Drona | Product Owner | Draupadi |
| 10 | Bhishma | Security Engineer | Yudhishthira |
| 11 | Vidura | QA Engineer | Arjuna |
| 12 | Hanuman | DevOps / SRE | Yudhishthira |
| 13 | Duryodhana | Red Team Lead | Krishna |
| 14 | Shakuni | Offensive Security | Bhishma |
| 15 | Abhimanyu | Junior Engineer | Arjuna |
| 16 | Ashwatthama | Incident Response | Hanuman |
| 17 | Dhrishtadyumna | Program Manager | Draupadi |

### 2.3 Skill Matrix
7 shared skills: HLD, LLD, code-review, testing, research, spec, zero-bias.
6 role-specific: product-spec, threat-modeling, incident-response, backtest-validation, design-system, ci-cd.

---

## 3. Tasks (Completed)

| Task | Status | Files Created |
|------|--------|---------------|
| Core skeleton + roles | Done | 3 package files + 15 role definitions |
| Master agents (17) | Done | 17 DKK-format agent definitions |
| Skills (13) | Done | 7 shared + 6 role-specific SKILL.md |
| Orchestration (5 topologies + 5 workflows) | Done | 10 YAML configs |
| Sepoy system | Done | 1 template + 3 examples |
| Context management | Done | Shruti + Smriti + Itihasa |
| Guardrails | Done | 3 guardrail documents |
| Install script + docs | Done | install.sh + 2 doc files |

**Total: 71 files across 8 task groups.**

---

## Research References

- `research/05_multi_agent_frameworks_deep_research.md` — 15 frameworks analyzed
- `research/05_role_definitions_faang.md` — 13 FAANG role definitions
- `research/06_mahabharata_agent_naming.md` — 16 character mappings

## Credits

Built on ideas from: MetaGPT (MIT), CrewAI (MIT), ChatDev (Apache 2.0), Swarms (MIT), MiroFish (AGPL-3.0), OpenViking (Apache 2.0), AutoGen (MIT), CAMEL (Apache 2.0), OpenHands (MIT). Full attribution in CREDITS.md.
