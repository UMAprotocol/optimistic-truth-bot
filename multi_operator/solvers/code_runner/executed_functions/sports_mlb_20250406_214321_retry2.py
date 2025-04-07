import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def fetch_mlb_game_result():
    api_key = os.getenv('SPORTS_DATA_IO_MLB_API_KEY')
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{datetime.now().strftime('%Y-%m-%d')}"
    headers = {
        'Ocp-Apim-Subscription-Key': api_key
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        games = response.json()
        for game in games:
            if game['HomeTeam'] == 'HOU' and game['AwayTeam'] == 'MIN':
                if game['Status'] == 'Final':
                    if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                        return "recommendation: p1"  # Houston Astros win
                    elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
                        return "recommendation: p2"  # Minnesota Twins win
                elif game['Status'] == 'Postponed':
                    return "recommendation: p4"  # Game postponed, too early to resolve
                elif game['Status'] == 'Canceled':
                    return "recommendation: p3"  # Game canceled, resolve 50-50
    return "recommendation: p4"  # Default case if no data matches or API fails

# Execute the function and print the result
print(fetch_mlb_game_result())