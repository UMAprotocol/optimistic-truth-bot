import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# NHL API endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Game and player details
GAME_DATE = "2025-06-14"
PLAYER_NAME = "Leon Draisaitl"
TEAMS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# Resolution conditions
RESOLUTION_MAP = {
    "Yes": "p2",  # Player scores more than 0.5 goals
    "No": "p1",   # Player does not score more than 0.5 goals
    "50-50": "p3" # Game not completed by the specified date
}

def get_game_data():
    # Construct the URL for the game date
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{GAME_DATE}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] in TEAMS.values() and game['AwayTeam'] in TEAMS.values():
                return game
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        # Fallback to proxy endpoint
        try:
            response = requests.get(PROXY_ENDPOINT, headers=HEADERS, timeout=10)
            response.raise_for_status()
            games = response.json()
            for game in games:
                if game['HomeTeam'] in TEAMS.values() and game['AwayTeam'] in TEAMS.values():
                    return game
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
    return None

def check_player_goals(game_id):
    url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        player_stats = response.json()
        for stat in player_stats:
            if stat['Name'] == PLAYER_NAME:
                goals = stat['Goals']
                return "Yes" if goals > 0.5 else "No"
    except requests.exceptions.RequestException as e:
        print(f"Error fetching player stats: {e}")
    return "No"

def main():
    game = get_game_data()
    if not game:
        print("Game data not found or error in fetching data.")
        return
    if datetime.now() > datetime.strptime("2025-12-31 23:59", "%Y-%m-%d %H:%M"):
        recommendation = RESOLUTION_MAP["50-50"]
    else:
        recommendation = check_player_goals(game['GameId'])
        recommendation = RESOLUTION_MAP[recommendation]
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()