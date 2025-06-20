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
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"
RESOLUTION_MAP = {
    "EDM": "p2",  # Edmonton Oilers
    "LAK": "p1",  # Los Angeles Kings
    "50-50": "p3"
}

# Function to make API requests
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return None

# Function to check the advancement of a team
def check_team_advancement():
    current_date = datetime.now()
    if current_date > datetime(2025, 5, 20, 23, 59):
        return RESOLUTION_MAP["50-50"]

    # Use proxy endpoint first
    url = f"{PROXY_ENDPOINT}/scores/json/PlayoffSeries"
    data = make_request(url, HEADERS)
    if not data:
        # Fallback to primary endpoint
        url = f"{PRIMARY_ENDPOINT}/scores/json/PlayoffSeries"
        data = make_request(url, HEADERS)

    if data:
        for series in data:
            if series['Round'] == 1 and {'EDM', 'LAK'} <= {series['HomeTeam'], series['AwayTeam']}:
                if series['Status'] == "Completed":
                    if series['Winner'] == "EDM":
                        return RESOLUTION_MAP["EDM"]
                    elif series['Winner'] == "LAK":
                        return RESOLUTION_MAP["LAK"]
                elif series['Status'] in ["Canceled", "Postponed"]:
                    return RESOLUTION_MAP["50-50"]
    return RESOLUTION_MAP["50-50"]

# Main execution
if __name__ == "__main__":
    result = check_team_advancement()
    print(f"recommendation: {result}")