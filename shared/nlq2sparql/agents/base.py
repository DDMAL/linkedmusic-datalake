"""Base agent interfaces and shared dataclasses."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import logging


@dataclass
class AgentConfig:
    settings: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.settings.get(key, default)


class BaseAgent(ABC):
    name: str = "base"

    def __init__(self, config: Optional[AgentConfig] = None, logger: Optional[logging.Logger] = None):
        self.config = config or AgentConfig()
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def run(self, **kwargs) -> Any:  # pragma: no cover
        raise NotImplementedError


__all__ = ["AgentConfig", "BaseAgent"]
