import requests
from dotenv import load_dotenv
import os

def fetch_nba_game_result():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
    url = "https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/2025-04-15"
    headers = {
        "Ocp-Apim-Subscription-Key": api_key
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json()
        
        for game in games:
            if game['HomeTeam'] == 'MEM' and game['AwayTeam'] == 'GSW':
                home_team_score = game['HomeTeamScore']
                away_team_score = game['AwayTeamScore']
                
                if home_team_score is None or away_team_score is None:
                    return "recommendation: p4"  # Game has not yet been played
                elif home_team_score > away_team_score:
                    return "recommendation: p2"  # Grizzlies win
                elif away_team_score > home_team_score:
                    return "recommendation: p1"  # Warriors win
                else:
                    return "recommendation: p4"  # In case of a tie or error
                
        return "recommendation: p4"  # No game found for the specific teams on the date

    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve data: {e}")
        return "recommendation: p4"  # Unable to resolve due to API error

# Example of calling the function
result = fetch_nba_game_result()
print(result)