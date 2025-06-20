import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not NHL_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Constants
HEADERS = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}
GAME_DATE = "2025-06-12"
PLAYER_NAME = "Evan Bouchard"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# API Endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nhl-proxy"

# Helper functions
def get_json_response(url, headers, tag="API Request"):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"{tag} failed: {e}")
        return None

def check_player_goals(game_id, player_name):
    url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
    game_stats = get_json_response(url, HEADERS, "Player Game Stats")
    if game_stats:
        for stat in game_stats:
            if stat["Name"] == player_name and stat["Goals"] > 0.5:
                return True
    return False

def find_game_id(team1, team2, date):
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date}"
    games = get_json_response(url, HEADERS, "Games By Date")
    if games:
        for game in games:
            if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2} and game["Status"] == "Final":
                return game["GameID"]
    return None

# Main execution
def main():
    team1 = TEAM_ABBREVIATIONS["Edmonton Oilers"]
    team2 = TEAM_ABBREVIATIONS["Florida Panthers"]
    game_id = find_game_id(team1, team2, GAME_DATE)
    if game_id:
        if check_player_goals(game_id, PLAYER_NAME):
            print("recommendation: p2")  # Player scored more than 0.5 goals
        else:
            print("recommendation: p1")  # Player did not score more than 0.5 goals
    else:
        print("recommendation: p3")  # Game not found or not completed

if __name__ == "__main__":
    main()