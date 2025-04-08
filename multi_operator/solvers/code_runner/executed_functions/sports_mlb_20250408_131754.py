import requests
from dotenv import load_dotenv
import os

def resolve_mlb_game():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
    if not api_key:
        return "recommendation: p4"  # API key not found, cannot resolve

    game_date = "2025-04-06"
    home_team = "Chicago Cubs"
    away_team = "San Diego Padres"
    RESOLUTION_MAP = {
        "Chicago Cubs": "p2",
        "San Diego Padres": "p1",
        "postponed": "p4",
        "canceled": "p3"
    }

    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{game_date}?key={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
                if game['Status'] == "Final":
                    if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                        return "recommendation: " + RESOLUTION_MAP[home_team]
                    elif game['AwayTeamRuns'] > game['HomeTeamRuns']:
                        return "recommendation: " + RESOLUTION_MAP[away_team]
                elif game['Status'] == "Postponed":
                    return "recommendation: " + RESOLUTION_MAP["postponed"]
                elif game['Status'] == "Canceled":
                    return "recommendation: " + RESOLUTION_MAP["canceled"]
        return "recommendation: p4"  # No matching game found or game not yet played
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return "recommendation: p4"  # Error in fetching data

# Example of calling the function
result = resolve_mlb_game()
print(result)