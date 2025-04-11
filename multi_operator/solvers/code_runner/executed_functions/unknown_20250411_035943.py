import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants for the game
GAME_DATE = "2025-04-10"
GAME_TIME = "21:00:00"  # 9:00 PM ET
TEAMS = ["Nashville Predators", "Utah"]  # Assuming Utah represents a team, though no NHL team by this name

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
    url = API_ENDPOINT.format(date=date)
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def analyze_game_data(games, teams, game_time):
    """
    Analyzes the game data to determine the outcome based on the teams and game time.
    """
    for game in games:
        if game['AwayTeam'] in teams and game['HomeTeam'] in teams and game['DateTime'].endswith(game_time):
            if game['Status'] == "Final":
                if game['AwayTeamScore'] > game['HomeTeamScore']:
                    return "Predators" if game['AwayTeam'] == "Nashville Predators" else "Utah"
                else:
                    return "Utah" if game['HomeTeam'] == "Nashville Predators" else "Predators"
            elif game['Status'] == "Postponed":
                return "Postponed"
            elif game['Status'] == "Canceled":
                return "Canceled"
    return "No Game Found"

def main():
    """
    Main function to execute the workflow.
    """
    games = fetch_game_data(GAME_DATE)
    if games:
        result = analyze_game_data(games, TEAMS, GAME_TIME)
        if result == "Predators":
            print("recommendation: p2")
        elif result == "Utah":
            print("recommendation: p1")
        elif result == "Postponed":
            print("recommendation: p4")  # Market remains open
        elif result == "Canceled":
            print("recommendation: p3")  # Resolve 50-50
        else:
            print("recommendation: p4")  # No game found, cannot resolve
    else:
        print("Error fetching data or API issue. Cannot resolve.")

if __name__ == "__main__":
    main()