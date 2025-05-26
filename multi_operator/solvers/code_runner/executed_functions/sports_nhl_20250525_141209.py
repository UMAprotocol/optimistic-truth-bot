import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nhl-proxy"

# Resolution map based on the ancillary data provided
RESOLUTION_MAP = {
    "DC": "p2",  # Delhi Capitals
    "PB": "p1",  # Punjab Kings
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Function to make API requests
def make_request(url, use_proxy=False):
    endpoint = PROXY_ENDPOINT if use_proxy else PRIMARY_ENDPOINT
    full_url = f"{endpoint}{url}"
    try:
        response = requests.get(full_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if use_proxy:
            print("Proxy failed, trying primary endpoint.")
            return make_request(url, use_proxy=False)
        else:
            print(f"HTTP Error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    return None

# Function to determine the outcome of the match
def determine_outcome(game_date, team1, team2):
    date_str = game_date.strftime("%Y-%m-%d")
    games = make_request(f"/scores/json/GamesByDate/{date_str}")
    if games:
        for game in games:
            if {game['HomeTeam'], game['AwayTeam']} == {team1, team2}:
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

# Main function to run the script
if __name__ == "__main__":
    game_date = datetime.strptime("2025-05-24 10:00", "%Y-%m-%d %H:%M")
    team1 = "PB"  # Punjab Kings
    team2 = "DC"  # Delhi Capitals
    result = determine_outcome(game_date, team1, team2)
    print("recommendation:", result)