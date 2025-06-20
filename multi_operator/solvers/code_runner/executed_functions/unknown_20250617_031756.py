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

# Function to determine the outcome of the game
def resolve_market(date_str, team1, team2):
    games_today = make_request(f"/scores/json/GamesByDate/{date_str}")
    if games_today is None:
        return "p4"  # Unable to retrieve data, assume in-progress

    for game in games_today:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            if game["Status"] == "Final":
                if game["HomeTeam"] == team1 and game["HomeTeamScore"] > game["AwayTeamScore"]:
                    return "p1"  # Team1 wins
                elif game["AwayTeam"] == team1 and game["AwayTeamScore"] > game["HomeTeamScore"]:
                    return "p1"  # Team1 wins
                else:
                    return "p2"  # Team2 wins
            elif game["Status"] == "Postponed":
                return "p4"  # Game postponed, market remains open
            elif game["Status"] == "Canceled":
                return "p3"  # Game canceled, resolve 50-50
    return "p4"  # No matching game found or not final, assume in-progress

# Main execution
if __name__ == "__main__":
    game_date = "2025-06-16"
    team1 = "OKC"  # Oklahoma City Thunder
    team2 = "IND"  # Indiana Pacers
    result = resolve_market(game_date, team1, team2)
    print(f"recommendation: {result}")