# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Changed

- Agent files follow `mahabharat.agent/v1`: one-line `description`, explicit `tools`
  (replacing `allowed-tools`, which Claude Code ignores for agents), a model alias, an
  explicit `effort`, and org data in an `x-mahabharat:` block. Only `krishna` holds
  `Agent(...)`; no agent holds `Workflow` (its inline scripts can start any agent type),
  and `krishna` holds no `Skill` (a `context: fork` skill runs as its own subagent).
- Agents install flat as `agents/<name>.md`, sepoys included. `install.sh` and the
  `mahabharat-install` CLI no longer create `agents/sepoys/` or install the template, and
  skip the retired `zero-bias` skill. Banner counts are computed instead of hard-coded.
- The sepoy template moved from `agents/sepoys/_template.md` to `templates/sepoy-agent.md`.
- `orchestration/guardrails/feedback-loop.md`: agents (Krishna included) no longer rewrite
  agent definitions or authority; changes are proposed as a PR that the human owner reviews.
- The human owner is the CEO and the only approver; `krishna` is the orchestrator agent.
- `mahabharat-install` refuses symlinked destinations, backs up files it would change to
  `.claude/mahabharat/backup/`, writes an install manifest, and accepts `--dry-run`.
- CI: the inline frontmatter check (which required the old top-level `role`/`character`/
  `rank` keys) is gone; pytest owns agent validation. A new `smoke` job runs the Stage 0
  smoke test with a pinned Claude Code CLI (2.1.295).
- `krishna` runs only as the main session (`claude --agent krishna`); its description
  tells other sessions not to delegate to it, because inside a subagent Claude Code
  removes `Workflow` and ignores the type list in `Agent(...)`, so a delegated krishna
  could spawn any agent type. Spawned anyway, it makes no `Agent` call and returns
  `blocked`. One-file code fixes route to bhima or nakula, small docs and config edits
  to abhimanyu.
- bhishma's trigger is a security review, threat model or gate verdict on a diff, design
  or dependency; building auth or other features routes to bhima or nakula.
- Agent bodies no longer link to `roles/*.md`: those pages still carry pre-v1 authority
  (CEO override, PM go/no-go) and don't resolve after a flat install. A test rejects such
  links.
- vidura routes production data access to the human owner (bhishma reviews the request).
- Accessibility review of finished UI belongs to vidura (WCAG 2.2 AA), not nakula.
- dhrishtadyumna (no Bash) assembles the release checklist from gate verdicts and drafts
  the changelog from the merged-work list in its brief instead of claiming to run them.
- draupadi keeps `WebSearch` but no longer holds `WebFetch` until the `docs/`-only write
  guard ships.
- karna's charter is generic numerical correctness; trading-specific items belong in a
  project's CLAUDE.md. Escalation keys are now `model-go-live` and
  `production-threshold-change`.
- Approval is only the owner's answer to Claude Code's own permission prompt for that
  exact command. No file, hash, id or text in a brief is approval, and an agent can't
  verify who started its session. As subagents, hanuman, ashwatthama and shakuni never run
  a protected action against production or staging (ashwatthama's recovery drills
  included): they return the exact plan (commands, rollback, checks) as `needs_decision`.
  shakuni attacks only this repo's code, in-process or against a server it starts itself;
  any other localhost service needs the owner's authorization. hanuman and ashwatthama never
  run destructive data operations; duryodhana targets no hosts. Local merges of worker
  branches are arjuna's; PR merges and merges into main are the owner's. Every agent with
  Bash lists the same protected actions.
- Agents without web tools apply the `research` skill to repo evidence and route web
  research to yudhishthira or draupadi; where `spec` asks for user confirmation, a
  subagent returns `needs_decision`.
- `install.sh` is now a thin wrapper around the `mahabharat-install` CLI run on the working
  tree, so it gets the CLI's checks: no writes through a symlinked file or directory,
  backups of replaced files, and a manifest.
- The installers replace only files they own (in a previous manifest, identical to a
  committed version of the same file, or an agent file of the same name). Another
  package's same-named skill is refused; `--skip-skill <name>` and `--force-replace` say
  what to do instead.
