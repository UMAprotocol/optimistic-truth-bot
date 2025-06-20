import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Constants
NBA_FINALS_END_DATE = datetime(2025, 7, 22, 23, 59)  # July 22, 2025, 11:59 PM ET
TEAMS = ["Oklahoma City Thunder", "Indiana Pacers"]
URL = "https://api.sportsdata.io/v3/nba/stats/json/PlayerGameStatsByDate/{date}"

# Headers for API request
HEADERS = {
    "Ocp-Apim-Subscription-Key": API_KEY
}

def fetch_data(date):
    formatted_date = date.strftime("%Y-%m-%d")
    response = requests.get(URL.format(date=formatted_date), headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def check_player_scores(data):
    for game in data:
        if game['Team'] in TEAMS and game['Points'] > 39.5:
            return True
    return False

def resolve_market():
    current_date = datetime.now()
    if current_date > NBA_FINALS_END_DATE:
        return "recommendation: p3"  # Market resolves 50-50 if beyond the final date

    start_date = datetime(2025, 6, 1)  # Assuming NBA Finals start in June
    while start_date <= current_date:
        game_data = fetch_data(start_date)
        if game_data and check_player_scores(game_data):
            return "recommendation: p2"  # Yes, a player scored more than 39.5 points
        start_date += timedelta(days=1)

    return "recommendation: p4"  # Too early to resolve or no data available

if __name__ == "__main__":
    result = resolve_market()
    print(result)