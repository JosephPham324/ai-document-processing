"""Base class and interface for typed agent tools."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class BaseTool(ABC):
    """Abstract base class for all allowlisted tools."""

    name: str
    description: str
    input_schema: type[BaseModel]
    output_schema: type[BaseModel]

    @abstractmethod
    async def run(self, args: Any) -> BaseModel:
        """Executes tool logic against validated input arguments."""
        pass
