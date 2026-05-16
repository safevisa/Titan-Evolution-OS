"""Hashline-style verifiable line edits (omo-inspired, M07d).

Format: ``path#L<line>:<sha256-prefix-8>`` followed by replacement content block.
Verifies the line hash before applying to prevent stale edits.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any

_HASHLINE_RE = re.compile(
    r"^#L(?P<line>\d+):(?P<hash>[0-9a-fA-F]{8})\s*$",
    re.MULTILINE,
)

_CODE_TASK_TYPES = frozenset(
    {
        "code_patch",
        "refactor",
        "bug_fix",
        "github_create_pr",
        "gitlab_create_mr",
    }
)


def line_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]


@dataclass
class HashlineEdit:
    path: str
    line_no: int
    expected_hash: str
    new_content: str


def parse_hashline_edits(raw: str) -> list[HashlineEdit]:
    """Parse edits from agent output text or artifacts.hashline_edits string."""
    edits: list[HashlineEdit] = []
    if not raw or not isinstance(raw, str):
        return edits

    blocks = re.split(r"\n---\n", raw.strip())
    for block in blocks:
        lines = block.strip().splitlines()
        if len(lines) < 2:
            continue
        path = lines[0].strip()
        if not path or path.startswith("#"):
            continue
        header = lines[1].strip()
        m = _HASHLINE_RE.match(header) or re.match(
            r"#L(?P<line>\d+):(?P<hash>[0-9a-fA-F]{8})",
            header,
        )
        if not m:
            continue
        new_content = "\n".join(lines[2:])
        edits.append(
            HashlineEdit(
                path=path,
                line_no=int(m.group("line")),
                expected_hash=m.group("hash").lower(),
                new_content=new_content,
            )
        )
    return edits


def verify_and_apply(
    file_contents: dict[str, str],
    edits: list[HashlineEdit],
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    """Apply edits in memory; return updated files + per-edit audit rows."""
    files = dict(file_contents)
    audit: list[dict[str, Any]] = []

    for edit in edits:
        content = files.get(edit.path)
        if content is None:
            audit.append(
                {
                    "path": edit.path,
                    "line": edit.line_no,
                    "ok": False,
                    "error": "file_not_found",
                }
            )
            continue
        lines = content.splitlines(keepends=True)
        if edit.line_no < 1 or edit.line_no > len(lines):
            audit.append(
                {
                    "path": edit.path,
                    "line": edit.line_no,
                    "ok": False,
                    "error": "line_out_of_range",
                }
            )
            continue
        current = lines[edit.line_no - 1].rstrip("\n\r")
        actual = line_hash(current)
        if actual != edit.expected_hash.lower():
            audit.append(
                {
                    "path": edit.path,
                    "line": edit.line_no,
                    "ok": False,
                    "error": "hash_mismatch",
                    "expected": edit.expected_hash,
                    "actual": actual,
                    "current_line": current[:200],
                }
            )
            continue
        replacement = edit.new_content
        if not replacement.endswith("\n"):
            replacement += "\n"
        lines[edit.line_no - 1] = replacement
        files[edit.path] = "".join(lines)
        audit.append({"path": edit.path, "line": edit.line_no, "ok": True})

    return files, audit


def format_hashline_prompt_snippet() -> str:
    return (
        "For code file edits, prefer hashline format:\n"
        "path/to/file.py\n"
        "#L42:abcd1234\n"
        "replacement line content\n"
        "---\n"
        "Hash is first 8 hex chars of SHA256 of the original line (no newline)."
    )


def is_code_task(task_type: str) -> bool:
    tt = (task_type or "").strip().lower()
    if tt in _CODE_TASK_TYPES:
        return True
    return any(k in tt for k in ("code", "patch", "refactor", "fix", "pr", "mr"))
