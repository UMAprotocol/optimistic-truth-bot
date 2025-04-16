import requests
from dotenv import load_dotenv
import os
from datetime import datetime

def fetch_nhl_game_result():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
    if not api_key:
        return "recommendation: p4"  # API key not found, cannot resolve

    # Define the game details
    game_date = "2025-04-15"
    team_home = "VGK"  # Vegas Golden Knights
    team_away = "CGY"  # Calgary Flames

    # Define the resolution map
    RESOLUTION_MAP = {
        "VGK": "p2",  # Golden Knights win
        "CGY": "p1",  # Flames win
        "50-50": "p3",
        "Too early to resolve": "p4",
    }

    # Check if the current date is before the game date
    if datetime.now() < datetime.strptime(game_date + " 21:00", "%Y-%m-%d %H:%M"):
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    # API endpoint setup
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{game_date}"
    headers = {
        'Ocp-Apim-Subscription-Key': api_key
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json()

        # Find the game
        for game in games:
            if game['HomeTeam'] == team_home and game['AwayTeam'] == team_away:
                if game['Status'] == "Final":
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    if home_score > away_score:
                        return "recommendation: " + RESOLUTION_MAP[team_home]
                    elif away_score > home_score:
                        return "recommendation: " + RESOLUTION_MAP[team_away]
                elif game['Status'] == "Postponed":
                    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
                elif game['Status'] == "Canceled":
                    return "recommendation: " + RESOLUTION_MAP["50-50"]
    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
        return "recommendation: p4"  # Error in fetching data

    return "recommendation: p4"  # Default case if no condition matched

# Run the function and print the result
print(fetch_nhl_game_result())