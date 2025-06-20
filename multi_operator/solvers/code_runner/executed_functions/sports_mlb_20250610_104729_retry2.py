import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/mlb"

# Function to make API requests
def make_api_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}/{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        if endpoint == PROXY_ENDPOINT:
            return None  # If proxy fails, return None
        else:
            # Fallback to proxy if primary fails
            return make_api_request(PROXY_ENDPOINT, path)

# Function to determine the outcome of the game
def determine_outcome(game_date, home_team, away_team):
    date_str = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today = make_api_request(PRIMARY_ENDPOINT, f"GamesByDate/{date_str}")

    if games_today is None:
        return "recommendation: p4"  # Unable to fetch data

    for game in games_today:
        if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
            if game['Status'] == 'Final':
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    return "recommendation: p1" if home_team == "Tampa Bay Rays" else "recommendation: p2"
                else:
                    return "recommendation: p2" if away_team == "Tampa Bay Rays" else "recommendation: p1"
            elif game['Status'] == 'Postponed':
                return "recommendation: p4"  # Game postponed, check later
            elif game['Status'] == 'Canceled':
                return "recommendation: p3"  # Game canceled, resolve 50-50
    return "recommendation: p4"  # No game found or in progress

# Main execution function
if __name__ == "__main__":
    game_date = "2025-06-09"
    home_team = "Boston Red Sox"
    away_team = "Tampa Bay Rays"
    print(determine_outcome(game_date, home_team, away_team))