import requests
from dotenv import load_dotenv
import os
import datetime

# Load environment variables
load_dotenv()

# Constants for the game
GAME_DATE = "2025-04-09"
GAME_TIME = "21:00:00"
TEAM_HOME = "Portland Trail Blazers"
TEAM_AWAY = "Utah Jazz"

# API Key for Sports Data IO
API_KEY = os.getenv('SPORTS_DATA_IO_MLB_API_KEY')

# Endpoint for NBA scores
NBA_SCORES_ENDPOINT = "https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date}"

def fetch_game_result(game_date):
    """
    Fetches the game result from the Sports Data IO API.
    """
    headers = {
        'Ocp-Apim-Subscription-Key': API_KEY
    }
    response = requests.get(NBA_SCORES_ENDPOINT.format(date=game_date), headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def process_game_data(games):
    """
    Processes the list of games to find the result of the specific game.
    """
    for game in games:
        if (game['HomeTeam'] == TEAM_HOME and game['AwayTeam'] == TEAM_AWAY) or \
           (game['HomeTeam'] == TEAM_AWAY and game['AwayTeam'] == TEAM_HOME):
            if game['Status'] == "Final":
                home_score = game['HomeTeamScore']
                away_score = game['AwayTeamScore']
                if home_score > away_score:
                    return "Trail Blazers" if game['HomeTeam'] == TEAM_HOME else "Jazz"
                else:
                    return "Jazz" if game['HomeTeam'] == TEAM_HOME else "Trail Blazers"
            elif game['Status'] == "Postponed":
                return "Postponed"
            elif game['Status'] == "Canceled":
                return "Canceled"
    return "No Game Found"

def main():
    # Convert game date and time to datetime object
    game_datetime = datetime.datetime.strptime(GAME_DATE + " " + GAME_TIME, "%Y-%m-%d %H:%M:%S")
    current_datetime = datetime.datetime.now()

    # Check if the game is in the future
    if game_datetime > current_datetime:
        print("recommendation: p4")
        return

    # Fetch game data
    games = fetch_game_result(GAME_DATE)

    # Process game data
    if games:
        result = process_game_data(games)
        if result == "Trail Blazers":
            print("recommendation: p2")
        elif result == "Jazz":
            print("recommendation: p1")
        elif result == "Postponed":
            print("recommendation: p4")
        elif result == "Canceled":
            print("recommendation: p3")
        else:
            print("recommendation: p3")
    else:
        print("recommendation: p3")

if __name__ == "__main__":
    main()