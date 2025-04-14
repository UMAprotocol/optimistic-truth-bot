import os
import requests
from dotenv import load_dotenv
import logging
import re

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

if not API_KEY:
    raise ValueError(
        "SPORTS_DATA_IO_NHL_API_KEY not found in environment variables. "
        "Please add it to your .env file."
    )

# Constants - RESOLUTION MAPPING using internal abbreviations
RESOLUTION_MAP = {
    "Golden Knights": "p1",  # Golden Knights
    "Kraken": "p2",  # Kraken
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Sensitive data patterns to mask in logs
SENSITIVE_PATTERNS = [
    re.compile(r"SPORTS_DATA_IO_NHL_API_KEY\s*=\s*['\"]?[\w-]+['\"]?", re.IGNORECASE),
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

def fetch_game_data(date, team1_api, team2_api):
    url = f"https://api.sportsdata.io/v3/nhl/stats/json/BoxScoresFinal/{date}?key={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        games = response.json()

        for game_data in games:
            game_info = game_data.get("Game", {})
            home_team = game_info.get("HomeTeam")
            away_team = game_info.get("AwayTeam")

            logger.debug(f"Checking game: {home_team} vs {away_team}")

            if {home_team, away_team} == {team1_api, team2_api}:
                return game_data

        logger.warning(f"No matching game found for teams: {team1_api} and {team2_api}")
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return None

def determine_resolution(game):
    if not game:
        return RESOLUTION_MAP["Too early to resolve"]

    game_info = game.get("Game", {})
    status = game_info.get("Status")
    home_score = game_info.get("HomeTeamScore")
    away_score = game_info.get("AwayTeamScore")
    home_team = game_info.get("HomeTeam")
    away_team = game_info.get("AwayTeam")

    logger.debug(f"Game status: {status}")
    logger.debug(f"Scores - Home: {home_score}, Away: {away_score}")

    if status in ["Scheduled", "Delayed", "InProgress", "Suspended"]:
        return RESOLUTION_MAP["Too early to resolve"]
    elif status in ["Postponed", "Canceled"]:
        return RESOLUTION_MAP["50-50"]
    elif status in ["Final", "F/OT", "F/SO"]:
        if home_score == away_score:
            return RESOLUTION_MAP["50-50"]
        winning_team = home_team if home_score > away_score else away_team
        if winning_team == "VGK":
            return RESOLUTION_MAP["Golden Knights"]
        elif winning_team == "SEA":
            return RESOLUTION_MAP["Kraken"]
        else:
            return RESOLUTION_MAP["50-50"]

    return RESOLUTION_MAP["Too early to resolve"]

def main():
    date = "2025-04-10"
    team1_api = "VGK"  # Vegas Golden Knights
    team2_api = "SEA"  # Seattle Kraken

    game = fetch_game_data(date, team1_api, team2_api)
    resolution = determine_resolution(game)

    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()