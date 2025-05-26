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
def get_team_keys():
    url = "https://api.sportsdata.io/v3/nhl/scores/json/teams"
    response = requests.get(url, headers=HEADERS)
    teams = response.json()
    team_keys = {}
    for team in teams:
        team_keys[team["Name"]] = team["Key"]
    return team_keys

def find_match(date, team1_key, team2_key):
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    games = response.json()
    for game in games:
        if team1_key in (game["HomeTeam"], game["AwayTeam"]) and team2_key in (game["HomeTeam"], game["AwayTeam"]):
            return game
    return None

def resolve_market(game, team1_key, team2_key):
    if not game:
        return "p4"
    if game["Status"] == "Final":
        if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
            winner = game["HomeTeam"]
        else:
            winner = game["AwayTeam"]
        if winner == team1_key:
            return RESOLUTION_MAP[team1_key]
        else:
            return RESOLUTION_MAP[team2_key]
    elif game["Status"] in ["Canceled", "Postponed"]:
        return "p3"
    else:
        return "p4"

# Main execution
team_keys = get_team_keys()
team1_key = team_keys.get(TEAM1, TEAM1)
team2_key = team_keys.get(TEAM2, TEAM2)

game = find_match(DATE, team1_key, team2_key)
recommendation = resolve_market(game, team1_key, team2_key)
print("recommendation:", recommendation)