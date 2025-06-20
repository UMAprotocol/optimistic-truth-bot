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
PLAYER_NAME = "Carter Verhaeghe"
TEAMS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# Resolution conditions
RESOLUTION_MAP = {
    "Yes": "p2",  # Player scores more than 0.5 goals
    "No": "p1",   # Player does not score more than 0.5 goals
    "50-50": "p3" # Game not completed by the specified date
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

def check_player_goals(game_id, player_name):
    url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        player_stats = response.json()
        for stat in player_stats:
            if player_name in stat['Name']:
                goals = stat.get('Goals', 0)
                return "Yes" if goals > 0.5 else "No"
    except requests.RequestException as e:
        print(f"Error fetching player stats: {e}")
    return "No"

def main():
    team1, team2 = TEAMS["Edmonton Oilers"], TEAMS["Florida Panthers"]
    game = get_game_data(GAME_DATE, team1, team2)
    if game:
        if datetime.now() > datetime.strptime("2025-12-31 23:59", "%Y-%m-%d %H:%M"):
            result = "50-50"
        else:
            result = check_player_goals(game['GameId'], PLAYER_NAME)
    else:
        result = "50-50"
    print("recommendation:", RESOLUTION_MAP[result])

if __name__ == "__main__":
    main()