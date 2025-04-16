import requests
from dotenv import load_dotenv
import os

def resolve_mlb_game():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
    if not api_key:
        return "recommendation: p4"  # API key not found, cannot proceed

    # Define the game details
    home_team = "Boston Red Sox"
    away_team = "Tampa Bay Rays"
    game_date = "2025-04-14T19:05:00"  # ISO 8601 format

    # Define resolution map based on the ancillary data provided
    RESOLUTION_MAP = {
        "Boston Red Sox": "p2",
        "Tampa Bay Rays": "p1",
        "Postponed": "p4",
        "Canceled": "p3"
    }

    # API endpoint setup
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{game_date[:10]}"
    headers = {
        'Ocp-Apim-Subscription-Key': api_key
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json()

        # Find the game
        for game in games:
            if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
                if game['Status'] == "Final":
                    if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                        return "recommendation: " + RESOLUTION_MAP[home_team]
                    elif game['AwayTeamRuns'] > game['HomeTeamRuns']:
                        return "recommendation: " + RESOLUTION_MAP[away_team]
                elif game['Status'] == "Postponed":
                    return "recommendation: " + RESOLUTION_MAP["Postponed"]
                elif game['Status'] == "Canceled":
                    return "recommendation: " + RESOLUTION_MAP["Canceled"]
        
        # If no specific game status is found, assume it's too early to resolve
        return "recommendation: p4"

    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return "recommendation: p4"  # Error in fetching data

# Run the function and print the result
result = resolve_mlb_game()
print(result)