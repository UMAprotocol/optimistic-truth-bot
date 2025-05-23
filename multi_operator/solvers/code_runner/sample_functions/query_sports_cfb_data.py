"""
CFB market resolver
p1 = Georgia Bulldogs
p2 = Alabama Crimson Tide
p3 = 50-50 (canceled / tie)
p4 = Too early / in-progress
"""
import os, time, logging, re, requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# ───────── config ─────────
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_CFB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_CFB_API_KEY")
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

logging.basicConfig(level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()])
logging.getLogger().addFilter(
    lambda r: setattr(r, "msg",
        re.sub(re.escape(API_KEY), "******", r.getMessage())) or True)
log = logging.getLogger(__name__)

def _get(url, tag, retries=3, backoff=1.5):
    for i in range(retries):
        log.debug(f"[{tag}] → {url}")
        r = requests.get(url, headers=HEADERS, timeout=10)
        log.debug(f"[{tag}] ← {r.status_code} {r.reason}")
        if r.ok:
            log.debug(f"[{tag}] payload length: {len(r.json())}")
            return r.json()
        if r.status_code in (401, 403):
            log.error(f"[{tag}] blocked — not in plan"); return None
        if r.status_code == 404:
            log.warning(f"[{tag}] 404 — not found"); return []
        if r.status_code == 429:
            wait = backoff * 2**i
            log.warning(f"[{tag}] 429 — back-off {wait:.1f}s")
            time.sleep(wait); continue
        r.raise_for_status()
    return None

# ───────── helpers ─────────
def team_keys():
    teams = _get("https://api.sportsdata.io/v3/cfb/scores/json/Teams", "Teams")
    m = {}
    for t in teams:
        school = t['School']                      # "Georgia"
        m[school.lower()] = t["Key"]
        # Add common team name variations
        if " " in school:
            parts = school.split()
            m[parts[0].lower()] = t["Key"]        # "Georgia" from "Georgia Bulldogs"
            m[" ".join(parts[1:]).lower()] = t["Key"]  # "Bulldogs" from "Georgia Bulldogs"
        # Add full name with common nicknames
        full_names = {
            "georgia": "georgia bulldogs",
            "alabama": "alabama crimson tide",
            "clemson": "clemson tigers",
            "ohio state": "ohio state buckeyes",
            "michigan": "michigan wolverines",
            "texas": "texas longhorns",
            "oklahoma": "oklahoma sooners",
            "lsu": "lsu tigers",
            "notre dame": "notre dame fighting irish",
            "usc": "usc trojans"
        }
        school_lower = school.lower()
        if school_lower in full_names:
            m[full_names[school_lower]] = t["Key"]
    return m

def fuzzy(name, table):
    n = name.strip().lower()
    return table.get(n, n)

def points(game):
    a, h = game.get("AwayTeamScore"), game.get("HomeTeamScore")
    if a or h:
        return a, h
    # CFB might use Periods instead of Quarters
    a_tot = h_tot = 0
    for period in game.get("Periods", []):
        a_tot += period.get("AwayScore", 0)
        h_tot += period.get("HomeScore", 0)
    return a_tot, h_tot

def season_year(d: datetime.date):
    # CFB season is labeled by the year in which it starts (fall)
    return d.year - (1 if d.month < 7 else 0)

def locate(date_str, k1, k2):
    base = datetime.strptime(date_str, "%Y-%m-%d").date()
    # 1️⃣ final slice local & +1d UTC
    for ds in (base, base + timedelta(days=1)):
        url = f"https://api.sportsdata.io/v3/cfb/scores/json/GamesByDateFinal/{ds}"
        for g in _get(url, f"GamesByDateFinal/{ds}"):
            if {g["HomeTeam"], g["AwayTeam"]} == {k1, k2}:
                log.info("Found FINAL boxscore"); return g, "final"
    # 2️⃣ schedule feeds (post-season then regular)
    for tag in ("POST", ""):
        season = f"{season_year(base)}{tag}"
        url = f"https://api.sportsdata.io/v3/cfb/scores/json/Games/{season}"
        for g in _get(url, f"Games/{season}"):
            if {g["HomeTeam"], g["AwayTeam"]} == {k1, k2}:
                log.info(f"Found in schedule {tag or 'REG'}"); return g, "scheduled"
    return None, None

def outcome(g, feed, k1, k2):
    if not g or feed == "scheduled":           return "p4"
    if g["Status"] in {"Postponed","Canceled"}:return "p3"
    if g["Status"] != "Final":                 return "p4"
    a, h = points(g)
    if a == h:                                 return "p3"
    winner = g["HomeTeam"] if h > a else g["AwayTeam"]
    return "p1" if winner == k1 else "p2"

# ───────── main ─────────
if __name__ == "__main__":
    DATE   = "2024-12-01"
    TEAM1  = "Georgia Bulldogs"   # p1
    TEAM2  = "Alabama"            # p2

    tbl = team_keys()
    k1, k2 = fuzzy(TEAM1, tbl), fuzzy(TEAM2, tbl)
    log.info(f"Searching with keys: {k1} vs {k2}")

    game, feed = locate(DATE, k1, k2)
    print("recommendation:", outcome(game, feed, k1, k2))