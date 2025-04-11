import requests
from datetime import datetime
from python_dotenv import load_dotenv
import os

def fetch_nba_game_result():
    load_dotenv()
    api_key = os.getenv('SPORTS_DATA_IO_NBA_API_KEY')
    url = "https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/2025-04-10"
    headers = {
        'Ocp-Apim-Subscription-Key': api_key
    }
    response = requests.get(url, headers=headers)
    games = response.json()

    for game in games:
        if game['HomeTeam'] == 'CLE' and game['AwayTeam'] == 'IND':
            if game['Status'] == 'Final':
                home_score = game['HomeTeamScore']
                away_score = game['AwayTeamScore']
                if home_score > away_score:
                    return "recommendation: p2"  # Cavaliers win
                elif away_score > home_score:
                    return "recommendation: p1"  # Pacers win
            elif game['Status'] == 'Postponed':
                return "recommendation: p4"  # Game postponed
            elif game['Status'] == 'Canceled':
                return "recommendation: p3"  # Game canceled, resolve 50-50
    return "recommendation: p4"  # No game found or future game

if __name__ == "__main__":
    recommendation = fetch_nba_game_result()
    print(recommendation)