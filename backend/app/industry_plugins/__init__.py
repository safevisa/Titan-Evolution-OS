"""Plugin registry — maps plugin_id → IndustryPlugin instance."""
from __future__ import annotations

from app.industry_data.catalog_sectors import INDUSTRY_CATALOG
from app.industry_plugins.base_plugin import IndustryPlugin
from app.industry_plugins.catalog_plugin import CatalogIndustryPlugin
from app.industry_plugins.payment_fintech.plugin import PaymentFintechPlugin
from app.industry_plugins.saas_b2b.plugin import SaasB2BPlugin

_BASE_PLUGINS: list[IndustryPlugin] = [
    PaymentFintechPlugin(),
    SaasB2BPlugin(),
]

_CATALOG_PLUGINS: list[IndustryPlugin] = [CatalogIndustryPlugin(row) for row in INDUSTRY_CATALOG]

_REGISTRY: dict[str, IndustryPlugin] = {}
for p in _BASE_PLUGINS + _CATALOG_PLUGINS:
    if p.plugin_id in _REGISTRY:
        raise RuntimeError(f"Duplicate industry plugin_id: {p.plugin_id}")
    _REGISTRY[p.plugin_id] = p


def get_plugin(plugin_id: str) -> IndustryPlugin | None:
    return _REGISTRY.get(plugin_id)


def list_plugins() -> list[dict]:
    plugins = list(_REGISTRY.values())
    plugins.sort(
        key=lambda p: (
            0 if p.plugin_id in ("payment_fintech", "saas_b2b") else 1,
            p.display_name.lower(),
        )
    )
    out: list[dict] = []
    for p in plugins:
        ui = p.get_custom_ui_config()
        entry = {
            "plugin_id": p.plugin_id,
            "display_name": p.display_name,
            "required_tools": p.get_required_tools(),
            "agent_roles": [a.role for a in p.get_agent_configs()],
            "name_zh": ui.get("name_zh", ""),
            "icon": ui.get("icon", ""),
            "catalog": bool(ui.get("catalog", False)),
        }
        out.append(entry)
    return out
