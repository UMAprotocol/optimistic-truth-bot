import os
import requests
from dotenv import load_dotenv

def fetch_mlb_game_result():
    load_dotenv()
    api_key = os.getenv('SPORTS_DATA_IO_MLB_API_KEY')
    url = "https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/2025-04-05"
    headers = {
        'Ocp-Apim-Subscription-Key': api_key
    }
    response = requests.get(url, headers=headers)
    games = response.json()

    for game in games:
        if game['HomeTeam'] == 'TEX' and game['AwayTeam'] == 'TBR':
            if game['Status'] == 'Final':
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return "recommendation: p2"  # Texas Rangers win
                elif away_score > home_score:
                    return "recommendation: p1"  # Tampa Bay Rays win
            elif game['Status'] == 'Postponed':
                return "recommendation: p4"  # Game postponed, too early to resolve
            elif game['Status'] == 'Canceled':
                return "recommendation: p3"  # Game canceled, resolve as 50-50
    return "recommendation: p4"  # No game found or future game

print(fetch_mlb_game_result())