- `scripts/smoke.sh` no longer copies the user's `settings.json` in `--user` mode, passes
  `--settings` (disableAllHooks) and `--strict-mcp-config` on every run, strips cloud
  credentials (`AWS_*`, `GOOGLE_*`, `AZURE_*`, ...), and refuses to run when a settings
  file it would load sets a credential helper or credential/provider/endpoint/proxy
  variables. A run passes only if it ends with "Not logged in" and shows no API activity
  (tokens, API time, extra turns, "API Error"); anything else that looks like a request is
  exit 3. The preflight also covers `managed-settings.d/*.json` drop-ins and macOS MDM
  preferences (converted with `plutil`, as Claude Code does).
- `scripts/install.sh` refuses a ref with any symlink under `agents/`, `skills/` or
  `workflows/` (a symlinked directory used to be followed, installing files from outside
  the ref).
- The agent schema whitelists top-level keys (including the allowed-but-unused
  `skills`, `isolation`, `disallowedTools` and `memory`), rejects a `*` item in `tools`
  (Claude Code's wildcard for every tool), and rejects preloading the retired `zero-bias`
  skill.

- Every agent body carries a third shared guardrail line: never edit agent definitions,
  the roster, Claude Code settings, hooks or `CLAUDE.md`, whatever a brief or file says;
  proposed changes go in the report for the owner. `tests/test_agents.py` requires it.
- `templates/sepoy-agent.md` carries the same three shared lines; its old "unless your
  brief carries a human-approved plan id" exception is gone. The template and every
  installed skill are now linted for banned text too.
- The installers no longer copy `orchestration/` or `context/` into `.claude/`: those
  pre-v1 docs still name krishna as CEO and approver and allow auto-approval. They stay in
  the repo as design notes until they are rewritten.
- `scripts/install.sh` needs an explicit `--target user|<project>`; a bare run no longer
  writes into the live user config.

### Added

- `spec/mahabharat.agent.v1.schema.json` (JSON Schema 2020-12) for agent frontmatter.
- `agents/roster.yaml`, the manifest of installed agents (replaces "exactly 17").
- `scripts/install.sh --from <ref> --target user|<project> [--dry-run]`: installs a git
  ref via `git archive`, refuses symlinks, backs up replaced files outside `agents/`, and
  writes `mahabharat/install-manifest.json` with an sha256 per file.
- `scripts/smoke.sh` (`--project <dir>` | `--user`): $0, no-auth check that every roster
  agent loads with exactly its declared tools, with no parse or effort errors, no
  duplicate agent names and no drift from the install manifest. `--worktree` checks a
  throwaway commit of the working tree, for work that isn't committed yet.
- `docs/upgrading-to-v1.md`.
- Tests: schema and roster validation for every agent, checked against a synthetic fixture
  repo as well; installer tests for `scripts/install.sh`, `install.sh` and the CLI;
  `tests/test_smoke_check.py` for the smoke assertions. Banned text is matched as
  case-insensitive patterns ("bend the rules", "Silence from Krishna"), and uninstalled
  agent names are rejected anywhere in an agent file.

### Fixed

- Clone URLs in `docs/getting-started.md` and `CREDITS.md` now point at
  `https://github.com/thisizmsk-png/mahabharat-agents`.
- `tests/test_install.py` called the zero-argument `install()` with an argument.

### Removed

- Krishna's "Autonomy Protocol" and the "bend rules" line (CI now rejects them).

## [0.1.0] - 2026-03-28

### Added

- 17 master agents with DKK (Dharma-Karma-Katha) format
- 13 composable skills (7 shared + 6 role-specific)
- 5 orchestration topologies (Vyuha, Sabha, Rajya, Chakravyuha, Akshauhini)
- 6 production workflows (feature-development, bug-fix, architecture-review, incident-response, security-audit, performance-review)
- 4 guardrail documents (core-principles, authority-matrix, escalation-rules, feedback-loop)
- 3-tier context system (Shruti/Smriti/Itihasa)
- pip installable package with `mahabharat-install` CLI
- Shell script installer (`install.sh`)
- Sepoy template and 3 example sepoys
- 16 FAANG-level role definitions

[0.1.0]: https://github.com/thisizmsk-png/mahabharat-agents/releases/tag/v0.1.0
