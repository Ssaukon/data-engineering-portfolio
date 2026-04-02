from pathlib import Path

BASE_URL = "https://api.coingecko.com/api/v3/coins/markets"

PARAMS = {
    "vs_currency": "usd",
    "order": "market_cap_desc",
    "per_page": 250,
}

PAGES = 5 # Total 1250 coins (250 per page)
RETRIES = 3 # Number of retries for failed requests
SLEEP_BETWEEN_REQUESTS = 1 # Delay between requests in seconds


RAW_DATA_PATH = Path("raw_data")
LOG_PATH = Path("logs/extract.log")