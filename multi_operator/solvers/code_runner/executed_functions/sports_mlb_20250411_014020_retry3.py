import requests
from datetime import datetime
from dotenv import load_dotenv
import os

def fetch_nhl_game_result():
    load_dotenv()
    api_key = os.getenv('SPORTS_DATA_IO_NHL_API_KEY')
    url = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/2025-04-10"
    headers = {
        'Ocp-Apim-Subscription-Key': api_key
    }
    response = requests.get(url, headers=headers)
    games = response.json()

    for game in games:
        if game['HomeTeam'] == 'DET' and game['AwayTeam'] == 'FLA':
            if game['Status'] == 'Final':
                home_score = game['HomeTeamScore']
                away_score = game['AwayTeamScore']
                if home_score > away_score:
                    return "recommendation: p2"  # Red Wings win
                elif away_score > home_score:
                    return "recommendation: p1"  # Panthers win
            elif game['Status'] == 'Postponed':
                return "recommendation: p4"  # Game postponed, too early to resolve
            elif game['Status'] == 'Canceled':
                return "recommendation: p3"  # Game canceled, resolve 50-50
    return "recommendation: p4"  # No game found or future game

# Execute the function and print the result
print(fetch_nhl_game_result())