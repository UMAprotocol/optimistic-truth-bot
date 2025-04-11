import requests
from dotenv import load_dotenv
import os
import datetime

# Load environment variables
load_dotenv()

# Constants
SPORTS_DATA_IO_API_KEY = os.getenv('SPORTS_DATA_IO_MLB_API_KEY')
SPORTS_DATA_IO_ENDPOINT = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}"
DATE_OF_GAME = "2025-04-10"

def fetch_game_data(date):
    """
    Fetches game data for the specified date.
    """
    url = SPORTS_DATA_IO_ENDPOINT.format(date=date)
    headers = {
        'Ocp-Apim-Subscription-Key': SPORTS_DATA_IO_API_KEY
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def analyze_game_data(games):
    """
    Analyzes the list of games to determine the outcome of the Blackhawks vs. Bruins game.
    """
    for game in games:
        if 'Chicago Blackhawks' in game['HomeTeam'] and 'Boston Bruins' in game['AwayTeam']:
            if game['Status'] == 'Final':
                if game['HomeTeamScore'] > game['AwayTeamScore']:
                    return 'Blackhawks'
                elif game['HomeTeamScore'] < game['AwayTeamScore']:
                    return 'Bruins'
            elif game['Status'] == 'Postponed':
                return 'Postponed'
            elif game['Status'] == 'Canceled':
                return 'Canceled'
    return 'No Game Found'

def main():
    """
    Main function to determine the outcome of the Blackhawks vs. Bruins game.
    """
    try:
        games = fetch_game_data(DATE_OF_GAME)
        if games:
            result = analyze_game_data(games)
            if result == 'Blackhawks':
                print('recommendation: p2')
            elif result == 'Bruins':
                print('recommendation: p1')
            elif result == 'Postponed':
                print('recommendation: p4')
            elif result == 'Canceled':
                print('recommendation: p3')
            else:
                print('recommendation: p4')
        else:
            print('recommendation: p4')
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print('recommendation: p4')

if __name__ == "__main__":
    main()