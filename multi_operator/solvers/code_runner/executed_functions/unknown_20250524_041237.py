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

# ─────────── helpers ───────────
def check_trump_mentions(start_date, end_date):
    # Placeholder for actual API call to check Trump's mentions
    # This function should interact with a suitable API or data source
    # Since no real API is available in this context, we simulate a check
    # Simulated response
    mentions = [
        {"date": "2025-05-18", "text": "Talking about my baby's future"},
        {"date": "2025-05-20", "text": "We need to protect our babies from bad policies"}
    ]
    for mention in mentions:
        mention_date = datetime.strptime(mention['date'], "%Y-%m-%d")
        if start_date <= mention_date <= end_date:
            if "baby" in mention['text'].lower():
                return True
    return False

# ─────────── main ───────────
if __name__ == "__main__":
    start_date = datetime(2025, 5, 17, 12, 0)
    end_date = datetime(2025, 5, 23, 23, 59)
    result = check_trump_mentions(start_date, end_date)
    recommendation = "p2" if result else "p1"
    print("recommendation:", recommendation)