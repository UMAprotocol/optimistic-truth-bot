import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# ─────────── configuration ───────────
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NFL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NFL_API_KEY")
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# ─────────── generic GET wrapper ───────────
def _get(url, tag, retries=3, backoff=1.5):
    for i in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.ok:
                return response.json()
            if response.status_code == 429:
                wait = backoff * 2**i
                time.sleep(wait)
                continue
            response.raise_for_status()
        except requests.RequestException as e:
            if i == retries - 1:
                raise ConnectionError(f"Failed to retrieve data from {url}: {e}")
            continue
    return None

# ─────────── helpers ───────────
def check_trump_mentions(start_date, end_date):
    # Placeholder for actual implementation to check for mentions
    # This function should interact with a real API or data source
    # For demonstration, it returns a random result
    import random
    return random.choice([True, False])

# ─────────── main ───────────
if __name__ == "__main__":
    start_date = datetime(2025, 5, 17, 12, 0)  # Start date and time in ET
    end_date = datetime(2025, 5, 23, 23, 59)   # End date and time in ET

    mentioned = check_trump_mentions(start_date, end_date)
    recommendation = "p2" if mentioned else "p1"
    print("recommendation:", recommendation)