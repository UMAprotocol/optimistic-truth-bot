import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants for the game
TEAM_KNICKS = "Knicks"
TEAM_PISTONS = "Pistons"
GAME_DATE = "2025-04-10"
GAME_TIME = "19:00:00"  # 7:00 PM ET in 24-hour format

# API Key for Sports Data IO
API_KEY = os.getenv('SPORTS_DATA_IO_MLB_API_KEY')

# API Endpoint
API_ENDPOINT = "https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date}"

def fetch_game_data(date):
    """
    Fetches game data for a specific date from the Sports Data IO API.
    """
    headers = {
        'Ocp-Apim-Subscription-Key': API_KEY
    }
    response = requests.get(API_ENDPOINT.format(date=date), headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

def analyze_game_data(games):
    """
    Analyzes the list of games to find the Knicks vs Pistons game and determine the outcome.
    """
    for game in games:
        if (game['HomeTeam'] == TEAM_KNICKS or game['AwayTeam'] == TEAM_KNICKS) and \
           (game['HomeTeam'] == TEAM_PISTONS or game['AwayTeam'] == TEAM_PISTONS):
            if game['Status'] == "Scheduled":
                print("The game is still scheduled.")
                return "recommendation: p4"
            elif game['Status'] == "Final":
                if game['Winner'] == TEAM_KNICKS:
                    return "recommendation: p2"
                elif game['Winner'] == TEAM_PISTONS:
                    return "recommendation: p1"
            elif game['Status'] == "Postponed":
                return "recommendation: p4"
            elif game['Status'] == "Canceled":
                return "recommendation: p3"
    return "recommendation: p4"

def main():
    try:
        games_on_date = fetch_game_data(GAME_DATE)
        result = analyze_game_data(games_on_date)
        print(result)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("recommendation: p4")

if __name__ == "__main__":
    main()