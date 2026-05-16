"""Computer use policy + runner client wiring."""
from __future__ import annotations

from app.computer_use.orchestrator import computer_use_enabled
from app.integrations.catalog import get_capability
from app.integrations.grants import can_execute_capability


def test_computer_use_disabled_without_tenant_flag() -> None:
    cap = get_capability("computer_use_submit")
    assert cap is not None
    can_run, reason = can_execute_capability({}, cap)
    assert not can_run
    assert reason == "computer_use_disabled"


def test_computer_use_enabled_requires_runner_env(monkeypatch) -> None:
    cap = get_capability("computer_use_submit")
    assert cap is not None
    monkeypatch.setattr("app.integrations.grants.settings.computer_use_runner_url", None)
    monkeypatch.setattr("app.integrations.grants.settings.computer_use_runner_token", None)
    cfg = {"computer_use": {"enabled": True}}
    assert computer_use_enabled(cfg)
    can_run, reason = can_execute_capability(cfg, cap)
    assert not can_run
    assert reason == "missing_server_credentials"


def test_computer_use_enabled_with_runner_env(monkeypatch) -> None:
    cap = get_capability("computer_use_submit")
    assert cap is not None
    monkeypatch.setattr(
        "app.integrations.grants.settings.computer_use_runner_url",
        "http://computer-use-runner:8090",
    )
    monkeypatch.setattr("app.integrations.grants.settings.computer_use_runner_token", "tok")
    cfg = {"computer_use": {"enabled": True}}
    can_run, reason = can_execute_capability(cfg, cap)
    assert can_run
    assert reason == "ok"
