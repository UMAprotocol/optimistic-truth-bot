import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Constants
HLTV_EVENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"
MATCH_DATE = "2025-06-14"
TEAM_3DMAX = "3DMAX"
TEAM_PAIN = "paiN"
RESOLUTION_MAP = {
    TEAM_3DMAX: "p2",  # 3DMAX win
    TEAM_PAIN: "p1",  # paiN win
    "50-50": "p3",    # Tie, canceled, or delayed
    "Too early to resolve": "p4"
}

# Function to get match results from HLTV
def get_match_result():
    try:
        response = requests.get(HLTV_EVENT_URL, timeout=10)
        response.raise_for_status()
        # Simulated parsing logic (actual logic would depend on the page structure)
        # This is a placeholder to illustrate how you might parse the result
        if datetime.now().strftime('%Y-%m-%d') < MATCH_DATE:
            return RESOLUTION_MAP["Too early to resolve"]
        # Example condition checks
        if "3DMAX defeated paiN" in response.text:
            return RESOLUTION_MAP[TEAM_3DMAX]
        elif "paiN defeated 3DMAX" in response.text:
            return RESOLUTION_MAP[TEAM_PAIN]
        elif "match was canceled" in response.text or "match was postponed" in response.text:
            return RESOLUTION_MAP["50-50"]
        else:
            return RESOLUTION_MAP["50-50"]
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return RESOLUTION_MAP["50-50"]

# Main execution
if __name__ == "__main__":
    result = get_match_result()
    print("recommendation:", result)