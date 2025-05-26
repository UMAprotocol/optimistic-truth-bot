import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Configuration for headers and API endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-nba-proxy"

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}/{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to resolve the market based on game outcome
def resolve_market(game_date, team1, team2):
    date_str = game_date.strftime("%Y-%m-%d")
    games_today = make_request(PROXY_ENDPOINT, f"GamesByDate/{date_str}")
    if not games_today:
        games_today = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{date_str}")
    
    if games_today:
        for game in games_today:
            if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
                if game["Status"] == "Final":
                    if game["HomeTeam"] == team1 and game["HomeTeamScore"] > game["AwayTeamScore"]:
                        return "recommendation: p1"
                    elif game["AwayTeam"] == team1 and game["AwayTeamScore"] > game["HomeTeamScore"]:
                        return "recommendation: p1"
                    elif game["HomeTeam"] == team2 and game["HomeTeamScore"] > game["AwayTeamScore"]:
                        return "recommendation: p2"
                    elif game["AwayTeam"] == team2 and game["AwayTeamScore"] > game["HomeTeamScore"]:
                        return "recommendation: p2"
                elif game["Status"] == "Canceled":
                    return "recommendation: p3"
                elif game["Status"] == "Postponed":
                    return "recommendation: p4"
    return "recommendation: p4"

# Main execution function
if __name__ == "__main__":
    game_date = datetime.strptime("2025-05-24 20:30", "%Y-%m-%d %H:%M")
    team1 = "MIN"  # Minnesota Timberwolves
    team2 = "OKC"  # Oklahoma City Thunder
    result = resolve_market(game_date, team1, team2)
    print(result)