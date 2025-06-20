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
GAME_DATE = "2025-06-12"
PLAYER_NAME = "Corey Perry"
TEAMS = ["EDM", "FLA"]  # Edmonton Oilers and Florida Panthers

# Resolution map based on the ancillary data
RESOLUTION_MAP = {
    "Yes": "p2",
    "No": "p1",
    "50-50": "p3"
}

def get_game_data():
    # Construct the URL for the game date
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{GAME_DATE}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] in TEAMS and game['AwayTeam'] in TEAMS:
                return game
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        # Fallback to proxy endpoint
        try:
            proxy_url = f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{GAME_DATE}"
            response = requests.get(proxy_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            games = response.json()
            for game in games:
                if game['HomeTeam'] in TEAMS and game['AwayTeam'] in TEAMS:
                    return game
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
            return None
    return None

def check_player_goals(game):
    game_id = game['GameID']
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
        return "50-50"
    return "No"

def main():
    current_date = datetime.utcnow().date()
    game_date = datetime.strptime(GAME_DATE, "%Y-%m-%d").date()
    if current_date > datetime.strptime("2025-12-31", "%Y-%m-%d").date():
        print("recommendation:", RESOLUTION_MAP["50-50"])
    elif game_date > current_date:
        print("recommendation:", RESOLUTION_MAP["50-50"])
    else:
        game = get_game_data()
        if not game:
            print("recommendation:", RESOLUTION_MAP["50-50"])
        else:
            result = check_player_goals(game)
            print("recommendation:", RESOLUTION_MAP[result])

if __name__ == "__main__":
    main()