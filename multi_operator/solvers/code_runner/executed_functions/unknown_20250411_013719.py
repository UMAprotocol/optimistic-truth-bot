import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants for the game
TEAM_HOME = "Chicago Blackhawks"
TEAM_AWAY = "Boston Bruins"
GAME_DATE = "2025-04-10"
GAME_TIME = "19:00:00"  # 7:00 PM ET in 24-hour format

# API Key for Sports Data IO
API_KEY = os.getenv('SPORTS_DATA_IO_MLB_API_KEY')

# API Endpoint
API_ENDPOINT = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}"

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
        return None

def analyze_game_data(games):
    """
    Analyzes the list of games to determine the outcome of the specific game.
    """
    for game in games:
        if (game['HomeTeam'] == TEAM_HOME and game['AwayTeam'] == TEAM_AWAY) or \
           (game['HomeTeam'] == TEAM_AWAY and game['AwayTeam'] == TEAM_HOME):
            if game['Status'] == "Final":
                if game['HomeTeam'] == TEAM_HOME and game['HomeTeamScore'] > game['AwayTeamScore']:
                    return "Blackhawks"
                elif game['HomeTeam'] == TEAM_AWAY and game['AwayTeamScore'] > game['HomeTeamScore']:
                    return "Blackhawks"
                elif game['HomeTeam'] == TEAM_HOME and game['HomeTeamScore'] < game['AwayTeamScore']:
                    return "Bruins"
                elif game['HomeTeam'] == TEAM_AWAY and game['AwayTeamScore'] < game['HomeTeamScore']:
                    return "Bruins"
            elif game['Status'] == "Postponed":
                return "Postponed"
            elif game['Status'] == "Canceled":
                return "Canceled"
    return "No Game Found"

def main():
    """
    Main function to determine the outcome of the Blackhawks vs. Bruins game.
    """
    games = fetch_game_data(GAME_DATE)
    if games:
        result = analyze_game_data(games)
        if result == "Blackhawks":
            print("recommendation: p2")
        elif result == "Bruins":
            print("recommendation: p1")
        elif result == "Postponed":
            print("recommendation: p4")
        elif result == "Canceled":
            print("recommendation: p3")
        else:
            print("recommendation: p4")
    else:
        print("Error fetching data or no data available.")
        print("recommendation: p4")

if __name__ == "__main__":
    main()