from app.agents.discipline_harness import (
    intent_gate_heuristic,
    max_tool_rounds_for_mode,
    resolve_harness_mode,
    role_category,
)


def test_ultrawork_mode_from_input():
    assert resolve_harness_mode({"ultrawork": True}, None) == "ultrawork"
    assert max_tool_rounds_for_mode("ultrawork") == 8


def test_intent_gate_strips_prefix():
    out = intent_gate_heuristic("Please help me research payment APIs in MENA")
    assert "research" in out["true_intent"].lower() or "payment" in out["true_intent"].lower()


def test_role_category_manager():
    assert role_category("manager") == "orchestrate"
