import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Game and player details
GAME_DATE = "2025-06-17"
PLAYER_NAME = "Connor McDavid"
TEAMS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# Resolution conditions
RESOLUTION_MAP = {
    "No": "p1",
    "Yes": "p2",
    "50-50": "p3"
}

def get_game_data():
    # Construct the URL for the game date
    date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date_formatted}"

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
    return None

def check_player_goals(game_id):
    url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        player_stats = response.json()
        for stat in player_stats:
            if stat['Name'] == PLAYER_NAME:
                goals = stat.get('Goals', 0)
                return goals > 0.5
    except requests.exceptions.RequestException as e:
        print(f"Error fetching player stats: {e}")
        return None
    return None

def main():
    game = get_game_data()
    if not game:
        print("recommendation:", RESOLUTION_MAP["50-50"])
        return

    if game['Status'] != 'Final':
        print("recommendation:", RESOLUTION_MAP["50-50"])
        return

    player_scored = check_player_goals(game['GameID'])
    if player_scored is None:
        print("recommendation:", RESOLUTION_MAP["50-50"])
    elif player_scored:
        print("recommendation:", RESOLUTION_MAP["Yes"])
    else:
        print("recommendation:", RESOLUTION_MAP["No"])

if __name__ == "__main__":
    main()