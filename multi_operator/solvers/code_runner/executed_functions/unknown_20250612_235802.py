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

# Function to make HTTP GET requests
def get_data(url, use_proxy=False):
    endpoint = PROXY_ENDPOINT if use_proxy else PRIMARY_ENDPOINT
    full_url = f"{endpoint}{url}"
    try:
        response = requests.get(full_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if use_proxy:
            print("Proxy failed, trying primary endpoint.")
            return get_data(url, use_proxy=False)
        else:
            print(f"HTTP Error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    return None

# Function to find the game and determine the outcome
def resolve_market():
    date_of_game = "2025-06-12"
    team1 = "G2"
    team2 = "paiN"
    games = get_data(f"/scores/json/GamesByDate/{date_of_game}", use_proxy=True)
    
    if games:
        for game in games:
            if team1 in game['HomeTeamName'] and team2 in game['AwayTeamName']:
                if game['Status'] == "Final":
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    if home_score > away_score:
                        return "recommendation: p1"  # G2 wins
                    elif away_score > home_score:
                        return "recommendation: p2"  # paiN wins
                elif game['Status'] in ["Canceled", "Postponed"]:
                    return "recommendation: p3"  # 50-50
    return "recommendation: p3"  # Default to 50-50 if no conclusive result

# Main execution
if __name__ == "__main__":
    result = resolve_market()
    print(result)