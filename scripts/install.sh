#!/bin/bash
# GhostWire Install Script
# Run: sudo bash install.sh

set -e

echo "╔══════════════════════════════════════╗"
echo "║   GhostWire Installer v1.0.0         ║"
echo "║   Wireless Exploitation Framework    ║"
echo "╚══════════════════════════════════════╝"

# Check root
if [ "$EUID" -ne 0 ]; then
    echo "[!] Run as root: sudo bash install.sh"
    exit 1
fi

# Detect platform
echo "[*] Detecting platform..."
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "[*] OS: $PRETTY_NAME"
fi
echo "[*] Kernel: $(uname -r)"

# Install dependencies
echo "[*] Installing dependencies..."

if command -v apt &>/dev/null; then
    apt update -qq
    apt install -y -qq \
        aircrack-ng \
        hcxdumptool \
        bluez \
        python3 \
        python3-pip \
        python3-scapy \
        wireless-tools \
        iw \
        ethtool \
        usbutils \
        2>/dev/null || echo "[!] Some packages may not be available"
elif command -v pacman &>/dev/null; then
    pacman -S --noconfirm \
        aircrack-ng \
        hcxdumptool \
        bluez \
        bluez-utils \
        python \
        python-scapy \
        wireless_tools \
        iw \
        ethtool \
        usbutils \
        2>/dev/null || echo "[!] Some packages may not be available"
fi

# Python dependencies
echo "[*] Installing Python packages..."
pip3 install scapy 2>/dev/null || echo "[!] scapy install failed"

# Create directories
echo "[*] Creating directories..."
mkdir -p /root/ghostwire/{output,logs,sessions}

# Install GhostWire
echo "[*] Installing GhostWire..."
INSTALL_DIR="/opt/ghostwire"
mkdir -p "$INSTALL_DIR"
cp -r src/ghostwire "$INSTALL_DIR/"
cp src/ghostwire/main.py "$INSTALL_DIR/ghostwire.py"

# Create launcher
cat > /usr/local/bin/ghostwire << 'LAUNCHER'
#!/bin/bash
cd /opt/ghostwire
sudo python3 ghostwire.py "$@"
LAUNCHER
chmod +x /usr/local/bin/ghostwire

# Verify
echo ""
echo "[*] Verifying installation..."
echo -n "  aircrack-ng: "; command -v aircrack-ng &>/dev/null && echo "OK" || echo "MISSING"
echo -n "  hcxdumptool: "; command -v hcxdumptool &>/dev/null && echo "OK" || echo "MISSING"
echo -n "  hcitool:     "; command -v hcitool &>/dev/null && echo "OK" || echo "MISSING"
echo -n "  scapy:       "; python3 -c "import scapy" 2>/dev/null && echo "OK" || echo "MISSING"
echo -n "  iw:          "; command -v iw &>/dev/null && echo "OK" || echo "MISSING"

# Check for MT7921
echo ""
echo "[*] Checking for MT7921AUN..."
if lsusb 2>/dev/null | grep -qi "14c3:7961\|mediatek.*7921"; then
    echo "  [OK] MT7921AUN detected!"
else
    echo "  [!] MT7921AUN not detected (may be on PCIe)"
fi

# Check wireless interface
IFACE=$(iw dev 2>/dev/null | grep Interface | awk '{print $2}' | head -1)
if [ -n "$IFACE" ]; then
    echo "  [OK] Wireless interface: $IFACE"
else
    echo "  [!] No wireless interface found"
fi

echo ""
echo "╔══════════════════════════════════════╗"
echo "║   Installation Complete!             ║"
echo "║                                      ║"
echo "║   Run: ghostwire                     ║"
echo "║   Or:  sudo python3 -m ghostwire     ║"
echo "╚══════════════════════════════════════╝"
