import requests
from dotenv import load_dotenv
import os

def resolve_mlb_game():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
    if not api_key:
        return "recommendation: p4"  # API key not found, cannot resolve

    game_date = "2025-04-14"
    home_team = "Minnesota Twins"
    away_team = "New York Mets"

    RESOLUTION_MAP = {
        "Minnesota Twins": "p1",
        "New York Mets": "p2",
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
                    return "recommendation: p4"  # Game postponed, resolve later
                elif game['Status'] == "Canceled":
                    return "recommendation: " + RESOLUTION_MAP["50-50"]
        return "recommendation: p4"  # No matching game found or future game

    except requests.exceptions.RequestException as e:
        print(f"API request error: {e}")
        return "recommendation: p4"  # API error, cannot resolve
    except KeyError as e:
        print(f"Data parsing error: {e}")
        return "recommendation: p4"  # Data error, cannot resolve

# Example usage
result = resolve_mlb_game()
print(result)