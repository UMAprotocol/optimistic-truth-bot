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

# Game details
GAME_DATE = "2025-06-06"
HOME_TEAM = "Nationals"
AWAY_TEAM = "Rangers"

# Resolution map
RESOLUTION_MAP = {
    "Nationals": "p1",
    "Rangers": "p2",
    "Canceled": "p3",
    "Postponed": "p4",
    "In Progress": "p4"
}

def get_game_data(date):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{formatted_date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            # Fallback to proxy if primary fails
            response = requests.get(f"{PROXY_ENDPOINT}/GamesByDate/{formatted_date}", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return None
    except requests.RequestException:
        return None

def analyze_game_results(games):
    for game in games:
        if game['HomeTeam'] == HOME_TEAM and game['AwayTeam'] == AWAY_TEAM:
            if game['Status'] == "Final":
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return RESOLUTION_MAP[HOME_TEAM]
                elif away_score > home_score:
                    return RESOLUTION_MAP[AWAY_TEAM]
            elif game['Status'] in ["Canceled", "Postponed"]:
                return RESOLUTION_MAP[game['Status']]
    return "p4"  # Default to unresolved if no matching game is found

def main():
    games = get_game_data(GAME_DATE)
    if games:
        result = analyze_game_results(games)
        print(f"recommendation: {result}")
    else:
        print("recommendation: p4")  # No data available

if __name__ == "__main__":
    main()