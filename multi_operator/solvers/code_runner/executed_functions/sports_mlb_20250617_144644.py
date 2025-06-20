import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for headers and API endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Constants for the event
EVENT_DATE = "2025-06-17"
TEAM1 = "Ugo Humbert"
TEAM2 = "Denis Shapovalov"
TOURNAMENT = "Terra Wortmann Open"
MATCH_STATUS_FINAL = "Final"

# Function to fetch data from API
def fetch_data(date):
    url = f"{PRIMARY_ENDPOINT}{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        try:
            response = requests.get(PROXY_ENDPOINT, headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
            return None

# Function to determine the outcome of the match
def determine_outcome(data, player1, player2):
    for game in data:
        if game['Tournament'] == TOURNAMENT and {player1, player2} == {game['HomePlayer'], game['AwayPlayer']}:
            if game['Status'] == MATCH_STATUS_FINAL:
                if game['Winner'] == player1:
                    return "p1"
                elif game['Winner'] == player2:
                    return "p2"
            else:
                return "p3"  # Match not final, canceled, or postponed
    return "p4"  # No data found or match not yet played

# Main execution function
def main():
    date_str = datetime.strptime(EVENT_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    data = fetch_data(date_str)
    if data:
        result = determine_outcome(data, TEAM1, TEAM2)
        print(f"recommendation: {result}")
    else:
        print("recommendation: p4")  # Unable to fetch data

if __name__ == "__main__":
    main()