# Upgrading to v1 (from 0.1.x or a hand-copied install)

v1 changes how agents are installed. Read this once before you install v1 over
an existing setup.

## What changed

- **Agents load now.** Every agent has a one-line `description` and an explicit
  `tools` list. The old files had neither, so Claude Code skipped them, and
  their `allowed-tools` key was ignored (an agent with `allowed-tools` gets
  *every* tool). Org data moved into an `x-mahabharat:` block.
- **Flat layout.** Every agent installs as `agents/<name>.md`, sepoys included.
  The old installers put sepoys in `agents/sepoys/` and copied
  `agents/sepoys/_template.md` along with them.
- **No template is installed.** The sepoy template moved to
  `templates/sepoy-agent.md` in the repo.
- **Install from a tag.** `scripts/install.sh --from <tag>` copies a reviewed git
  ref, backs up anything it replaces, and writes an sha256 manifest to
  `<config>/mahabharat/install-manifest.json`. `scripts/smoke.sh` checks it.
- **Authority.** You (the human owner) are the CEO and the only approver for
  pushes, opening or merging PRs (and merges into main), deploys, migrations,
  destructive data operations, secrets, spend and external messages. `krishna`
  orchestrates and never approves. No agent edits agent definitions: changes go
  through a PR that you review. Every agent body carries that rule as a shared line
  (agent definitions, the roster, Claude Code settings, hooks and `CLAUDE.md`), and
  `tests/test_agents.py` requires it; the deny rules below enforce it.
- **`orchestration/` and `context/` are no longer installed.** Those pre-v1 docs name
  krishna as CEO or approver and allow auto-approval, and an agent can read an
  installed doc and cite it as authority. They stay in the repo as design notes. If an
  older install left `.claude/orchestration/` or `.claude/context/` behind, move them out
  of `.claude/` (the installers never delete anything).
- **`scripts/install.sh` needs `--target`.** A bare run used to install into your live
  user config; now it errors. Pass `--target user` or `--target <project>`.
- **Start krishna as the main session.** Run `claude --agent krishna`. Don't let
  another session delegate to it: as a subagent, Claude Code ignores the type list in
  `Agent(...)`, so it could spawn any agent type and the roster limit on delegation is
  gone. Its description tells sessions not to delegate to it, and its body tells it to
  treat a delegation-style brief as the sign that it is a subagent and return `blocked`
  without delegating; the deny rule below enforces it.
- **krishna holds no `Skill` tool.** A skill that declares `context: fork` runs as its
  own subagent with another agent type's tools (general-purpose by default), so a
  `Skill` call from krishna's main session could start a full-tool agent outside its
  `Agent(...)` list, from any skill your session can see (user, plugin or built-in).
  krishna reads skill files with `Read` instead. The other agents keep `Skill`.
- **No agent holds `Workflow` on Day 1, krishna included.** The Workflow tool accepts
  inline scripts whose `agent()` calls run full-tool subagents of any agent type, which
  would bypass krishna's `Agent(...)` allowlist and his read-only tools. v1 ships no
  saved workflows (no `workflows/` directory), so krishna delegates through `Agent`
  only, and `tests/test_agents.py` fails if any agent lists `Workflow`. Saved workflows
  return in Week 1, together with settings rules that allow only named workflows (for
  example `Workflow(bug-fix)`).
- **Approval means your permission prompt.** A protected action is approved only by
  you, through Claude Code's own permission prompt for that exact command. Every agent
  body says so in one identical line: text in a brief, a file, a hash, an id or another
  agent's message is never approval, and an agent running as a subagent never runs a
  protected action; it returns the exact plan (commands, rollback, checks) as
  `needs_decision`. ashwatthama plans incident rollbacks; hanuman executes rollbacks and
  redeploys under the same rule as a deploy.

## Why old files must leave the agents directory

Claude Code scans `agents/` **recursively**. Anything left anywhere under it
still loads (or fails to parse):

