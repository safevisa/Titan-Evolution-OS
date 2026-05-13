from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class AgentConfig:
    role: str
    name: str
    default_prompt: str


@dataclass
class WorkflowTemplate:
    name: str
    dag_config: dict[str, Any]


@dataclass
class PluginSkillDoc:
    name: str
    content_md: str
    role_tags: list[str]


@dataclass
class KPIDefinition:
    formula: str


class IndustryPlugin(ABC):
    """Industry extension point — core must not import concrete plugins."""

    @property
    @abstractmethod
    def plugin_id(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def display_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_agent_configs(self) -> list[AgentConfig]:
        raise NotImplementedError

    @abstractmethod
    def get_workflow_templates(self) -> list[WorkflowTemplate]:
        raise NotImplementedError

    @abstractmethod
    def get_default_skills(self) -> list[PluginSkillDoc]:
        raise NotImplementedError

    @abstractmethod
    def get_kpi_definition(self) -> KPIDefinition:
        raise NotImplementedError

    @abstractmethod
    def get_required_tools(self) -> list[str]:
        raise NotImplementedError

    def get_custom_ui_config(self) -> dict[str, Any]:
        return {}
