import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API configuration
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Game details
GAME_DATE = "2025-05-24"
HOME_TEAM = "Toronto Blue Jays"
AWAY_TEAM = "Tampa Bay Rays"

# Resolution map
RESOLUTION_MAP = {
    "Blue Jays": "p2",  # Home team wins
    "Rays": "p1",       # Away team wins
    "50-50": "p3",      # Game canceled or postponed without resolution
    "Too early to resolve": "p4"  # Not enough data or game not completed
}

def get_games_by_date(date):
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        # Fallback to proxy
        try:
            proxy_url = f"{PROXY_ENDPOINT}/mlb/GamesByDate/{date}"
            response = requests.get(proxy_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
            return None

def resolve_market(games):
    for game in games:
        if game['HomeTeam'] == HOME_TEAM and game['AwayTeam'] == AWAY_TEAM:
            if game['Status'] == 'Final':
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return RESOLUTION_MAP[HOME_TEAM.split()[-1]]
                elif away_score > home_score:
                    return RESOLUTION_MAP[AWAY_TEAM.split()[-1]]
            elif game['Status'] == 'Canceled':
                return RESOLUTION_MAP["50-50"]
            elif game['Status'] == 'Postponed':
                # Check if the game is rescheduled within the season
                new_date = game.get('RescheduledDate')
                if new_date and datetime.strptime(new_date, "%Y-%m-%dT%H:%M:%S").date() <= datetime.now().date():
                    return resolve_market(get_games_by_date(new_date.split('T')[0]))
                else:
                    return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    games = get_games_by_date(GAME_DATE)
    if games:
        recommendation = resolve_market(games)
    else:
        recommendation = RESOLUTION_MAP["Too early to resolve"]
    print(f"recommendation: {recommendation}")