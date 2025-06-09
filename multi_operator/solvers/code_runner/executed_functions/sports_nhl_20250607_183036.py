import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Constants
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
DATE = "2025-06-07"
TEAM1 = "MIBR"  # p2
TEAM2 = "Legacy"  # p1
RESOLUTION_MAP = {
    "MIBR": "p2",
    "Legacy": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Helper functions
def get_json_response(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def find_match_result(date, team1, team2):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{formatted_date}"
    games = get_json_response(url, HEADERS)
    if games:
        for game in games:
            teams = {game['HomeTeam'], game['AwayTeam']}
            if team1 in teams and team2 in teams:
                if game['Status'] == "Final":
                    if game['HomeTeam'] == team1 and game['HomeTeamScore'] > game['AwayTeamScore']:
                        return RESOLUTION_MAP[team1]
                    elif game['AwayTeam'] == team1 and game['AwayTeamScore'] > game['HomeTeamScore']:
                        return RESOLUTION_MAP[team1]
                    elif game['HomeTeam'] == team2 and game['HomeTeamScore'] > game['AwayTeamScore']:
                        return RESOLUTION_MAP[team2]
                    elif game['AwayTeam'] == team2 and game['AwayTeamScore'] > game['HomeTeamScore']:
                        return RESOLUTION_MAP[team2]
                elif game['Status'] in ["Canceled", "Postponed"]:
                    return RESOLUTION_MAP["50-50"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    result = find_match_result(DATE, TEAM1, TEAM2)
    print(f"recommendation: {result}")