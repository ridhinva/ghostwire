"""
GhostWire — Interactive CLI Shell
Command-line interface for the wireless exploitation framework.
"""

import os
import sys
import cmd
import shlex
import importlib
from pathlib import Path
from datetime import datetime


class GhostWireShell(cmd.Cmd):
    """Interactive shell for GhostWire framework."""

    intro = r"""
   ╔══════════════════════════════════════════════════════╗
   ║                                                      ║
   ║   ██████╗ ██╗  ██╗ ██████╗ ███████╗████████╗██╗    ██╗██╗██████╗ ███████╗  ║
   ║  ██╔════╝ ██║  ██║██╔═══██╗██╔════╝╚══██╔══╝██║    ██║██║██╔══██╗██╔════╝  ║
   ║  ██║  ███╗███████║██║   ██║███████╗   ██║   ██║ █╗ ██║██║██████╔╝█████╗    ║
   ║  ██║   ██║██╔══██║██║   ██║╚════██║   ██║   ██║███╗██║██║██╔══██╗██╔══╝    ║
   ║  ╚██████╔╝██║  ██║╚██████╔╝███████║   ██║   ██║╚███╔███╔╝██║██║  ██║███████║  ║
   ║   ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝   ╚═╝ ╚══╝╚══╝ ╚═╝╚═╝  ╚═╝╚══════╝  ║
   ║                                                      ║
   ║   Modular Wireless Exploitation Framework v1.0       ║
   ║   WiFi 6E (802.11ax) + Bluetooth 5.2                 ║
   ║   Built for Flipper One / RK3576 platforms           ║
   ║                                                      ║
   ╚══════════════════════════════════════════════════════╝

   Type 'help' for commands. Type 'modules' to list attack modules.
   Use 'quit' or Ctrl+D to exit.
"""

    prompt = "ghostwire> "

    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.logger = ctx.logger
        self.current_module = None
        self.module_instance = None

    # ─── Core Commands ────────────────────────────────────────────────────

    def do_modules(self, arg):
        """List all available attack modules. Usage: modules [wifi|bt|saer]"""
        category = arg.strip() or None
        modules = self.ctx.loader.list_modules(category)

        if not modules:
            self.logger.warn("No modules found")
            return

        current_cat = None
        for name in sorted(modules):
            cat = name.split("/")[0]
            if cat != current_cat:
                current_cat = cat
                self.logger.info(f"\n[{cat.upper()}]")
            info = self.ctx.loader.get_module_info(name)
            desc = info.get("description", "?") if info else "?"
            reqs = info.get("requirements", []) if info else []
            req_str = f" (needs: {', '.join(reqs)})" if reqs else ""
            print(f"  {name:25s} {desc}{req_str}")

    def do_use(self, arg):
        """Load a module. Usage: use <category/module>"""
        if not arg:
            self.logger.error("Usage: use <category/module>")
            return

        name = arg.strip()
        mod = self.ctx.loader.get_module(name)
        if not mod:
            self.logger.error(f"Module not found: {name}")
            return

        self.current_module = name
        self.module_instance = mod.Module(self.ctx)
        self.prompt = f"ghostwire({name})> "
        self.logger.success(f"Loaded: {name}")
        self.logger.info(self.module_instance.info())

    def do_info(self, arg):
        """Show current module info and options."""
        if not self.module_instance:
            self.logger.warn("No module loaded. Use 'use <module>' first.")
            return

        meta = self.module_instance.Meta
        self.logger.info(f"Module: {meta.name}")
        self.logger.info(f"Description: {meta.description}")
        self.logger.info(f"Category: {meta.category}")
        self.logger.info(f"Version: {meta.version}")

        if meta.options:
            self.logger.info("Options:")
            for opt_name, opt_meta in meta.options.items():
                req = " [REQUIRED]" if opt_meta.get("required") else ""
                default = opt_meta.get("default", "None")
                desc = opt_meta.get("description", "")
                current = self.module_instance.get_option(opt_name)
                val = current if current is not None else default
                print(f"  {opt_name:15s} = {val!s:20s} {desc}{req}")

        # Check requirements
        reqs = self.module_instance.check_requirements()
        if reqs:
            self.logger.info("Requirements:")
            for tool, ok in reqs.items():
                status = "OK" if ok else "MISSING"
                print(f"  {tool:20s} [{status}]")

    def do_set(self, arg):
        """Set a module option. Usage: set <option> <value>"""
        if not self.module_instance:
            self.logger.warn("No module loaded.")
            return

        parts = shlex.split(arg)
        if len(parts) < 2:
            self.logger.error("Usage: set <option> <value>")
            return

        key, value = parts[0], " ".join(parts[1:])
        # Try to convert to int/float/bool
        if value.lower() == "true":
            value = True
        elif value.lower() == "false":
            value = False
        else:
            try:
                value = int(value)
            except ValueError:
                try:
                    value = float(value)
                except ValueError:
                    pass

        self.module_instance.set_option(key, value)
        self.logger.info(f"Set {key} = {value}")

    def do_run(self, arg):
        """Execute the current module. Usage: run"""
        if not self.module_instance:
            self.logger.warn("No module loaded.")
            return

        self.logger.info(f"Running {self.current_module}...")
        self.ctx.session.module = self.current_module
        try:
            self.module_instance.run()
        except KeyboardInterrupt:
            self.logger.warn("Interrupted by user")
        except Exception as e:
            self.logger.error(f"Module error: {e}")
        finally:
            self.module_instance.cleanup()

    def do_back(self, arg):
        """Unload current module and return to main prompt."""
        self.current_module = None
        self.module_instance = None
        self.prompt = "ghostwire> "

    # ─── Utility Commands ─────────────────────────────────────────────────

    def do_config(self, arg):
        """Show current configuration. Usage: config"""
        self.logger.info("Configuration:")
        for key, val in self.ctx.config.values.items():
            print(f"  {key:20s} = {val}")

    def do_setconfig(self, arg):
        """Set a config value. Usage: setconfig <key> <value>"""
        parts = shlex.split(arg)
        if len(parts) < 2:
            self.logger.error("Usage: setconfig <key> <value>")
            return
        self.ctx.config.set(parts[0], parts[1])
        self.logger.info(f"Config: {parts[0]} = {parts[1]}")

    def do_status(self, arg):
        """Show session status."""
        s = self.ctx.session
        self.logger.info(f"Session: {s.id}")
        self.logger.info(f"Started: {s.started}")
        self.logger.info(f"Module: {s.module or 'None'}")
        self.logger.info(f"Results: {len(s.results)}")
        self.logger.info(f"Target: {s.target or 'None'}")
        self.logger.info(f"Interface: {s.iface or 'None'}")

    def do_sessions(self, arg):
        """Save current session. Usage: sessions [save|list]"""
        if arg.strip() == "save":
            self.ctx.session.save()
            self.logger.success("Session saved")
        else:
            session_dir = Path(self.ctx.config.get("session_dir"))
            if session_dir.exists():
                for f in sorted(session_dir.glob("*.json")):
                    print(f"  {f.name}")
            else:
                self.logger.info("No sessions found")

    def do_clear(self, arg):
        """Clear the screen."""
        os.system("clear")

    def do_quit(self, arg):
        """Exit GhostWire."""
        self.logger.info("Shutting down GhostWire...")
        self.ctx.running = False
        return True

    def do_exit(self, arg):
        """Exit GhostWire."""
        return self.do_quit(arg)

    def do_EOF(self, arg):
        """Handle Ctrl+D."""
        print()
        return self.do_quit(arg)

    # ─── Shortcuts ────────────────────────────────────────────────────────

    def do_wifi(self, arg):
        """Quick WiFi scan. Usage: wifi [scan|deauth|pmkid]"""
        sub = arg.strip() or "scan"
        shortcuts = {
            "scan": "wifi/scan",
            "deauth": "wifi/deauth",
            "pmkid": "wifi/pmkid",
        }
        if sub in shortcuts:
            self.do_use(shortcuts[sub])
        else:
            self.logger.error(f"Unknown WiFi command: {sub}")

    def do_bt(self, arg):
        """Quick BT operation. Usage: bt [scan|knob|flood]"""
        sub = arg.strip() or "scan"
        shortcuts = {
            "scan": "bt/btscan",
            "knob": "bt/knob",
            "flood": "bt/l2flood",
        }
        if sub in shortcuts:
            self.do_use(shortcuts[sub])
        else:
            self.logger.error(f"Unknown BT command: {sub}")

    def do_saer(self, arg):
        """Load SAE Dragonblood module. Usage: saer"""
        self.do_use("saer/sae")

    # ─── Help Overrides ───────────────────────────────────────────────────

    def do_help(self, arg):
        if arg:
            super().do_help(arg)
        else:
            print("""
Core Commands:
  modules [cat]          List attack modules (optionally filter by category)
  use <module>           Load a module (e.g., use wifi/deauth)
  info                   Show current module info and options
  set <opt> <val>        Set module option
  run                    Execute current module
  back                   Unload current module

Quick Commands:
  wifi [scan|deauth|pmkid]   Quick WiFi operations
  bt [scan|knob|flood]       Quick Bluetooth operations
  saer                       Load SAE Dragonblood module

System:
  config                 Show configuration
  setconfig <k> <v>      Set config value
  status                 Show session status
  sessions [save|list]   Manage sessions
  clear                  Clear screen
  quit / exit            Exit GhostWire

Module Categories:
  wifi/    WiFi attacks (scan, deauth, pmkid)
  bt/      Bluetooth attacks (btscan, knob, l2flood)
  saer/    WPA3 SAE Dragonblood (sae)
""")


def run_cli(ctx):
    """Start the interactive CLI."""
    shell = GhostWireShell(ctx)
    try:
        shell.cmdloop()
    except KeyboardInterrupt:
        print("\n[!] Interrupted. Shutting down.")
        ctx.running = False
