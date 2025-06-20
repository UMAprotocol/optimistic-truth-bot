import os
import requests
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Constants
EVENT_DATE = "2025-06-12"
MATCH_TIME = "18:15"  # 6:15 PM ET
TEAMS = ("MOUZ", "FaZe")
HLTV_EVENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"
RESOLUTION_MAP = {
    "MOUZ": "p2",
    "FaZe": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Function to fetch data from HLTV
def fetch_hltv_data(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch data from HLTV: {e}")
        return None

# Function to determine the outcome of the match
def determine_outcome(data):
    if not data:
        return RESOLUTION_MAP["Too early to resolve"]

    for match in data.get('matches', []):
        if match['date'] == EVENT_DATE and match['time'] == MATCH_TIME and set(match['teams']) == set(TEAMS):
            if match['status'] == 'completed':
                winner = match['winner']
                return RESOLUTION_MAP[winner]
            elif match['status'] in ['canceled', 'postponed']:
                return RESOLUTION_MAP["50-50"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main function to resolve the market
def resolve_market():
    data = fetch_hltv_data(HLTV_EVENT_URL)
    recommendation = determine_outcome(data)
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    resolve_market()