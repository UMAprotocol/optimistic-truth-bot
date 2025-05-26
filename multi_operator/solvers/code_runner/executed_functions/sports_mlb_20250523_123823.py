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

# Game and player details
GAME_DATE = "2025-05-22"
TEAM_NAME = "Minnesota Timberwolves"
PLAYER_NAME = "Anthony Edwards"
OPPONENT_TEAM = "Oklahoma City Thunder"

# API endpoints
NBA_SCORES_ENDPOINT = "https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/"
NBA_STATS_ENDPOINT = "https://api.sportsdata.io/v3/nba/stats/json/PlayerGameStatsByDate/"

def get_games_by_date(date):
    url = f"{NBA_SCORES_ENDPOINT}{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to retrieve games data: {response.status_code} {response.text}")

def get_player_stats_by_date(date):
    url = f"{NBA_STATS_ENDPOINT}{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to retrieve player stats: {response.status_code} {response.text}")

def resolve_market():
    try:
        games = get_games_by_date(GAME_DATE)
        player_stats = get_player_stats_by_date(GAME_DATE)

        # Find the specific game
        game = next((g for g in games if TEAM_NAME in [g['HomeTeam'], g['AwayTeam']] and OPPONENT_TEAM in [g['HomeTeam'], g['AwayTeam']]), None)
        if not game:
            return "recommendation: p1"  # No game found, resolve as "No"

        # Check if the game was postponed or not played on the scheduled date
        if game['Status'] != 'Final':
            return "recommendation: p1"  # Game not completed on the scheduled date, resolve as "No"

        # Check if Timberwolves won
        timberwolves_won = (game['HomeTeam'] == TEAM_NAME and game['HomeTeamScore'] > game['AwayTeamScore']) or (game['AwayTeam'] == TEAM_NAME and game['AwayTeamScore'] > game['HomeTeamScore'])

        # Find Anthony Edwards' performance
        edwards_performance = next((stat for stat in player_stats if stat['Name'] == PLAYER_NAME and stat['Team'] == TEAM_NAME), None)
        if not edwards_performance:
            return "recommendation: p1"  # No performance data for Anthony Edwards, resolve as "No"

        # Check if Anthony Edwards scored 25+ points
        edwards_scored_25_plus = edwards_performance['Points'] > 24.5

        # Final resolution based on conditions
        if timberwolves_won and edwards_scored_25_plus:
            return "recommendation: p2"  # Yes, both conditions met
        else:
            return "recommendation: p1"  # No, one or both conditions not met

    except Exception as e:
        print(f"Error resolving market: {str(e)}")
        return "recommendation: p3"  # Unknown or error state

if __name__ == "__main__":
    result = resolve_market()
    print(result)