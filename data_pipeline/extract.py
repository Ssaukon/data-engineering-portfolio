import requests
import json
import time
import logging
from datetime import datetime
from pathlib import Path


from config.config import (
    BASE_URL,
    PARAMS,
    PAGES,
    RETRIES,
    SLEEP_BETWEEN_REQUESTS,
    RAW_DATA_PATH,
    LOG_PATH,
)

# ---------------- LOGGING ---------------- #
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# ---------------- HELPERS ---------------- #
def fetch_page(page: int) -> list:
    """Fetch one page with retry logic"""
    for attempt in range(1, RETRIES + 1):
        try:
            response = requests.get(
                BASE_URL,
                params={**PARAMS, "page": page},
                timeout=10,
            )

            if response.status_code == 200:
                logging.info(f"Page {page} fetched successfully")
                return response.json()

            logging.warning(
                f"Page {page} failed with status {response.status_code}"
            )

        except Exception as e:
            logging.error(f"Error fetching page {page}: {e}")

        time.sleep(2 * attempt)  # exponential backoff

    logging.error(f"Page {page} failed after {RETRIES} retries")
    return []


def fetch_all_data() -> list:
    """Fetch all pages"""
    all_data = []

    for page in range(1, PAGES + 1):
        data = fetch_page(page)
        all_data.extend(data)

        time.sleep(SLEEP_BETWEEN_REQUESTS)

    logging.info(f"Total records fetched: {len(all_data)}")
    return all_data


def save_data(data: list) -> Path:
    """Save data to file with timestamp"""
    RAW_DATA_PATH.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filepath = RAW_DATA_PATH / f"{timestamp}.json"

    with filepath.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    logging.info(f"Data saved to {filepath}")
    return filepath


# ---------------- MAIN ---------------- #
def main():
    logging.info("Starting extraction process")

    data = fetch_all_data()

    if not data:
        logging.error("No data fetched. Exiting.")
        return

    save_data(data)

    logging.info("Extraction finished successfully")


if __name__ == "__main__":
    main()