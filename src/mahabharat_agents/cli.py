"""CLI entry point for mahabharat-agents installation."""

import argparse
import shutil
import sys
from pathlib import Path


# When installed via pip, data files are bundled under mahabharat_agents/data/
# When running from source, fall back to the repo root
_BUNDLED_DATA = Path(__file__).parent / "data"
_REPO_ROOT = Path(__file__).parent.parent.parent

DATA_ROOT = _BUNDLED_DATA if _BUNDLED_DATA.is_dir() else _REPO_ROOT


def install():
    """Install mahabharat-agents into a target project."""
    parser = argparse.ArgumentParser(
        description="Install Mahabharat Agents into a project"
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Target project directory (default: current directory)",
    )
    parser.add_argument(
        "--agents-only",
        action="store_true",
        help="Install only agent definitions",
    )
    parser.add_argument(
        "--skills-only",
        action="store_true",
        help="Install only skills",
    )
    args = parser.parse_args()

    target = Path(args.target).resolve()
    if not target.is_dir():
        print(f"Error: '{target}' is not a directory.")
        sys.exit(1)

    claude_dir = target / ".claude"
    print(f"\nInstalling Mahabharat Agents to {target}/.claude/\n")

    # Install agents
    if not args.skills_only:
        agents_src = DATA_ROOT / "agents" / "masters"
        agents_dst = claude_dir / "agents"
        agents_dst.mkdir(parents=True, exist_ok=True)

        count = 0
        for f in sorted(agents_src.glob("*.md")):
            shutil.copy2(f, agents_dst / f.name)
            count += 1
        print(f"  Installed {count} master agents")

        # Sepoys
        sepoys_src = DATA_ROOT / "agents" / "sepoys"
        sepoys_dst = claude_dir / "agents" / "sepoys"
        sepoys_dst.mkdir(parents=True, exist_ok=True)
        if (sepoys_src / "_template.md").exists():
            shutil.copy2(sepoys_src / "_template.md", sepoys_dst / "_template.md")
        examples_src = sepoys_src / "examples"
        if examples_src.is_dir():
            for f in sorted(examples_src.glob("*.md")):
                shutil.copy2(f, sepoys_dst / f.name)
            print(f"  Installed sepoy template + examples")

    # Install skills
    if not args.agents_only:
        for skill_type in ["shared", "role-specific"]:
            skills_src = DATA_ROOT / "skills" / skill_type
            if not skills_src.is_dir():
                continue
            for skill_dir in sorted(skills_src.iterdir()):
                if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                    dst = claude_dir / "skills" / skill_dir.name
                    dst.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(skill_dir / "SKILL.md", dst / "SKILL.md")
        print(f"  Installed skills (shared + role-specific)")

    # Install orchestration + context
    if not args.agents_only and not args.skills_only:
        for sub in ["topologies", "workflows", "guardrails"]:
            src = DATA_ROOT / "orchestration" / sub
            dst = claude_dir / "orchestration" / sub
            dst.mkdir(parents=True, exist_ok=True)
            for f in sorted(src.iterdir()):
                if f.is_file():
                    shutil.copy2(f, dst / f.name)
        print(f"  Installed orchestration configs")

        # Context
        for tier in ["shruti", "smriti", "itihasa"]:
            src = DATA_ROOT / "context" / tier
            dst = claude_dir / "context" / tier
            dst.mkdir(parents=True, exist_ok=True)
            for f in sorted(src.iterdir()):
                if f.is_file():
                    shutil.copy2(f, dst / f.name)
        print(f"  Installed context tiers (Shruti/Smriti/Itihasa)")

    print(f"\nDone! Jai Shri Krishna!\n")


if __name__ == "__main__":
    install()
