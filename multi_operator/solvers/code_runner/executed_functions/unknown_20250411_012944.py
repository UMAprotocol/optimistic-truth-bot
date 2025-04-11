import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants for the game
GAME_DATE = "2025-04-10"
GAME_TIME = "19:00:00"  # 7:00 PM ET
TEAM_1 = "Cleveland Cavaliers"
TEAM_2 = "Indiana Pacers"

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
    url = API_ENDPOINT.format(date=date)
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
        if game['AwayTeam'] == "CLE" and game['HomeTeam'] == "IND" or game['AwayTeam'] == "IND" and game['HomeTeam'] == "CLE":
            if game['Status'] == "Final":
                if game['AwayTeam'] == "CLE" and game['AwayTeamScore'] > game['HomeTeamScore']:
                    return "recommendation: p2"  # Cavaliers win
                elif game['HomeTeam'] == "CLE" and game['HomeTeamScore'] > game['AwayTeamScore']:
                    return "recommendation: p2"  # Cavaliers win
                else:
                    return "recommendation: p1"  # Pacers win
            elif game['Status'] == "Postponed":
                return "recommendation: p4"  # Market remains open
            elif game['Status'] == "Canceled":
                return "recommendation: p3"  # Resolve 50-50
    return "recommendation: p4"  # No game found or future game

def main():
    """
    Main function to orchestrate the fetching and analysis of NBA game data.
    """
    try:
        games = fetch_game_data(GAME_DATE)
        if games:
            result = analyze_game_data(games)
            print(result)
        else:
            print("Error fetching data or no games scheduled on this date.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()