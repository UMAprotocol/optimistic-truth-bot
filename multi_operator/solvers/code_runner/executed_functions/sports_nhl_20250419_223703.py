import os
import requests
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()
SPORTS_DATA_IO_NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants
RESOLUTION_MAP = {
    "LAC": "p2",  # LA Clippers
    "DEN": "p1",  # Denver Nuggets
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# API Endpoints
NBA_PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba/scores/json/GamesByDate"
NBA_PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nba-proxy"

def fetch_nba_game_data(date):
    headers = {"Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_NBA_API_KEY}
    url = f"{NBA_PRIMARY_ENDPOINT}/{date}"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        # Fallback to proxy endpoint
        try:
            response = requests.get(NBA_PROXY_ENDPOINT, params={"date": date}, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch data from both primary and proxy endpoints: {e}")
            return None

def resolve_market(games):
    for game in games:
        if game['HomeTeam'] == "LAC" or game['AwayTeam'] == "LAC":
            if game['HomeTeam'] == "DEN" or game['AwayTeam'] == "DEN":
                if game['Status'] == "Final":
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    if home_score > away_score:
                        winner = game['HomeTeam']
                    else:
                        winner = game['AwayTeam']
                    return RESOLUTION_MAP.get(winner, "p4")
                elif game['Status'] == "Canceled":
                    return RESOLUTION_MAP["50-50"]
                elif game['Status'] == "Postponed":
                    return "p4"  # Market remains open
                else:
                    return "p4"  # Game not completed yet
    return "p4"  # No relevant game found

def main():
    today_date = datetime.utcnow().strftime("%Y-%m-%d")
    games = fetch_nba_game_data(today_date)
    if games:
        recommendation = resolve_market(games)
    else:
        recommendation = "p4"  # Unable to fetch data or no games scheduled
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()