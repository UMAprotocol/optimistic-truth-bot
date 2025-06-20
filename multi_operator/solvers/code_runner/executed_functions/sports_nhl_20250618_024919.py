import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Constants
GAME_DATE = "2025-06-17"
PLAYER_NAME = "Connor McDavid"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# API Endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Resolution map
RESOLUTION_MAP = {
    "Yes": "p2",  # Player scored more than 0.5 goals
    "No": "p1",   # Player did not score more than 0.5 goals
    "50-50": "p3" # Game not completed by the specified date
}

def get_game_data(date, team1, team2):
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] == team1 and game['AwayTeam'] == team2:
                return game
            if game['HomeTeam'] == team2 and game['AwayTeam'] == team1:
                return game
    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
    return None

def check_player_goals(game_id, player_name):
    url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        player_stats = response.json()
        for stat in player_stats:
            if stat['Name'] == player_name:
                goals = stat.get('Goals', 0)
                return "Yes" if goals > 0.5 else "No"
    except requests.RequestException as e:
        print(f"Error fetching player stats: {e}")
    return "No"

def main():
    game = get_game_data(GAME_DATE, TEAM_ABBREVIATIONS["Edmonton Oilers"], TEAM_ABBREVIATIONS["Florida Panthers"])
    if not game:
        print("Game data not found or error occurred.")
        return

    if datetime.now() > datetime.strptime("2025-12-31 23:59", "%Y-%m-%d %H:%M"):
        print("recommendation:", RESOLUTION_MAP["50-50"])
        return

    result = check_player_goals(game['GameID'], PLAYER_NAME)
    print("recommendation:", RESOLUTION_MAP[result])

if __name__ == "__main__":
    main()