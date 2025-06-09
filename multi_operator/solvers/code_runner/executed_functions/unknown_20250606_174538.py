import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# ─────────── configuration ───────────
load_dotenv()
HLTV_EVENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"

# ─────────── generic GET wrapper ───────────
def _get(url, retries=3, backoff=1.5):
    for i in range(retries):
        try:
            response = requests.get(url, timeout=10)
            if response.ok:
                return response.json()
            if response.status_code == 429:
                wait = backoff * 2**i
                time.sleep(wait)
                continue
            response.raise_for_status()
        except requests.RequestException as e:
            if i == retries - 1:
                raise
            time.sleep(backoff * 2**i)

# ─────────── check qualification ───────────
def check_qualification():
    try:
        data = _get(HLTV_EVENT_URL)
        if not data:
            return "p3"  # Unknown or 50-50 if no data could be fetched

        # Check if NRG has qualified for Stage 2
        teams_qualified = data.get('teams_qualified', [])
        if 'NRG' in teams_qualified:
            return "p2"  # Yes, NRG qualified
        else:
            return "p1"  # No, NRG did not qualify

    except Exception as e:
        print(f"Error checking qualification: {str(e)}")
        return "p3"  # Unknown or 50-50 in case of error

# ─────────── main ───────────
if __name__ == "__main__":
    result = check_qualification()
    print("recommendation:", result)