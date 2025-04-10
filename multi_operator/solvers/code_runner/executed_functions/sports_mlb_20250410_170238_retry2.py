import requests
from datetime import datetime
from dotenv import load_dotenv
import os

def fetch_nba_game_result():
    load_dotenv()
    api_key = os.getenv('SPORTS_DATA_IO_NBA_API_KEY')
    url = "https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/2025-04-09"
    headers = {
        'Ocp-Apim-Subscription-Key': api_key
    }
    response = requests.get(url, headers=headers)
    games = response.json()

    for game in games:
        if game['HomeTeam'] == 'POR' and game['AwayTeam'] == 'UTA':
            if game['Status'] == 'Final':
                home_score = game['HomeTeamScore']
                away_score = game['AwayTeamScore']
                if home_score > away_score:
                    return "recommendation: p2"  # Trail Blazers win
                elif away_score > home_score:
                    return "recommendation: p1"  # Jazz win
            elif game['Status'] == 'Postponed':
                return "recommendation: p4"  # Game postponed
            elif game['Status'] == 'Canceled':
                return "recommendation: p3"  # Game canceled, resolve 50-50
    return "recommendation: p4"  # No data or game not yet played

# Execute the function and print the result
print(fetch_nba_game_result())