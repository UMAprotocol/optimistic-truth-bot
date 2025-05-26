import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# ─────────── configuration ───────────
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# ─────────── generic GET wrapper ───────────
def _get(url, tag, retries=3, backoff=1.5):
    for i in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.ok:
                return response.json()
            if response.status_code in (401, 403):
                return None
            if response.status_code == 404:
                return []
            if response.status_code == 429:
                wait = backoff * 2**i
                time.sleep(wait)
                continue
            response.raise_for_status()
        except requests.RequestException as e:
            if i == retries - 1:
                raise ConnectionError(f"Failed to retrieve data after {retries} attempts: {e}")
    return None

# ─────────── helpers ───────────
def team_keys():
    teams = _get("https://api.sportsdata.io/v3/mlb/scores/json/Teams", "Teams")
    m = {}
    for t in teams:
        full = f"{t['City']} {t['Name']}"
        m[full] = t["Key"]
        m[t["Name"]] = t["Key"]
        if t["Name"].endswith('s'):
            m[t["Name"][:-1]] = t["Key"]
    m["A's"] = m.get("Athletics", "ATH")
    return m

def final_runs(g):
    a, h = g.get("AwayTeamRuns"), g.get("HomeTeamRuns")
    if a is not None or h is not None:
        return a, h
    a_tot = h_tot = 0
    for inn in g.get("Innings", []):
        a_tot += inn.get("AwayTeamRuns", 0)
        h_tot += inn.get("HomeTeamRuns", 0)
    return a_tot, h_tot

def locate(date_str, k1, k2):
    base = datetime.strptime(date_str, "%Y-%m-%d").date()
    for ds in (base, base + timedelta(days=1)):
        url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDateFinal/{ds}"
        games = _get(url, f"GamesByDateFinal/{ds}")
        if games:
            for g in games:
                if {g["HomeTeam"], g["AwayTeam"]} == {k1, k2}:
                    return g, "final"
    season = base.year
    games = _get(f"https://api.sportsdata.io/v3/mlb/scores/json/Games/{season}", f"Games/{season}")
    if games:
        for g in games:
            if {g["HomeTeam"], g["AwayTeam"]} == {k1, k2}:
                return g, "scheduled"
    return None, None

def outcome(g, feed, k1, k2):
    if not g or feed == "scheduled":
        return "p4"
    if g["Status"] in {"Postponed", "Canceled"}:
        return "p3"
    if g["Status"] != "Final":
        return "p4"
    a, h = final_runs(g)
    if a == h:
        return "p3"
    winner = g["HomeTeam"] if h > a else g["AwayTeam"]
    return "p1" if winner == k1 else "p2"

# ─────────── main ───────────
if __name__ == "__main__":
    DATE = "2025-04-23"
    TEAM1 = "Texas Rangers"
    TEAM2 = "Athletics"

    tbl = team_keys()
    k1, k2 = tbl.get(TEAM1, TEAM1), tbl.get(TEAM2, TEAM2)

    game, feed = locate(DATE, k1, k2)
    print("recommendation:", outcome(game, feed, k1, k2))