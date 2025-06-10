import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nba-proxy"

# Function to make API requests
def make_request(endpoint, path):
    url = f"{endpoint}{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if endpoint == PROXY_ENDPOINT:
            print("Proxy failed, trying primary endpoint")
            return make_request(PRIMARY_ENDPOINT, path)
        else:
            print(f"Error: {e}")
            return None

# Function to determine the advancing team
def get_advancing_team():
    current_year = datetime.now().year
    # Check if the current year matches the event year, if not, use the event year
    if current_year != 2025:
        current_year = 2025

    # Fetch playoff bracket for the year
    playoff_bracket = make_request(PROXY_ENDPOINT, f"/scores/json/PlayoffBracket/{current_year}")
    if playoff_bracket:
        for round_info in playoff_bracket:
            if round_info['Round'] == 4:  # NBA Finals
                for matchup in round_info['Games']:
                    if 'Indiana Pacers' in matchup['Teams'] or 'New York Knicks' in matchup['Teams']:
                        if matchup['Winner'] == 'Indiana Pacers':
                            return "Pacers"
                        elif matchup['Winner'] == 'New York Knicks':
                            return "Knicks"
    return "unknown"

# Main execution
if __name__ == "__main__":
    advancing_team = get_advancing_team()
    if advancing_team == "Pacers":
        print("recommendation: p2")
    elif advancing_team == "Knicks":
        print("recommendation: p1")
    else:
        print("recommendation: p3")