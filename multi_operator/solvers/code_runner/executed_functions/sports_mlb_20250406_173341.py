import requests
from dotenv import load_dotenv
import os

def resolve_mlb_game():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
    if not api_key:
        return "recommendation: p4"  # Return "Too early to resolve" if API key is missing

    game_date = "2025-04-04"
    home_team = "Atlanta Braves"
    away_team = "Miami Marlins"
    RESOLUTION_MAP = {
        "Atlanta Braves": "p2",  # Home team wins
        "Miami Marlins": "p1",   # Away team wins
        "50-50": "p3",           # Game canceled with no make-up
        "Too early to resolve": "p4"  # Not enough data or future event
    }

    try:
        response = requests.get(
            f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{game_date}",
            headers={"Ocp-Apim-Subscription-Key": api_key}
        )
        games = response.json()

        # Find the game between the specified teams
        game_info = next((game for game in games if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team), None)
        if not game_info:
            return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

        if game_info['Status'] == "Final":
            if game_info['HomeTeamRuns'] > game_info['AwayTeamRuns']:
                return "recommendation: " + RESOLUTION_MAP[home_team]
            elif game_info['HomeTeamRuns'] < game_info['AwayTeamRuns']:
                return "recommendation: " + RESOLUTION_MAP[away_team]
        elif game_info['Status'] == "Postponed":
            return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
        elif game_info['Status'] == "Canceled":
            return "recommendation: " + RESOLUTION_MAP["50-50"]
    except Exception as e:
        print(f"Error occurred: {e}")
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

# Example usage
result = resolve_mlb_game()
print(result)