import requests
from dotenv import load_dotenv
import os

def resolve_mlb_game():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
    if not api_key:
        return "recommendation: p4"  # API key not found, cannot proceed

    # Define the teams and date from the question
    home_team = "San Francisco Giants"
    away_team = "Philadelphia Phillies"
    game_date = "2025-04-14"

    # Define the resolution map
    RESOLUTION_MAP = {
        "San Francisco Giants": "p2",  # Home team wins
        "Philadelphia Phillies": "p1",  # Away team wins
        "50-50": "p3",  # Game canceled with no make-up
        "Too early to resolve": "p4"  # Not enough data or future event
    }

    # API endpoint setup
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
                    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
                elif game['Status'] == "Canceled":
                    return "recommendation: " + RESOLUTION_MAP["50-50"]
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return "recommendation: p4"  # Error in fetching data
    except KeyError as e:
        print(f"Key error: {e}")
        return "recommendation: p4"  # Error in data processing

# Run the function and print the result
print(resolve_mlb_game())