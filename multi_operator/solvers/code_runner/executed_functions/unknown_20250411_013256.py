import requests
from dotenv import load_dotenv
import os
import datetime

# Load environment variables
load_dotenv()

# Constants
SPORTS_DATA_IO_API_KEY = os.getenv('SPORTS_DATA_IO_MLB_API_KEY')
SPORTS_DATA_IO_NBA_ENDPOINT = "https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date}"

# Date of the game
game_date = "2025-04-10"

def fetch_game_data(date):
    """
    Fetch NBA game data for a specific date.
    """
    headers = {
        'Ocp-Apim-Subscription-Key': SPORTS_DATA_IO_API_KEY
    }
    response = requests.get(SPORTS_DATA_IO_NBA_ENDPOINT.format(date=date), headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def analyze_game_data(games):
    """
    Analyze game data to determine the outcome of the Knicks vs. Pistons game.
    """
    for game in games:
        if game['HomeTeam'] == 'NY' and game['AwayTeam'] == 'DET' or game['HomeTeam'] == 'DET' and game['AwayTeam'] == 'NY':
            if game['Status'] == 'Final':
                if game['HomeTeam'] == 'NY' and game['HomeTeamScore'] > game['AwayTeamScore']:
                    return 'Knicks'
                elif game['HomeTeam'] == 'DET' and game['HomeTeamScore'] > game['AwayTeamScore']:
                    return 'Pistons'
                elif game['AwayTeam'] == 'NY' and game['AwayTeamScore'] > game['HomeTeamScore']:
                    return 'Knicks'
                elif game['AwayTeam'] == 'DET' and game['AwayTeamScore'] > game['HomeTeamScore']:
                    return 'Pistons'
            elif game['Status'] == 'Postponed':
                return 'Postponed'
            elif game['Status'] == 'Canceled':
                return 'Canceled'
    return 'No Game Found'

def main():
    """
    Main function to determine the outcome of the Knicks vs. Pistons game.
    """
    games = fetch_game_data(game_date)
    if games:
        result = analyze_game_data(games)
        if result == 'Knicks':
            print('recommendation: p2')
        elif result == 'Pistons':
            print('recommendation: p1')
        elif result == 'Postponed':
            print('The game is postponed. Market remains open.')
        elif result == 'Canceled':
            print('recommendation: p3')
        else:
            print('No relevant game found on the specified date.')
    else:
        print('Failed to fetch data or API key might be missing/invalid.')

if __name__ == "__main__":
    main()