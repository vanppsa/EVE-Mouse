import atexit
import logging
import sys
import os
import ctypes

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    ctypes.CDLL("libc.so.6").prctl(15, b"EVE Mouse", 0, 0, 0)
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
    logging.getLogger("eve mouse").info("EVE Mouse iniciando...")
    logging.getLogger("eve mouse").info(f"Acesse: {get_url(10101)}")
    run_gui()
