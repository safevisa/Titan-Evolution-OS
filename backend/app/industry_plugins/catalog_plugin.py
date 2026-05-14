"""Dynamically built industry plugin — full corporate roster + sector label."""
from __future__ import annotations

from typing import Any

from app.industry_data.catalog_sectors import IndustryRow
from app.industry_data.enterprise_roster import (
    default_sector_kpi,
    get_corporate_agent_configs,
    get_corporate_skills,
    get_default_gtm_workflow,
)
from app.industry_plugins.base_plugin import (
    AgentConfig,
    IndustryPlugin,
    KPIDefinition,
    PluginSkillDoc,
    WorkflowTemplate,
)


class CatalogIndustryPlugin(IndustryPlugin):
    """One plugin per global sector row; shares enterprise workforce + skills."""

    def __init__(self, row: IndustryRow) -> None:
        self._row = row

    @property
    def plugin_id(self) -> str:
        return self._row["id"]

    @property
    def display_name(self) -> str:
        return self._row["name_en"]

    def get_agent_configs(self) -> list[AgentConfig]:
        return get_corporate_agent_configs()

    def get_workflow_templates(self) -> list[WorkflowTemplate]:
        return get_default_gtm_workflow()

    def get_default_skills(self) -> list[PluginSkillDoc]:
        skills = get_corporate_skills()
        sector = self._row["name_en"]
        zh = self._row["name_zh"]
        extra = PluginSkillDoc(
            name=f"Sector context — {sector}",
            content_md=(
                f"# Industry context: {sector} ({zh})\n\n"
                "When reasoning, prefer regulations, buyer personas, and KPI norms "
                f"typical for **{sector}**. Call out region-specific compliance only when "
                "the user specifies a geography."
            ),
            role_tags=[
                "strategy_director",
                "compliance_officer",
                "product_marketing_manager",
                "risk_manager",
                "manager",
            ],
        )
        return [extra, *skills]

    def get_kpi_definition(self) -> KPIDefinition:
        return default_sector_kpi(self._row["id"])

    def get_required_tools(self) -> list[str]:
        return []

    def get_custom_ui_config(self) -> dict[str, Any]:
        return {
            "catalog": True,
            "icon": self._row.get("icon", "🏢"),
            "name_zh": self._row.get("name_zh", ""),
        }
