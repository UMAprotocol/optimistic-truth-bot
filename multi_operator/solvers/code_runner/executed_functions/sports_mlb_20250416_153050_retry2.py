import os
import requests
from dotenv import load_dotenv

def fetch_mlb_game_result():
    load_dotenv()
    api_key = os.getenv('SPORTS_DATA_IO_MLB_API_KEY')
    url = "https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/2025-04-15"
    headers = {
        'Ocp-Apim-Subscription-Key': api_key
    }
    response = requests.get(url, headers=headers)
    games = response.json()

    for game in games:
        if game['AwayTeam'] == 'OAK' and game['HomeTeam'] == 'CWS':
            if game['Status'] == 'Final':
                if game['AwayTeamRuns'] > game['HomeTeamRuns']:
                    return "recommendation: p2"  # Athletics win
                elif game['AwayTeamRuns'] < game['HomeTeamRuns']:
                    return "recommendation: p1"  # Chicago White Sox win
            elif game['Status'] == 'Postponed':
                return "recommendation: p4"  # Game postponed, too early to resolve
            elif game['Status'] == 'Canceled':
                return "recommendation: p3"  # Game canceled, resolve 50-50
    return "recommendation: p4"  # No data or game not found, too early to resolve

print(fetch_mlb_game_result())