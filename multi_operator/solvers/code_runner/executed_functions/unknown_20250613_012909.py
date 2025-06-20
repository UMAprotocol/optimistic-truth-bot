import os
import requests
from datetime import datetime
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
                time.sleep(backoff * 2**i)
        except requests.RequestException as e:
            if i == retries - 1:
                raise ConnectionError(f"Failed to retrieve data from {url}: {e}")
    return None

# ─────────── helpers ───────────
def check_israel_iran_conflict(start_date, end_date):
    # Placeholder for actual data fetching logic
    # This function should query a relevant API or data source to check for military actions
    # For demonstration, it returns None (no data found)
    return None

# ─────────── main ───────────
if __name__ == "__main__":
    start_date = "2025-03-31"
    end_date = "2025-06-30"
    conflict_data = check_israel_iran_conflict(start_date, end_date)
    
    if conflict_data:
        print("recommendation: p2")  # p2 corresponds to "Yes"
    else:
        print("recommendation: p1")  # p1 corresponds to "No"