import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
SPORTS_DATA_IO_MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# API endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_MLB_API_KEY}

def get_data_from_api(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error accessing API: {e}")
        return None

def resolve_market():
    # Example data for demonstration
    date = "2025-04-23"
    team1 = "Texas Rangers"
    team2 = "Oakland Athletics"

    # Construct the API URL
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"

    # Attempt to fetch data from the proxy endpoint first
    games = get_data_from_api(PROXY_ENDPOINT)
    if not games:
        # Fallback to the primary endpoint if proxy fails
        games = get_data_from_api(url)

    if not games:
        return "recommendation: p4"  # Unable to retrieve data

    # Process the games data
    for game in games:
        if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or \
           (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
            if game['Status'] == 'Final':
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    winner = game['HomeTeam']
                else:
                    winner = game['AwayTeam']

                if winner == team1:
                    return "recommendation: p1"
                else:
                    return "recommendation: p2"
            elif game['Status'] in ['Canceled', 'Postponed']:
                return "recommendation: p3"
            else:
                return "recommendation: p4"

    return "recommendation: p4"  # No relevant game found or game not final

if __name__ == "__main__":
    result = resolve_market()
    print(result)