"""M07a / M07d unit tests."""
from __future__ import annotations

from app.agents.hashline_edit import line_hash, parse_hashline_edits, verify_and_apply
from app.workers.goal_pipeline import _topo_levels


def test_topo_levels_diamond() -> None:
    nodes = [
        {"id": "a", "role": "hunter"},
        {"id": "b", "role": "researcher"},
        {"id": "c", "role": "outreach"},
        {"id": "d", "role": "delivery"},
    ]
    edges = [
        {"from": "a", "to": "b"},
        {"from": "a", "to": "c"},
        {"from": "b", "to": "d"},
        {"from": "c", "to": "d"},
    ]
    levels = _topo_levels(nodes, edges)
    assert len(levels) == 3
    assert [n["id"] for n in levels[0]] == ["a"]
    assert sorted(n["id"] for n in levels[1]) == ["b", "c"]
    assert [n["id"] for n in levels[2]] == ["d"]


def test_hashline_verify_and_apply() -> None:
    original = "hello world\nsecond line\n"
    h = line_hash("second line")
    raw = f"src.py\n#L2:{h}\nreplaced line\n"
    edits = parse_hashline_edits(raw)
    assert len(edits) == 1
    updated, audit = verify_and_apply({"src.py": original}, edits)
    assert audit[0]["ok"] is True
    assert "replaced line" in updated["src.py"]
    assert "second line" not in updated["src.py"]


def test_hashline_mismatch() -> None:
    edits = parse_hashline_edits("src.py\n#L1:deadbeef\nnew\n")
    _, audit = verify_and_apply({"src.py": "actual\n"}, edits)
    assert audit[0]["ok"] is False
    assert audit[0]["error"] == "hash_mismatch"
