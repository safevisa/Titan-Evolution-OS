from app.agents.base_agent import BaseAgent, TaskResult, TaskStub


class OutreachAgent(BaseAgent):
    role = "outreach"

    async def run(self, task: TaskStub) -> TaskResult:
        return TaskResult(output={}, token_used=0)
