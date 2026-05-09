#!/bin/bash
set -euo pipefail

INSTALL_DIR="/opt/eve-mouse"
VENV_DIR="${INSTALL_DIR}/venv"

if [ ! -d "${VENV_DIR}" ] || [ ! -f "${VENV_DIR}/bin/python" ]; then
    python3 -m venv --system-site-packages "${VENV_DIR}" 2>/dev/null || {
        echo "Error: Failed to create virtual environment." >&2
        exit 1
    }
    "${VENV_DIR}/bin/pip" install -q -r "${INSTALL_DIR}/requirements.txt" 2>/dev/null || {
        echo "Warning: Failed to install some Python dependencies." >&2
    }
fi

exec "${VENV_DIR}/bin/python" "${INSTALL_DIR}/main.py" "$@"
