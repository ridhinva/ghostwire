"""
GhostWire — Shared Utilities
Packet crafting, crypto helpers, and common functions.
"""

import struct
import hashlib
import hmac
import secrets
from typing import Optional


def random_mac() -> str:
    """Generate a random locally-administered MAC address."""
    mac = [0x02, 0x00,
           secrets.randbelow(256), secrets.randbelow(256),
           secrets.randbelow(256), secrets.randbelow(256)]
    return ":".join(f"{b:02x}" for b in mac)


def mac_to_bytes(mac: str) -> bytes:
    """Convert MAC string to bytes."""
    return bytes(int(b, 16) for b in mac.split(":"))


def bytes_to_mac(data: bytes) -> str:
    """Convert bytes to MAC string."""
    return ":".join(f"{b:02x}" for b in data)


def crc32(data: bytes) -> int:
    """Calculate CRC32 checksum."""
    import binascii
    return binascii.crc32(data) & 0xFFFFFFFF


def pmk(passphrase: str, ssid: str) -> bytes:
    """Derive PMK from passphrase and SSID using PBKDF2."""
    return hashlib.pbkdf2_hmac(
        "sha1", passphrase.encode(), ssid.encode(), 4096, 32
    )


def prf(key: str, label: str, data: bytes, length: int = 64) -> bytes:
    """Pseudo-random function for WPA key derivation."""
    result = b""
    counter = 0
    while len(result) < length:
        counter += 1
        h = hmac.new(
            key.encode(),
            label.encode() + b"\x00" + data + bytes([counter]),
            hashlib.sha1
        )
        result += h.digest()
    return result[:length]


def parse_rsn_ie(data: bytes) -> Optional[dict]:
    """Parse RSN Information Element from beacon/probe response."""
    if len(data) < 2:
        return None
    result = {"version": struct.unpack("<H", data[:2])[0]}
    offset = 2
    if len(data) >= offset + 4:
        result["group_cipher"] = data[offset:offset+4].hex()
        offset += 4
    return result


def format_duration(seconds: float) -> str:
    """Format seconds into human-readable duration."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"
