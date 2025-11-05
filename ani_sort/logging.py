import logging
from pathlib import Path

def setup_logger(verbose: bool = False):
    logger = logging.getLogger("AniSort")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    Path("logs").mkdir(exist_ok=True)
    file_handler = logging.FileHandler("logs/anisort.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
