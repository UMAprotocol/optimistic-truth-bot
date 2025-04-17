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
    "New York Mets": "p2",
    "Minnesota Twins": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4",
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
    proxy_url = f"https://minimal-ubuntu-production.up.railway.app/sportsdata-proxy/mlb/GamesByDate/{date}?key={API_KEY}"
    
    try:
        response = requests.get(proxy_url, timeout=10)
        response.raise_for_status()
        games = response.json()
    except requests.exceptions.RequestException:
        logger.warning("Proxy failed, falling back to primary endpoint.")
        try:
            response = requests.get(primary_url, timeout=10)
            response.raise_for_status()
            games = response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Primary request failed: {e}")
            return None

    for game in games:
        if game['HomeTeam'] == 'NYM' and game['AwayTeam'] == 'MIN':
            return game
    return None

def determine_resolution(game):
    if not game:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    status = game.get("Status")
    if status == "Final":
        home_score = game.get("HomeTeamRuns")
        away_score = game.get("AwayTeamRuns")
        if home_score > away_score:
            return "recommendation: " + RESOLUTION_MAP["New York Mets"]
        else:
            return "recommendation: " + RESOLUTION_MAP["Minnesota Twins"]
    elif status == "Postponed":
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    elif status == "Canceled":
        return "recommendation: " + RESOLUTION_MAP["50-50"]

    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

def main():
    date = "2025-04-16"
    game = fetch_game_data(date)
    resolution = determine_resolution(game)
    print(resolution)

if __name__ == "__main__":
    main()