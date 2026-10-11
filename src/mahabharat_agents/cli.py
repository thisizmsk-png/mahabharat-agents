"""CLI entry point for mahabharat-agents installation (`mahabharat-install`).

Installs into a project's ``.claude/`` directory:

* every agent in ``agents/roster.yaml``, flat, as ``.claude/agents/<name>.md``
  (Claude Code scans ``agents/`` recursively, so nothing is nested and the
  sepoy template in ``templates/`` is never installed);
* skills from ``skills/shared`` and ``skills/role-specific`` (except the retired
  ``zero-bias`` skill) as ``.claude/skills/<name>/...``.

``orchestration/`` and ``context/`` are not installed: those pre-v1 docs still name
krishna as CEO and approver, and an installed doc is one an agent can read and cite as
authority. They stay in the repo as design notes until they are rewritten.

Like ``scripts/install.sh`` it refuses symlinked destinations and symlinked sources
(any symlinked file or directory under the data root's ``agents/`` or ``skills/``,
or a source that resolves outside it), backs up any
existing file it would change to ``.claude/mahabharat/backup/<id>/<relpath>``
(never under ``agents/``), and writes ``.claude/mahabharat/install-manifest.json``.
It only replaces files it owns: paths in the previous install manifest, agent files
that define the same agent name. An existing skill directory that is neither in the manifest nor identical to
the skill it ships (for example another package's skill with the same name) is
refused unless ``--skip-skill <name>`` or ``--force-replace`` is given.
From a git checkout, prefer ``scripts/install.sh --from <tag>``: it installs a
reviewed ref instead of whatever is on disk.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

from mahabharat_agents import __version__

# When installed via pip, data files are bundled under mahabharat_agents/data/.
# When running from source, fall back to the repo root.
_BUNDLED_DATA = Path(__file__).parent / "data"
_REPO_ROOT = Path(__file__).parent.parent.parent

DATA_ROOT = _BUNDLED_DATA if _BUNDLED_DATA.is_dir() else _REPO_ROOT

RETIRED_SKILLS = {"zero-bias"}

_ROSTER_LINE = re.compile(
    r"^\s*-\s*\{\s*name:\s*(?P<name>[a-z][a-z0-9-]*)\s*,\s*"
    r"file:\s*(?P<file>[A-Za-z0-9._/-]+)\s*,\s*"
    r"rank:\s*(?P<rank>god|master|sepoy)\s*\}\s*$"
)


class InstallError(Exception):
    """Raised when the install must be refused; nothing has been written."""


def read_roster(data_root: Path = DATA_ROOT) -> list[dict]:
    """Parse agents/roster.yaml without a YAML dependency (one mapping per line)."""
    roster_path = data_root / "agents" / "roster.yaml"
    if not roster_path.is_file():
        raise InstallError(f"missing {roster_path}")
    entries = []
    for line in roster_path.read_text(encoding="utf-8").splitlines():
        if "{name:" not in line:
            continue
        match = _ROSTER_LINE.match(line)
        if not match:
            raise InstallError(f"cannot parse roster line: {line!r}")
        entries.append(match.groupdict())
    if not entries:
        raise InstallError("agents/roster.yaml lists no agents")
    names = [e["name"] for e in entries]
    dupes = sorted({n for n in names if names.count(n) > 1})
    if dupes:
        raise InstallError(f"duplicate roster names: {dupes}")
    return entries


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _frontmatter_name(path: Path) -> str | None:
    """The ``name:`` value of a file's frontmatter (frontmatter must start on line 1)."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return None
    if not lines or lines[0] != "---":
        return None
    for line in lines[1:]:
        if line == "---":
            return None
        m = re.match(r"^name:\s*(.*?)\s*$", line)
        if m:
            return m.group(1).strip("'\"") or None
    return None


