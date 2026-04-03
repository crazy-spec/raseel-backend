import logging
import os
from datetime import datetime

_logger = None

def get_logger():
    global _logger
    if _logger:
        return _logger

    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")
    os.makedirs(log_dir, exist_ok=True)

    _logger = logging.getLogger("raseel")
    _logger.setLevel(logging.INFO)

    if not _logger.handlers:
        log_file = os.path.join(log_dir, "raseel_" + datetime.now().strftime("%Y%m%d") + ".log")
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setLevel(logging.INFO)

        ch = logging.StreamHandler()
        ch.setLevel(logging.WARNING)

        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        fh.setFormatter(fmt)
        ch.setFormatter(fmt)

        _logger.addHandler(fh)
        _logger.addHandler(ch)

    return _logger

