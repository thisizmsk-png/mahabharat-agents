"""CLI entry point for mahabharat-agents installation."""

import argparse
import shutil
import sys
from pathlib import Path


PACKAGE_ROOT = Path(__file__).parent.parent.parent


def get_source_dirs():
    """Get source directories relative to package root."""
    return {
        "agents/masters": "agents",
        "agents/sepoys": "agents/sepoys",
        "skills/shared": "skills",
        "skills/role-specific": "skills",
        "orchestration/topologies": "orchestration/topologies",
        "orchestration/workflows": "orchestration/workflows",
        "orchestration/guardrails": "orchestration/guardrails",
        "context/shruti": "context/shruti",
        "context/smriti": "context/smriti",
        "context/itihasa": "context/itihasa",
    }


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
        agents_src = PACKAGE_ROOT / "agents" / "masters"
        agents_dst = claude_dir / "agents"
        agents_dst.mkdir(parents=True, exist_ok=True)

        count = 0
        for f in sorted(agents_src.glob("*.md")):
            shutil.copy2(f, agents_dst / f.name)
            count += 1
        print(f"  Installed {count} master agents")

        # Sepoys
        sepoys_src = PACKAGE_ROOT / "agents" / "sepoys"
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
            skills_src = PACKAGE_ROOT / "skills" / skill_type
            if not skills_src.is_dir():
                continue
            for skill_dir in sorted(skills_src.iterdir()):
                if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                    dst = claude_dir / "skills" / skill_dir.name
                    dst.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(skill_dir / "SKILL.md", dst / "SKILL.md")
        print(f"  Installed 13 skills (7 shared + 6 role-specific)")

    # Install orchestration
    if not args.agents_only and not args.skills_only:
        for sub in ["topologies", "workflows", "guardrails"]:
            src = PACKAGE_ROOT / "orchestration" / sub
            dst = claude_dir / "orchestration" / sub
            dst.mkdir(parents=True, exist_ok=True)
            for f in sorted(src.iterdir()):
                if f.is_file():
                    shutil.copy2(f, dst / f.name)
        print(f"  Installed orchestration configs")

        # Context
        for tier in ["shruti", "smriti", "itihasa"]:
            src = PACKAGE_ROOT / "context" / tier
            dst = claude_dir / "context" / tier
            dst.mkdir(parents=True, exist_ok=True)
            for f in sorted(src.iterdir()):
                if f.is_file():
                    shutil.copy2(f, dst / f.name)
        print(f"  Installed context tiers (Shruti/Smriti/Itihasa)")

    print(f"\nDone! Jai Shri Krishna!\n")


if __name__ == "__main__":
    install()