def _previous_manifest_paths(base: Path) -> set[str]:
    mpath = base / "mahabharat" / "install-manifest.json"
    if not mpath.is_file() or mpath.is_symlink():
        return set()
    try:
        data = json.loads(mpath.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return set()
    return {
        str(e.get("path")) for e in data.get("installed", []) if isinstance(e, dict) and e.get("path")
    }


def _confined(root: Path, rel: str) -> Path:
    """``root/rel``, refusing a symlink at any component below ``root`` and any path that
    resolves outside ``root`` (``root`` must already be resolved).

    A symlinked source (say ``skills/shared/hld -> /elsewhere``) would otherwise install
    files from the installing machine as if they shipped with the package, the same thing
    ``scripts/install.sh`` refuses in a git ref.
    """
    if not rel or rel.startswith("/") or "\\" in rel:
        raise InstallError(f"refusing: unsafe source path {rel!r}")
    p = root
    for part in rel.split("/"):
        if part in ("", ".", ".."):
            raise InstallError(f"refusing: unsafe source path {rel!r}")
        p = p / part
        if p.is_symlink():
            raise InstallError(
                f"refusing: source {p} is a symlink (sources must be real files inside {root})"
            )
    try:
        p.resolve().relative_to(root)
    except ValueError:
        raise InstallError(f"refusing: source {p} resolves outside {root}") from None
    return p


def _tree_files(root: Path, rel_dir: str) -> list[Path]:
    """Every regular file under ``root/rel_dir`` (sorted), refusing any symlink in the tree."""
    top = _confined(root, rel_dir)
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(top, followlinks=False):
        here = Path(dirpath)
        for name in dirnames + filenames:
            entry = here / name
            if entry.is_symlink():
                raise InstallError(
                    f"refusing: source {entry} is a symlink (sources must be real files inside {root})"
                )
        dirnames.sort()
        for name in sorted(filenames):
            entry = here / name
            if name != ".DS_Store" and entry.is_file():
                out.append(entry)
    return sorted(out)


def _plan(
    data_root: Path,
    agents: bool,
    skills: bool,
    skip_skills: frozenset[str] = frozenset(),
) -> list[tuple[Path, str]]:
    """Return (source, destination relative to .claude/) pairs.

    Every source is confined to ``data_root``: a symlinked file or directory anywhere on a
    source path, or a source that resolves outside ``data_root``, is refused.
    """
    root = Path(data_root).resolve()
    plan: list[tuple[Path, str]] = []
    if agents:
        if (root / "agents").is_symlink():
            raise InstallError(f"refusing: source {root / 'agents'} is a symlink")
        _confined(root, "agents/roster.yaml")
        for entry in read_roster(root):
            rel = entry["file"]
            if not (rel.startswith("agents/") and rel.endswith(".md")):
                raise InstallError(f"roster file for {entry['name']!r} must be agents/**/*.md, got {rel!r}")
            src = _confined(root, rel)
            if not src.is_file():
                raise InstallError(f"roster lists {rel} but it does not exist")
            plan.append((src, f"agents/{entry['name']}.md"))
    if skills:
        seen: set[str] = set()
        for group in ("shared", "role-specific"):
            group_rel = f"skills/{group}"
            group_dir = _confined(root, group_rel)
            if not group_dir.is_dir():
                continue
            for skill_dir in sorted(group_dir.iterdir()):
                skill_rel = f"{group_rel}/{skill_dir.name}"
                if skill_dir.is_symlink():
                    raise InstallError(
                        f"refusing: source {skill_dir} is a symlink (sources must be real files inside {root})"
                    )
                if not (skill_dir / "SKILL.md").is_file() or skill_dir.name in RETIRED_SKILLS:
                    continue
                if skill_dir.name in skip_skills:
                    continue
                if skill_dir.name in seen:
                    raise InstallError(f"skill {skill_dir.name!r} exists in more than one group")
                seen.add(skill_dir.name)
                for f in _tree_files(root, skill_rel):
                    plan.append((f, f"skills/{skill_dir.name}/{f.relative_to(skill_dir).as_posix()}"))
    for src, _ in plan:  # belt and braces: every planned source is a real file inside root
        if src.is_symlink() or not src.is_file():
            raise InstallError(f"refusing: source {src} is not a regular file")
        try:
            src.resolve().relative_to(root)
        except ValueError:
            raise InstallError(f"refusing: source {src} resolves outside {root}") from None
    return plan


def _check_dest(base: Path, rel: str) -> None:
    """Refuse if base or any component of base/rel is a symlink (or a file where a dir goes)."""
    if base.is_symlink():
        raise InstallError(f"refusing: {base} is a symlink")
    p = base
    parts = rel.split("/")
    for i, part in enumerate(parts):
        p = p / part
        if p.is_symlink():
            raise InstallError(f"refusing: {p} is a symlink")
        last = i == len(parts) - 1
        if not last and p.exists() and not p.is_dir():
            raise InstallError(f"refusing: {p} exists and is not a directory")
        if last and p.exists() and not p.is_file():
            raise InstallError(f"refusing: {p} exists and is not a regular file")


def _backup_path(base: Path, install_id: str, rel: str, current: Path) -> Path:
    """Where ``current`` is (or would be) backed up; every candidate is checked like a
    destination, so a backup is never read or written through a symlink."""
    brel = f"mahabharat/backup/{install_id}/{rel}"
    _check_dest(base, brel)
    bp = base / brel
    candidate, k = bp, 0
    while candidate.exists() or candidate.is_symlink():
        _check_dest(base, candidate.relative_to(base).as_posix())
        if candidate.read_bytes() == current.read_bytes():
            return candidate
        k += 1
        candidate = bp.with_name(f"{bp.name}.{k}")
    _check_dest(base, candidate.relative_to(base).as_posix())
    return candidate


def _write_atomic(dest: Path, data: bytes) -> None:
    """Write ``data`` to ``dest`` via a fresh temp file in the same directory.

    The temp file is created exclusively (``mkstemp``), so a symlink planted at a
    predictable temp name can never redirect the write; ``os.replace`` then swaps it in
    (replacing a path, never writing through one)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{dest.name}.mahabharat-tmp.", dir=dest.parent)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        os.chmod(tmp, 0o644)
        os.replace(tmp, dest)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def run_install(
    target: Path,
    *,
    agents: bool = True,
    skills: bool = True,
    dry_run: bool = False,
    data_root: Path = DATA_ROOT,
    out=sys.stdout,
    force_replace: bool = False,
    skip_skills: tuple[str, ...] | list[str] = (),
) -> dict:
    """Install into ``target/.claude``. Returns the manifest dict."""
    target = Path(target)
    if target.is_symlink():
        raise InstallError(f"refusing: target {target} is a symlink; pass the real path")
    if not target.is_dir():
        raise InstallError(f"{target} is not a directory")
    base = target.resolve() / ".claude"

    plan = _plan(data_root, agents, skills, frozenset(skip_skills))
    entries = [{"path": rel, "sha256": _sha256(src)} for src, rel in plan]
    digest = hashlib.sha256(
        "".join(f"{e['path']} {e['sha256']}\n" for e in entries).encode()
    ).hexdigest()[:40]
    manifest = {
        "ref": f"mahabharat-agents {__version__} (python cli)",
        "sha": digest,
        "installed": entries,
    }
    manifest_rel = "mahabharat/install-manifest.json"

    # Validate everything before the first write.
    _check_dest(base, manifest_rel)
    previous = _previous_manifest_paths(base)
    foreign: list[str] = []

    # Skill directories: an existing skills/<name>/ must be ours before any file in it
    # is touched, so another package's same-named skill is never turned into a hybrid.
    shipped_skill_md = {
        rel.split("/")[1]: src for src, rel in plan if rel.startswith("skills/") and rel.count("/") == 2
        and rel.endswith("/SKILL.md")
    }
    for sname, src in sorted(shipped_skill_md.items()):
        _check_dest(base, f"skills/{sname}/SKILL.md")
        sdir = base / "skills" / sname
        if not sdir.is_dir():
            continue
        files = [p for p in sdir.rglob("*") if p.is_file() and p.name != ".DS_Store"]
        if not files or any(r.startswith(f"skills/{sname}/") for r in previous):
            continue
        current = sdir / "SKILL.md"
        if current.is_file() and current.read_bytes() == src.read_bytes():
            continue
        other = _frontmatter_name(current) if current.is_file() else None
        named = f" named {other!r}" if other else ""
        foreign.append(
            f"skills/{sname}/ (existing skill{named}, {len(files)} file(s); not installed by "
            f"mahabharat-agents and not identical to its {sname!r} skill)"
        )

    _check_dest(base, f"mahabharat/backup/{digest}/.probe")
    actions = []
    backups: dict[str, Path] = {}
    for src, rel in plan:
        _check_dest(base, rel)
        dest = base / rel
        if not dest.exists():
            actions.append("new")
        elif dest.read_bytes() == src.read_bytes():
            actions.append("same")
        else:
            backups[rel] = _backup_path(base, digest, rel, dest)
            actions.append("replace")
            if rel.startswith("skills/") or rel in previous:
                continue  # skills were judged per directory
            if rel.startswith("agents/") and _frontmatter_name(dest) == rel[len("agents/"):-3]:
                continue  # a copy of the same agent (e.g. hand-edited); it is backed up
            foreign.append(f"{rel} (existing file is not from mahabharat-agents)")

    if foreign:
        if not force_replace:
            raise InstallError(
                "refusing to replace files this installer does not own (nothing was written):\n  "
                + "\n  ".join(foreign)
                + f"\nMove them out of {base}, pass --skip-skill <name> to leave a skill alone, "
                "or pass --force-replace to back them up and replace them anyway."
            )
        for f in foreign:
            print(f"  warning: --force-replace: replacing {f}; current files are backed up first",
                  file=sys.stderr)

    print(f"\nInstalling Mahabharat Agents to {base}/{' (dry run)' if dry_run else ''}\n", file=out)
    for (src, rel), action in zip(plan, actions):
        dest = base / rel
        if action == "same":
            continue
        if action == "replace":
            bp = backups[rel]
            if not dry_run and not bp.exists():
                _write_atomic(bp, dest.read_bytes())
                shutil.copystat(dest, bp)
            print(f"  ~ {rel} (previous version backed up to {bp.relative_to(base)})", file=out)
        else:
            print(f"  + {rel}", file=out)
        if not dry_run:
            _write_atomic(dest, src.read_bytes())

    n_agents = sum(1 for _, rel in plan if rel.startswith("agents/"))
    n_skills = len({rel.split("/")[1] for _, rel in plan if rel.startswith("skills/")})
    if not dry_run:
        mpath = base / manifest_rel
        text = json.dumps(manifest, indent=2) + "\n"
        if not (mpath.is_file() and mpath.read_text(encoding="utf-8") == text):
            _write_atomic(mpath, text.encode("utf-8"))
    # Old layouts (agents/sepoys/, _template.md) redefine agent names because Claude Code
    # scans agents/ recursively. Report them; moving the user's files is the user's call.
    planned = {rel for _, rel in plan}
    agents_dir = base / "agents"
    if agents and agents_dir.is_dir():
        for f in sorted(agents_dir.rglob("*.md")):
            rel = f.relative_to(base).as_posix()
            if rel not in planned:
                print(
                    f"  warning: {rel} is not part of this install and is still under agents/; "
                    "if it is an old copy, move it OUT of the agents directory "
                    "(see docs/upgrading-to-v1.md)",
                    file=sys.stderr,
                )
    changed = sum(1 for a in actions if a != "same")
    print(
        f"\n  {n_agents} agents, {n_skills} skills; {changed} file(s) "
        f"{'would change' if dry_run else 'changed'}; manifest: {manifest_rel}",
        file=out,
    )
    return manifest


def install(argv: list[str] | None = None) -> None:
    """Console entry point: ``mahabharat-install [target] [--agents-only|--skills-only] [--dry-run]``."""
    parser = argparse.ArgumentParser(
        prog="mahabharat-install",
        description="Install Mahabharat Agents into a project's .claude/ directory",
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Target project directory (default: current directory)",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--agents-only", action="store_true", help="Install only agent definitions")
    group.add_argument("--skills-only", action="store_true", help="Install only skills")
    parser.add_argument("--dry-run", action="store_true", help="Print actions; write nothing")
    parser.add_argument(
        "--skip-skill", action="append", default=[], metavar="NAME",
        help="Leave .claude/skills/NAME alone (repeatable), e.g. another package's skill",
    )
    parser.add_argument(
        "--force-replace", action="store_true",
        help="Replace files this installer does not own (they are still backed up first)",
    )
    parser.add_argument(
        "--source", metavar="DIR", type=Path, default=None,
        help="Install from this mahabharat-agents checkout instead of the bundled data",
    )
    args = parser.parse_args(argv)

    try:
        run_install(
            Path(args.target),
            agents=not args.skills_only,
            skills=not args.agents_only,
            dry_run=args.dry_run,
            data_root=args.source.resolve() if args.source else DATA_ROOT,
            force_replace=args.force_replace,
            skip_skills=args.skip_skill,
        )
    except InstallError as exc:
        print(f"mahabharat-install: error: {exc}", file=sys.stderr)
        sys.exit(1)
    print("\nDone. Verify with scripts/smoke.sh --project <dir> from a checkout.\n")


if __name__ == "__main__":
    install()
