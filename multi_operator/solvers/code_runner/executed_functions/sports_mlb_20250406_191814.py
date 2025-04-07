from dotenv import load_dotenv
import os
import requests

def resolve_mlb_game():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
    game_date = "2025-04-05"
    home_team = "New York Mets"
    away_team = "Toronto Blue Jays"

    RESOLUTION_MAP = {
        "New York Mets": "p2",
        "Toronto Blue Jays": "p1",
        "50-50": "p3",
        "Too early to resolve": "p4"
    }

    if not api_key:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

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
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

print(resolve_mlb_game())