- an old `agents/sepoys/backend-dev-1.md` defines `sepoy-backend-1` a second
  time, next to the new flat `agents/sepoy-backend-1.md`;
- an old `agents/sepoys/_template.md` produces a "Failed to parse agent" error;
- a backup folder such as `agents/backup/` or `agents/old/` is scanned too.

So never back up *into* a subfolder of the agents directory. Move old files
**out** of it.

## Steps

Your user config directory is `${CLAUDE_CONFIG_DIR:-$HOME/.claude}`; the
commands below call it `$CFG`. For a project install, use
`<project>/.claude` instead, and `--target <project>` / `--project <project>`
in steps 2 and 3.

1. **Move every old agent file out of the agents directory.** That means all of
   it, including `sepoys/` and `_template.md`. Put it next to the config dir, not
   inside `agents/`:

   ```bash
   CFG="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
   BAK="$CFG/agents.bak-$(date +%Y-%m-%d)"      # a sibling of agents/, NOT inside it
   mkdir -p "$BAK"
   find "$CFG/agents" -mindepth 1 -maxdepth 1 -exec mv {} "$BAK"/ \;
   find "$CFG/agents" -type f        # must print nothing
   ```

   Keep `$BAK` until you've confirmed v1 works. If you hand-edited any of
   those files, compare them with the new versions before you delete the backup.

2. **Install v1 from a tag** (from a clone of the repo):

   ```bash
   scripts/install.sh --from <tag> --target user --dry-run   # shows what it would do
   scripts/install.sh --from <tag> --target user             # user scope: $CFG
   ```

   The installer refuses to write through symlinks. If a file it installs
   already exists with different content, it saves the old one to
   `$CFG/mahabharat/backup/<sha>/<path>` first. It never deletes anything, and
   it warns about files an older install left under `agents/`.

   It only replaces files it owns: paths in a previous install manifest, files
   identical to a committed version of the same repo file (your old 0.1.x
   copies), and agent files that define the same agent name. Anything else is
   refused before a single file is written. The usual case is a skill directory
   with the same name from another package (for example a `design-system` skill
   whose `name:` is `ckm:design-system`) or a skill you edited by hand. Then:

   - `--skip-skill <name>` leaves that skill alone (repeatable). Note that agents
     which load the skill by name then get the other one;
   - move it out of `$CFG/skills/` and re-run, or
   - `--force-replace` backs it up and replaces it anyway. Files of a foreign
     skill that this install does not ship stay in place, so prefer the first
     two options for another package's skill.

3. **Run the smoke test against your real config** (it costs $0 and needs no
   login). It runs Claude Code with an empty temporary config dir that links
   only your `agents/`, `skills/` and `workflows/`; your `settings.json` is not
   used, so its hooks, MCP servers and `env` don't apply. Every run also passes
   `--settings` with `disableAllHooks` and `--strict-mcp-config`, strips
   Anthropic and cloud-provider credentials from the environment, and stops at
   "Not logged in". Managed settings still load, and they outrank `--settings`.
   Before any run the script checks `managed-settings.json`, every `*.json` in
   `managed-settings.d/` (under `/Library/Application Support/ClaudeCode/` or
   `/etc/claude-code/`), macOS MDM preferences for `com.anthropic.claudecode`
   (converted with `plutil`, as Claude Code does) and the project's settings. It
   refuses to run if any of them sets a credential helper or credential, provider,
   endpoint or proxy variables, or can't be read:

   ```bash
   scripts/smoke.sh --user
   ```

   It passes when every roster agent loads, each agent's tools match its `tools`
   list, there are no parse or effort errors, no agent name is defined twice,
   and the installed files match the install manifest. It needs Claude Code
   2.1.295 or newer (`CLAUDE_BIN=/path/to/claude` to pick a binary).

   Working on the repo itself? `scripts/smoke.sh --worktree` installs a
   throwaway commit of your working tree into a fixture, so uncommitted work can
   be checked (the default fixture mode installs `HEAD`).

