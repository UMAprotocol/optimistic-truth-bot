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
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy/GamesByDate/"

# Date and teams for the query
DATE = "2025-06-12"
TEAM1 = "Perricard"  # Giovanni Mpetshi Perricard
TEAM2 = "Aliassime"  # Felix Auger-Aliassime

# Resolution map
RESOLUTION_MAP = {
    TEAM1: "p2",
    TEAM2: "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def fetch_data(date):
    """ Fetch data from the API, try proxy first then primary endpoint """
    try:
        response = requests.get(PROXY_ENDPOINT + date, headers=HEADERS, timeout=10)
        if not response.ok:
            raise Exception("Proxy failed")
        return response.json()
    except Exception as e:
        print(f"Proxy failed with error {e}, trying primary endpoint.")
        response = requests.get(PRIMARY_ENDPOINT + date, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()

def analyze_match(data, team1, team2):
    """ Analyze the match data to determine the outcome """
    for game in data:
        if team1 in game['HomeTeamName'] or team1 in game['AwayTeamName']:
            if team2 in game['HomeTeamName'] or team2 in game['AwayTeamName']:
                if game['Status'] == "Final":
                    if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                        winner = game['HomeTeamName']
                    else:
                        winner = game['AwayTeamName']
                    return RESOLUTION_MAP.get(winner, "p4")
                elif game['Status'] in ["Canceled", "Postponed"]:
                    return "p3"
                else:
                    return "p4"
    return "p4"

def main():
    """ Main function to handle the market resolution logic """
    try:
        games_data = fetch_data(DATE)
        recommendation = analyze_match(games_data, TEAM1, TEAM2)
        print(f"recommendation: {recommendation}")
    except Exception as e:
        print(f"An error occurred: {e}")
        print("recommendation: p4")

if __name__ == "__main__":
    main()