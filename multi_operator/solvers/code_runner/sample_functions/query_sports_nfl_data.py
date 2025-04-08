#!/usr/bin/env python3
"""
Sample script to query NFL data from Sports Data IO API.
This is a template that can be used as a reference for generating
code to answer NFL-related queries.
"""

import os
import re
import sys
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API key from environment
API_KEY = os.getenv("SPORTS_DATA_IO_NFL_API_KEY")

if not API_KEY:
    print("Error: SPORTS_DATA_IO_NFL_API_KEY not found in environment variables.")
    print("Please set this in your .env file or in your environment.")
    sys.exit(1)

# Constants and configuration
BASE_URL = "https://api.sportsdata.io/v3/nfl"
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Define resolution mapping for outcomes
RESOLUTION_MAP = {
    "Team A": "p1",  # Home team wins
    "Team B": "p2",  # Away team wins
    "Tie": "p3",  # Game ended in a tie
    "Not played": "p4",  # Game hasn't been played or enough data isn't available
}


def fetch_game_by_date(date_str):
    """
    Fetch NFL games for a specific date.

    Args:
        date_str: Date string in YYYY-MM-DD format

    Returns:
        JSON response with games data
    """
    endpoint = f"/scores/json/ScoresByDate/{date_str}"
    url = BASE_URL + endpoint

    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()  # Raise exception for 4XX/5XX status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching game data: {e}")
        return None


def fetch_standings(season_year="2023"):
    """
    Fetch NFL standings for a specific season.

    Args:
        season_year: The year of the season

    Returns:
        JSON response with standings data
    """
    endpoint = f"/scores/json/Standings/{season_year}"
    url = BASE_URL + endpoint

    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching standings data: {e}")
        return None


def extract_team_names_from_question(question):
    """
    Extract team names from the question.

    Args:
        question: The query string

    Returns:
        Tuple of (team1, team2) or None if not found
    """
    # List of NFL team names to look for
    nfl_teams = [
        "Cardinals",
        "Falcons",
        "Ravens",
        "Bills",
        "Panthers",
        "Bears",
        "Bengals",
        "Browns",
        "Cowboys",
        "Broncos",
        "Lions",
        "Packers",
        "Texans",
        "Colts",
        "Jaguars",
        "Chiefs",
        "Raiders",
        "Chargers",
        "Rams",
        "Dolphins",
        "Vikings",
        "Patriots",
        "Saints",
        "Giants",
        "Jets",
        "Eagles",
        "Steelers",
        "49ers",
        "Seahawks",
        "Buccaneers",
        "Titans",
        "Commanders",
    ]

    # Alternative names and cities
    team_aliases = {
        "Arizona": "Cardinals",
        "Atlanta": "Falcons",
        "Baltimore": "Ravens",
        "Buffalo": "Bills",
        "Carolina": "Panthers",
        "Chicago": "Bears",
        "Cincinnati": "Bengals",
        "Cleveland": "Browns",
        "Dallas": "Cowboys",
        "Denver": "Broncos",
        "Detroit": "Lions",
        "Green Bay": "Packers",
        "Houston": "Texans",
        "Indianapolis": "Colts",
        "Jacksonville": "Jaguars",
        "Kansas City": "Chiefs",
        "Las Vegas": "Raiders",
        "Los Angeles Chargers": "Chargers",
        "Los Angeles Rams": "Rams",
        "Miami": "Dolphins",
        "Minnesota": "Vikings",
        "New England": "Patriots",
        "New Orleans": "Saints",
        "New York Giants": "Giants",
        "New York Jets": "Jets",
        "Philadelphia": "Eagles",
        "Pittsburgh": "Steelers",
        "San Francisco": "49ers",
        "Seattle": "Seahawks",
        "Tampa Bay": "Buccaneers",
        "Tennessee": "Titans",
        "Washington": "Commanders",
    }

    found_teams = []

    # Check for team names in question
    for team in nfl_teams:
        if team in question:
            found_teams.append(team)

    # Check for team aliases
    for alias, team in team_aliases.items():
        if alias in question and team not in found_teams:
            found_teams.append(team)

    if len(found_teams) >= 2:
        return (found_teams[0], found_teams[1])

    return None


