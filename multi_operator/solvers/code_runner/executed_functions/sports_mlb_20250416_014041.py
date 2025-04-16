import requests
import datetime
from dotenv import load_dotenv
import os

def fetch_game_result():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
    if not api_key:
        return "recommendation: p4"  # API key not found, cannot proceed

    # Define the teams and date from the question
    home_team = "New York Yankees"
    away_team = "Kansas City Royals"
    game_date = "2025-04-15"

    # Prepare API request
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{game_date}"
    headers = {
        'Ocp-Apim-Subscription-Key': api_key
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json()

        # Find the game between the specified teams
        for game in games:
            if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
                if game['Status'] == "Final":
                    if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                        return "recommendation: p1"  # Home team (Yankees) wins
                    elif game['AwayTeamRuns'] > game['HomeTeamRuns']:
                        return "recommendation: p2"  # Away team (Royals) wins
                elif game['Status'] == "Postponed":
                    return "recommendation: p4"  # Game postponed, resolve later
                elif game['Status'] == "Canceled":
                    return "recommendation: p3"  # Game canceled, resolve 50-50
        return "recommendation: p4"  # Game not found or not yet played

    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
        return "recommendation: p4"  # Error in fetching data

# Run the function and print the result
result = fetch_game_result()
print(result)