import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants for the game
TEAM_HURRICANES = "Carolina Hurricanes"
TEAM_CAPITALS = "Washington Capitals"
GAME_DATE = "2025-04-10"
GAME_TIME = "19:30:00"  # 7:30 PM ET in 24-hour format

# API Key for Sports Data IO
API_KEY = os.getenv('SPORTS_DATA_IO_MLB_API_KEY')

# API Endpoint
API_ENDPOINT = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}"

def fetch_game_data(date):
    """Fetch game data from the Sports Data IO API."""
    headers = {
        'Ocp-Apim-Subscription-Key': API_KEY
    }
    response = requests.get(API_ENDPOINT.format(date=date), headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch data: {response.status_code} - {response.text}")

def analyze_game_data(games):
    """Analyze game data to determine the outcome."""
    for game in games:
        if (game['AwayTeam'] == TEAM_CAPITALS and game['HomeTeam'] == TEAM_HURRICANES) or \
           (game['HomeTeam'] == TEAM_CAPITALS and game['AwayTeam'] == TEAM_HURRICANES):
            if 'Status' in game:
                if game['Status'] == 'Final':
                    if game['AwayTeamScore'] > game['HomeTeamScore']:
                        return 'Capitals' if game['AwayTeam'] == TEAM_CAPITALS else 'Hurricanes'
                    else:
                        return 'Hurricanes' if game['HomeTeam'] == TEAM_HURRICANES else 'Capitals'
                elif game['Status'] == 'Postponed':
                    return 'Postponed'
                elif game['Status'] == 'Canceled':
                    return 'Canceled'
    return 'No Game Found'

def main():
    try:
        games = fetch_game_data(GAME_DATE)
        result = analyze_game_data(games)
        if result == 'Capitals':
            print('recommendation: p1')
        elif result == 'Hurricanes':
            print('recommendation: p2')
        elif result == 'Postponed' or result == 'No Game Found':
            print('recommendation: p3')
        elif result == 'Canceled':
            print('recommendation: p3')
    except Exception as e:
        print(f"Error: {str(e)}")
        print('recommendation: p3')

if __name__ == "__main__":
    main()