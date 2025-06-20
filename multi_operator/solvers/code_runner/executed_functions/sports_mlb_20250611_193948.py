import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/mlb"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "Reds": "p2",
    "Guardians": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_game_data(date, proxy_first=True):
    url = f"{PROXY_ENDPOINT if proxy_first else PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        return games, True
    except Exception as e:
        if proxy_first:
            # Fallback to primary endpoint if proxy fails
            return get_game_data(date, proxy_first=False)
        else:
            print(f"Failed to retrieve data from both endpoints: {str(e)}")
            return None, False

def analyze_game(games):
    for game in games:
        if game['HomeTeam'] == 'CIN' and game['AwayTeam'] == 'CLE':
            if game['Status'] == 'Final':
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return RESOLUTION_MAP['Reds']
                elif away_score > home_score:
                    return RESOLUTION_MAP['Guardians']
            elif game['Status'] == 'Canceled':
                return RESOLUTION_MAP['50-50']
            elif game['Status'] == 'Postponed':
                return RESOLUTION_MAP['Too early to resolve']
    return RESOLUTION_MAP['Too early to resolve']

def main():
    today_date = datetime.now().strftime("%Y-%m-%d")
    games, success = get_game_data(today_date)
    if success and games:
        result = analyze_game(games)
        print(f"recommendation: {result}")
    else:
        print("recommendation: p4")

if __name__ == "__main__":
    main()