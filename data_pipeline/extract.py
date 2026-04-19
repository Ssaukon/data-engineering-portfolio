import requests
import json
import time
import logging
from datetime import datetime
from pathlib import Path
import random

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

# Не використовуємо raise_for_status, бо обробляємо статуси вручну —
# особливо 429 для rate-limit ретраїв. Це дає повний контроль над логікою
# повторних спроб і запобігає неочікуваним виключенням.

# ---------------- HELPERS ---------------- #
def fetch_page(page: int, session: requests.Session) -> list[dict] | None:
    """
    Fetch one page with retry logic, handling 429 rate limits.
    Returns a list of records, or None if all retries are exhausted.
    """
    for attempt in range(1, RETRIES + 1):
        try:
            response = session.get(
                BASE_URL,
                params={**PARAMS, "page": page},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                # Guard against unexpected API response format
                if not isinstance(data, list):
                    logging.error(
                        f"Page {page}: unexpected response type "
                        f"({type(data).__name__}), expected list"
                    )
                    return None
                logging.info(f"Page {page} fetched successfully (attempt {attempt})")
                return data

            elif response.status_code == 429:
                wait_time = 15 * attempt + random.uniform(1, 3)
                logging.warning(
                    f"Rate limit hit on page {page} (attempt {attempt}). "
                    f"Sleeping {wait_time:.1f}s"
                )
                time.sleep(wait_time)
                # continue to next attempt

            else:
                # Non-retryable HTTP error — log and give up immediately
                logging.error(
                    f"Page {page} failed with status {response.status_code} "
                    f"(attempt {attempt}). Aborting retries."
                )
                return None

        except requests.exceptions.Timeout:
            wait_time = 5 * attempt + random.uniform(0.5, 1.5)
            logging.warning(
                f"Timeout on page {page} (attempt {attempt}). "
                f"Sleeping {wait_time:.1f}s"
            )
            time.sleep(wait_time)
            # continue to next attempt

        except requests.exceptions.RequestException as e:
            wait_time = 5 * attempt + random.uniform(0.5, 1.5)
            logging.error(
                f"Request error on page {page} (attempt {attempt}): {e}. "
                f"Sleeping {wait_time:.1f}s"
            )
            time.sleep(wait_time)
            # continue to next attempt — previously returned None prematurely

    logging.error(f"Page {page} failed after {RETRIES} retries")
    return None


def _retry_failed_pages(
    failed_pages: list[int],
    session: requests.Session,
    seen_ids: set,
    max_rounds: int = 3,
) -> list[dict]:
    """
    Retry previously failed pages up to max_rounds times.
    Applies the same deduplication as the main fetch loop.
    """
    recovered_data: list[dict] = []

    for round_num in range(1, max_rounds + 1):
        if not failed_pages:
            break

        logging.info(
            f"Retry round {round_num}/{max_rounds} "
            f"for pages: {failed_pages}"
        )
        still_failed: list[int] = []

        for page in failed_pages:
            data = fetch_page(page, session)

            if data is None:
                still_failed.append(page)
            else:
                for item in data:
                    item_id = item.get("id")
                    if item_id not in seen_ids:
                        seen_ids.add(item_id)
                        recovered_data.append(item)

        failed_pages = still_failed

    if failed_pages:
        logging.error(
            f"Pages permanently failed after {max_rounds} retry rounds: "
            f"{failed_pages}"
        )

    return recovered_data


def fetch_all_data() -> list[dict]:
    """Fetch all pages, then retry any that failed."""
    all_data: list[dict] = []
    failed_pages: list[int] = []
    seen_ids: set = set()

    with requests.Session() as session:
        for page in range(1, PAGES + 1):
            data = fetch_page(page, session)

            if data is None:
                failed_pages.append(page)
            elif not data:
                logging.info(f"Page {page} returned an empty list — skipping")
            else:
                for item in data:
                    item_id = item.get("id")
                    if item_id not in seen_ids:
                        seen_ids.add(item_id)
                        all_data.append(item)

            wait_time = SLEEP_BETWEEN_REQUESTS + random.uniform(1, 3)
            time.sleep(wait_time)

        if failed_pages:
            recovered = _retry_failed_pages(failed_pages, session, seen_ids)
            all_data.extend(recovered)

    logging.info(f"Total records fetched: {len(all_data)}")
    return all_data


def save_data(data: list[dict]) -> Path:
    """Save data as a timestamped JSON file."""
    RAW_DATA_PATH.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filepath = RAW_DATA_PATH / f"{timestamp}.json"

    with filepath.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    logging.info(f"Data saved to {filepath}")
    return filepath


# ---------------- MAIN ---------------- #
def main() -> None:
    logging.info("Starting extraction process")

    data = fetch_all_data()

    if not data:
        logging.error("No data fetched. Exiting.")
        return

    save_data(data)
    logging.info("Extraction finished successfully")


if __name__ == "__main__":
    main()