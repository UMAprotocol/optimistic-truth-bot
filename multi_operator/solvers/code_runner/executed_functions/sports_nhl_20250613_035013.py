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
PLAYER_NAME = "Evan Bouchard"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# Resolution conditions
RESOLUTION_MAP = {
    "Yes": "p2",  # Player scores more than 0.5 goals
    "No": "p1",   # Player does not score more than 0.5 goals
    "50-50": "p3" # Game not completed by the specified date
}

def get_data(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def check_player_goals(game_data, player_name):
    for player in game_data.get('PlayerStats', []):
        if player.get('Name') == player_name:
            goals = player.get('Goals', 0)
            return "Yes" if goals > 0.5 else "No"
    return "No"

def resolve_market():
    # Construct URL for game data
    game_date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{game_date_formatted}"

    # Fetch game data
    games = get_data(url, HEADERS)
    if not games:
        # Fallback to primary endpoint if proxy fails
        url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{game_date_formatted}"
        games = get_data(url, HEADERS)
        if not games:
            return "recommendation: p4"  # Unable to fetch data

    # Check for the specific game
    for game in games:
        if game['HomeTeam'] in TEAM_ABBREVIATIONS.values() and game['AwayTeam'] in TEAM_ABBREVIATIONS.values():
            if game['Status'] == 'Final':
                result = check_player_goals(game, PLAYER_NAME)
                return f"recommendation: {RESOLUTION_MAP[result]}"
            elif game['Day'].startswith("2025-12-31"):
                return "recommendation: p3"  # Game not completed by the end of 2025
            else:
                return "recommendation: p4"  # Game not yet completed

    return "recommendation: p4"  # No relevant game found

if __name__ == "__main__":
    print(resolve_market())