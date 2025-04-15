import requests
from dotenv import load_dotenv
import os

def fetch_nhl_game_result():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
    url = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/2025-04-14"
    headers = {
        "Ocp-Apim-Subscription-Key": api_key
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json()
        
        for game in games:
            if game['HomeTeam'] == 'NYR' and game['AwayTeam'] == 'FLA':
                if game['Status'] == 'Final':
                    if game['HomeTeamScore'] > game['AwayTeamScore']:
                        return "recommendation: p2"  # Rangers win
                    elif game['HomeTeamScore'] < game['AwayTeamScore']:
                        return "recommendation: p1"  # Panthers win
                elif game['Status'] == 'Postponed':
                    return "recommendation: p4"  # Game postponed
                elif game['Status'] == 'Canceled':
                    return "recommendation: p3"  # Game canceled, resolve 50-50
        return "recommendation: p4"  # No game found or not yet played
    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
        return "recommendation: p4"  # Unable to resolve due to error

# Example usage
result = fetch_nhl_game_result()
print(result)