import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Constants
DATE_LIMIT = datetime.strptime("2025-05-20 23:59", "%Y-%m-%d %H:%M")
TEAM1 = "EDM"  # Edmonton Oilers
TEAM2 = "LAK"  # Los Angeles Kings
RESOLUTION_MAP = {
    TEAM1: "p2",  # Oilers
    TEAM2: "p1",  # Kings
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Function to get data from API
def get_data(url, tag):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {tag}: {e}")
        return None

# Function to determine the outcome
def determine_outcome():
    current_date = datetime.now()
    if current_date > DATE_LIMIT:
        return RESOLUTION_MAP["50-50"]

    # Fetch playoff data
    season = current_date.year
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/PlayoffTeams/{season}"
    playoff_teams = get_data(url, "PlayoffTeams")

    if playoff_teams is None:
        return RESOLUTION_MAP["Too early to resolve"]

    # Check if teams have advanced
    teams_advanced = {team["Key"]: team["Advanced"] for team in playoff_teams if team["Key"] in (TEAM1, TEAM2)}
    if TEAM1 in teams_advanced and teams_advanced[TEAM1]:
        return RESOLUTION_MAP[TEAM1]
    elif TEAM2 in teams_advanced and teams_advanced[TEAM2]:
        return RESOLUTION_MAP[TEAM2]

    return RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    result = determine_outcome()
    print(f"recommendation: {result}")