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
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/cbb"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/cbb-proxy"

# Function to make API requests
def make_request(url, use_proxy=False):
    endpoint = PROXY_ENDPOINT if use_proxy else PRIMARY_ENDPOINT
    full_url = f"{endpoint}{url}"
    try:
        response = requests.get(full_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if use_proxy:
            print("Proxy failed, trying primary endpoint.")
            return make_request(url, use_proxy=False)
        else:
            print(f"Failed to retrieve data: {e}")
            return None

# Function to determine the outcome of the match
def resolve_match():
    # Match details
    event_date = "2025-06-03"
    team1 = "B8"
    team2 = "Imperial"
    
    # Format date for API request
    formatted_date = datetime.strptime(event_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    
    # API request to get the match result
    match_data = make_request(f"/scores/json/GamesByDate/{formatted_date}", use_proxy=True)
    
    if match_data is None:
        return "recommendation: p3"  # Unknown or API failure, resolve as 50-50
    
    # Find the specific match
    for match in match_data:
        if match['HomeTeam'] == team1 and match['AwayTeam'] == team2 or \
           match['HomeTeam'] == team2 and match['AwayTeam'] == team1:
            if match['Status'] == "Final":
                home_score = match['HomeTeamScore']
                away_score = match['AwayTeamScore']
                if home_score > away_score:
                    winner = match['HomeTeam']
                else:
                    winner = match['AwayTeam']
                
                if winner == team1:
                    return "recommendation: p2"  # B8 wins
                else:
                    return "recommendation: p1"  # Imperial wins
            else:
                return "recommendation: p3"  # Match not final, resolve as 50-50

    return "recommendation: p3"  # No match found or other conditions, resolve as 50-50

# Main execution
if __name__ == "__main__":
    result = resolve_match()
    print(result)