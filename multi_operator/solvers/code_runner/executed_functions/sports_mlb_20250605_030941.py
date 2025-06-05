import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API configuration
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/mlb"

# Resolution map
RESOLUTION_MAP = {
    "Diamondbacks": "p2",
    "Braves": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Helper functions
def get_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None

def resolve_game(date, home_team, away_team):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today = get_data(f"{PROXY_ENDPOINT}/GamesByDate/{formatted_date}")
    if not games_today:
        games_today = get_data(f"{PRIMARY_ENDPOINT}/GamesByDate/{formatted_date}")

    if games_today:
        for game in games_today:
            if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
                if game['Status'] == 'Final':
                    if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                        return RESOLUTION_MAP[home_team]
                    elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
                        return RESOLUTION_MAP[away_team]
                elif game['Status'] in ['Canceled', 'Postponed']:
                    return RESOLUTION_MAP["50-50"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    game_date = "2025-06-04"
    home_team = "Braves"
    away_team = "Diamondbacks"
    recommendation = resolve_game(game_date, home_team, away_team)
    print(f"recommendation: {recommendation}")