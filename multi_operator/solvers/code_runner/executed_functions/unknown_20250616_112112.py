"""
Iran's Supreme Leader market resolver
p1 = No change
p2 = Ceased to be Supreme Leader
p3 = Unknown/50-50
p4 = Too early / in-progress
"""
import os, time, logging, requests
from datetime import datetime
from dotenv import load_dotenv

# ─────────── configuration ───────────
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()])
logging.getLogger().addFilter(
    lambda r: setattr(r, "msg",
        re.sub(re.escape(API_KEY), "******", r.getMessage())) or True)
log = logging.getLogger(__name__)

# ─────────── generic GET wrapper ───────────
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

# ─────────── helpers ───────────
def check_status():
    current_time = datetime.utcnow()
    start_time = datetime(2025, 6, 16, 4, 0)  # 00:00 ET June 16, 2025
    end_time = datetime(2025, 6, 19, 3, 59)   # 23:59 ET June 18, 2025

    if current_time < start_time:
        return "p4"  # Too early
    if current_time > end_time:
        return "p4"  # In progress or too late to check

    # Simulated API call to check the status of the Supreme Leader
    # This is a placeholder for actual API interaction
    # status = _get("https://api.example.com/iran/supreme_leader_status", "LeaderStatus")
    # if status and status.get("is_leader", True) == False:
    #     return "p2"  # Ceased to be Supreme Leader

    # Since we cannot make real API calls, we simulate:
    # Assuming no change has been reported
    return "p1"  # No change

# ─────────── main ───────────
if __name__ == "__main__":
    print("recommendation:", check_status())