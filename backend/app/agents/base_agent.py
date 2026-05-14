from __future__ import annotations

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

    def __init__(self, agent_id: str, tenant_id: str, current_prompt: str = "") -> None:
        self.agent_id = agent_id
        self.tenant_id = tenant_id
        self.current_prompt = current_prompt

    async def get_enhanced_prompt(self, task: TaskStub) -> str:
        """Return base prompt enriched with memories + skills if DB is available."""
        try:
            from app.core.database import AsyncSessionLocal
            from app.memory.prompt_builder import build_enhanced_prompt

            task_context = str(task.input)[:300]
            async with AsyncSessionLocal() as db:
                return await build_enhanced_prompt(
                    base_prompt=self.current_prompt,
                    agent_role=self.role,
                    tenant_id=self.tenant_id,
                    agent_id=self.agent_id,
                    task_type=task.type,
                    task_context=task_context,
                    db=db,
                )
        except Exception:
            return self.current_prompt

    @abstractmethod
    async def run(self, task: TaskStub) -> TaskResult:
        """Execute one task and return structured output."""
