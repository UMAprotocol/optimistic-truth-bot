#!/usr/bin/env python3
"""
MLB Game Result Resolver

Usage:
    python mlb_final_result.py --teamA "Detroit Tigers" --teamB "Chicago White Sox" --gameDate "2025-06-04"

Returns:
    "Winner: {team_name}" for a win
    "Result: 50-50" for canceled games
    "Status: PENDING" for unresolved games
"""

import os
import sys
import json
import time
import logging
import argparse
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(message)s", handlers=[logging.StreamHandler()]
)
log = logging.getLogger(__name__)

# MLB Team mapping data
MLB_TEAMS = {
    "Los Angeles Angels": {
        "code": "LAA",
        "abbreviation": "LAA",
        "name": "LA Angels",
        "full_name": "Los Angeles Angels",
    },
    "Arizona Diamondbacks": {
        "code": "ARI",
        "abbreviation": "ARI",
        "name": "Arizona",
        "full_name": "Arizona Diamondbacks",
    },
    "Baltimore Orioles": {
        "code": "BAL",
        "abbreviation": "BAL",
        "name": "Baltimore",
        "full_name": "Baltimore Orioles",
    },
    "Boston Red Sox": {
        "code": "BOS",
        "abbreviation": "BOS",
        "name": "Boston",
        "full_name": "Boston Red Sox",
    },
    "Chicago Cubs": {
        "code": "CHC",
        "abbreviation": "CHC",
        "name": "Chi Cubs",
        "full_name": "Chicago Cubs",
    },
    "Cincinnati Reds": {
        "code": "CIN",
        "abbreviation": "CIN",
        "name": "Cincinnati",
        "full_name": "Cincinnati Reds",
    },
    "Cleveland Indians": {
        "code": "CLE",
        "abbreviation": "CLE",
        "name": "Cleveland",
        "full_name": "Cleveland Indians",
    },
    "Colorado Rockies": {
        "code": "COL",
        "abbreviation": "COL",
        "name": "Colorado",
        "full_name": "Colorado Rockies",
    },
    "Detroit Tigers": {
        "code": "DET",
        "abbreviation": "DET",
        "name": "Detroit",
        "full_name": "Detroit Tigers",
    },
    "Houston Astros": {
        "code": "HOU",
        "abbreviation": "HOU",
        "name": "Houston",
        "full_name": "Houston Astros",
    },
    "Kansas City Royals": {
        "code": "KC",
        "abbreviation": "KC",
        "name": "Kansas City",
        "full_name": "Kansas City Royals",
    },
    "Los Angeles Dodgers": {
        "code": "LAD",
        "abbreviation": "LAD",
        "name": "LA Dodgers",
        "full_name": "Los Angeles Dodgers",
    },
    "Washington Nationals": {
        "code": "WSH",
        "abbreviation": "WSH",
        "name": "Washington",
        "full_name": "Washington Nationals",
    },
    "New York Mets": {
        "code": "NYM",
        "abbreviation": "NYM",
        "name": "NY Mets",
        "full_name": "New York Mets",
    },
    "Oakland Athletics": {
        "code": "OAK",
        "abbreviation": "OAK",
        "name": "Oakland",
        "full_name": "Oakland Athletics",
    },
    "Pittsburgh Pirates": {
        "code": "PIT",
        "abbreviation": "PIT",
        "name": "Pittsburgh",
        "full_name": "Pittsburgh Pirates",
    },
    "San Diego Padres": {
        "code": "SD",
        "abbreviation": "SD",
        "name": "San Diego",
        "full_name": "San Diego Padres",
    },
    "Seattle Mariners": {
        "code": "SEA",
        "abbreviation": "SEA",
        "name": "Seattle",
        "full_name": "Seattle Mariners",
    },
    "San Francisco Giants": {
        "code": "SF",
        "abbreviation": "SF",
        "name": "San Francisco",
        "full_name": "San Francisco Giants",
    },
    "St. Louis Cardinals": {
        "code": "STL",
        "abbreviation": "STL",
        "name": "St. Louis",
        "full_name": "St. Louis Cardinals",
    },
    "Tampa Bay Rays": {
        "code": "TB",
        "abbreviation": "TB",
        "name": "Tampa Bay",
        "full_name": "Tampa Bay Rays",
    },
    "Texas Rangers": {
        "code": "TEX",
        "abbreviation": "TEX",
        "name": "Texas",
        "full_name": "Texas Rangers",
    },
    "Toronto Blue Jays": {
        "code": "TOR",
        "abbreviation": "TOR",
        "name": "Toronto",
        "full_name": "Toronto Blue Jays",
    },
    "Minnesota Twins": {
        "code": "MIN",
        "abbreviation": "MIN",
        "name": "Minnesota",
        "full_name": "Minnesota Twins",
    },
    "Philadelphia Phillies": {
        "code": "PHI",
        "abbreviation": "PHI",
        "name": "Philadelphia",
        "full_name": "Philadelphia Phillies",
    },
    "Atlanta Braves": {
        "code": "ATL",
        "abbreviation": "ATL",
        "name": "Atlanta",
        "full_name": "Atlanta Braves",
    },
    "Chicago White Sox": {
        "code": "CHW",
        "abbreviation": "CHW",
        "name": "Chi White Sox",
        "full_name": "Chicago White Sox",
    },
    "Miami Marlins": {
        "code": "MIA",
        "abbreviation": "MIA",
        "name": "Miami",
        "full_name": "Miami Marlins",
    },
    "New York Yankees": {
        "code": "NYY",
        "abbreviation": "NYY",
        "name": "NY Yankees",
        "full_name": "New York Yankees",
    },
    "Milwaukee Brewers": {
        "code": "MIL",
        "abbreviation": "MIL",
        "name": "Milwaukee",
        "full_name": "Milwaukee Brewers",
    },
}

