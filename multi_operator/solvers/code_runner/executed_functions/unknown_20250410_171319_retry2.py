import requests
from dotenv import load_dotenv
import os

def fetch_game_result():
    load_dotenv()
    api_key = os.getenv('SPORTS_DATA_IO_NBA_API_KEY')
    url = "https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/2025-04-09"
    headers = {
        'Ocp-Apim-Subscription-Key': api_key
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        games = response.json()
        for game in games:
            if game['HomeTeam'] == 'MIA' and game['AwayTeam'] == 'CHI':
                if game['Status'] == 'Final':
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    if home_score > away_score:
                        return "recommendation: p2"  # Heat win
                    elif away_score > home_score:
                        return "recommendation: p1"  # Bulls win
                elif game['Status'] == 'Postponed':
                    return "recommendation: p4"  # Game postponed
                elif game['Status'] == 'Canceled':
                    return "recommendation: p3"  # Game canceled
    elif response.status_code == 401:
        return "Error: Access denied due to invalid subscription key."
    else:
        return "Error: Failed to fetch data with status code " + str(response.status_code)

    return "recommendation: p4"  # Default to too early to resolve if no data matches

print(fetch_game_result())