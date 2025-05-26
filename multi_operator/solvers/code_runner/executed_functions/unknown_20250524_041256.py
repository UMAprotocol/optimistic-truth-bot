import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
API_KEY = os.getenv("SPORTS_DATA_IO_NFL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NFL_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nfl/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nfl-proxy"

# Function to make API requests
def make_request(endpoint, path):
    url = f"{endpoint}/{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to check for the term "Baby" in NFL transcripts
def check_for_term(start_date, end_date):
    current_date = start_date
    while current_date <= end_date:
        games = make_request(PROXY_ENDPOINT, f"GamesByDate/{current_date.strftime('%Y-%m-%d')}")
        if not games:
            games = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{current_date.strftime('%Y-%m-%d')}")
        if games:
            for game in games:
                game_id = game.get("GameId")
                transcripts = make_request(PROXY_ENDPOINT, f"GameTranscripts/{game_id}")
                if not transcripts:
                    transcripts = make_request(PRIMARY_ENDPOINT, f"GameTranscripts/{game_id}")
                if transcripts:
                    for transcript in transcripts:
                        if "baby" in transcript.get("Text", "").lower():
                            return "Yes"
        current_date += timedelta(days=1)
    return "No"

# Main function to run the script
if __name__ == "__main__":
    start_date = datetime(2025, 5, 17, 12, 0)
    end_date = datetime(2025, 5, 23, 23, 59)
    result = check_for_term(start_date, end_date)
    print(f"recommendation: {'p2' if result == 'Yes' else 'p1'}")