import requests
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()

# Constants for the game
GAME_DATE = "2025-04-10"
GAME_TIME = "21:00:00"  # 9:00 PM ET
TEAMS = ["Nashville Predators", "Utah"]  # Assuming Utah represents a team, typically NHL does not have a team named "Utah"

# API Key for Sports Data IO
API_KEY = os.getenv('SPORTS_DATA_IO_MLB_API_KEY')

# Endpoint for NHL scores (Note: Adjust the endpoint as per the actual API documentation)
API_ENDPOINT = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}"

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
        response.raise_for_status()

def analyze_game_data(games):
    """
    Analyzes the list of games to find the outcome of the specific game between Nashville Predators and Utah.
    """
    for game in games:
        if "Nashville Predators" in game['HomeTeam'] and "Utah" in game['AwayTeam']:
            if game['Status'] == "Final":
                if game['HomeTeamScore'] > game['AwayTeamScore']:
                    return "Predators"
                else:
                    return "Utah"
            elif game['Status'] == "Postponed":
                return "Postponed"
            elif game['Status'] == "Canceled":
                return "Canceled"
    return "No Game Found"

def main():
    try:
        games_on_date = fetch_game_data(GAME_DATE)
        result = analyze_game_data(games_on_date)
        if result == "Predators":
            print("recommendation: p2")
        elif result == "Utah":
            print("recommendation: p1")
        elif result == "Postponed":
            print("recommendation: p4")  # Market remains open
        elif result == "Canceled":
            print("recommendation: p3")  # Market resolves 50-50
        else:
            print("recommendation: p4")  # No game found, unable to resolve
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("recommendation: p4")  # Unable to resolve due to error

if __name__ == "__main__":
    main()