from pathlib import Path

BASEL_URL = "https://api.coingecko.com/api/v3/coins/markets"

PARAMS = {
    "vs_currency": "usd",
    "order": "market_cap_desc",
    "per_page": 250,
}

PAGES = 5 
RETRIES = 3 
SLEEP_BETWEEN_RETRIES = 1 


RAW_DATA_PATH = Path("raw_data")
LOG_PATH = Path("logs/extract.log")