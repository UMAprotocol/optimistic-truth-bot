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
def make_api_request(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to find the game and determine the outcome
def resolve_game(date, home_team, away_team):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{formatted_date}"
    games = make_api_request(url)
    if games is None:
        print("Using proxy endpoint due to primary endpoint failure.")
        url = f"{PROXY_ENDPOINT}/GamesByDate/{formatted_date}"
        games = make_api_request(url)
        if games is None:
            return "p4"  # Unable to resolve due to API failure

    for game in games:
        if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
            if game['Status'] == 'Final':
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    return "p1" if home_team == "Pirates" else "p2"
                else:
                    return "p2" if away_team == "Pirates" else "p1"
            elif game['Status'] in ['Canceled', 'Postponed']:
                return "p3"
            else:
                return "p4"  # Game not final
    return "p4"  # No game found

# Main execution
if __name__ == "__main__":
    date_of_game = "2025-06-13"
    home_team = "Cubs"
    away_team = "Pirates"
    result = resolve_game(date_of_game, home_team, away_team)
    print(f"recommendation: {result}")