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
GAME_DATE = "2025-06-12"
PLAYER_NAME = "Sam Reinhart"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# API Endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Headers for API request
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

def get_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def check_player_goals(game_data, player_name):
    for player in game_data.get('PlayerStats', []):
        if player.get('Name') == player_name and player.get('Goals', 0) > 0.5:
            return True
    return False

def find_game(games, team1, team2):
    for game in games:
        teams = {game['HomeTeam'], game['AwayTeam']}
        if teams == {team1, team2} and game['Status'] == 'Final':
            return game
    return None

def main():
    current_date = datetime.utcnow().date()
    game_date = datetime.strptime(GAME_DATE, "%Y-%m-%d").date()
    if current_date < game_date:
        print("recommendation: p4")  # Game has not occurred yet
        return

    # Fetch games data
    games_url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{GAME_DATE}"
    games_data = get_data(games_url)
    if not games_data:
        print("recommendation: p3")  # Unable to fetch data
        return

    # Find the specific game
    game = find_game(games_data, TEAM_ABBREVIATIONS["Edmonton Oilers"], TEAM_ABBREVIATIONS["Florida Panthers"])
    if not game:
        print("recommendation: p3")  # Game not found or not completed
        return

    # Check if Sam Reinhart scored a goal
    if check_player_goals(game, PLAYER_NAME):
        print("recommendation: p2")  # Sam Reinhart scored a goal
    else:
        print("recommendation: p1")  # Sam Reinhart did not score a goal

if __name__ == "__main__":
    main()