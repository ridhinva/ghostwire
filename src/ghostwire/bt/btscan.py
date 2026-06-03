"""
GhostWire Bluetooth Module — Device Scanner
Classic BT + BLE device discovery and SDP enumeration.
"""

import subprocess
import re
from ghostwire.core.base import BaseModule, Meta


class Module(BaseModule):
    class Meta(Meta):
        name = "btscan"
        description = "Bluetooth device scan — Classic + BLE discovery with SDP enumeration"
        category = "bt"
        requirements = ["hcitool", "sdptool", "bluetoothctl"]
        options = {
            "hci": {"description": "HCI device", "required": False},
            "duration": {"description": "Scan duration in seconds", "default": 15},
        }

    def info(self):
        return f"BT scan on {self.get_option('hci', 'auto')} for {self.get_option('duration', 15)}s"

    def run(self, **kwargs):
        hci = self.get_option("hci") or self.ctx.config.get("bt_iface") or "hci0"
        duration = int(self.get_option("duration", 15))

        self.logger.info(f"Bluetooth scan on {hci} ({duration}s)")

        # Controller info
        self.logger.info("--- Controller ---")
        result = subprocess.run(
            f"hciconfig -a {hci}", shell=True, capture_output=True, text=True
        )
        for line in result.stdout.strip().split("\n")[:15]:
            self.logger.info(f"  {line.strip()}")

        # Firmware check
        result = subprocess.run(
            "dmesg | grep -i 'bluetooth\\|btusb\\|hci' | tail -15",
            shell=True, capture_output=True, text=True
        )
        if result.stdout:
            self.logger.info("--- Firmware ---")
            for line in result.stdout.strip().split("\n"):
                self.logger.info(f"  {line.strip()}")

        # Classic BT scan
        self.logger.info("--- Classic BT Scan ---")
        result = subprocess.run(
            f"hcitool -i {hci} scan --flush 2>/dev/null",
            shell=True, capture_output=True, text=True, timeout=duration + 5
        )

        devices = []
        for line in result.stdout.strip().split("\n")[1:]:
            parts = line.strip().split("\t")
            if len(parts) >= 2:
                mac, name = parts[0], parts[1]
                devices.append({"mac": mac, "name": name})
                self.logger.info(f"  {mac}  {name}")

                # SDP enumeration
                self.logger.info(f"    Enumerating services...")
                sdp = subprocess.run(
                    f"sdptool browse {mac} 2>/dev/null",
                    shell=True, capture_output=True, text=True, timeout=10
                )
                if sdp.stdout:
                    services = re.findall(r'Service Name: (.+)', sdp.stdout)
                    for svc in services:
                        self.logger.info(f"      Service: {svc}")

        # BLE scan
        self.logger.info("--- BLE Scan ---")
        result = subprocess.run(
            f"hcitool -i {hci} lescan --passive 2>/dev/null",
            shell=True, capture_output=True, text=True, timeout=duration
        )
        for line in result.stdout.strip().split("\n"):
            if ":" in line and len(line) >= 17:
                self.logger.info(f"  BLE: {line.strip()}")

        # Security check
        self.logger.info("--- Security Check ---")
        result = subprocess.run(
            f"hcitool -i {hci} cmd 0x04 0x0009 2>/dev/null",
            shell=True, capture_output=True, text=True
        )
        self.logger.info(f"  LMP features: {result.stdout.strip()}")

        # KNOB mitigation check
        result = subprocess.run(
            "btmgmt info 2>/dev/null | grep -i 'supported\\|secure\\|le'",
            shell=True, capture_output=True, text=True
        )
        if result.stdout:
            for line in result.stdout.strip().split("\n"):
                self.logger.info(f"  {line.strip()}")

        self.session.add_result({
            "module": "bt/btscan",
            "devices": devices,
            "device_count": len(devices),
            "status": "complete",
        })
