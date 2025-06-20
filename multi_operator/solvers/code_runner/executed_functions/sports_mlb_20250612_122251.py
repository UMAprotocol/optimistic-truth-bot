import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy/GamesByDate/"

# Date and teams for the query
DATE = "2025-06-12"
TEAM1 = "Giovanni Mpetshi Perricard"
TEAM2 = "Felix Auger-Aliassime"

# Resolution map based on the outcome
RESOLUTION_MAP = {
    TEAM1: "p2",  # Perricard wins
    TEAM2: "p1",  # Aliassime wins
    "50-50": "p3",  # Tie, canceled, or delayed
    "Too early to resolve": "p4"  # Not enough data
}

def get_games_by_date(date):
    """ Fetch games data from the API by date """
    url = PRIMARY_ENDPOINT + date
    proxy_url = PROXY_ENDPOINT + date
    try:
        response = requests.get(proxy_url, headers=HEADERS, timeout=10)
        if not response.ok:
            response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def resolve_market(games, team1, team2):
    """ Determine the outcome of the market based on the games data """
    for game in games:
        if team1 in game['HomeTeam'] or team1 in game['AwayTeam']:
            if team2 in game['HomeTeam'] or team2 in game['AwayTeam']:
                if game['Status'] == "Final":
                    if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                        winner = game['HomeTeam']
                    else:
                        winner = game['AwayTeam']
                    return "recommendation: " + RESOLUTION_MAP.get(winner, "p3")
                elif game['Status'] in ["Canceled", "Postponed"]:
                    return "recommendation: p3"
                else:
                    return "recommendation: p4"
    return "recommendation: p4"

if __name__ == "__main__":
    games = get_games_by_date(DATE)
    if games:
        result = resolve_market(games, TEAM1, TEAM2)
    else:
        result = "recommendation: p4"
    print(result)