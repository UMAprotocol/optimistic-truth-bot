from dotenv import load_dotenv
import os
import requests
import datetime

def resolve_mlb_game():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
    if not api_key:
        return "recommendation: p4"  # API key not found, cannot proceed

    # Define the game details
    home_team = "Boston Red Sox"
    away_team = "St. Louis Cardinals"
    game_date = "2025-04-06T19:00:00"  # Date and time in ISO format

    # Define resolution map
    RESOLUTION_MAP = {
        "Boston Red Sox": "p2",
        "St. Louis Cardinals": "p1",
        "50-50": "p3",
        "Too early to resolve": "p4"
    }

    # Check if the current date is before the game date
    current_time = datetime.datetime.utcnow()
    game_datetime = datetime.datetime.fromisoformat(game_date)
    if current_time < game_datetime:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    # API endpoint and parameters
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
                    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
                elif game['Status'] == "Canceled":
                    return "recommendation: " + RESOLUTION_MAP["50-50"]
        return "recommendation: p4"  # Game not found or no clear outcome

    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
        return "recommendation: p4"  # Error in fetching data

# Call the function and print the result
result = resolve_mlb_game()
print(result)