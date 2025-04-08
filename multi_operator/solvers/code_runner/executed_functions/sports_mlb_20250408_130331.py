import requests
from dotenv import load_dotenv
import os

def resolve_mlb_game():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
    if not api_key:
        return "recommendation: p4"  # API key not found, cannot proceed

    game_date = "2025-04-04"
    home_team = "Boston Red Sox"
    away_team = "St. Louis Cardinals"
    RESOLUTION_MAP = {
        "Boston Red Sox": "p2",
        "St. Louis Cardinals": "p1",
        "50-50": "p3",
        "Too early to resolve": "p4"
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
                    elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
                        return "recommendation: " + RESOLUTION_MAP[away_team]
                elif game['Status'] == "Postponed":
                    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
                elif game['Status'] == "Canceled":
                    return "recommendation: " + RESOLUTION_MAP["50-50"]
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]  # No matching game found
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return "recommendation: p4"  # Error in fetching data

# Example usage
result = resolve_mlb_game()
print(result)