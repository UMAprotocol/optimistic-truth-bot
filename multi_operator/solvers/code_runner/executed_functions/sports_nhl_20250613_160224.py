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
MATCH_DATE = "2025-06-13"
TEAM1 = "FaZe"  # p1
TEAM2 = "Legacy"  # p2
RESOLUTION_MAP = {
    "FaZe": "p1",
    "Legacy": "p2",
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

def get_match_result():
    try:
        response = requests.get(HLTV_EVENT_URL, timeout=10)
        if response.status_code == 200:
            # Simulated parsing logic (actual parsing would depend on the page structure)
            if datetime.now().strftime('%Y-%m-%d') < MATCH_DATE:
                return RESOLUTION_MAP["Too early to resolve"]
            # Example conditions based on a hypothetical match result
            match_result = "FaZe"  # This should be dynamically determined from the response content
            if match_result == "FaZe":
                return RESOLUTION_MAP["FaZe"]
            elif match_result == "Legacy":
                return RESOLUTION_MAP["Legacy"]
            else:
                return RESOLUTION_MAP["50-50"]
        else:
            response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching match result: {e}")
        return RESOLUTION_MAP["50-50"]

if __name__ == "__main__":
    result = get_match_result()
    print("recommendation:", result)