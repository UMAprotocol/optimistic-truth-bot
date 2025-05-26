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
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nhl-proxy"
DATE = "2025-05-24"
TEAM1 = "Delhi Capitals"
TEAM2 = "Punjab Kings"
RESOLUTION_MAP = {
    "DEL": "p2",  # Delhi Capitals
    "PUN": "p1",  # Punjab Kings
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Helper functions
def get_data(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def resolve_match(date, team1, team2):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{formatted_date}"
    games = get_data(url, HEADERS)
    if games:
        for game in games:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or \
               (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                if game['Status'] == "Final":
                    if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                        winner = game['HomeTeam']
                    else:
                        winner = game['AwayTeam']
                    return RESOLUTION_MAP.get(winner, "p4")
                elif game['Status'] in ["Canceled", "Postponed"]:
                    return "p3"
                else:
                    return "p4"
    return "p4"

# Main execution
if __name__ == "__main__":
    recommendation = resolve_match(DATE, TEAM1, TEAM2)
    print(f"recommendation: {recommendation}")