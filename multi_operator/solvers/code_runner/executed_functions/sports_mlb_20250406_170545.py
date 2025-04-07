import requests
from dotenv import load_dotenv
import os

def fetch_game_result():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
    url = "https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/2025-04-04"
    headers = {
        "Ocp-Apim-Subscription-Key": api_key
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json()
        
        for game in games:
            if game['HomeTeam'] == "MIL" and game['AwayTeam'] == "CIN":
                if game['Status'] == "Final":
                    if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                        return "recommendation: p2"  # Milwaukee Brewers win
                    elif game['AwayTeamRuns'] > game['HomeTeamRuns']:
                        return "recommendation: p1"  # Cincinnati Reds win
                elif game['Status'] == "Postponed":
                    return "recommendation: p4"  # Game postponed, resolve later
                elif game['Status'] == "Canceled":
                    return "recommendation: p3"  # Game canceled, resolve 50-50
        return "recommendation: p4"  # No game found or not yet played
    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
        return "recommendation: p4"  # Error case, unable to resolve

if __name__ == "__main__":
    result = fetch_game_result()
    print(result)