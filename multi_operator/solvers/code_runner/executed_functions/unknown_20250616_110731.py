import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# ─────────── configuration ───────────
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# ─────────── generic GET wrapper ───────────
def _get(url, tag, retries=3, backoff=1.5):
    for i in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.ok:
                return response.json()
            if response.status_code in (401, 403):
                print(f"Access denied or bad request at {url}")
                return None
            if response.status_code == 404:
                print(f"Resource not found at {url}")
                return None
            if response.status_code == 429:
                wait = backoff * 2**i
                print(f"Rate limit exceeded, retrying in {wait} seconds")
                time.sleep(wait)
                continue
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            if i == retries - 1:
                return None
    return None

# ─────────── main ───────────
if __name__ == "__main__":
    # Define the period of interest
    start_date = datetime(2025, 6, 16)
    end_date = datetime(2025, 6, 18, 23, 59)

    # URLs for checking the status of Ali Khamenei
    urls = [
        "https://api.example.com/check_status",  # Placeholder for actual API endpoint
    ]

    # Check the status of Ali Khamenei
    status = None
    for url in urls:
        data = _get(url, "CheckStatus")
        if data and data.get("status") == "ceased":
            status = "ceased"
            break

    # Determine the recommendation based on the status
    if status == "ceased":
        print("recommendation: p2")  # Yes, he ceased to be the Supreme Leader
    else:
        print("recommendation: p1")  # No, he did not cease to be the Supreme Leader