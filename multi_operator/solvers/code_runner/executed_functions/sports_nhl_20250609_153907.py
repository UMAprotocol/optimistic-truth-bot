import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not NHL_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration for API access
HEADERS = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nhl-proxy"

# Resolution map based on the outcome
RESOLUTION_MAP = {
    "Yes": "p2",  # Connor McDavid scores 1+ goals
    "No": "p1"    # Connor McDavid does not score
}

# Function to fetch game data
def fetch_game_data(date, team1, team2):
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if team1 in game['Teams'] and team2 in game['Teams']:
                return game
    except requests.exceptions.RequestException as e:
        print(f"Primary endpoint failed, trying proxy. Error: {e}")
        try:
            proxy_url = f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{date}"
            response = requests.get(proxy_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            games = response.json()
            for game in games:
                if team1 in game['Teams'] and team2 in game['Teams']:
                    return game
        except requests.exceptions.RequestException as e:
            print(f"Both primary and proxy endpoints failed. Error: {e}")
    return None

# Function to check if Connor McDavid scored
def check_mcdavid_score(game_id):
    url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        stats = response.json()
        for stat in stats:
            if stat['PlayerID'] == 8478402:  # Connor McDavid's PlayerID
                return "Yes" if stat['Goals'] >= 1 else "No"
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch player stats. Error: {e}")
    return "No"

# Main function to resolve the market
def resolve_market():
    game_date = "2025-05-29"
    team1 = "EDM"
    team2 = "DAL"
    game = fetch_game_data(game_date, team1, team2)
    if game:
        result = check_mcdavid_score(game['GameID'])
        recommendation = RESOLUTION_MAP[result]
        print(f"recommendation: {recommendation}")
    else:
        print("recommendation: p1")  # Resolve to "No" if game data is not found or McDavid did not play

if __name__ == "__main__":
    resolve_market()