import requests
from dotenv import load_dotenv
import os
import datetime

# Load environment variables
load_dotenv()

# Constants
SPORTS_DATA_IO_API_KEY = os.getenv('SPORTS_DATA_IO_MLB_API_KEY')
SPORTS_DATA_IO_NBA_ENDPOINT = "https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date}"

# Game details
game_date = "2025-04-10"
teams = ["Cavaliers", "Pacers"]

def fetch_game_data(date):
    """
    Fetch NBA game data for a specific date.
    """
    url = SPORTS_DATA_IO_NBA_ENDPOINT.format(date=date)
    headers = {'Ocp-Apim-Subscription-Key': SPORTS_DATA_IO_API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch data: {response.status_code} - {response.text}")

def resolve_market(games):
    """
    Resolve the market based on game results.
    """
    for game in games:
        if game['HomeTeam'] in teams and game['AwayTeam'] in teams:
            if game['Status'] == "Final":
                if game['HomeTeam'] == "Cavaliers" and game['HomeTeamScore'] > game['AwayTeamScore']:
                    return "recommendation: p2"
                elif game['AwayTeam'] == "Pacers" and game['AwayTeamScore'] > game['HomeTeamScore']:
                    return "recommendation: p1"
            elif game['Status'] == "Postponed":
                return "recommendation: p4"
            elif game['Status'] == "Canceled":
                return "recommendation: p3"
    return "recommendation: p4"

def main():
    """
    Main function to handle the market resolution logic.
    """
    try:
        games = fetch_game_data(game_date)
        result = resolve_market(games)
        print(result)
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()