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
                return response.text
            if response.status_code in {401, 403, 404, 429}:
                wait = backoff * 2**i
                time.sleep(wait)
                continue
            response.raise_for_status()
        except requests.RequestException as e:
            if i == retries - 1:
                raise ConnectionError(f"Failed to retrieve data after {retries} attempts: {e}")
            time.sleep(backoff * 2**i)

# ─────────── helpers ───────────
def parse_match_result(html_content):
    if "Vitality win" in html_content:
        return "p2"  # Vitality win
    elif "Legacy win" in html_content:
        return "p1"  # Legacy win
    elif "match postponed" in html_content or "match canceled" in html_content:
        return "p3"  # 50-50
    else:
        return "p3"  # Default to 50-50 if unclear

# ─────────── main ───────────
if __name__ == "__main__":
    current_date = datetime.utcnow()
    match_date = datetime(2025, 6, 12, 15, 0)  # 11:00 AM ET converted to UTC
    if current_date < match_date:
        print("recommendation: p4")  # Too early / in-progress
    elif current_date > datetime(2025, 6, 28, 23, 59):
        print("recommendation: p3")  # Resolved to 50-50 if delayed beyond June 28, 2025
    else:
        try:
            html_content = _get(HLTV_EVENT_URL)
            result = parse_match_result(html_content)
            print(f"recommendation: {result}")
        except Exception as e:
            print("recommendation: p3")  # Resolve to 50-50 in case of errors