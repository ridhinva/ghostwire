"""
GhostWire Core — Module Loader, Session Manager, Event System
"""

import os
import sys
import json
import time
import importlib
import pkgutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable


class EventBus:
    """Simple pub/sub event system for inter-module communication."""

    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}

    def on(self, event: str, handler: Callable):
        self._handlers.setdefault(event, []).append(handler)

    def emit(self, event: str, **kwargs):
        for handler in self._handlers.get(event, []):
            try:
                handler(**kwargs)
            except Exception as e:
                pass  # Don't let event handlers crash the framework

    def off(self, event: str, handler: Callable = None):
        if handler is None:
            self._handlers.pop(event, None)
        else:
            self._handlers.get(event, []).remove(handler)


class Logger:
    """Structured logger with file and console output."""

    COLORS = {
        "INFO": "\033[36m",     # Cyan
        "WARN": "\033[33m",     # Yellow
        "ERROR": "\033[31m",    # Red
        "SUCCESS": "\033[32m",  # Green
        "DEBUG": "\033[35m",    # Magenta
        "RESET": "\033[0m",
    }

    def __init__(self, log_dir: Path = None):
        self.log_dir = log_dir or Path("/root/ghostwire/logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / f"ghostwire_{datetime.now().strftime('%Y%m%d')}.log"

    def _write(self, level: str, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        color = self.COLORS.get(level, "")
        reset = self.COLORS["RESET"]
        line = f"[{ts}] [{level:8s}] {msg}"
        print(f"{color}{line}{reset}")
        with open(self.log_file, "a") as f:
            f.write(line + "\n")

    def info(self, msg): self._write("INFO", msg)
    def warn(self, msg): self._write("WARN", msg)
    def error(self, msg): self._write("ERROR", msg)
    def success(self, msg): self._write("SUCCESS", msg)
    def debug(self, msg): self._write("DEBUG", msg)


class Session:
    """Manages the current attack session state."""

    def __init__(self):
        self.id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.started = datetime.now().isoformat()
        self.module: Optional[str] = None
        self.options: Dict[str, Any] = {}
        self.results: List[Dict] = []
        self.target: Optional[str] = None
        self.iface: Optional[str] = None
        self.running = False

    def set_option(self, key: str, value: Any):
        self.options[key] = value

    def get_option(self, key: str, default: Any = None) -> Any:
        return self.options.get(key, default)

    def add_result(self, result: Dict):
        result["timestamp"] = datetime.now().isoformat()
        self.results.append(result)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "started": self.started,
            "module": self.module,
            "options": self.options,
            "results_count": len(self.results),
            "target": self.target,
            "iface": self.iface,
        }

    def save(self, path: Path = None):
        path = path or Path(f"/root/ghostwire/sessions/session_{self.id}.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)


class ModuleLoader:
    """Dynamically loads attack modules from ghostwire.wifi, ghostwire.bt, etc."""

    def __init__(self):
        self.modules: Dict[str, Dict] = {}
        self._discover()

    def _discover(self):
        """Auto-discover all modules in ghostwire.wifi, ghostwire.bt, ghostwire.saer."""
        import ghostwire
        for pkg_name in ["wifi", "bt", "saer"]:
            try:
                pkg = importlib.import_module(f"ghostwire.{pkg_name}")
                pkg_path = Path(pkg.__file__).parent
                for _, modname, _ in pkgutil.iter_modules([str(pkg_path)]):
                    full_name = f"{pkg_name}/{modname}"
                    self.modules[full_name] = {
                        "package": pkg_name,
                        "module": modname,
                        "path": f"ghostwire.{pkg_name}.{modname}",
                        "loaded": False,
                        "instance": None,
                    }
            except ImportError:
                pass

    def list_modules(self, category: str = None) -> List[str]:
        if category:
            return [k for k in self.modules if k.startswith(f"{category}/")]
        return list(self.modules.keys())

    def get_module(self, name: str) -> Optional[object]:
        """Load and return a module instance."""
        info = self.modules.get(name)
        if not info:
            return None
        if not info["loaded"]:
            try:
                mod = importlib.import_module(info["path"])
                info["loaded"] = True
                info["instance"] = mod
            except ImportError as e:
                return None
        return info["instance"]

    def get_module_info(self, name: str) -> Optional[Dict]:
        mod = self.get_module(name)
        if mod and hasattr(mod, "Meta"):
            return getattr(mod, "Meta")
        return None


class Config:
    """Global configuration manager."""

    DEFAULTS = {
        "wifi_iface": None,
        "bt_iface": None,
        "output_dir": "/root/ghostwire/output",
        "log_dir": "/root/ghostwire/logs",
        "session_dir": "/root/ghostwire/sessions",
        "wordlist": "/usr/share/wordlists/rockyou.txt",
        "timeout": 30,
        "verbose": False,
        "color": True,
    }

    def __init__(self):
        self.values = dict(self.DEFAULTS)
        self._load_system_info()

    def _load_system_info(self):
        """Auto-detect system capabilities."""
        import subprocess
        # Detect wireless interface
        try:
            out = subprocess.check_output(
                "iw dev 2>/dev/null | grep Interface | awk '{print $2}' | head -1",
                shell=True, text=True
            ).strip()
            if out:
                self.values["wifi_iface"] = out
        except:
            pass

        # Detect BT interface
        try:
            out = subprocess.check_output(
                "hcitool dev 2>/dev/null | awk 'NR>1{print $2}' | head -1",
                shell=True, text=True
            ).strip()
            if out:
                self.values["bt_iface"] = out
        except:
            pass

    def get(self, key: str, default=None):
        return self.values.get(key, default)

    def set(self, key: str, value):
        self.values[key] = value


class Context:
    """Global context — singleton holding all framework state."""

    def __init__(self):
        self.config = Config()
        self.logger = Logger(Path(self.config.get("log_dir")))
        self.events = EventBus()
        self.session = Session()
        self.loader = ModuleLoader()
        self.running = True

    def new_session(self):
        self.session = Session()
        self.events.emit("session_new", session=self.session)
