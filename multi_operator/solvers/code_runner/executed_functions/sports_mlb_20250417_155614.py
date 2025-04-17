import os
import requests
from dotenv import load_dotenv
import logging
import re

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

if not API_KEY:
    raise ValueError(
        "SPORTS_DATA_IO_MLB_API_KEY not found in environment variables. "
        "Please add it to your .env file."
    )

# Constants - RESOLUTION MAPPING using internal abbreviations
RESOLUTION_MAP = {
    "New York Mets": "p2",  # Mets win
    "Minnesota Twins": "p1",  # Twins win
    "50-50": "p3",  # Game canceled or unresolved
    "Too early to resolve": "p4",  # Not enough data
}

# Sensitive data patterns to mask in logs
SENSITIVE_PATTERNS = [
    re.compile(r"SPORTS_DATA_IO_MLB_API_KEY\s*=\s*['\"]?[\w-]+['\"]?", re.IGNORECASE),
    re.compile(r"api_key\s*=\s*['\"]?[\w-]+['\"]?", re.IGNORECASE),
    re.compile(r"key\s*=\s*['\"]?[\w-]+['\"]?", re.IGNORECASE),
    re.compile(r"Authorization\s*:\s*['\"]?[\w-]+['\"]?", re.IGNORECASE),
]

class SensitiveDataFilter(logging.Filter):
    def filter(self, record):
        original_msg = record.getMessage()
        masked_msg = original_msg
        for pattern in SENSITIVE_PATTERNS:
            masked_msg = pattern.sub("******", masked_msg)
        record.msg = masked_msg
        return True

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

console_handler.addFilter(SensitiveDataFilter())

logger.addHandler(console_handler)

def fetch_game_data(date):
    primary_url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={API_KEY}"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    headers = {"Ocp-Apim-Subscription-Key": API_KEY}

    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, headers=headers, timeout=10)
        if response.status_code != 200:
            raise Exception("Proxy failed, trying primary endpoint.")
        games = response.json()
    except Exception as e:
        logger.warning(f"Proxy failed with error: {e}, trying primary endpoint.")
        # Fallback to primary endpoint
        response = requests.get(primary_url, headers=headers, timeout=10)
        response.raise_for_status()
        games = response.json()

    return games

def determine_resolution(games):
    for game in games:
        if game['HomeTeam'] == "New York Mets" and game['AwayTeam'] == "Minnesota Twins":
            if game['Status'] == "Final":
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return RESOLUTION_MAP["New York Mets"]
                elif away_score > home_score:
                    return RESOLUTION_MAP["Minnesota Twins"]
            elif game['Status'] == "Canceled":
                return RESOLUTION_MAP["50-50"]
            elif game['Status'] in ["Scheduled", "InProgress"]:
                return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

def main():
    date = "2025-04-16"
    games = fetch_game_data(date)
    resolution = determine_resolution(games)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()