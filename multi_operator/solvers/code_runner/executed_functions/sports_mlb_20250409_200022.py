import requests
from dotenv import load_dotenv
import os

def resolve_mlb_game():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
    if not api_key:
        return "recommendation: p4"  # API key not found, cannot proceed

    # Define the teams and date from the question
    home_team = "Pittsburgh Pirates"
    away_team = "St. Louis Cardinals"
    game_date = "2025-04-09"

    # Define the resolution map
    RESOLUTION_MAP = {
        "Pittsburgh Pirates": "p2",  # Home team wins
        "St. Louis Cardinals": "p1",  # Away team wins
        "50-50": "p3",  # Game canceled with no make-up
        "Too early to resolve": "p4"  # Not enough data or future event
    }

    # API endpoint and parameters
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{game_date}"
    headers = {
        'Ocp-Apim-Subscription-Key': api_key
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json()

        # Find the game in question
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
        return "recommendation: p4"  # Game not found or future event

    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return "recommendation: p4"  # Error in fetching data

# Run the function and print the result
print(resolve_mlb_game())