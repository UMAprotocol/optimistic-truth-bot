import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nhl-proxy"

# Resolution map based on the ancillary data provided
RESOLUTION_MAP = {
    "Alcaraz": "p2",  # Carlos Alcaraz
    "Fokina": "p1",   # Alejandro Davidovich Fokina
    "50-50": "p3"
}

# Function to make API requests
def make_request(endpoint, path):
    url = f"{endpoint}{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to check the match result
def check_match_result():
    # Define the match date and players
    match_date = "2025-06-17"
    player1 = "Alcaraz"
    player2 = "Fokina"

    # Format the date for the API endpoint
    formatted_date = datetime.strptime(match_date, "%Y-%m-%d").strftime("%Y-%m-%d")

    # Try proxy endpoint first
    games = make_request(PROXY_ENDPOINT, f"/scores/json/GamesByDate/{formatted_date}")
    if not games:
        # Fallback to primary endpoint if proxy fails
        games = make_request(PRIMARY_ENDPOINT, f"/scores/json/GamesByDate/{formatted_date}")

    if games:
        for game in games:
            if game['Status'] == "Final":
                if game['HomeTeam'] == player1 and game['AwayTeam'] == player2:
                    if game['HomeTeamScore'] > game['AwayTeamScore']:
                        return RESOLUTION_MAP[player1]
                    elif game['HomeTeamScore'] < game['AwayTeamScore']:
                        return RESOLUTION_MAP[player2]
                elif game['HomeTeam'] == player2 and game['AwayTeam'] == player1:
                    if game['HomeTeamScore'] > game['AwayTeamScore']:
                        return RESOLUTION_MAP[player2]
                    elif game['HomeTeamScore'] < game['AwayTeamScore']:
                        return RESOLUTION_MAP[player1]
            elif game['Status'] in ["Canceled", "Postponed"]:
                return RESOLUTION_MAP["50-50"]
    return RESOLUTION_MAP["50-50"]

# Main function to run the program
if __name__ == "__main__":
    result = check_match_result()
    print(f"recommendation: {result}")