# Create reverse mappings
TEAM_CODE_TO_FULL = {
    team_data["code"]: full_name for full_name, team_data in MLB_TEAMS.items()
}
TEAM_NAME_TO_CODE = {
    full_name: team_data["code"] for full_name, team_data in MLB_TEAMS.items()
}
# Add alternative names
for full_name, team_data in MLB_TEAMS.items():
    TEAM_NAME_TO_CODE[team_data["name"]] = team_data["code"]
    TEAM_NAME_TO_CODE[team_data["abbreviation"]] = team_data["code"]


def get_team_code(team_name):
    """Convert team name to API code, trying various formats."""
    code = TEAM_NAME_TO_CODE.get(team_name)
    if not code:
        raise ValueError(f"Unknown team: {team_name}")
    return code


def get_team_full_name(team_code):
    """Convert team code to full name."""
    name = TEAM_CODE_TO_FULL.get(team_code)
    if not name:
        raise ValueError(f"Unknown team code: {team_code}")
    return name


def api_get(url, retries=3, backoff=1.5):
    """Make API request with retries and error handling."""
    headers = {"Ocp-Apim-Subscription-Key": os.getenv("SPORTS_DATA_IO_MLB_API_KEY")}

    for i in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if i == retries - 1:  # Last retry
                log.error(f"API request failed: {e}")
                return None
            wait = backoff * 2**i
            time.sleep(wait)
    return None


def find_game(date, team_a_code, team_b_code):
    """Find game between two teams on a specific date."""
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDateFinal/{formatted_date}"

    games = api_get(url)
    if not games:
        return None

    team_codes = {team_a_code, team_b_code}
    for game in games:
        game_teams = {game["HomeTeam"], game["AwayTeam"]}
        if game_teams == team_codes:
            return game

    return None


def determine_winner(game):
    """Determine the winner of a game based on its data."""
    if not game:
        return "Status: PENDING", "Game not found"

    if game["Status"] != "Final":
        if game["Status"] in ["Canceled", "Postponed"]:
            return "Result: 50-50", f"Game was {game['Status'].lower()}"
        return "Status: PENDING", f"Game status is {game['Status']}"

    away_team = get_team_full_name(game["AwayTeam"])
    home_team = get_team_full_name(game["HomeTeam"])
    away_runs = game["AwayTeamRuns"]
    home_runs = game["HomeTeamRuns"]

    if away_runs > home_runs:
        return f"Winner: {away_team}", f"{away_team} won {away_runs}-{home_runs}"
    elif home_runs > away_runs:
        return f"Winner: {home_team}", f"{home_team} won {home_runs}-{away_runs}"
    else:
        return "Status: PENDING", "Game tied or in extra innings"


def main():
    parser = argparse.ArgumentParser(description="Get MLB game result")
    parser.add_argument("--teamA", required=True, help="First team name")
    parser.add_argument("--teamB", required=True, help="Second team name")
    parser.add_argument("--gameDate", required=True, help="Game date (YYYY-MM-DD)")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed output"
    )
    args = parser.parse_args()

    # Set logging level based on verbose flag
    log.setLevel(logging.DEBUG if args.verbose else logging.INFO)

    # Load environment variables
    load_dotenv()
    if not os.getenv("SPORTS_DATA_IO_MLB_API_KEY"):
        log.error("Missing SPORTS_DATA_IO_MLB_API_KEY environment variable")
        sys.exit(1)

    try:
        # Convert team names to codes
        team_a_code = get_team_code(args.teamA)
        team_b_code = get_team_code(args.teamB)

        # Find and process the game
        game = find_game(args.gameDate, team_a_code, team_b_code)
        result, details = determine_winner(game)

        # Output
        if args.verbose:
            log.info(details)
        print(result)

    except ValueError as e:
        log.error(str(e))
        sys.exit(1)
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
