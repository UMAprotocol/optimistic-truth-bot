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
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}/{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if endpoint == PROXY_ENDPOINT:
            print("Proxy failed, trying primary endpoint")
            return make_request(PRIMARY_ENDPOINT, path)
        else:
            print(f"Failed to retrieve data: {e}")
            return None

# Function to find the game and determine the outcome
def resolve_nba_game(date, team1, team2):
    games_today = make_request(PROXY_ENDPOINT, f"GamesByDate/{date}")
    if games_today is None:
        return "p4"  # Unable to retrieve data

    for game in games_today:
        if {game['HomeTeam'], game['AwayTeam']} == {team1, team2}:
            if game['Status'] == 'Final':
                if game['HomeTeam'] == team1 and game['HomeTeamScore'] > game['AwayTeamScore']:
                    return "p1"
                elif game['AwayTeam'] == team1 and game['AwayTeamScore'] > game['HomeTeamScore']:
                    return "p1"
                elif game['HomeTeam'] == team2 and game['HomeTeamScore'] > game['AwayTeamScore']:
                    return "p2"
                elif game['AwayTeam'] == team2 and game['AwayTeamScore'] > game['HomeTeamScore']:
                    return "p2"
            elif game['Status'] == 'Postponed':
                return "p4"  # Market remains open
            elif game['Status'] == 'Canceled':
                return "p3"  # Resolve as 50-50
    return "p4"  # No matching game found or game not final

# Main execution function
if __name__ == "__main__":
    date_str = "2025-06-05"
    team1 = "OKL"  # Oklahoma City Thunder
    team2 = "IND"  # Indiana Pacers
    result = resolve_nba_game(date_str, team1, team2)
    print(f"recommendation: {result}")