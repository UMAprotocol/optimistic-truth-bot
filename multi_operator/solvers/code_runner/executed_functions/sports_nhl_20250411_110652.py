import os
import requests
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

if not API_KEY:
    raise ValueError(
        "SPORTS_DATA_IO_NHL_API_KEY not found in environment variables. "
        "Please add it to your .env file."
    )

# Mapping of internal team abbreviations to API team keys
TEAM_ABBREVIATION_MAP = {
    "VGK": "VEG",  # Vegas Golden Knights
    "SEA": "SEA",  # Seattle Kraken
    # Add other teams as needed
}

# Constants - RESOLUTION MAPPING using internal abbreviations
RESOLUTION_MAP = {
    "VGK": "p1",  # Golden Knights
    "SEA": "p2",  # Kraken
    "50-50": "p3",
    "Too early to resolve": "p4",
}

def fetch_game_data(date, team1, team2):
    url = f"https://api.sportsdata.io/v3/nhl/stats/json/BoxScoresFinal/{date}?key={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        games = response.json()

        # Map internal abbreviations to API abbreviations
        team1_api = TEAM_ABBREVIATION_MAP.get(team1, team1)
        team2_api = TEAM_ABBREVIATION_MAP.get(team2, team2)

        for game_data in games:
            game_info = game_data.get("Game", {})
            home_team = game_info.get("HomeTeam")
            away_team = game_info.get("AwayTeam")

            logging.debug(f"Checking game: {home_team} vs {away_team}")

            if {home_team, away_team} == {team1_api, team2_api}:
                game_data["team1"] = team1
                game_data["team2"] = team2
                return game_data

        logging.warning(f"No matching game found for teams: {team1} and {team2}")
        return None

    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
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

    team1 = game.get("team1")
    team2 = game.get("team2")

    logging.debug(f"Game status: {status}")
    logging.debug(f"Scores - Home: {home_score}, Away: {away_score}")

    if status in ["Scheduled", "Delayed", "InProgress", "Suspended"]:
        return RESOLUTION_MAP["Too early to resolve"]
    elif status in ["Postponed", "Canceled"]:
        return RESOLUTION_MAP["50-50"]
    elif status in ["Final", "F/OT", "F/SO"]:
        if home_score == away_score:
            return RESOLUTION_MAP["50-50"]
        winning_team_api = home_team if home_score > away_score else away_team
        # Map API abbreviation back to internal abbreviation
        winning_team_internal = next(
            (k for k, v in TEAM_ABBREVIATION_MAP.items() if v == winning_team_api),
            winning_team_api
        )
        return RESOLUTION_MAP.get(winning_team_internal, RESOLUTION_MAP["50-50"])

    return RESOLUTION_MAP["Too early to resolve"]

def main():
    date = "2025-04-10"
    team1 = "VGK"
    team2 = "SEA"

    game = fetch_game_data(date, team1, team2)
    resolution = determine_resolution(game)

    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()