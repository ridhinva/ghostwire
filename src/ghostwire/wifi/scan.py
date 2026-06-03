"""
GhostWire WiFi Module — Network Scanner
Comprehensive WiFi reconnaissance with MT7921-specific details.
"""

import subprocess
import re
from pathlib import Path
from ghostwire.core.base import BaseModule, Meta


class Module(BaseModule):
    class Meta(Meta):
        name = "scan"
        description = "WiFi network scan — discover APs, clients, and security configs"
        category = "wifi"
        requirements = ["iw", "airodump-ng"]
        options = {
            "iface": {"description": "Wireless interface", "required": False},
            "duration": {"description": "Scan duration in seconds", "default": 30},
            "band": {"description": "Frequency band (2.4/5/6)", "default": "all"},
        }

    def info(self):
        return f"WiFi scan on {self.get_option('iface', 'auto')} for {self.get_option('duration', 30)}s"

    def run(self, **kwargs):
        iface = self.get_option("iface") or self.ctx.config.get("wifi_iface")
        duration = int(self.get_option("duration", 30))

        if not iface:
            self.logger.error("No wireless interface found")
            return

        self.logger.info(f"WiFi scan on {iface} ({duration}s)")

        # Driver info
        self.logger.info("--- Driver/Firmware ---")
        result = subprocess.run(
            f"ethtool -i {iface} 2>/dev/null",
            shell=True, capture_output=True, text=True
        )
        if result.stdout:
            for line in result.stdout.strip().split("\n"):
                self.logger.info(f"  {line.strip()}")

        # Kernel messages
        result = subprocess.run(
            "dmesg | grep -i 'mt7921\\|firmware.*load' | tail -10",
            shell=True, capture_output=True, text=True
        )
        if result.stdout:
            for line in result.stdout.strip().split("\n"):
                self.logger.info(f"  {line.strip()}")

        # Monitor mode check
        result = subprocess.run(
            f"iw list 2>/dev/null | grep -A5 'Supported interface modes'",
            shell=True, capture_output=True, text=True
        )
        if "monitor" in result.stdout.lower():
            self.logger.success("Monitor mode: SUPPORTED")
        else:
            self.logger.warn("Monitor mode: NOT SUPPORTED")

        # Scan with iw
        self.logger.info("--- Active Scan ---")
        subprocess.run(f"ip link set {iface} up", shell=True, capture_output=True)
        result = subprocess.run(
            f"iw dev {iface} scan 2>/dev/null",
            shell=True, capture_output=True, text=True, timeout=20
        )

        networks = self._parse_iw_scan(result.stdout)
        self.logger.info(f"Found {len(networks)} networks:")
        for net in networks:
            sec = net.get("security", "Open")
            band = net.get("band", "?")
            self.logger.info(
                f"  {net['bssid']:17s} CH:{net['channel']:3s} "
                f"PWR:{net['power']:4s} {sec:12s} {band:8s} {net['essid']}"
            )

        # airodump for client discovery
        self.logger.info("--- Client Discovery ---")
        out_dir = Path(self.ctx.config.get("output_dir"))
        out_dir.mkdir(parents=True, exist_ok=True)
        scan_file = out_dir / f"scan_{iface}"

        subprocess.run(
            f"airodump-ng --output-format csv -w {scan_file} {iface}",
            shell=True, timeout=duration + 5
        )

        csv_file = Path(f"{scan_file}-01.csv")
        if csv_file.exists():
            clients = self._parse_clients(csv_file)
            self.logger.info(f"Found {len(clients)} clients:")
            for c in clients[:20]:
                self.logger.info(
                    f"  {c['mac']:17s} PWR:{c['power']:4s} "
                    f"Pkts:{c['packets']:6s} AP:{c.get('bssid','?')}"
                )

        self.session.add_result({
            "module": "wifi/scan",
            "networks": networks,
            "iface": iface,
            "status": "complete",
        })

    def _parse_iw_scan(self, output):
        networks = []
        current = {}
        for line in output.split("\n"):
            line = line.strip()
            if line.startswith("BSS "):
                if current.get("bssid"):
                    networks.append(current)
                bssid = line.split(" ")[1].split("(")[0]
                current = {"bssid": bssid, "essid": "", "channel": "", "power": "", "security": "Open", "band": ""}
            elif "SSID:" in line:
                current["essid"] = line.split("SSID:")[-1].strip()
            elif "DS Parameter set: channel" in line:
                current["channel"] = line.split("channel")[-1].strip()
            elif "signal:" in line:
                current["power"] = line.split("signal:")[-1].strip().split()[0]
            elif "WPA:" in line or "RSN:" in line:
                current["security"] = "WPA2" if "RSN" in line else "WPA"
            elif "SAE" in line:
                current["security"] = "WPA3"
            elif "freq:" in line:
                freq = int(line.split("freq:")[-1].strip().split()[0])
                if freq >= 5925:
                    current["band"] = "6GHz"
                elif freq >= 4900:
                    current["band"] = "5GHz"
                else:
                    current["band"] = "2.4GHz"
        if current.get("bssid"):
            networks.append(current)
        return networks

    def _parse_clients(self, csv_path):
        clients = []
        try:
            content = csv_path.read_text()
            sections = content.split("\r\n\r\n")
            if len(sections) >= 2:
                for line in sections[1].split("\n")[1:]:
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 7:
                        clients.append({
                            "mac": parts[0], "power": parts[3],
                            "packets": parts[4], "bssid": parts[5],
                        })
        except:
            pass
        return clients
