import os
import requests
from dotenv import load_dotenv

load_dotenv()

def fetch_mlb_game_result():
    api_key = os.getenv('SPORTS_DATA_IO_MLB_API_KEY')
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/2025-04-04?key={api_key}"
    response = requests.get(url)
    games = response.json()

    for game in games:
        if game['HomeTeam'] == 'NYM' and game['AwayTeam'] == 'TOR':
            if game['Status'] == 'Final':
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    return "recommendation: p2"  # Mets win
                elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
                    return "recommendation: p1"  # Blue Jays win
            elif game['Status'] == 'Postponed':
                return "recommendation: p4"  # Game postponed, too early to resolve
            elif game['Status'] == 'Canceled':
                return "recommendation: p3"  # Game canceled, resolve as 50-50
    return "recommendation: p4"  # No game found or not yet played

print(fetch_mlb_game_result())