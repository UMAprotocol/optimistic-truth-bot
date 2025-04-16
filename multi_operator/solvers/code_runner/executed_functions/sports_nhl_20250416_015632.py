import requests
from dotenv import load_dotenv
import os
from datetime import datetime

# Load environment variables
load_dotenv()
api_key = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Define the resolution map using team abbreviations
RESOLUTION_MAP = {
    "FLA": "p2",  # Florida Panthers
    "TBL": "p1",  # Tampa Bay Lightning
    "50-50": "p3",
    "Too early to resolve": "p4",
}

def fetch_nhl_game_result(team1, team2, game_date):
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{game_date}"
    headers = {'Ocp-Apim-Subscription-Key': api_key}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                if game['Status'] == "Final":
                    if game['HomeTeamScore'] > game['AwayTeamScore']:
                        return RESOLUTION_MAP[game['HomeTeam']]
                    elif game['AwayTeamScore'] > game['HomeTeamScore']:
                        return RESOLUTION_MAP[game['AwayTeam']]
                elif game['Status'] == "Postponed":
                    return RESOLUTION_MAP["Too early to resolve"]
                elif game['Status'] == "Canceled":
                    return RESOLUTION_MAP["50-50"]
    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
        return RESOLUTION_MAP["Too early to resolve"]

    return RESOLUTION_MAP["Too early to resolve"]

# Define the game details
team1 = "FLA"  # Florida Panthers
team2 = "TBL"  # Tampa Bay Lightning
game_date = "2025-04-15"  # Format YYYY-MM-DD

# Check if the current date is past the game date
current_date = datetime.now().strftime("%Y-%m-%d")
if current_date > game_date:
    result = fetch_nhl_game_result(team1, team2, game_date)
    print(f"recommendation: {result}")
else:
    print("recommendation: " + RESOLUTION_MAP["Too early to resolve"])