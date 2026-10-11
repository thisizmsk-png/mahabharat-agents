"""Tests for scripts/frontmatter_loader.py: frontmatter parsing that rejects duplicate keys.

YAML loaders keep the last value of a repeated key without a word, so a second
`tools:` line would silently replace the first. Both the stdlib scanner (used by
scripts/smoke_check.py) and the PyYAML loader (for tests/test_agents.py) must refuse it.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load():
    path = REPO_ROOT / "scripts" / "frontmatter_loader.py"
    spec = importlib.util.spec_from_file_location("frontmatter_loader_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fl = _load()


@pytest.mark.parametrize(
    "fm, dupes",
    [
        ("name: a\ntools: Read\ntools: Write\n", ["tools"]),
        ("name: a\n'name': b\n", ["name"]),
        ('name: a\n"name": b\n', ["name"]),
        ("x-mahabharat:\n  rank: master\n  title: T\n  rank: god\n", ["x-mahabharat.rank"]),
        ("a:\n  b:\n    c: 1\n    c: 2\n", ["a.b.c"]),
        ("items:\n  - k: 1\n    k: 2\n  - k: 3\n", ["items.k"]),
        ("name: a  # first\ndescription: d\nname: b\n", ["name"]),
    ],
)
def test_stdlib_scanner_finds_duplicates(fm, dupes):
    assert fl.duplicate_keys(fm) == dupes
    with pytest.raises(fl.DuplicateKeyError):
        fl.check_no_duplicate_keys(fm)


@pytest.mark.parametrize(
    "fm",
    [
        "name: a\ntools: Read, Grep\n",
        # the same key in different mappings, list items and block scalars is fine
        "a:\n  k: 1\nb:\n  k: 1\nk: 2\n",
        "items:\n- k: 1\n- k: 2\nother:\n  - k: 3\n",
        "tools:\n  - Read\n  - Read\nname: a\n",
        "description: |\n  name: not a key\n  name: still not a key\nname: a\n",
        "description: >-\n  tools: x\n\n  tools: y\ntools: Read\n",
        "# name: commented\nname: a\n",
        'description: "Use when: a; tools: b"\ntools: Read\n',
        "owns: [a, b]\nescalates: {x: human, y: human}\n",
    ],
)
def test_stdlib_scanner_has_no_false_positives(fm):
    assert fl.duplicate_keys(fm) == []
    fl.check_no_duplicate_keys(fm)


def test_split_frontmatter():
    assert fl.split_frontmatter("---\nname: a\n---\nbody\n") == ("name: a", "body\n")
    assert fl.split_frontmatter("---\nname: a\n---") == ("name: a", "")
    assert fl.split_frontmatter("\n---\nname: a\n---\n")[0] is None
    assert fl.split_frontmatter("---\nname: a\n")[0] is None


# ------------------------------------------------------------- PyYAML loader ---

yaml = pytest.importorskip("yaml")


@pytest.mark.parametrize(
    "text",
    [
        "---\nname: a\ntools: Read\ntools: Write\n---\nbody\n",
        "---\nname: a\nx-mahabharat:\n  rank: master\n  rank: god\n---\n",
        "---\nname: a\nescalates: {x: human, x: bhima}\n---\n",  # flow mapping
        "---\nitems:\n  - k: 1\n    k: 2\n---\n",
    ],
)
def test_yaml_loader_rejects_duplicates(text):
    with pytest.raises(fl.DuplicateKeyError, match="duplicate key"):
        fl.load_frontmatter(text)
    # plain safe_load would have accepted it silently -- the reason this loader exists
    assert isinstance(yaml.safe_load(fl.split_frontmatter(text)[0]), dict)


def test_yaml_loader_matches_safe_load_without_duplicates():
    text = "---\nname: a\ntools: Read, Grep\nx-mahabharat:\n  rank: master\n  owns: [x, y]\n---\nBody\n"
    data, body = fl.load_frontmatter(text)
    assert data == yaml.safe_load(fl.split_frontmatter(text)[0])
    assert body == "Body\n"
    assert fl.load_frontmatter("no frontmatter\n") == (None, "no frontmatter\n")
    assert fl.load_frontmatter("---\n- a\n- b\n---\n")[0] is None
    # the loader is a SafeLoader: no arbitrary object construction
    with pytest.raises(yaml.YAMLError):
        fl.load_yaml("!!python/object/apply:os.system ['true']")


def test_repo_frontmatter_has_no_duplicate_keys():
    """Every agent, template and skill file in the repo passes both checks."""
    files = sorted(
        list((REPO_ROOT / "agents").rglob("*.md"))
        + list((REPO_ROOT / "templates").rglob("*.md"))
        + list((REPO_ROOT / "skills").rglob("SKILL.md"))
    )
    checked = 0
    for path in files:
        text = path.read_text(encoding="utf-8")
        fm_text, _ = fl.split_frontmatter(text)
        if fm_text is None:
            continue
        checked += 1
        assert fl.duplicate_keys(fm_text) == [], path
        fl.load_frontmatter(text)
    assert checked > 0
