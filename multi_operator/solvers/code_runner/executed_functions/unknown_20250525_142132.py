import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
SPORTS_DATA_IO_MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
SPORTS_DATA_IO_NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
SPORTS_DATA_IO_NFL_API_KEY = os.getenv("SPORTS_DATA_IO_NFL_API_KEY")
SPORTS_DATA_IO_NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
SPORTS_DATA_IO_CFB_API_KEY = os.getenv("SPORTS_DATA_IO_CFB_API_KEY")
SPORTS_DATA_IO_CBB_API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")

# API endpoints
BINANCE_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
MLB_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json/Teams"
NBA_ENDPOINT = "https://api.sportsdata.io/v3/nba/scores/json/Teams"
NFL_ENDPOINT = "https://api.sportsdata.io/v3/nfl/scores/json/Teams"
NHL_ENDPOINT = "https://api.sportsdata.io/v3/nhl/scores/json/Teams"
CFB_ENDPOINT = "https://api.sportsdata.io/v3/cfb/scores/json/Teams"
CBB_ENDPOINT = "https://api.sportsdata.io/v3/cbb/scores/json/Teams"

# Headers for requests
HEADERS_MLB = {"Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_MLB_API_KEY}
HEADERS_NBA = {"Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_NBA_API_KEY}
HEADERS_NFL = {"Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_NFL_API_KEY}
HEADERS_NHL = {"Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_NHL_API_KEY}
HEADERS_CFB = {"Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_CFB_API_KEY}
HEADERS_CBB = {"Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_CBB_API_KEY}

def get_data(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def main():
    # Example usage of the MLB API
    mlb_teams = get_data(MLB_ENDPOINT, HEADERS_MLB)
    if mlb_teams:
        print("MLB Teams Data Fetched Successfully")
        for team in mlb_teams:
            print(team["Name"], team["City"])
    else:
        print("Failed to fetch MLB teams data")

if __name__ == "__main__":
    main()