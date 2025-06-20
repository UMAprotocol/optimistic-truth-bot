import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
EVENT_DATE = "2025-06-15"
TEAM1 = "Virtus.pro"
TEAM2 = "paiN"
HLTV_EVENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"
TIMEOUT = 10

# Load API key from environment
HLTV_API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")
if not HLTV_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_CBB_API_KEY")

# Headers for HTTP requests
HEADERS = {"Ocp-Apim-Subscription-Key": HLTV_API_KEY}

def get_match_result():
    try:
        response = requests.get(HLTV_EVENT_URL, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        matches = response.json()

        # Find the specific match
        for match in matches:
            if match['team1']['name'] == TEAM1 and match['team2']['name'] == TEAM2:
                match_date = datetime.strptime(match['date'], "%Y-%m-%d %H:%M:%S")
                if match_date.strftime("%Y-%m-%d") == EVENT_DATE:
                    if match['winner'] == TEAM1:
                        return "p1"
                    elif match['winner'] == TEAM2:
                        return "p2"
                    else:
                        return "p3"  # Assuming tie or no result as 50-50
        return "p3"  # No match found or no result, assume canceled or postponed

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return "p3"  # Assume 50-50 in case of request failure

if __name__ == "__main__":
    result = get_match_result()
    print(f"recommendation: {result}")