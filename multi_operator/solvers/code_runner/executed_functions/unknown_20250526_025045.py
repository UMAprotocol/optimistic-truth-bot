import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not NBA_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# API configuration
HEADERS = {"Ocp-Apim-Subscription-Key": NBA_API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{PROXY_ENDPOINT}{path}", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            # Fallback to primary endpoint if proxy fails
            response = requests.get(f"{PRIMARY_ENDPOINT}{path}", headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
    except requests.RequestException as e:
        print(f"Error during API request: {e}")
        return None

# Function to determine the outcome of the game
def resolve_market(date_str, team1, team2):
    path = f"/scores/json/GamesByDate/{date_str}"
    games = make_request(PRIMARY_ENDPOINT, path)
    if games is None:
        return "p3"  # Assume unknown/50-50 if API fails

    for game in games:
        if {game['HomeTeam'], game['AwayTeam']} == {team1, team2}:
            if game['Status'] == "Final":
                if game['HomeTeam'] == team1 and game['HomeTeamScore'] > game['AwayTeamScore']:
                    return "p1"
                elif game['AwayTeam'] == team1 and game['AwayTeamScore'] > game['HomeTeamScore']:
                    return "p1"
                elif game['HomeTeam'] == team2 and game['HomeTeamScore'] > game['AwayTeamScore']:
                    return "p2"
                elif game['AwayTeam'] == team2 and game['AwayTeamScore'] > game['HomeTeamScore']:
                    return "p2"
            elif game['Status'] == "Canceled":
                return "p3"
            elif game['Status'] == "Postponed":
                return "p3"
    return "p3"  # Default to unknown/50-50 if no matching game found or game not final

# Main execution
if __name__ == "__main__":
    game_date = "2025-05-25"
    team_knicks = "NYK"
    team_pacers = "IND"
    result = resolve_market(game_date, team_knicks, team_pacers)
    print(f"recommendation: {result}")