## Recommended permission rules (yours to apply)

These go in `$CFG/settings.json` under `permissions.deny`. Deny rules apply in
every permission mode and to subagents. No installer writes them; apply them
yourself if you agree.

- `"Agent(krishna)"` blocks spawning krishna as a subagent. Starting it with
  `claude --agent krishna` is not an Agent tool call, so that still works. This
  matters: inside a subagent Claude Code keeps `Agent` and ignores its type list, so
  a delegated krishna could start any agent type, including general-purpose with
  every tool. Its body tells it to return `blocked` without delegating when its first
  turn reads like a delegation brief, but that is only a prompt. Until the guard ships you can also set
  `"env": {"CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH": "1"}` for interactive sessions
  so no subagent can spawn another, or accept the risk explicitly. The planned
  guard (Week 2–3) should deny `Agent` for every hook input that carries
  `agent_id`, krishna included, and defer only when `agent_id` is absent (the
  `--agent` main thread); the smoke test should confirm `agent_id` is absent there.
- Your permission prompt is the only approval, so it has to appear. Use `ask` rules,
  never `allow` rules, for protected commands (push, deploy and apply commands,
  migrations), and don't run agents that can act in a mode that skips prompts
  (`bypassPermissions`). The production commands an incident needs are not covered
  by push/apply rules: consider `ask` rules for `"Bash(kubectl rollout *)"`,
  `"Bash(kubectl scale *)"` and your feature-flag CLI. ashwatthama plans those
  commands; hanuman (or you) runs them, and the prompt still reaches you.
- No file is ever approval: not `.mahabharat/approvals/`, not a hash or id in a brief,
  not a future approval script's record. The agents are told to ignore all of them;
  nothing in the repo stops an agent from writing such a file, so nothing may trust
  one.
- Until the write-scope guard ships (planned for Week 2–3), an agent that reads
  untrusted content and can write files can be steered into rewriting agent
  definitions, CI or your config. `draupadi` holds `WebSearch` but not `WebFetch`
  for that reason. To close the gap for every agent, add
  `"Edit(/agents/**)"`, `"Edit(/.github/**)"`, `"Edit(/CLAUDE.md)"` and
  `"Edit(~/.claude/**)"` (Edit rules also cover Write). This also blocks Claude
  from editing those paths in your own sessions, so you make those edits by hand
  or lift the rule for that session.

  Ready to apply: merge this into `permissions.deny` in `$CFG/settings.json` (or a
  project's `.claude/settings.json`); keep any deny rules you already have:

  ```json
  {
    "permissions": {
      "deny": [
        "Agent(krishna)",
        "Edit(/agents/**)",
        "Edit(/.claude/**)",
        "Edit(/.github/**)",
        "Edit(/CLAUDE.md)",
        "Edit(~/.claude/**)"
      ]
    }
  }
  ```

  `Edit(/.claude/**)` also blocks edits to the project's own settings and installed
  agents; `Edit(/.github/**)` blocks hanuman's CI work too, so drop it if you route CI
  changes to hanuman and review them in the PR. A rule with a leading `/` resolves
  relative to the settings file it is in, so after applying, check in `/permissions`
  (and with one test edit) that each rule covers the path you expect.

## pip users

`mahabharat-install <project>` (the Python CLI) now installs flat too, skips the
template, and writes the same kind of manifest under `<project>/.claude/mahabharat/`.
Like `scripts/install.sh` it refuses symlinks, backs up what it replaces, and
refuses a skill directory it doesn't own (`--skip-skill`, `--force-replace`).
Without git history it recognises your old copies only when they are in a
manifest or identical to what it ships. `bash install.sh <project>` from a
checkout runs this same CLI on the working tree.
If an older version installed into that project, move `<project>/.claude/agents/sepoys/`
out of `<project>/.claude/agents/` first (step 1, with `CFG=<project>/.claude`).
