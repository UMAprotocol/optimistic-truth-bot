import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API headers
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Game details
GAME_DATE = "2025-05-28"
TEAM1 = "St. Louis Cardinals"
TEAM2 = "Baltimore Orioles"

# API endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/mlb/scores/json"

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
def resolve_game():
    date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PROXY_ENDPOINT}/GamesByDate/{date_formatted}"
    games = make_api_request(url)
    if not games:
        url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date_formatted}"
        games = make_api_request(url)
    if games:
        for game in games:
            if {game["HomeTeam"], game["AwayTeam"]} == {TEAM1, TEAM2}:
                if game["Status"] == "Final":
                    if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                        return "p2" if game["HomeTeam"] == TEAM1 else "p1"
                    else:
                        return "p1" if game["HomeTeam"] == TEAM2 else "p2"
                elif game["Status"] == "Canceled":
                    return "p3"
                elif game["Status"] == "Postponed":
                    # Market remains open, but we return p4 for now
                    return "p4"
    return "p4"

# Main function to run the resolver
if __name__ == "__main__":
    result = resolve_game()
    print(f"recommendation: {result}")