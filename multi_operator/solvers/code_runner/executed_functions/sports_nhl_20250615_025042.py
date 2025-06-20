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

# Resolution conditions mapping
RESOLUTION_MAP = {
    "No": "p1",
    "Yes": "p2",
    "50-50": "p3"
}

def get_game_data(date, team1, team2):
    """
    Fetch game data for the specified date and teams.
    """
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if team1 in game['HomeTeam'] or team1 in game['AwayTeam']:
                if team2 in game['HomeTeam'] or team2 in game['AwayTeam']:
                    return game
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        try:
            response = requests.get(PROXY_ENDPOINT, headers=HEADERS, timeout=10)
            response.raise_for_status()
            games = response.json()
            for game in games:
                if team1 in game['HomeTeam'] or team1 in game['AwayTeam']:
                    if team2 in game['HomeTeam'] or team2 in game['AwayTeam']:
                        return game
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
    return None

def check_player_goals(game_id, player_name):
    """
    Check if the specified player scored a goal in the game.
    """
    url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        player_stats = response.json()
        for stat in player_stats:
            if player_name in stat['Name']:
                return stat['Goals'] > 0.5
    except requests.exceptions.RequestException as e:
        print(f"Error fetching player stats: {e}")
    return False

def resolve_market():
    """
    Resolve the market based on the game data and player performance.
    """
    game_date = "2025-06-14"
    team1 = "EDM"
    team2 = "FLA"
    player_name = "Carter Verhaeghe"
    game = get_game_data(game_date, team1, team2)
    if game:
        if datetime.now() > datetime.strptime("2025-12-31 23:59", "%Y-%m-%d %H:%M"):
            return RESOLUTION_MAP["50-50"]
        player_scored = check_player_goals(game['GameID'], player_name)
        return RESOLUTION_MAP["Yes"] if player_scored else RESOLUTION_MAP["No"]
    return RESOLUTION_MAP["50-50"]

if __name__ == "__main__":
    recommendation = resolve_market()
    print(f"recommendation: {recommendation}")