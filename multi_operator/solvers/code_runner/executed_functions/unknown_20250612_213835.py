import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# ─────────── configuration ───────────
load_dotenv()
HLTV_API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")
if not HLTV_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_CBB_API_KEY")
HEADERS = {"Ocp-Apim-Subscription-Key": HLTV_API_KEY}

# ─────────── generic GET wrapper ───────────
def _get(url, headers=None, timeout=10):
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# ─────────── main logic ───────────
def resolve_match():
    event_date = "2025-06-12"
    match_date = datetime.strptime(event_date, "%Y-%m-%d")
    current_date = datetime.now()

    if current_date < match_date:
        return "recommendation: p4"  # Match has not occurred yet

    # URL and headers for HLTV
    url = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"
    headers = {"User-Agent": "Mozilla/5.0"}

    # Fetch match data
    data = _get(url, headers=headers)
    if data is None:
        return "recommendation: p3"  # Unable to fetch data, assume unknown

    # Analyze the match result
    try:
        # This is a placeholder for actual data parsing logic
        # You would need to parse the HTML or JSON from HLTV to find the match result
        # For example, you might look for a specific match ID and check the winner
        # Here we just simulate the logic assuming data is available
        match_info = data.get('matches', {}).get('551975', {})
        if not match_info:
            return "recommendation: p3"  # Match data not found, assume unknown

        if match_info.get('status') in ['canceled', 'postponed']:
            return "recommendation: p3"  # Match canceled or postponed

        winner = match_info.get('winner')
        if winner == "Spirit":
            return "recommendation: p2"
        elif winner == "Lynn Vision":
            return "recommendation: p1"
        else:
            return "recommendation: p3"  # No clear winner or data is ambiguous
    except Exception as e:
        print(f"Error processing match data: {e}")
        return "recommendation: p3"  # Fallback in case of unexpected error

# ─────────── run the resolver ───────────
if __name__ == "__main__":
    result = resolve_match()
    print(result)