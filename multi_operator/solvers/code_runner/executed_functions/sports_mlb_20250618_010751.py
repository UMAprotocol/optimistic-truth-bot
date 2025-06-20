import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not MLB_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API configuration
HEADERS = {"Ocp-Apim-Subscription-Key": MLB_API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "Pirates": "p2",  # Pittsburgh Pirates win
    "Tigers": "p1",   # Detroit Tigers win
    "Canceled": "p3", # Game canceled
    "Postponed": "p4" # Game postponed or in progress
}

def get_game_data(date, home_team, away_team):
    # Format the date for the API endpoint
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{formatted_date}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
    except requests.exceptions.RequestException:
        # Fallback to proxy if primary fails
        url = f"{PROXY_ENDPOINT}/GamesByDate/{formatted_date}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()

    # Search for the specific game
    for game in games:
        if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
            return game
    return None

def resolve_market(game):
    if not game:
        return "recommendation: p4"  # No game data found

    status = game['Status']
    if status == "Final":
        home_score = game['HomeTeamRuns']
        away_score = game['AwayTeamRuns']
        if home_score > away_score:
            return f"recommendation: {RESOLUTION_MAP[game['HomeTeam']]}"
        elif away_score > home_score:
            return f"recommendation: {RESOLUTION_MAP[game['AwayTeam']]}"
    elif status in ["Canceled", "Postponed"]:
        return f"recommendation: {RESOLUTION_MAP[status]}"

    return "recommendation: p4"  # Default case if none of the above conditions met

if __name__ == "__main__":
    # Game details
    game_date = "2025-06-17"
    home_team = "Tigers"  # Detroit Tigers
    away_team = "Pirates"  # Pittsburgh Pirates

    game_info = get_game_data(game_date, home_team, away_team)
    result = resolve_market(game_info)
    print(result)