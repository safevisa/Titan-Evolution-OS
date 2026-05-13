from app.industry_plugins.base_plugin import (
    AgentConfig,
    IndustryPlugin,
    KPIDefinition,
    PluginSkillDoc,
    WorkflowTemplate,
)


class PaymentFintechPlugin(IndustryPlugin):
    @property
    def plugin_id(self) -> str:
        return "payment_fintech"

    @property
    def display_name(self) -> str:
        return "Payment & Fintech"

    def get_agent_configs(self) -> list[AgentConfig]:
        return []

    def get_workflow_templates(self) -> list[WorkflowTemplate]:
        return []

    def get_default_skills(self) -> list[PluginSkillDoc]:
        return []

    def get_kpi_definition(self) -> KPIDefinition:
        return KPIDefinition(formula="default")

    def get_required_tools(self) -> list[str]:
        return ["apollo", "resend", "airtable"]
