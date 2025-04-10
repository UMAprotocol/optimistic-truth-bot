import requests
from dotenv import load_dotenv
import os

def resolve_mlb_game():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
    if not api_key:
        return "recommendation: p3"  # Return 50-50 if API key is not set

    # Define the teams and date from the question
    home_team = "Arizona Diamondbacks"
    away_team = "Baltimore Orioles"
    game_date = "2025-04-09"

    # API endpoint and parameters
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{game_date}"
    headers = {
        'Ocp-Apim-Subscription-Key': api_key
    }

    # RESOLUTION_MAP based on the outcomes
    RESOLUTION_MAP = {
        "Arizona Diamondbacks": "p2",
        "Baltimore Orioles": "p1",
        "50-50": "p3",
        "Too early to resolve": "p4"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json()

        # Find the game and determine the outcome
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
        return "recommendation: p3"  # Return 50-50 in case of API errors

# Run the function and print the result
print(resolve_mlb_game())