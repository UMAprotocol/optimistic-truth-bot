from dotenv import load_dotenv
import os
import requests

def resolve_mlb_game():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
    game_date = "2025-04-15"
    home_team = "San Francisco Giants"
    away_team = "Philadelphia Phillies"

    RESOLUTION_MAP = {
        "San Francisco Giants": "p2",
        "Philadelphia Phillies": "p1",
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
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

print(resolve_mlb_game())