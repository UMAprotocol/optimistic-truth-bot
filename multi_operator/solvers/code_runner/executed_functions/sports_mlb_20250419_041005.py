import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nba-proxy"
TEAM = "Dallas Mavericks"
SEASON = "2024REG"  # Regular season for 2024-2025

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_nba_standings():
    """
    Fetches NBA standings and checks if the Dallas Mavericks have made the playoffs.
    """
    headers = {'Ocp-Apim-Subscription-Key': NBA_API_KEY}
    url = f"{PROXY_ENDPOINT}/scores/json/Standings/{SEASON}"
    primary_url = f"{PRIMARY_ENDPOINT}/scores/json/Standings/{SEASON}"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        logging.warning("Proxy failed, falling back to primary endpoint.")
        response = requests.get(primary_url, headers=headers, timeout=10)
        response.raise_for_status()

    standings = response.json()
    return standings

def check_playoffs(standings):
    """
    Determines if the Dallas Mavericks are in the top 16 teams of the standings.
    """
    playoff_teams = [team for team in standings if team['PlayoffRank'] <= 16]
    mavs_in_playoffs = any(team['Team'] == TEAM for team in playoff_teams)
    return mavs_in_playoffs

def main():
    """
    Main function to determine if the Dallas Mavericks make the NBA Playoffs.
    """
    try:
        standings = fetch_nba_standings()
        if check_playoffs(standings):
            print("recommendation: p2")  # Mavericks make the playoffs
        else:
            print("recommendation: p1")  # Mavericks do not make the playoffs
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        print("recommendation: p3")  # Unable to determine

if __name__ == "__main__":
    main()