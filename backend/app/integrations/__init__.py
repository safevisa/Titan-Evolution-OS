"""External capability catalog, tenant grants, and execution router for agents."""

from app.integrations.catalog import CAPABILITIES, get_capability
from app.integrations.executor import execute_capability

__all__ = ["CAPABILITIES", "execute_capability", "get_capability"]
