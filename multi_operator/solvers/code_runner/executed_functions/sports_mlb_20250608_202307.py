import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# UEFA Nations League Final match date and teams
MATCH_DATE = "2025-06-08"
TEAM_PORTUGAL = "Portugal"
TEAM_SPAIN = "Spain"
PLAYER_NAME = "Cristiano Ronaldo"

# URL for the UEFA Nations League data
UEFA_API_URL = "https://api.sportsdata.io/v3/soccer/scores/json/GamesByDate/{date}"

def get_games_on_date(date):
    """ Fetch games on a specific date from the UEFA Nations League API """
    formatted_url = UEFA_API_URL.format(date=date)
    response = requests.get(formatted_url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def find_match(games, team1, team2):
    """ Find the match between two specific teams """
    for game in games:
        if team1 in game['HomeTeamName'] and team2 in game['AwayTeamName']:
            return game
        if team2 in game['HomeTeamName'] and team1 in game['AwayTeamName']:
            return game
    return None

def check_player_goals(game, player_name):
    """ Check if a specific player scored in the game """
    # Assuming the API provides a list of goal scorers in the game data
    goal_scorers = game.get('GoalScorers', [])
    for scorer in goal_scorers:
        if player_name in scorer['Player']:
            return True
    return False

def resolve_market():
    """ Resolve the market based on the game data """
    games = get_games_on_date(MATCH_DATE)
    if not games:
        return "recommendation: p1"  # No games found, resolve to "No"

    match = find_match(games, TEAM_PORTUGAL, TEAM_SPAIN)
    if not match:
        return "recommendation: p1"  # No match found, resolve to "No"

    if match['Status'] != 'Final':
        return "recommendation: p1"  # Match not completed, resolve to "No"

    if check_player_goals(match, PLAYER_NAME):
        return "recommendation: p2"  # Ronaldo scored, resolve to "Yes"
    else:
        return "recommendation: p1"  # Ronaldo did not score, resolve to "No"

if __name__ == "__main__":
    print(resolve_market())