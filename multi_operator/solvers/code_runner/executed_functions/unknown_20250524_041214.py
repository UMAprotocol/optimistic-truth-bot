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
    # Placeholder for actual API call to check Trump's mentions
    # This function should interact with a real or simulated API that provides access to Trump's public speeches
    # Since no real API is provided in the prompt, this is a mock-up
    # Example: _get("https://api.example.com/trump_mentions?start_date={start_date}&end_date={end_date}", "TrumpMentions")
    # For demonstration, let's assume it returns a list of mentions
    return ["Today, we need to take care of our babies.", "The baby boomers are retiring."]

def analyze_mentions(mentions):
    for mention in mentions:
        if "baby" in mention.lower():
            return "p2"  # Yes, Trump said "baby"
    return "p1"  # No, Trump did not say "baby"

# ─────────── main ───────────
if __name__ == "__main__":
    start_date = datetime(2025, 5, 17, 12, 0)  # Start date and time
    end_date = datetime(2025, 5, 23, 23, 59)  # End date and time
    mentions = check_trump_mentions(start_date, end_date)
    result = analyze_mentions(mentions)
    print("recommendation:", result)