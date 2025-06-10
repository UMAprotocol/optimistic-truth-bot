import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Constants
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"

# Function to make API requests
def make_request(endpoint, path, use_proxy=False):
    url = f"{PROXY_ENDPOINT if use_proxy else PRIMARY_ENDPOINT}{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if use_proxy:
            print("Proxy failed, trying primary endpoint...")
            return make_request(endpoint, path, use_proxy=False)
        else:
            print(f"Error: {e}")
            return None

# Function to determine the advancing team
def determine_advancing_team():
    current_date = datetime.now()
    if current_date > datetime(2025, 7, 20, 23, 59):
        return "p3"  # Market resolves 50-50 if beyond July 20, 2025

    # Fetch playoff data
    playoff_data = make_request(PRIMARY_ENDPOINT, "/scores/json/PlayoffTeams/2025", use_proxy=True)
    if playoff_data is None:
        return "p3"  # Resolve as unknown/50-50 if data cannot be fetched

    # Check teams in the finals
    for team in playoff_data:
        if team["Key"] == "IND" and team["Conference"] == "Eastern" and team["PlayoffStatus"] == "Finals":
            return "p2"  # Pacers advance to the finals
        elif team["Key"] == "NYK" and team["Conference"] == "Eastern" and team["PlayoffStatus"] == "Finals":
            return "p1"  # Knicks advance to the finals

    return "p4"  # Too early to resolve if no team has advanced yet

# Main execution
if __name__ == "__main__":
    result = determine_advancing_team()
    print(f"recommendation: {result}")