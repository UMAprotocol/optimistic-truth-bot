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
GAME_DATE = "2025-06-04"
TEAM_ABBR_EDMONTON = "EDM"
TEAM_ABBR_FLORIDA = "FLA"
PLAYER_NAME = "Connor McDavid"

# Resolution conditions
RESOLUTION_MAP = {
    "YES": "p2",  # McDavid scores 1+ goals
    "NO": "p1",   # McDavid does not score
    "UNKNOWN": "p3"  # Game postponed, cancelled, or McDavid does not play
}

def get_game_data():
    """Fetch game data for the specified date and teams."""
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{GAME_DATE}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if {game["HomeTeam"], game["AwayTeam"]} == {TEAM_ABBR_EDMONTON, TEAM_ABBR_FLORIDA}:
                return game
    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
    return None

def check_player_performance(game_id):
    """Check if Connor McDavid scored 1+ goals in the specified game."""
    url = f"{PRIMARY_ENDPOINT}/scores/json/BoxScore/{game_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        box_score = response.json()
        for player_stats in box_score["PlayerGames"]:
            if player_stats["Name"] == PLAYER_NAME:
                goals = player_stats.get("Goals", 0)
                return "YES" if goals >= 1 else "NO"
    except requests.RequestException as e:
        print(f"Error fetching player performance: {e}")
    return "UNKNOWN"

def main():
    game = get_game_data()
    if not game:
        print("recommendation:", RESOLUTION_MAP["UNKNOWN"])
        return

    if game["Status"] != "Final":
        print("recommendation:", RESOLUTION_MAP["UNKNOWN"])
        return

    recommendation = check_player_performance(game["GameID"])
    print("recommendation:", RESOLUTION_MAP[recommendation])

if __name__ == "__main__":
    main()