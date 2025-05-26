import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Team abbreviations
TEAMS = {
    "Dallas Stars": "DAL",
    "Edmonton Oilers": "EDM"
}

# Resolution map based on team abbreviations
RESOLUTION_MAP = {
    "DAL": "p2",  # Dallas Stars win
    "EDM": "p1",  # Edmonton Oilers win
    "50-50": "p3",  # Game canceled
    "Too early to resolve": "p4"  # Game not yet played or in progress
}

def get_game_data(date):
    """ Fetch game data for a specific date """
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        # Fallback to proxy endpoint
        try:
            response = requests.get(f"{PROXY_ENDPOINT}/GamesByDate/{date}", headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
            return None

def resolve_market(games, team1, team2):
    """ Determine the outcome of the market based on game results """
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            if game["Status"] == "Final":
                if game["HomeTeam"] == team1 and game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                    return RESOLUTION_MAP[team1]
                elif game["AwayTeam"] == team1 and game["AwayTeamRuns"] > game["HomeTeamRuns"]:
                    return RESOLUTION_MAP[team1]
                elif game["HomeTeam"] == team2 and game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                    return RESOLUTION_MAP[team2]
                elif game["AwayTeam"] == team2 and game["AwayTeamRuns"] > game["HomeTeamRuns"]:
                    return RESOLUTION_MAP[team2]
            elif game["Status"] == "Canceled":
                return RESOLUTION_MAP["50-50"]
            elif game["Status"] == "Postponed":
                return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    # Define the date of the game
    game_date = "2025-05-25"
    # Teams involved in the game
    team1 = TEAMS["Edmonton Oilers"]
    team2 = TEAMS["Dallas Stars"]

    # Fetch game data
    games = get_game_data(game_date)

    # Resolve the market based on the game data
    if games:
        recommendation = resolve_market(games, team1, team2)
    else:
        recommendation = RESOLUTION_MAP["Too early to resolve"]

    print("recommendation:", recommendation)