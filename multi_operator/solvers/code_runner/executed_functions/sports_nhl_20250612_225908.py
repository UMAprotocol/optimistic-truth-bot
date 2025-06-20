import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Constants
HLTV_BASE_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"
MATCH_DATE = datetime(2025, 6, 12, 18, 15)  # 6:15 PM ET
END_DATE = datetime(2025, 6, 28, 23, 59)  # End of the day on June 28, 2025
TEAM_MOUZ = "MOUZ"
TEAM_FAZE = "FaZe"
RESOLUTION_MAP = {
    TEAM_MOUZ: "p2",
    TEAM_FAZE: "p1",
    "50-50": "p3"
}

# Helper function to make HTTP GET requests
def make_request(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Function to determine the outcome of the match
def resolve_match():
    current_time = datetime.utcnow()
    if current_time < MATCH_DATE:
        return "p4"  # Match has not yet occurred

    # Fetch match data from HLTV
    match_data = make_request(HLTV_BASE_URL)
    if not match_data:
        return "p3"  # Unable to fetch data, resolve as 50-50

    # Check if the match is postponed or canceled
    if match_data.get('status') in ['postponed', 'canceled']:
        return RESOLUTION_MAP["50-50"]

    # Check if the match is delayed beyond the allowed date
    if current_time > END_DATE:
        return RESOLUTION_MAP["50-50"]

    # Determine the winner
    winner = match_data.get('winner')
    if winner == TEAM_MOUZ:
        return RESOLUTION_MAP[TEAM_MOUZ]
    elif winner == TEAM_FAZE:
        return RESOLUTION_MAP[TEAM_FAZE]
    else:
        return RESOLUTION_MAP["50-50"]

# Main execution
if __name__ == "__main__":
    recommendation = resolve_match()
    print(f"recommendation: {recommendation}")