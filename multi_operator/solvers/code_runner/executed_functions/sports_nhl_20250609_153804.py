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
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Game and player details
GAME_DATE = "2025-05-29"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Dallas Stars": "DAL"}
PLAYER_NAME = "Connor McDavid"

# Resolution map based on the outcome
RESOLUTION_MAP = {
    "Yes": "p2",  # Connor McDavid scores 1+ goals
    "No": "p1",   # Connor McDavid does not score 1+ goals
    "Unknown": "p3"  # Game canceled, postponed, or player did not play
}

def get_game_data(date, team1, team2):
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if team1 in game['HomeTeam'] or team1 in game['AwayTeam']:
                if team2 in game['HomeTeam'] or team2 in game['AwayTeam']:
                    return game
    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
    return None

def check_player_performance(game_id, player_name):
    url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        player_stats = response.json()
        for stat in player_stats:
            if player_name in stat['Name']:
                return stat['Goals'] >= 1
    except requests.RequestException as e:
        print(f"Error fetching player stats: {e}")
    return False

def main():
    team1 = TEAM_ABBREVIATIONS["Edmonton Oilers"]
    team2 = TEAM_ABBREVIATIONS["Dallas Stars"]
    game = get_game_data(GAME_DATE, team1, team2)
    if not game:
        print("recommendation:", RESOLUTION_MAP["Unknown"])
        return

    if game['Status'] != "Final":
        print("recommendation:", RESOLUTION_MAP["No"])
        return

    scored = check_player_performance(game['GameId'], PLAYER_NAME)
    if scored:
        print("recommendation:", RESOLUTION_MAP["Yes"])
    else:
        print("recommendation:", RESOLUTION_MAP["No"])

if __name__ == "__main__":
    main()