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
PLAYER_NAME = "Carter Verhaeghe"
TEAMS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# Resolution map based on the outcome
RESOLUTION_MAP = {
    "Yes": "p2",  # Player scores more than 0.5 goals
    "No": "p1",   # Player does not score more than 0.5 goals
    "50-50": "p3" # Game not completed by the specified date
}

def get_game_data(date, team1, team2):
    """Fetch game data for the specified date and teams."""
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
    """Check if the specified player scored more than 0.5 goals in the game."""
    url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        player_stats = response.json()
        for stat in player_stats:
            if stat['Name'] == player_name:
                return "Yes" if stat['Goals'] > 0.5 else "No"
    except requests.exceptions.RequestException as e:
        print(f"Error fetching player stats: {e}")
    return "No"

def main():
    # Check if the current date is past the game date
    current_date = datetime.now().strftime("%Y-%m-%d")
    if current_date > "2025-12-31":
        print("recommendation:", RESOLUTION_MAP["50-50"])
        return

    # Fetch game data
    game = get_game_data(GAME_DATE, TEAMS["Edmonton Oilers"], TEAMS["Florida Panthers"])
    if not game:
        print("recommendation:", RESOLUTION_MAP["50-50"])
        return

    # Check player goals
    result = check_player_goals(game['GameId'], PLAYER_NAME)
    print("recommendation:", RESOLUTION_MAP[result])

if __name__ == "__main__":
    main()