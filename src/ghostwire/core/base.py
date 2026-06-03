"""
GhostWire — Base Module Class
All attack modules inherit from this.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any


class Meta:
    """Module metadata. Override in each module."""
    name: str = "base"
    description: str = "Base module"
    category: str = "core"
    version: str = "1.0.0"
    author: str = "OWL"
    requirements: list = []  # External tool dependencies
    options: Dict[str, Dict] = {}


class BaseModule(ABC):
    """Abstract base for all GhostWire modules."""

    Meta = Meta

    def __init__(self, ctx):
        self.ctx = ctx
        self.logger = ctx.logger
        self.events = ctx.events
        self.session = ctx.session
        self.options: Dict[str, Any] = {}

    def set_option(self, key: str, value: Any):
        self.options[key] = value

    def get_option(self, key: str, default: Any = None) -> Any:
        return self.options.get(key, default)

    def check_requirements(self) -> Dict[str, bool]:
        """Check if all required external tools are available."""
        import subprocess
        results = {}
        for tool in self.Meta.requirements:
            try:
                subprocess.check_call(
                    ["which", tool],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                results[tool] = True
            except:
                results[tool] = False
        return results

    @abstractmethod
    def info(self) -> str:
        """Return module description."""
        pass

    @abstractmethod
    def run(self, **kwargs):
        """Execute the module."""
        pass

    def cleanup(self):
        """Override for cleanup after module execution."""
        pass
