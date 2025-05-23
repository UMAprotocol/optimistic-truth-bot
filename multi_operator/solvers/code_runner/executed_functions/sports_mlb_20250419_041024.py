import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants
RESOLUTION_MAP = {
    "Yes": "p2",
    "No": "p1",
    "Unknown": "p3"
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_nba_playoff_status():
    """
    Fetches the current playoff status of the Dallas Mavericks from the NBA API.
    """
    primary_url = "https://api.sportsdata.io/v3/nba/scores/json/Standings/2025"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nba-proxy"
    headers = {"Ocp-Apim-Subscription-Key": API_KEY}

    try:
        # Try fetching via proxy first
        response = requests.get(proxy_url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        logging.warning(f"Proxy failed with error: {e}, trying primary endpoint.")
        try:
            # Fallback to primary endpoint if proxy fails
            response = requests.get(primary_url, headers=headers, timeout=10)
            response.raise_for_status()
        except Exception as e:
            logging.error(f"Primary endpoint failed with error: {e}")
            return None

    data = response.json()
    # Check if Dallas Mavericks are in the top 16 teams
    for team_data in data:
        if team_data["Team"] == "DAL" and team_data["PlayoffRank"] <= 16:
            return "Yes"
    return "No"

def main():
    """
    Main function to determine if the Dallas Mavericks made the NBA Playoffs.
    """
    playoff_status = fetch_nba_playoff_status()
    if playoff_status:
        recommendation = RESOLUTION_MAP.get(playoff_status, "p3")
    else:
        recommendation = "p3"  # Unknown or API failure
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()