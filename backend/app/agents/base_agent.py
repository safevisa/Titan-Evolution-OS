from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class TaskStub:
    id: str
    type: str
    input: dict[str, Any]


@dataclass
class TaskResult:
    output: dict[str, Any]
    token_used: int = 0


class BaseAgent(ABC):
    role: str = "base"

    def __init__(self, agent_id: str, tenant_id: str) -> None:
        self.agent_id = agent_id
        self.tenant_id = tenant_id

    @abstractmethod
    async def run(self, task: TaskStub) -> TaskResult:
        """Execute one task and return structured output."""
