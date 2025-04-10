import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Constants for the game details
GAME_DATE = "2023-04-09"
GAME_TIME = "19:00:00"  # 7:00 PM ET in 24-hour format
TEAM_HOME = "Tampa Bay Lightning"
TEAM_AWAY = "Toronto Maple Leafs"

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
                    return "recommendation: p1"  # Lightning win
                elif game['AwayTeam'] == TEAM_AWAY and game['AwayTeamScore'] > game['HomeTeamScore']:
                    return "recommendation: p2"  # Maple Leafs win
            elif game['Status'] == "Postponed":
                return "recommendation: p3"  # Game postponed, resolve as unknown/50-50
            elif game['Status'] == "Canceled":
                return "recommendation: p3"  # Game canceled, resolve as unknown/50-50
    return "recommendation: p3"  # If no specific game found or other conditions, resolve as unknown/50-50

def main():
    """
    Main function to orchestrate the fetching and analysis of NHL game data.
    """
    try:
        games = fetch_game_data(GAME_DATE)
        if games:
            result = analyze_game_data(games)
            print(result)
        else:
            print("Error: Failed to fetch data or no games found on the specified date.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()