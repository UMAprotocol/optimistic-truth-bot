import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_CBB_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/cbb"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/cbb-proxy"

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return None

# Function to resolve the market based on the match result
def resolve_market(date, team1, team2):
    # Format the date for the API request
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    path = f"/scores/json/GamesByDate/{formatted_date}"

    # Try proxy endpoint first
    games = make_request(PROXY_ENDPOINT, path)
    if games is None:
        # Fallback to primary endpoint
        games = make_request(PRIMARY_ENDPOINT, path)
        if games is None:
            return "recommendation: p3"  # Unable to retrieve data, resolve as unknown/50-50

    # Search for the specific game
    for game in games:
        if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or \
           (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
            if game['Status'] == "Final":
                if game['HomeTeamScore'] > game['AwayTeamScore']:
                    winner = game['HomeTeam']
                else:
                    winner = game['AwayTeam']
                
                if winner == team1:
                    return "recommendation: p1"
                else:
                    return "recommendation: p2"
            else:
                return "recommendation: p3"  # Game not final, resolve as unknown/50-50

    # If no game found or other conditions met
    return "recommendation: p3"

# Main execution function
if __name__ == "__main__":
    # Specific game details
    date = "2025-06-12"
    team1 = "Vitality"
    team2 = "Legacy"

    # Resolve the market based on the game outcome
    result = resolve_market(date, team1, team2)
    print(result)