import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
HLTV_API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")
if not HLTV_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_CBB_API_KEY")

# Configuration for headers and API endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": HLTV_API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/cbb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/cbb-proxy"

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}/{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return None

# Function to resolve the market based on the match result
def resolve_market(match_date, team1, team2):
    date_formatted = datetime.strptime(match_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today = make_request(PROXY_ENDPOINT, f"GamesByDate/{date_formatted}") or \
                  make_request(PRIMARY_ENDPOINT, f"GamesByDate/{date_formatted}")

    if games_today:
        for game in games_today:
            if {game['HomeTeam'], game['AwayTeam']} == {team1, team2}:
                if game['Status'] == 'Final':
                    if game['HomeTeam'] == team1 and game['HomeTeamScore'] > game['AwayTeamScore']:
                        return "recommendation: p1"
                    elif game['AwayTeam'] == team1 and game['AwayTeamScore'] > game['HomeTeamScore']:
                        return "recommendation: p1"
                    elif game['HomeTeam'] == team2 and game['HomeTeamScore'] > game['AwayTeamScore']:
                        return "recommendation: p2"
                    elif game['AwayTeam'] == team2 and game['AwayTeamScore'] > game['HomeTeamScore']:
                        return "recommendation: p2"
                elif game['Status'] in ['Canceled', 'Postponed']:
                    return "recommendation: p3"
    return "recommendation: p3"

# Main execution function
if __name__ == "__main__":
    match_date = "2025-06-07"
    team1 = "3DMAX"
    team2 = "Legacy"
    result = resolve_market(match_date, team1, team2)
    print(result)