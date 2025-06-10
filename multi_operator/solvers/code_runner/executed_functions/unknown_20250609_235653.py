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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Function to make API requests
def make_request(endpoint, path):
    url = f"{endpoint}/scores/json/{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if endpoint == PROXY_ENDPOINT:
            print(f"Proxy failed, trying primary endpoint. Error: {e}")
            return make_request(PRIMARY_ENDPOINT, path)
        else:
            print(f"Failed to retrieve data from primary endpoint. Error: {e}")
            return None

# Function to determine the outcome of the game
def resolve_market(date, team1, team2):
    games_today = make_request(PROXY_ENDPOINT, f"GamesByDate/{date}")
    if games_today is None:
        return "recommendation: p4"  # Unable to retrieve data

    for game in games_today:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            if game["Status"] == "Final":
                if game["HomeTeam"] == team1 and game["HomeTeamScore"] > game["AwayTeamScore"]:
                    return "recommendation: p1"
                elif game["AwayTeam"] == team1 and game["AwayTeamScore"] > game["HomeTeamScore"]:
                    return "recommendation: p1"
                elif game["HomeTeam"] == team2 and game["HomeTeamScore"] > game["AwayTeamScore"]:
                    return "recommendation: p2"
                elif game["AwayTeam"] == team2 and game["AwayTeamScore"] > game["HomeTeamScore"]:
                    return "recommendation: p2"
            elif game["Status"] == "Postponed":
                return "recommendation: p4"  # Market remains open
            elif game["Status"] == "Canceled":
                return "recommendation: p3"  # Resolve as 50-50
    return "recommendation: p4"  # No matching game found or game not final

# Main execution
if __name__ == "__main__":
    DATE = "2025-05-31"
    TEAM1 = "IND"  # Indiana Pacers
    TEAM2 = "NYK"  # New York Knicks
    print(resolve_market(DATE, TEAM1, TEAM2))