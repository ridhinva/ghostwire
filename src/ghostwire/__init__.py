"""
GhostWire — Modular Wireless Exploitation Framework
====================================================
Built for Flipper One (MediaTek MT7921AUN — WiFi 6E + Bluetooth 5.2)

Architecture:
  - core/     : Framework core (module loader, session, config, events)
  - wifi/     : WiFi attack modules (deauth, PMKID, probe, evil twin, etc.)
  - bt/       : Bluetooth attack modules (KNOB, BLUR, L2CAP flood, SDP)
  - saer/     : WPA3 SAE Dragonblood exploitation
  - cli/      : Interactive CLI shell
  - utils/    : Shared utilities (logging, packet crafting, crypto)

Usage:
  ghostwire> use wifi/deauth
  ghostwire(deauth)> set target AA:BB:CC:DD:EE:FF
  ghostwire(deauth)> set iface wlan0
  ghostwire(deauth)> run

Author: Ridhin V A / OWL
License: MIT
"""

__version__ = "1.0.0"
__author__ = "Ridhin V A"
__license__ = "MIT"
