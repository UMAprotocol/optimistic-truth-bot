import requests
from dotenv import load_dotenv
import os

def fetch_game_result():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
    url = "https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/2025-04-14"
    headers = {
        "Ocp-Apim-Subscription-Key": api_key
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] == "HOU" and game['AwayTeam'] == "STL":
                if game['Status'] == "Final":
                    if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                        return "recommendation: p2"  # Houston Astros win
                    elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
                        return "recommendation: p1"  # St. Louis Cardinals win
                elif game['Status'] == "Postponed":
                    return "recommendation: p4"  # Game postponed, unresolved
                elif game['Status'] == "Canceled":
                    return "recommendation: p3"  # Game canceled, resolve 50-50
        return "recommendation: p4"  # No game found or future game
    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
        return "recommendation: p4"  # Error case, unresolved

if __name__ == "__main__":
    result = fetch_game_result()
    print(result)