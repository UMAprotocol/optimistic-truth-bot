import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
HLTV_API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")

# Constants
EVENT_DATE = "2025-06-14"
MATCH_TIME = "11:00 AM ET"
TEAM_1 = "3DMAX"
TEAM_2 = "paiN"
HLTV_EVENT_ID = "7902"
HLTV_BASE_URL = "https://api.sportsdata.io/v3/cbb/scores/json"
HLTV_PROXY_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Headers for API request
HEADERS = {
    "Ocp-Apim-Subscription-Key": HLTV_API_KEY
}

def get_match_result():
    # Construct URL
    url = f"{HLTV_BASE_URL}/GamesByDate/{EVENT_DATE}"
    proxy_url = f"{HLTV_PROXY_URL}/GamesByDate/{EVENT_DATE}"

    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, headers=HEADERS, timeout=10)
        if not response.ok:
            # Fallback to primary endpoint if proxy fails
            response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return "p4"  # Unable to fetch data

    # Parse response
    games = response.json()
    for game in games:
        if game['HomeTeamName'] == TEAM_1 and game['AwayTeamName'] == TEAM_2:
            if game['Status'] == "Final":
                if game['HomeTeamScore'] > game['AwayTeamScore']:
                    return "p2"  # 3DMAX wins
                elif game['HomeTeamScore'] < game['AwayTeamScore']:
                    return "p1"  # paiN wins
                else:
                    return "p3"  # Tie
            elif game['Status'] in ["Canceled", "Postponed"]:
                return "p3"  # Canceled or postponed
            else:
                return "p4"  # In progress or not started
    return "p4"  # No match found or other cases

if __name__ == "__main__":
    result = get_match_result()
    print(f"recommendation: {result}")