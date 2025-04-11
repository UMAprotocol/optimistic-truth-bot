import os
import requests
from datetime import datetime
from dotenv import load_dotenv

def fetch_game_result():
    load_dotenv()
    api_key = os.getenv('SPORTS_DATA_IO_NBA_API_KEY')
    url = "https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/2025-04-10"
    headers = {
        'Ocp-Apim-Subscription-Key': api_key
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        games = response.json()
        for game in games:
            if game['HomeTeam'] == 'NYK' and game['AwayTeam'] == 'DET':
                if game['Status'] == 'Final':
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    if home_score > away_score:
                        return "recommendation: p2"  # Knicks win
                    elif away_score > home_score:
                        return "recommendation: p1"  # Pistons win
                elif game['Status'] == 'Postponed':
                    return "recommendation: p4"  # Game postponed
                elif game['Status'] == 'Canceled':
                    return "recommendation: p3"  # Game canceled, resolve 50-50
    return "recommendation: p4"  # Default to unresolved if data fetching fails or no specific condition met

print(fetch_game_result())