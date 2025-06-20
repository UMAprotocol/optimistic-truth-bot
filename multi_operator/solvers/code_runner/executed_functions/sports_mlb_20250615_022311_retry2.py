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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/mlb"

# Game details
GAME_DATE = "2025-06-14"
HOME_TEAM = "San Diego Padres"
AWAY_TEAM = "Arizona Diamondbacks"

# Resolution map
RESOLUTION_MAP = {
    HOME_TEAM: "p2",  # Padres win
    AWAY_TEAM: "p1",  # Diamondbacks win
    "Canceled": "p3",  # Game canceled
    "Postponed": "p4",  # Game postponed
    "In Progress": "p4",  # Game not completed
    "Scheduled": "p4"  # Game not started
}

def get_game_data(date):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{formatted_date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        return games
    except requests.exceptions.RequestException:
        # Fallback to proxy endpoint
        proxy_url = f"{PROXY_ENDPOINT}/GamesByDate/{formatted_date}"
        response = requests.get(proxy_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()

def analyze_game(games, home_team, away_team):
    for game in games:
        if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
            status = game['Status']
            if status == "Final":
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return RESOLUTION_MAP[home_team]
                elif away_score > home_score:
                    return RESOLUTION_MAP[away_team]
            else:
                return RESOLUTION_MAP.get(status, "p4")
    return "p4"

if __name__ == "__main__":
    games = get_game_data(GAME_DATE)
    recommendation = analyze_game(games, HOME_TEAM, AWAY_TEAM)
    print(f"recommendation: {recommendation}")