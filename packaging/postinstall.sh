#!/bin/bash
set -euo pipefail

INSTALL_DIR="/opt/eve-mouse"
VENV_DIR="${INSTALL_DIR}/venv"
UDEV_SRC="${INSTALL_DIR}/99-eve-mouse-uinput.rules"
UDEV_DST="/etc/udev/rules.d/99-eve-mouse-uinput.rules"

if [ ! -d "${VENV_DIR}" ] || [ ! -f "${VENV_DIR}/bin/python" ]; then
    echo "[EVE Mouse] Setting up Python environment..."
    python3 -m venv --system-site-packages "${VENV_DIR}" 2>/dev/null || true
    "${VENV_DIR}/bin/pip" install -q -r "${INSTALL_DIR}/requirements.txt" 2>/dev/null || {
        echo "[EVE Mouse] Warning: pip install failed. Run manually:"
        echo "  ${VENV_DIR}/bin/pip install -r ${INSTALL_DIR}/requirements.txt"
    }
fi

if [ -f "${UDEV_SRC}" ] && [ ! -f "${UDEV_DST}" ]; then
    echo "[EVE Mouse] Installing udev rule..."
    cp "${UDEV_SRC}" "${UDEV_DST}"
    udevadm control --reload-rules 2>/dev/null || true
    udevadm trigger /dev/uinput 2>/dev/null || true
fi

systemctl --user enable --now ydotool.service 2>/dev/null || true

echo ""
echo "========================================"
echo "  EVE Mouse installed successfully!"
echo "========================================"
echo ""
echo "Launch from your application menu or run: eve-mouse"
echo ""
if ! groups "$(logname 2>/dev/null || whoami)" 2>/dev/null | grep -qw 'input'; then
    echo "IMPORTANT: Run 'sudo usermod -aG input \$USER' then log out and back in."
fi
