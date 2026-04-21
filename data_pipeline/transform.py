import json
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd


# ---------------- CONFIG ---------------- #
# RAW_DATA_PATH = Path("raw_data")
# PROCESSED_PATH = Path("processed_data")

# FACT_PATH = PROCESSED_PATH / "fact_prices"
# DIM_PATH = PROCESSED_PATH / "dim_currency"

# LOG_PATH = Path("logs/transform.log")

from config.config import (
    RAW_DATA_PATH,
    PROCESSED_PATH,
    FACT_PATH,
    DIM_PATH,
    LOG_PATH_TRANSFORM,
)

# ---------------- LOGGING ---------------- #
LOG_PATH_TRANSFORM.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=LOG_PATH_TRANSFORM,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# ---------------- HELPERS ---------------- #
# def get_latest_file() -> Path:
#     files = sorted(RAW_DATA_PATH.glob("*.json"))
#     if not files:
#         raise FileNotFoundError("No raw data files found")
#     return files[-1]

def get_latest_file(path: Path) -> Path:
    files = list(path.glob("*.json"))

    if not files:
        logging.error("No files found")
        raise FileNotFoundError("No raw data files found")

    latest = max(files, key=lambda f: f.stat().st_mtime)
  
    logging.info(f"Selected file: {latest}")

    return latest 


#get_latest_file(RAW_DATA_PATH)