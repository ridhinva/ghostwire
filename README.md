# GhostWire — Modular Wireless Exploitation Framework

> **WiFi 6E (802.11ax) + Bluetooth 5.2**
> Built for Flipper One and RK3576 platforms

[![Python](https://img.shields.io/badge/python-3.10+-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Flipper%20One%20%7C%20RK3576-orange)](#compatible-hardware)

## What is GhostWire?

GhostWire is a **modular wireless exploitation framework** designed for the [Flipper One](https://docs.flipper.net/one) portable security device. It targets the **MediaTek MT7921AUN** combo chip (WiFi 6E + Bluetooth 5.2) and provides a clean, extensible architecture for wireless security testing.

Unlike monolithic tools, GhostWire uses a **module-based architecture** — each attack is a self-contained module that can be loaded, configured, and executed independently through an interactive shell.

## Architecture

```
ghostwire/
├── core/           Framework engine
│   ├── base.py     Abstract module class (all modules inherit from this)
│   ├── __init__.py Module loader, session manager, event bus, config, logger
│
├── wifi/           WiFi attack modules
│   ├── scan.py     Network discovery, driver analysis, client enumeration
│   ├── deauth.py   802.11 deauthentication attack
│   └── pmkid.py    PMKID capture for offline cracking
│
├── bt/             Bluetooth attack modules
│   ├── btscan.py   Classic + BLE scan, SDP enumeration
│   ├── knob.py     KNOB attack (CVE-2019-9506)
│   └── l2flood.py  L2CAP flood DoS
│
├── saer/           WPA3 SAE Dragonblood
│   └── sae.py      Invalid group, reflection, timing, anti-clogging
│
├── cli/            Interactive shell
│   └── shell.py    Full-featured CLI with tab completion
│
└── utils/          Shared utilities
    └── helpers.py  Packet crafting, crypto helpers
```

## Quick Start

### Install

```bash
git clone https://github.com/ridhinva/ghostwire.git
cd ghostwire
sudo bash scripts/install.sh
```

### Interactive Shell

```bash
$ sudo ghostwire

   ╔══════════════════════════════════════════════════════╗
   ║   ██████╗ ██╗  ██╗ ██████╗ ███████╗████████╗██╗    ██╗██╗██████╗ ███████╗  ║
   ║   ...                                                    ║
   ╚══════════════════════════════════════════════════════╝

ghostwire> modules

[WIFI]
  wifi/deauth    802.11 deauthentication attack
  wifi/pmkid     Capture PMKID from WPA2/WPA3 access points
  wifi/scan      WiFi network scan — discover APs and clients

[BT]
  bt/btscan      Bluetooth device scan — Classic + BLE + SDP
  bt/knob        KNOB attack (CVE-2019-9506) — force 1-byte BT key
  bt/l2flood     L2CAP flood DoS

[SAER]
  saer/sae       WPA3 SAE Dragonblood tests

ghostwire> use wifi/scan
ghostwire(wifi/scan)> set iface wlan0
ghostwire(wifi/scan)> run
```

### Quick Commands

```bash
ghostwire> wifi scan          # Quick WiFi scan
ghostwire> wifi deauth        # Load deauth module
ghostwire> bt scan            # Quick BT scan
ghostwire> bt knob            # Load KNOB module
ghostwire> saer               # Load Dragonblood module
```

## Module Reference

### WiFi Modules

#### `wifi/scan` — Network Scanner
Discovers access points, clients, and security configurations.

```
ghostwire> use wifi/scan
ghostwire(wifi/scan)> set iface wlan0
ghostwire(wifi/scan)> set duration 30
ghostwire(wifi/scan)> run
```

**Output:** BSSID, channel, power, encryption (WPA2/WPA3/Open), band (2.4/5/6GHz), ESSID, connected clients.

#### `wifi/deauth` — Deauthentication Attack
Sends 802.11 deauthentication frames to disconnect clients.

```
ghostwire> use wifi/deauth
ghostwire(wifi/deauth)> set target AA:BB:CC:DD:EE:FF
ghostwire(wifi/deauth)> set count 100
ghostwire(wifi/deauth)> run
```

**Requirements:** aircrack-ng, monitor mode support

#### `wifi/pmkid` — PMKID Capture
Captures PMKID from WPA2/WPA3 APs for offline password cracking.

```
ghostwire> use wifi/pmkid
ghostwire(wifi/pmkid)> set target AA:BB:CC:DD:EE:FF
ghostwire(wifi/pmkid)> set duration 120
ghostwire(wifi/pmkid)> run
# Then: hashcat -m 22000 output.hc22000 wordlist.txt
```

**Requirements:** hcxdumptool, hcxpcapngtool

### Bluetooth Modules

#### `bt/btscan` — Device Scanner
Classic Bluetooth + BLE discovery with SDP service enumeration.

```
ghostwire> use bt/btscan
ghostwire(bt/btscan)> set hci hci0
ghostwire(bt/btscan)> run
```

#### `bt/knob` — KNOB Attack (CVE-2019-9506)
Forces Bluetooth pairing to use 1-byte encryption key entropy.

```
ghostwire> use bt/knob
ghostwire(bt/knob)> set target AA:BB:CC:DD:EE:FF
ghostwire(bt/knob)> run
# Generates standalone attack script
```

#### `bt/l2flood` — L2CAP Flood DoS
Exhausts target resources with rapid L2CAP connection requests.

```
ghostwire> use bt/l2flood
ghostwire(bt/l2flood)> set target AA:BB:CC:DD:EE:FF
ghostwire(bt/l2flood)> set duration 30
ghostwire(bt/l2flood)> run
```

### WPA3 SAE Dragonblood

#### `saer/sae` — Full Dragonblood Suite
Tests WPA3-Personal (SAE) access points for all Dragonblood vulnerabilities.

```
ghostwire> use saer/sae
ghostwire(saer/sae)> set target AA:BB:CC:DD:EE:FF
ghostwire(saer/sae)> set test all
ghostwire(saer/sae)> run
```

**Tests:**
- **Invalid Group (CVE-2019-9494):** SAE Commit with group 0 / 65535
- **Reflection (CVE-2019-9494):** SAE Commit with AP's own MAC as source
- **Timing Side-Channel (CVE-2019-9496):** Measures SAE processing time differences
- **Anti-Clogging Bypass (CVE-2019-9497):** Floods to exhaust token cache
- **Transition Downgrade:** Checks WPA2/WPA3 transition mode

## Compatible Hardware

### Primary Target: Flipper One
| Component | Detail |
|-----------|--------|
| SoC | Rockchip RK3576 (8-core, Mali G52, 6 TOPS NPU) |
| MCU | Raspberry Pi RP2350 (FreeRTOS) |
| WiFi/BT | MediaTek MT7921AUN via USB 3.0 |
| WiFi | 802.11ax (WiFi 6E), 2x2 MIMO, 2.4/5/6 GHz |
| Bluetooth | 5.2 (Classic + LE) |
| OS | Flipper OS (Debian-based) |

### Compatible RK3576 Boards
- Armsom Sige5 / Banana Pi BPI-M5 Pro
- FireFly ROC-RK3576-PC
- Luckfox Omni3576
- Radxa ROCK 4D

## Vulnerability Coverage

| ID | Module | Severity | Description |
|----|--------|----------|-------------|
| CVE-2019-9494 | saer/sae | HIGH | SAE invalid group / reflection |
| CVE-2019-9496 | saer/sae | HIGH | SAE timing side-channel |
| CVE-2019-9497 | saer/sae | HIGH | Anti-clogging bypass |
| CVE-2019-9506 | bt/knob | HIGH | KNOB key downgrade |
| CVE-2020-15802 | bt/btscan | HIGH | BLUR cross-transport |
| CVE-2022-3564 | wifi/scan | HIGH | Driver buffer overflow |
| CVE-2023-32233 | wifi/scan | CRITICAL | Use-after-free |
| FragAttacks | wifi/deauth | HIGH | Frame injection |
| PMKID | wifi/pmkid | MEDIUM | Offline cracking |

## Extending GhostWire

Create a new module by inheriting from `BaseModule`:

```python
from ghostwire.core.base import BaseModule, Meta

class Module(BaseModule):
    class Meta(Meta):
        name = "myattack"
        description = "My custom attack"
        category = "wifi"
        requirements = ["tool1"]
        options = {
            "target": {"description": "Target", "required": True},
            "count": {"description": "Count", "default": 10},
        }

    def info(self):
        return f"MyAttack -> {self.get_option('target')}"

    def run(self, **kwargs):
        target = self.get_option("target")
        self.logger.info(f"Attacking {target}...")
        # Your attack code here
        self.session.add_result({"status": "done"})
```

Save as `src/ghostwire/wifi/myattack.py` — it's auto-discovered.

## Legal

**Authorized use only.** Only test devices and networks you own or have explicit written permission to assess. The authors are not responsible for misuse.

## Author

**Ridhin V A** — [@ridhinva](https://github.com/ridhinva)
