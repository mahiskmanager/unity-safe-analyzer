import logging
import os

def setup_logging(log_dir="output"):
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "analyzer.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
