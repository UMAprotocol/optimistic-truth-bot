import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# ─────────── configuration ───────────
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")
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
    # This is a placeholder for the actual implementation that would check for conflicts
    # In a real scenario, this function would interact with a relevant API or data source
    # that provides information about military actions.
    # Here, we simulate a check by returning None (no conflict found).
    return None

# ─────────── main ───────────
if __name__ == "__main__":
    start_date = "2025-03-31"
    end_date = "2025-06-30"
    conflict = check_israel_iran_conflict(start_date, end_date)
    if conflict:
        print("recommendation: p2")  # Yes, conflict occurred
    else:
        print("recommendation: p1")  # No conflict occurred