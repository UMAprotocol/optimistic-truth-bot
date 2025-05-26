import os
import requests
from datetime import datetime, timedelta
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
MLB_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"

# Headers for Sports Data IO APIs
HEADERS = {
    "Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_MLB_API_KEY
}

# Function to make API requests
def make_request(url, headers=None, fallback_url=None):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if fallback_url:
            try:
                response = requests.get(fallback_url, headers=headers, timeout=10)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException:
                return None
        return None

# Example function to get MLB teams
def get_mlb_teams():
    url = f"{MLB_ENDPOINT}/Teams"
    teams = make_request(url, HEADERS, fallback_url=f"{url}?useFallback=true")
    if teams:
        return {team['Name']: team['Key'] for team in teams}
    return {}

# Main function to execute the script logic
def main():
    teams = get_mlb_teams()
    if teams:
        print("Teams loaded successfully.")
        for name, key in teams.items():
            print(f"{name}: {key}")
    else:
        print("Failed to load teams.")

if __name__ == "__main__":
    main()