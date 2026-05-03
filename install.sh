#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${SCRIPT_DIR}"
VENV_DIR="${INSTALL_DIR}/venv"
DESKTOP_SRC="${INSTALL_DIR}/com.eve.mouse.desktop.template"
DESKTOP_DST="${HOME}/.local/share/applications/com.eve.mouse.desktop"
ICON_SRC="${INSTALL_DIR}/app/static/icons/com.eve.mouse.png"
ICON_DST="${HOME}/.local/share/icons/hicolor/256x256/apps/com.eve.mouse.png"
UDEV_RULE="${INSTALL_DIR}/99-eve-mouse-uinput.rules"
UDEV_DST="/etc/udev/rules.d/99-eve-mouse-uinput.rules"

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

check_dep() {
    if command -v "$1" &>/dev/null; then
        return 0
    fi
    return 1
}

install_system_deps() {
    local distro
    distro=$(detect_distro)

    case "$distro" in
        fedora)
            info "Detected Fedora. Installing system dependencies..."
            sudo dnf install -y python3-gobject python3-venv gtk4 ydotool
            ;;
        debian)
            info "Detected Debian/Ubuntu. Installing system dependencies..."
            sudo apt install -y python3-gi python3-venv gir1.2-gtk-4.0 ydotool
            ;;
        arch)
            info "Detected Arch Linux. Installing system dependencies..."
            sudo pacman -S --needed python-gobject gtk4 ydotool python-virtualenv
            ;;
        opensuse)
            info "Detected openSUSE. Installing system dependencies..."
            sudo zypper install -y python3-gobject python3-venv gtk4 ydotool
            ;;
        *)
            err "Unsupported distribution. Install manually: python3-gobject, gtk4, ydotool, python3-venv"
            return 1
            ;;
    esac
}

setup_udev() {
    if [ ! -f "$UDEV_DST" ]; then
        info "Installing udev rule for /dev/uinput access..."
        sudo cp "$UDEV_RULE" "$UDEV_DST"
        sudo udevadm control --reload-rules
        sudo udevadm trigger /dev/uinput 2>/dev/null || true
        ok "Udev rule installed. /dev/uinput should be accessible."
    else
        ok "Udev rule already installed."
    fi
}

setup_input_group() {
    if groups "$USER" | grep -q '\binput\b'; then
        ok "User already in 'input' group."
    else
        info "Adding user to 'input' group..."
        sudo usermod -aG input "$USER"
        warn "You must log out and log back in for group change to take effect."
    fi
}

setup_ydotool() {
    if systemctl --user is-active ydotool.service &>/dev/null; then
        ok "ydotool service already running."
    else
        info "Enabling ydotool user service..."
        systemctl --user enable --now ydotool.service
        ok "ydotool service started."
    fi
}

setup_venv() {
    if [ -d "$VENV_DIR" ] && [ -f "${VENV_DIR}/bin/python" ]; then
        ok "Virtual environment already exists."
    else
        info "Creating virtual environment with --system-site-packages..."
        python3 -m venv --system-site-packages "$VENV_DIR"
        ok "Virtual environment created."
    fi

    info "Installing Python dependencies..."
    "${VENV_DIR}/bin/pip" install -r "${INSTALL_DIR}/requirements.txt"
    ok "Python dependencies installed."
}

setup_desktop_entry() {
  mkdir -p "$(dirname "$DESKTOP_DST")"

  local python_path
  python_path="${VENV_DIR}/bin/python"

  sed \
    -e "s|__PYTHON__|${python_path}|g" \
    -e "s|__INSTALL_DIR__|${INSTALL_DIR}|g" \
    "$DESKTOP_SRC" > "$DESKTOP_DST"

  ok "Desktop entry created at ${DESKTOP_DST}"
}

setup_icon() {
  mkdir -p "$(dirname "$ICON_DST")"

  if [ -f "$ICON_SRC" ]; then
    cp "$ICON_SRC" "$ICON_DST"
    ok "Icon installed at ${ICON_DST}"
  else
    warn "Icon source not found at ${ICON_SRC}"
  fi

  if command -v gtk-update-icon-cache &>/dev/null; then
    gtk-update-icon-cache -f "${HOME}/.local/share/icons/hicolor" 2>/dev/null || true
  fi
}

main() {
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}   EVE Mouse - Installer${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""

    if [ "$(id -u)" -eq 0 ]; then
        err "Do not run this script as root."
        exit 1
    fi

info "Step 1/7: System dependencies"
install_system_deps

info "Step 2/7: /dev/uinput access (udev rule)"
setup_udev

info "Step 3/7: Input group"
setup_input_group

info "Step 4/7: ydotool service"
setup_ydotool

info "Step 5/7: Python virtual environment"
setup_venv

info "Step 6/7: Desktop entry"
setup_desktop_entry

info "Step 7/7: Application icon"
setup_icon

    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}   Installation complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Run EVE Mouse with:"
    echo "  ${VENV_DIR}/bin/python ${INSTALL_DIR}/main.py"
    echo ""
    echo "Or launch from your GNOME application menu."
    echo ""
    warn "If this is your first time adding the 'input' group, log out and back in."
}

main "$@"
