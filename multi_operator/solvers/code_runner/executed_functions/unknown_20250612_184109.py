import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
HLTV_EVENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"
MATCH_DATE = "2025-06-12"
MATCH_TIME = "14:45"
TEAM_A = "Natus Vincere"
TEAM_B = "Nemiga"
TIMEOUT_DELAY = 10

# Load API key from environment
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing API key for Sports Data IO NBA")

# Headers for HTTP requests
HEADERS = {
    "Ocp-Apim-Subscription-Key": API_KEY
}

# Function to fetch match data from HLTV
def fetch_match_data():
    try:
        response = requests.get(HLTV_EVENT_URL, headers=HEADERS, timeout=TIMEOUT_DELAY)
        response.raise_for_status()
        matches = response.json()
        for match in matches:
            if match['date'] == MATCH_DATE and match['time'] == MATCH_TIME:
                if match['teamA']['name'] == TEAM_A and match['teamB']['name'] == TEAM_B:
                    return match
        return None
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Function to determine the outcome of the match
def determine_outcome(match):
    if not match:
        return "p3"  # Assume 50-50 if no match data is found
    if match['status'] == "canceled":
        return "p3"
    if match['winner'] == TEAM_A:
        return "p2"
    elif match['winner'] == TEAM_B:
        return "p1"
    else:
        return "p3"

# Main function to run the script
def main():
    match_data = fetch_match_data()
    result = determine_outcome(match_data)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()