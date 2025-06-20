import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not NHL_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Constants
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nhl-proxy"
HEADERS = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}
DEADLINE = datetime(2025, 7, 24, 23, 59)  # July 24, 2025, 11:59 PM ET

# Function to make API requests
def make_request(url, use_proxy=False):
    endpoint = PROXY_ENDPOINT if use_proxy else PRIMARY_ENDPOINT
    full_url = f"{endpoint}{url}"
    try:
        response = requests.get(full_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if use_proxy:
            print("Proxy failed, trying primary endpoint.")
            return make_request(url, use_proxy=False)
        else:
            print(f"Failed to retrieve data: {e}")
            return None

# Function to check if a Canadian team won the Stanley Cup
def check_canadian_team_winner():
    current_time = datetime.now()
    if current_time > DEADLINE:
        print("recommendation: p1")  # No, because deadline has passed
        return

    # Fetch the latest season winner
    season_winner_data = make_request("/scores/json/CurrentSeason")
    if season_winner_data:
        season = season_winner_data['Season']
        winner_info = make_request(f"/scores/json/Standings/{season}")
        if winner_info:
            for team in winner_info:
                if team['Conference'] == 'Stanley Cup' and 'Canada' in team['City']:
                    print("recommendation: p2")  # Yes, Canadian team won
                    return
    print("recommendation: p1")  # No, no Canadian team won or data unavailable

# Main execution
if __name__ == "__main__":
    check_canadian_team_winner()