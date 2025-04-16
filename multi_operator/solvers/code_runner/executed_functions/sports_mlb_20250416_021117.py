from dotenv import load_dotenv
import os
import requests

def resolve_mlb_game():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
    if not api_key:
        return "recommendation: p4"  # API key not found, cannot proceed

    game_date = "2025-04-15"
    home_team = "St. Louis Cardinals"
    away_team = "Houston Astros"
    RESOLUTION_MAP = {
        "St. Louis Cardinals": "p1",
        "Houston Astros": "p2",
        "50-50": "p3",
        "Too early to resolve": "p4"
    }

    try:
        response = requests.get(
            f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{game_date}",
            headers={"Ocp-Apim-Subscription-Key": api_key}
        )
        games = response.json()
        for game in games:
            if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
                if game['Status'] == "Final":
                    if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                        return "recommendation: " + RESOLUTION_MAP[home_team]
                    elif game['AwayTeamRuns'] > game['HomeTeamRuns']:
                        return "recommendation: " + RESOLUTION_MAP[away_team]
                elif game['Status'] == "Postponed":
                    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
                elif game['Status'] == "Canceled":
                    return "recommendation: " + RESOLUTION_MAP["50-50"]
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    except Exception as e:
        print(f"Error occurred: {e}")
        return "recommendation: p4"  # Error handling case

print(resolve_mlb_game())