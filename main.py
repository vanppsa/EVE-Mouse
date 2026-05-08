import atexit
import logging
import sys
import os
import ctypes

from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import ctypes.util

    libc_path = ctypes.util.find_library("c")
    if libc_path:
        ctypes.CDLL(libc_path).prctl(15, b"EVE Mouse", 0, 0, 0)
except Exception:
    pass

from app.config import get_url
from app import input_ctrl  # noqa: F401

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def _cleanup():
    input_ctrl.destroy_devices()


atexit.register(_cleanup)

from app.gui import run_gui  # noqa: E402

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--stop-server", action="store_true")
    parser.add_argument("--quit", action="store_true")
    args = parser.parse_args()

    if args.stop_server or args.quit:
        pid_file = Path.home() / ".config" / "EVE-Mouse" / "app.pid"
        if pid_file.exists():
            try:
                pid = int(pid_file.read_text().strip())
                os.kill(pid, 15)
            except Exception:
                pass
        sys.exit(0)

    logging.getLogger("eve mouse").info("EVE Mouse starting...")
    logging.getLogger("eve mouse").info(f"Access: {get_url(10101)}")
    run_gui()
