import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API configuration
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/mlb"

# Resolution map
RESOLUTION_MAP = {
    "Rockies": "p2",
    "Braves": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Function to make API requests
def make_api_request(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        try:
            # Fallback to proxy endpoint if primary fails
            proxy_url = url.replace(PRIMARY_ENDPOINT, PROXY_ENDPOINT)
            response = requests.get(proxy_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Failed to retrieve data from both primary and proxy endpoints: {e}")
            return None

# Function to determine the outcome of the game
def determine_outcome(game_date, home_team, away_team):
    date_formatted = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today_url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date_formatted}"
    games = make_api_request(games_today_url)

    if not games:
        return RESOLUTION_MAP["Too early to resolve"]

    for game in games:
        if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
            if game['Status'] == 'Final':
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return RESOLUTION_MAP[home_team]
                elif away_score > home_score:
                    return RESOLUTION_MAP[away_team]
            elif game['Status'] in ['Canceled', 'Postponed']:
                return RESOLUTION_MAP["50-50"]
            else:
                return RESOLUTION_MAP["Too early to resolve"]

    return RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    game_date = "2025-06-15"
    home_team = "Braves"
    away_team = "Rockies"
    result = determine_outcome(game_date, home_team, away_team)
    print(f"recommendation: {result}")