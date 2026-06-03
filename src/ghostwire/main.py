"""
GhostWire — Main Entry Point
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from ghostwire.core import Context
from ghostwire.cli.shell import run_cli


def main():
    ctx = Context()

    if not os.geteuid() == 0:
        ctx.logger.error("GhostWire requires root privileges. Run with sudo.")
        sys.exit(1)

    ctx.logger.info(f"GhostWire v1.0.0 — Wireless Exploitation Framework")
    ctx.logger.info(f"Loaded {len(ctx.loader.modules)} modules")

    if len(sys.argv) > 1:
        # CLI mode
        from ghostwire.cli.shell import GhostWireShell
        shell = GhostWireShell(ctx)
        command = " ".join(sys.argv[1:])
        shell.onecmd(command)
    else:
        # Interactive mode
        run_cli(ctx)


if __name__ == "__main__":
    main()
