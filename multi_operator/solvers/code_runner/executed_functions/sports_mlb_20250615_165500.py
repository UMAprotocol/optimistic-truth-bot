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
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy/GamesByDate/"

# Date and teams for the query
MATCH_DATE = "2025-06-15"
TEAMS = ("Bayern Munich", "Auckland City")

# Resolution conditions
RESOLUTION_MAP = {
    "Yes": "p2",  # More than 4.5 goals
    "No": "p1",   # 4.5 goals or fewer
    "Unknown": "p3"  # Canceled or postponed
}

def get_games_by_date(date):
    """
    Fetch games data from the API for a specific date.
    """
    url = f"{PROXY_ENDPOINT}{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if not response.ok:
            # Fallback to primary endpoint if proxy fails
            url = f"{PRIMARY_ENDPOINT}{date}"
            response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def analyze_match(games):
    """
    Analyze the fetched games to determine the outcome based on the total goals.
    """
    for game in games:
        if game['HomeTeamName'] in TEAMS and game['AwayTeamName'] in TEAMS:
            if game['Status'] == "Final":
                total_goals = game['HomeTeamScore'] + game['AwayTeamScore']
                return "Yes" if total_goals > 4.5 else "No"
            elif game['Status'] in ["Canceled", "Postponed"]:
                return "Unknown"
    return "Unknown"

def main():
    games = get_games_by_date(MATCH_DATE)
    if games is None:
        print("recommendation:", RESOLUTION_MAP["Unknown"])
    else:
        result = analyze_match(games)
        print("recommendation:", RESOLUTION_MAP[result])

if __name__ == "__main__":
    main()