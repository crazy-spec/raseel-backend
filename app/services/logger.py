import os
import logging
from datetime import datetime

log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")
os.makedirs(log_dir, exist_ok=True)

_logger = None


def get_logger():
    global _logger
    if _logger is None:
        _logger = logging.getLogger("raseel")
        _logger.setLevel(logging.DEBUG)

        if not _logger.handlers:
            log_file = os.path.join(log_dir, "raseel_" + datetime.now().strftime("%Y%m%d") + ".log")
            fh = logging.FileHandler(log_file, encoding="utf-8")
            fh.setLevel(logging.DEBUG)

            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)

            fmt = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")
            fh.setFormatter(fmt)
            ch.setFormatter(fmt)

            _logger.addHandler(fh)
            _logger.addHandler(ch)

    return _logger
