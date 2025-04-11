import os
from python_dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()
SPORTS_DATA_IO_NBA_API_KEY = os.getenv('SPORTS_DATA_IO_NBA_API_KEY')

def fetch_nba_game_result():
    # Define the API endpoint
    url = "https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/2025-04-10"
    headers = {
        'Ocp-Apim-Subscription-Key': SPORTS_DATA_IO_NBA_API_KEY
    }

    # Make the API request
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        games = response.json()
        for game in games:
            if game['HomeTeam'] == 'MIN' and game['AwayTeam'] == 'MEM':
                if game['Status'] == 'Final':
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    if home_score > away_score:
                        return "recommendation: p2"  # Timberwolves win
                    elif away_score > home_score:
                        return "recommendation: p1"  # Grizzlies win
                elif game['Status'] == 'Postponed':
                    return "recommendation: p4"  # Game postponed
                elif game['Status'] == 'Canceled':
                    return "recommendation: p3"  # Game canceled, resolve 50-50
    return "recommendation: p4"  # Default case if no data matches or API fails

# Execute the function and print the result
print(fetch_nba_game_result())