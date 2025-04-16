from dotenv import load_dotenv
import os
import requests

def fetch_game_result():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
    url = "https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/2025-04-15"
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
                    return "recommendation: p4"  # Game postponed, resolve later
                elif game['Status'] == "Canceled":
                    return "recommendation: p3"  # Game canceled, resolve 50-50
        return "recommendation: p4"  # No game found or not yet played
    except requests.RequestException as e:
        print(f"API request failed: {e}")
        return "recommendation: p4"  # API error or data access issue
    except KeyError as e:
        print(f"Data parsing error: {e}")
        return "recommendation: p4"  # Data format error

# Run the function and print the result
print(fetch_game_result())