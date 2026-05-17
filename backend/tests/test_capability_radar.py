from app.evolution.capability_radar import list_radar_items, radar_summary


def test_capability_radar_is_ranked_and_actionable() -> None:
    items = list_radar_items()

    assert len(items) >= 5
    assert items[0]["titan_fit_score"] >= items[-1]["titan_fit_score"]
    assert all(item["url"].startswith("https://github.com/") for item in items)
    assert all(item["recommended_action"] for item in items)
    assert any(item["id"] == "github_mcp_server" for item in items)


def test_capability_radar_category_filter() -> None:
    items = list_radar_items(category="mcp")

    assert items
    assert all("mcp" in item["category"] for item in items)


def test_capability_radar_summary_has_principles() -> None:
    summary = radar_summary()

    assert summary["version"] == "2026-05-17"
    assert summary["category"] == "all"
    assert summary["item_count"] >= 5
    assert summary["integration_principles"]


def test_capability_radar_summary_matches_category_filter() -> None:
    items = list_radar_items(category="workflow")
    summary = radar_summary(category="workflow")

    assert summary["category"] == "workflow"
    assert summary["item_count"] == len(items)
    assert summary["top_recommendations"] == items[:3]
