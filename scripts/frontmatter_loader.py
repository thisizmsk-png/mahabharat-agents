"""Shared frontmatter loader that rejects duplicate YAML keys. Stdlib only.

YAML loaders (PyYAML's safe_load, and most others) silently keep the *last* value of a
duplicated key, so an agent file with two ``tools:`` lines passes review showing one
tool list while Claude Code may load the other. Every reader of agent and skill
frontmatter in this repo should go through this module so a duplicate key is an error,
never a silent override.

Two entry points:

* ``duplicate_keys(fm_text)`` -- stdlib only, used by ``scripts/smoke_check.py`` (which
  runs under ``python3 -I`` with no third-party packages). It scans block-style YAML
  by indentation and reports every key that appears twice in the same mapping,
  including nested mappings and mappings inside list items. Block scalars (``|``/``>``)
  are skipped. Flow mappings on one line (``{a: 1, a: 2}``) are not inspected; the
  PyYAML loader below catches those.
* ``load_frontmatter(text)`` -- full YAML parse with PyYAML (imported lazily), using a
  SafeLoader subclass that raises ``DuplicateKeyError`` for a duplicate key at any
  level, flow mappings included. ``tests/test_agents.py`` can switch to it.

Load this file by path (``importlib.util.spec_from_file_location``) or put ``scripts/``
on ``sys.path``; it has no package.
"""

from __future__ import annotations

import re

__all__ = [
    "DuplicateKeyError",
    "split_frontmatter",
    "duplicate_keys",
    "check_no_duplicate_keys",
    "unique_key_loader",
    "load_yaml",
    "load_frontmatter",
]


class DuplicateKeyError(ValueError):
    """A YAML mapping defines the same key more than once."""


def split_frontmatter(text: str) -> tuple[str | None, str]:
    """Return (frontmatter_yaml, body). Frontmatter must start on line 1 with ``---``."""
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---\n", 4)
    if end == -1:
        if text.endswith("\n---"):
            return text[4:-4], ""
        return None, text
    return text[4:end], text[end + 5:]


# `key:` (plain, or single/double quoted), optionally after a `- ` list-item marker.
_KEY_LINE = re.compile(
    r"""^(?P<indent>[ ]*)(?P<dash>-[ ]+)?"""
    r"""(?P<key>"(?:[^"\\]|\\.)*"|'(?:[^']|'')*'|[^\s#'"\-?:{}\[\],&*!|>%@`][^#]*?|-[^\s][^#]*?)"""
    r"""[ ]*:(?:[ ]+(?P<value>.*))?$"""
)
_LIST_ITEM = re.compile(r"^(?P<indent>[ ]*)-(?:[ ]|$)")
_BLOCK_SCALAR = re.compile(r"^[|>][0-9+-]*\s*(?:#.*)?$")


def _unquote(key: str) -> str:
    key = key.strip()
    if len(key) >= 2 and key[0] == key[-1] and key[0] in "\"'":
        inner = key[1:-1]
        return inner.replace("''", "'") if key[0] == "'" else inner.replace('\\"', '"')
    return key


def duplicate_keys(fm_text: str) -> list[str]:
    """Duplicate keys in block-style YAML, as dotted paths (``tools``, ``x-mahabharat.rank``).

    Stdlib only; see the module docstring for what it does and does not inspect.
    """
    dupes: list[str] = []
    # Stack of open mappings: (column of their keys, keys seen, dotted path of the mapping).
    stack: list[tuple[int, set[str], str]] = []
    last_key: tuple[int, str] | None = None  # (column, dotted path) of the previous key line
    block_indent: int | None = None  # inside a block scalar owned by a key at this column

    for raw in fm_text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        if block_indent is not None:
            if indent > block_indent:
                continue
            block_indent = None

        m = _KEY_LINE.match(raw)
        if not m:
            li = _LIST_ITEM.match(raw)
            if li:  # a scalar list item: it closes deeper mappings, opens none
                col = len(li.group("indent"))
                while stack and stack[-1][0] > col:
                    stack.pop()
            continue

        col = len(m.group("indent"))
        if m.group("dash"):
            col += len(m.group("dash"))
            # A new list item starts a new mapping: siblings from the previous item close.
            while stack and stack[-1][0] >= col:
                stack.pop()
        else:
            while stack and stack[-1][0] > col:
                stack.pop()

        key = _unquote(m.group("key"))
        if stack and stack[-1][0] == col and not m.group("dash"):
            _, seen, path = stack[-1]
        else:
            # A deeper mapping opens under the previous key (or a list item of it).
            parent = last_key[1] if last_key and last_key[0] < col else (stack[-1][2] if stack else "")
            seen, path = set(), parent
            stack.append((col, seen, path))
        full = f"{path}.{key}" if path else key
        if key in seen:
            dupes.append(full)
        seen.add(key)
        last_key = (col, full)

        value = (m.group("value") or "").strip()
        if _BLOCK_SCALAR.match(value):
            block_indent = col
    return dupes


def check_no_duplicate_keys(fm_text: str, where: str = "frontmatter") -> None:
    """Raise DuplicateKeyError if ``fm_text`` repeats a key (stdlib scan)."""
    dupes = duplicate_keys(fm_text)
    if dupes:
        raise DuplicateKeyError(f"{where}: duplicate key(s) {sorted(set(dupes))}")


_LOADER = None


def unique_key_loader():
    """A PyYAML SafeLoader subclass that raises DuplicateKeyError on a repeated key."""
    global _LOADER
    if _LOADER is not None:
        return _LOADER
    import yaml  # lazy: smoke_check.py must work without PyYAML

    class UniqueKeySafeLoader(yaml.SafeLoader):
        pass

    def construct_mapping(loader, node, deep=False):
        loader.flatten_mapping(node)
        seen = set()
        for key_node, _ in node.value:
            key = loader.construct_object(key_node, deep=True)
            try:
                hash(key)
            except TypeError:
                continue  # PyYAML reports unhashable keys itself
            if key in seen:
                mark = key_node.start_mark
                raise DuplicateKeyError(
                    f"duplicate key {key!r} at line {mark.line + 1}, column {mark.column + 1}"
                )
            seen.add(key)
        return yaml.SafeLoader.construct_mapping(loader, node, deep=deep)

    UniqueKeySafeLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping
    )
    _LOADER = UniqueKeySafeLoader
    return _LOADER


def load_yaml(text: str):
    """``yaml.safe_load`` that raises DuplicateKeyError on a repeated key at any level."""
    import yaml

    return yaml.load(text, Loader=unique_key_loader())  # noqa: S506 -- a SafeLoader subclass


def load_frontmatter(text: str) -> tuple[dict | None, str]:
    """Return (frontmatter mapping or None, body); DuplicateKeyError on a repeated key.

    Returns None for the mapping when there is no frontmatter on line 1 or it is not a
    mapping. YAML syntax errors propagate as ``yaml.YAMLError``.
    """
    fm_text, body = split_frontmatter(text)
    if fm_text is None:
        return None, body
    data = load_yaml(fm_text)
    return (data if isinstance(data, dict) else None), body
