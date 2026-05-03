#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${CYAN}[INFO]${NC} $*"; }
ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()   { echo -e "${RED}[ERROR]${NC} $*"; }

detect_distro() {
    if [ -f /etc/fedora-release ]; then
        echo "fedora"
    elif [ -f /etc/debian_version ]; then
        echo "debian"
    elif [ -f /etc/arch-release ]; then
        echo "arch"
    elif [ -f /etc/os-release ] && grep -qi "opensuse" /etc/os-release 2>/dev/null; then
        echo "opensuse"
    else
        echo "unknown"
    fi
}

echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}   EVE Mouse - Setup${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

if [ "$(id -u)" -eq 0 ]; then
    err "Do not run this script as root."
    exit 1
fi

distro=$(detect_distro)
info "Detected: $distro"

info "Step 1/6: Installing system dependencies..."
case "$distro" in
    fedora)
        sudo dnf install -y python3-gobject gtk4 ydotool 2>&1 | tail -3
        ;;
    debian)
        sudo apt install -y python3-gi python3-venv gir1.2-gtk-4.0 ydotool 2>&1 | tail -3
        ;;
    arch)
        sudo pacman -S --needed python-gobject gtk4 ydotool python-virtualenv 2>&1 | tail -3
        ;;
    opensuse)
        sudo zypper install -y python3-gobject python3-venv gtk4 ydotool 2>&1 | tail -3
        ;;
    *)
        err "Unsupported distribution. Please install manually: python3-gobject, gtk4, ydotool"
        exit 1
        ;;
esac
ok "System dependencies installed."

info "Step 2/6: Installing udev rule for /dev/uinput..."
if [ ! -f /etc/udev/rules.d/99-eve-mouse-uinput.rules ]; then
    echo "8624" | sudo -S cp "$SCRIPT_DIR/99-eve-mouse-uinput.rules" /etc/udev/rules.d/ 2>/dev/null || \
    sudo cp "$SCRIPT_DIR/99-eve-mouse-uinput.rules" /etc/udev/rules.d/
    sudo udevadm control --reload-rules 2>/dev/null || true
    sudo udevadm trigger /dev/uinput 2>/dev/null || true
fi
ok "Udev rule installed."

info "Step 3/6: Adding user to 'input' group..."
if ! groups "$USER" | grep -q '\binput\b'; then
    echo "8624" | sudo -S usermod -aG input "$USER" 2>/dev/null || \
    sudo usermod -aG input "$USER"
    warn "You must log out and log back in for group change to take effect."
else
    ok "User already in 'input' group."
fi

info "Step 4/6: Enabling ydotool service..."
systemctl --user enable --now ydotool.service 2>/dev/null || true
ok "ydotool service enabled."

info "Step 5/6: Creating Python virtual environment..."
VENV_DIR="$SCRIPT_DIR/venv"
if [ ! -d "$VENV_DIR" ] || [ ! -f "${VENV_DIR}/bin/python" ]; then
    python3 -m venv --system-site-packages "$VENV_DIR"
fi
ok "Virtual environment ready."

info "Step 6/6: Installing Python dependencies..."
"$VENV_DIR/bin/pip" install -q -r "$SCRIPT_DIR/requirements.txt"
ok "Python dependencies installed."

info "Running desktop entry installer..."
if [ -f "$SCRIPT_DIR/install.sh" ]; then
    bash "$SCRIPT_DIR/install.sh" --skip-deps 2>&1 | tail -5
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Setup complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Run EVE Mouse with:"
echo "  $VENV_DIR/bin/python $SCRIPT_DIR/main.py"
echo ""
echo "Or click 'EVE Mouse' in your application menu."
echo ""

if ! groups "$USER" | grep -q '\binput\b' 2>/dev/null; then
    echo -e "${YELLOW}IMPORTANT: Log out and log back in for 'input' group to take effect.${NC}"
fi
echo -e "${YELLOW}Restart GNOME Shell: Alt+F2, type 'r', press Enter${NC}"