import requests
from dotenv import load_dotenv
import os
import datetime

# Load environment variables
load_dotenv()

# Constants
SPORTS_DATA_IO_API_KEY = os.getenv('SPORTS_DATA_IO_MLB_API_KEY')
SPORTS_DATA_IO_NHL_ENDPOINT = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}"

# Game details
game_date = "2025-04-10"
team1 = "Nashville Predators"
team2 = "Utah"  # Assuming Utah represents a team, though no NHL team by this name; placeholder

def fetch_game_data(date):
    """
    Fetches game data for a specific date from the SportsData.io NHL API.
    """
    url = SPORTS_DATA_IO_NHL_ENDPOINT.format(date=date)
    headers = {'Ocp-Apim-Subscription-Key': SPORTS_DATA_IO_API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def analyze_game_data(games, team1, team2):
    """
    Analyzes the list of games to determine the outcome of the specified game.
    """
    for game in games:
        if team1 in game['HomeTeamName'] and team2 in game['AwayTeamName'] or \
           team1 in game['AwayTeamName'] and team2 in game['HomeTeamName']:
            if game['Status'] == "Final":
                if game['HomeTeamName'] == team1 and game['HomeTeamScore'] > game['AwayTeamScore']:
                    return "Predators"
                elif game['AwayTeamName'] == team1 and game['AwayTeamScore'] > game['HomeTeamScore']:
                    return "Predators"
                else:
                    return "Utah"
            elif game['Status'] == "Postponed":
                return "Postponed"
            elif game['Status'] == "Canceled":
                return "Canceled"
    return "No Game Found"

def main():
    """
    Main function to determine the outcome of the NHL game.
    """
    games = fetch_game_data(game_date)
    if games:
        result = analyze_game_data(games, team1, team2)
        if result == "Predators":
            print("recommendation: p2")
        elif result == "Utah":
            print("recommendation: p1")
        elif result == "Postponed":
            print("The game is postponed. Market remains open.")
        elif result == "Canceled":
            print("recommendation: p3")
        else:
            print("No relevant game found on the specified date.")
    else:
        print("Failed to fetch data or API error occurred.")

if __name__ == "__main__":
    main()