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
GAME_DATE = "2025-06-14"
PLAYER_NAME = "Connor McDavid"
TEAMS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# Resolution conditions
RESOLUTION_MAP = {
    "Yes": "p2",  # Player scores more than 0.5 goals
    "No": "p1",   # Player scores 0.5 goals or less
    "50-50": "p3" # Game not completed by the deadline
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
    except requests.exceptions.RequestException as e:
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
                return stat['Goals']
    except requests.exceptions.RequestException as e:
        print(f"Error fetching player stats: {e}")
    return None

def resolve_market():
    current_time = datetime.utcnow()
    deadline = datetime.strptime("2025-12-31 23:59", "%Y-%m-%d %H:%M")
    if current_time > deadline:
        return "recommendation: " + RESOLUTION_MAP["50-50"]

    game = get_game_data(GAME_DATE, TEAMS["Edmonton Oilers"], TEAMS["Florida Panthers"])
    if not game:
        return "recommendation: " + RESOLUTION_MAP["50-50"]

    goals = check_player_goals(game['GameID'], PLAYER_NAME)
    if goals is None:
        return "recommendation: " + RESOLUTION_MAP["50-50"]

    if goals > 0.5:
        return "recommendation: " + RESOLUTION_MAP["Yes"]
    else:
        return "recommendation: " + RESOLUTION_MAP["No"]

if __name__ == "__main__":
    result = resolve_market()
    print(result)