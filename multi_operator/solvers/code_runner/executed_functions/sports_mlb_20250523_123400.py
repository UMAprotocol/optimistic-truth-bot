import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not NBA_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# API headers
HEADERS = {"Ocp-Apim-Subscription-Key": NBA_API_KEY}

# NBA API endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nba-proxy"

# Game and player details
GAME_DATE = "2025-05-22"
TEAM_NAME = "Oklahoma City Thunder"
PLAYER_NAME = "Shai Gilgeous-Alexander"
POINTS_THRESHOLD = 30.5

def get_game_data():
    date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date_formatted}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] == TEAM_NAME or game['AwayTeam'] == TEAM_NAME:
                return game
    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
    return None

def get_player_stats(game_id, player_name):
    url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        player_stats = response.json()
        for stat in player_stats:
            if stat['Name'] == player_name:
                return stat
    except requests.RequestException as e:
        print(f"Error fetching player stats: {e}")
    return None

def resolve_market():
    game = get_game_data()
    if not game:
        return "recommendation: p1"  # No game found, resolve as "No"

    if game['Status'] != 'Final':
        return "recommendation: p1"  # Game not completed, resolve as "No"

    player_stats = get_player_stats(game['GameID'], PLAYER_NAME)
    if not player_stats:
        return "recommendation: p1"  # No player stats found, resolve as "No"

    team_won = (game['HomeTeam'] == TEAM_NAME and game['HomeTeamScore'] > game['AwayTeamScore']) or \
               (game['AwayTeam'] == TEAM_NAME and game['AwayTeamScore'] > game['HomeTeamScore'])

    player_scored_enough = player_stats['Points'] > POINTS_THRESHOLD

    if team_won and player_scored_enough:
        return "recommendation: p2"  # Both conditions met, resolve as "Yes"
    else:
        return "recommendation: p1"  # Conditions not met, resolve as "No"

if __name__ == "__main__":
    result = resolve_market()
    print(result)