import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

from app.gui import run_gui
from app import auth, input_ctrl

if __name__ == "__main__":
    from app.config import get_url
    logging.getLogger("eve-mouse").info("EVE-Mouse iniciando...")
    logging.getLogger("eve-mouse").info(f"Acesse: {get_url(10101)}")
    run_gui()
