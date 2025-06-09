import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for headers and API endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/mlb"

# Resolution map based on the outcomes
RESOLUTION_MAP = {
    "Blue Jays": "p2",
    "Twins": "p1",
    "50-50": "p3"
}

# Function to make API requests
def make_api_request(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        # Fallback to proxy if primary fails
        try:
            proxy_url = PROXY_ENDPOINT + url.split(PRIMARY_ENDPOINT)[-1]
            response = requests.get(proxy_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Failed to retrieve data from both primary and proxy endpoints: {e}")
            return None

# Function to determine the outcome of the game
def determine_outcome(game_date, home_team, away_team):
    formatted_date = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today_url = f"{PRIMARY_ENDPOINT}/GamesByDate/{formatted_date}"
    games = make_api_request(games_today_url)

    if games is None:
        return "recommendation: p4"  # Unable to retrieve data

    for game in games:
        if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
            if game['Status'] == 'Final':
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return f"recommendation: {RESOLUTION_MAP[home_team]}"
                elif away_score > home_score:
                    return f"recommendation: {RESOLUTION_MAP[away_team]}"
            elif game['Status'] == 'Canceled':
                return f"recommendation: {RESOLUTION_MAP['50-50']}"
            else:
                return "recommendation: p4"  # Game not final or canceled
    return "recommendation: p4"  # No matching game found

# Main execution function
if __name__ == "__main__":
    game_date = "2025-06-06"
    home_team = "Twins"
    away_team = "Blue Jays"
    print(determine_outcome(game_date, home_team, away_team))