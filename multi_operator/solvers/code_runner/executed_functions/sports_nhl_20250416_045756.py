import requests
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
api_key = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Define the resolution map using team abbreviations
RESOLUTION_MAP = {
    "MEM": "p2",  # Memphis Grizzlies
    "GSW": "p1",  # Golden State Warriors
    "50-50": "p3",
    "Too early to resolve": "p4",
}

def fetch_nba_game_result(team1, team2, game_date):
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{game_date}"
    headers = {'Ocp-Apim-Subscription-Key': api_key}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] == team1 and game['AwayTeam'] == team2 or game['HomeTeam'] == team2 and game['AwayTeam'] == team1:
                if game['Status'] == "Final":
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    if home_score > away_score:
                        return RESOLUTION_MAP[game['HomeTeam']]
                    else:
                        return RESOLUTION_MAP[game['AwayTeam']]
                elif game['Status'] == "Postponed":
                    return RESOLUTION_MAP["Too early to resolve"]
                elif game['Status'] == "Canceled":
                    return RESOLUTION_MAP["50-50"]
    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
        return RESOLUTION_MAP["Too early to resolve"]

# Define the teams and game date
team1 = "MEM"  # Memphis Grizzlies
team2 = "GSW"  # Golden State Warriors
game_date = "2025-04-15"

# Fetch the game result and print the recommendation
result = fetch_nba_game_result(team1, team2, game_date)
print(f"recommendation: {result}")