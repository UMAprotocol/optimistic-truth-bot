import requests
from datetime import datetime
from dotenv import load_dotenv
import os

def fetch_game_result():
    load_dotenv()
    api_key = os.getenv('SPORTS_DATA_IO_NHL_API_KEY')
    url = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/2025-04-09"
    headers = {
        'Ocp-Apim-Subscription-Key': api_key
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        games = response.json()
        for game in games:
            if 'Maple Leafs' in game['HomeTeam'] or 'Maple Leafs' in game['AwayTeam']:
                if 'Lightning' in game['HomeTeam'] or 'Lightning' in game['AwayTeam']:
                    if game['Status'] == "Final":
                        home_team_score = game['HomeTeamScore']
                        away_team_score = game['AwayTeamScore']
                        if game['HomeTeam'] == 'Maple Leafs':
                            maple_leafs_score = home_team_score
                            lightning_score = away_team_score
                        else:
                            maple_leafs_score = away_team_score
                            lightning_score = home_team_score

                        if maple_leafs_score > lightning_score:
                            return "recommendation: p2"  # Maple Leafs win
                        elif lightning_score > maple_leafs_score:
                            return "recommendation: p1"  # Lightning win
                    elif game['Status'] == "Postponed":
                        return "recommendation: p4"  # Game postponed
                    elif game['Status'] == "Canceled":
                        return "recommendation: p3"  # Game canceled
    return "recommendation: p4"  # Default to unresolved if no data matches or API fails

print(fetch_game_result())