#!/bin/bash
set -euo pipefail

INSTALL_DIR="/opt/eve-mouse"
VENV_DIR="${INSTALL_DIR}/venv"
UDEV_DST="/etc/udev/rules.d/99-eve-mouse-uinput.rules"

if [ -d "${VENV_DIR}" ]; then
    rm -rf "${VENV_DIR}"
fi

if [ "$1" = "remove" ] || [ "$1" = "0" ] 2>/dev/null; then
    if [ -f "${UDEV_DST}" ]; then
        rm -f "${UDEV_DST}"
        udevadm control --reload-rules 2>/dev/null || true
    fi
fi
