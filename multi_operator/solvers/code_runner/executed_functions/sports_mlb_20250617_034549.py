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
NBA_API_URL = "https://api.sportsdata.io/v3/nba/stats/json/PlayerGameStatsByDate"
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
FINAL_DATE = datetime(2025, 7, 22, 23, 59)  # July 22, 2025, 11:59 PM ET

# Helper functions
def get_player_stats(date):
    formatted_date = date.strftime("%Y-%m-%d")
    response = requests.get(f"{NBA_API_URL}/{formatted_date}", headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

def check_high_scores(stats):
    for stat in stats:
        if stat['Points'] > 39.5:
            return True
    return False

def resolve_market():
    today = datetime.now()
    if today > FINAL_DATE:
        return "recommendation: p3"  # Market resolves 50-50 if beyond final date

    start_date = datetime(2025, 6, 1)  # Assuming NBA Finals start in June
    while start_date <= today:
        try:
            daily_stats = get_player_stats(start_date)
            if check_high_scores(daily_stats):
                return "recommendation: p2"  # Yes, a player scored 40+ points
        except Exception as e:
            print(f"Error fetching data for {start_date}: {e}")
        start_date += timedelta(days=1)

    return "recommendation: p4"  # Too early to resolve if series is ongoing

# Main execution
if __name__ == "__main__":
    result = resolve_market()
    print(result)