def extract_date_from_question(question):
    """
    Extract date from the question.

    Args:
        question: The query string

    Returns:
        Date string in YYYY-MM-DD format or None if not found
    """
    # Look for dates in various formats
    date_patterns = [
        r"(\d{4}-\d{2}-\d{2})",  # YYYY-MM-DD
        r"(\d{1,2}/\d{1,2}/\d{2,4})",  # MM/DD/YYYY or MM/DD/YY
        r"(\d{1,2}-\d{1,2}-\d{2,4})",  # MM-DD-YYYY or MM-DD-YY
    ]

    for pattern in date_patterns:
        match = re.search(pattern, question)
        if match:
            date_str = match.group(1)

            # Try to parse the date
            try:
                if "-" in date_str and date_str.count("-") == 2:
                    # Check if it's already in YYYY-MM-DD format
                    parts = date_str.split("-")
                    if len(parts[0]) == 4:
                        return date_str
                    else:
                        # MM-DD-YYYY to YYYY-MM-DD
                        month, day, year = date_str.split("-")
                        if len(year) == 2:
                            year = f"20{year}"
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

                elif "/" in date_str:
                    # MM/DD/YYYY to YYYY-MM-DD
                    month, day, year = date_str.split("/")
                    if len(year) == 2:
                        year = f"20{year}"
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

            except Exception as e:
                print(f"Error parsing date: {e}")

    # Look for relative dates like "yesterday", "last Sunday", etc.
    today = datetime.now()

    if "yesterday" in question.lower():
        yesterday = today - timedelta(days=1)
        return yesterday.strftime("%Y-%m-%d")

    if "last week" in question.lower():
        last_week = today - timedelta(days=7)
        return last_week.strftime("%Y-%m-%d")

    # Default to today if no date found
    return today.strftime("%Y-%m-%d")


def analyze_game_result(game_data, team1, team2):
    """
    Analyze the game result between two teams.

    Args:
        game_data: Game data from the API
        team1: First team name
        team2: Second team name

    Returns:
        Dictionary with game analysis and recommendation
    """
    if not game_data:
        return {
            "status": "error",
            "message": "No game data available",
            "recommendation": RESOLUTION_MAP["Not played"],
        }

    # Find the game between these teams
    target_game = None

    for game in game_data:
        home_team = game.get("HomeTeam", "")
        away_team = game.get("AwayTeam", "")

        # Check if the teams match (in either order)
        if (team1 in home_team and team2 in away_team) or (
            team2 in home_team and team1 in away_team
        ):
            target_game = game
            break

    if not target_game:
        return {
            "status": "error",
            "message": f"Could not find game between {team1} and {team2}",
            "recommendation": RESOLUTION_MAP["Not played"],
        }

    # Check game status
    status = target_game.get("Status", "")
    home_score = target_game.get("HomeScore", 0)
    away_score = target_game.get("AwayScore", 0)
    home_team = target_game.get("HomeTeam", "")
    away_team = target_game.get("AwayTeam", "")

    # If game is not final, return "not played" resolution
    if status != "Final":
        return {
            "status": "pending",
            "message": f"Game between {home_team} and {away_team} has not been completed",
            "game_status": status,
            "recommendation": RESOLUTION_MAP["Not played"],
        }

    # Determine winner
    if home_score > away_score:
        winner = "Team A"  # Home team wins
        message = f"{home_team} won against {away_team} with a score of {home_score}-{away_score}"
    elif away_score > home_score:
        winner = "Team B"  # Away team wins
        message = f"{away_team} won against {home_team} with a score of {away_score}-{home_score}"
    else:
        winner = "Tie"
        message = f"The game between {home_team} and {away_team} ended in a tie with a score of {home_score}-{away_score}"

    return {
        "status": "completed",
        "message": message,
        "home_team": home_team,
        "away_team": away_team,
        "home_score": home_score,
        "away_score": away_score,
        "winner": winner,
        "recommendation": RESOLUTION_MAP[winner],
    }


def main():
    """Main function to process NFL queries and return a recommendation."""
    try:
        # This would normally come from command line args, but for this use case
        # we'll just define it here
        question = "Did the Cowboys beat the Eagles in their NFL game on 2023-11-05?"

        # Extract team names and date from the question
        teams = extract_team_names_from_question(question)
        date = extract_date_from_question(question)

        if not teams:
            print("Could not identify NFL teams in the question.")
            print(f"recommendation: {RESOLUTION_MAP['Not played']}")
            return

        team1, team2 = teams
        print(f"Analyzing game between {team1} and {team2} on {date}")

        # Fetch game data
        game_data = fetch_game_by_date(date)

        if not game_data:
            print("No games found for the specified date.")
            print(f"recommendation: {RESOLUTION_MAP['Not played']}")
            return

        # Analyze game result
        result = analyze_game_result(game_data, team1, team2)

        # Print the analysis and recommendation
        print(json.dumps(result, indent=2))
        print(f"recommendation: {result['recommendation']}")

    except Exception as e:
        print(f"Error processing NFL query: {e}")
        print(f"recommendation: {RESOLUTION_MAP['Not played']}")


if __name__ == "__main__":
    main()
