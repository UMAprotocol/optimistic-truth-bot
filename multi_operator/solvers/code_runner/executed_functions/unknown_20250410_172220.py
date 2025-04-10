import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Constants for the game details
GAME_DATE = "2025-04-09"
GAME_TIME = "19:00:00"  # 7:00 PM ET in 24-hour format
TEAM_HOME = "Toronto Maple Leafs"
TEAM_AWAY = "Tampa Bay Lightning"

# API Key for Sports Data IO
API_KEY = os.getenv('SPORTS_DATA_IO_MLB_API_KEY')

# API Endpoint for NHL Scores
API_ENDPOINT = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}"

def fetch_game_data(date):
    """
    Fetches game data for a specific date from the Sports Data IO API.
    """
    url = API_ENDPOINT.format(date=date)
    headers = {
        'Ocp-Apim-Subscription-Key': API_KEY
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def analyze_game_data(games):
    """
    Analyzes the list of games to find the specific game and determine the outcome.
    """
    for game in games:
        if (game['HomeTeam'] == TEAM_HOME and game['AwayTeam'] == TEAM_AWAY) or \
           (game['HomeTeam'] == TEAM_AWAY and game['AwayTeam'] == TEAM_HOME):
            if game['Status'] == "Final":
                if game['HomeTeam'] == TEAM_HOME and game['HomeTeamScore'] > game['AwayTeamScore']:
                    return "Maple Leafs"
                elif game['AwayTeam'] == TEAM_HOME and game['AwayTeamScore'] > game['HomeTeamScore']:
                    return "Maple Leafs"
                else:
                    return "Lightning"
            elif game['Status'] == "Postponed":
                return "Postponed"
            elif game['Status'] == "Canceled":
                return "Canceled"
    return "No Game Found"

def main():
    """
    Main function to execute the workflow.
    """
    games_data = fetch_game_data(GAME_DATE)
    if games_data is None:
        print("Failed to fetch data.")
        return

    result = analyze_game_data(games_data)
    if result == "Maple Leafs":
        print("recommendation: p2")
    elif result == "Lightning":
        print("recommendation: p1")
    elif result == "Postponed":
        print("The game is postponed. Market remains open.")
    elif result == "Canceled":
        print("recommendation: p3")
    else:
        print("No relevant game found on the specified date.")

if __name__ == "__main__":
    main()