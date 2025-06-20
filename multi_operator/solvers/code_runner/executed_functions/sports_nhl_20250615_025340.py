import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
GAME_DATE = "2025-06-14"
PLAYER_NAME = "Aleksander Barkov"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# API Endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Resolution map
RESOLUTION_MAP = {
    "Yes": "p2",  # Player scored more than 0.5 goals
    "No": "p1",   # Player did not score more than 0.5 goals
    "50-50": "p3"
}

def get_data(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def check_player_goals(game_id, player_name):
    url = f"{PRIMARY_ENDPOINT}/scores/json/PlayerGameStatsByGame/{game_id}"
    data = get_data(url, HEADERS)
    if data:
        for player in data:
            if player["Name"] == player_name:
                goals = player.get("Goals", 0)
                return "Yes" if goals > 0.5 else "No"
    return "50-50"

def find_game_id(team1, team2, game_date):
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{game_date}"
    games = get_data(url, HEADERS)
    if games:
        for game in games:
            if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2} and game["Status"] == "Final":
                return game["GameID"]
    return None

def main():
    team1 = TEAM_ABBREVIATIONS["Edmonton Oilers"]
    team2 = TEAM_ABBREVIATIONS["Florida Panthers"]
    game_id = find_game_id(team1, team2, GAME_DATE)
    if game_id:
        result = check_player_goals(game_id, PLAYER_NAME)
        print("recommendation:", RESOLUTION_MAP[result])
    else:
        print("recommendation:", RESOLUTION_MAP["50-50"])

if __name__ == "__main__":
    main()