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
DATE = "2025-06-05"
TEAM1 = "Complexity"  # p2
TEAM2 = "TYLOO"       # p1
EVENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"

# Mapping of teams to resolution conditions
RESOLUTION_MAP = {
    TEAM1: "p2",
    TEAM2: "p1",
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Function to fetch data from HLTV
def fetch_match_result():
    try:
        response = requests.get(EVENT_URL, timeout=10)
        if response.status_code == 200:
            # This is a placeholder for actual data parsing logic
            # You would parse the HTML or JSON response here to find the match result
            # For example, you might look for a specific element containing the match score
            # Let's assume we find the match result as follows:
            match_result = "Complexity"  # This should be dynamically extracted from the response

            if match_result == TEAM1:
                return RESOLUTION_MAP[TEAM1]
            elif match_result == TEAM2:
                return RESOLUTION_MAP[TEAM2]
            else:
                return RESOLUTION_MAP["50-50"]
        else:
            return RESOLUTION_MAP["Too early to resolve"]
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    result = fetch_match_result()
    print(f"recommendation: {result}")