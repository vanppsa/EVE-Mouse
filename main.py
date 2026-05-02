import logging
import sys
import os
import ctypes

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    ctypes.CDLL("libc.so.6").prctl(15, b"EVE Mouse", 0, 0, 0)
except Exception:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

from app.gui import run_gui
from app import auth, input_ctrl

if __name__ == "__main__":
    from app.config import get_url
    logging.getLogger("eve-mouse").info("EVE Mouse iniciando...")
    logging.getLogger("eve-mouse").info(f"Acesse: {get_url(10101)}")
    run_gui()
