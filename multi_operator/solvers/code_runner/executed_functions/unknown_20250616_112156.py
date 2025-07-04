"""
Iran's Supreme Leader market resolver
p1 = No change
p2 = Ceased to be Supreme Leader
p3 = Unknown/50-50
p4 = Too early / in-progress
"""
import os, time, logging, requests
from datetime import datetime, timedelta
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

# ─────────── main ───────────
if __name__ == "__main__":
    # Define the period of interest
    start_date = datetime(2025, 6, 16, 0, 0)  # June 16, 2025 at 00:00 ET
    end_date = datetime(2025, 6, 18, 23, 59)  # June 18, 2025 at 23:59 ET
    current_time = datetime.utcnow()

    # Check if the current time is within the specified period
    if current_time < start_date or current_time > end_date:
        print("recommendation: p4")  # Too early or too late to resolve
    else:
        # Normally here you would check the official sources or news APIs
        # Since we cannot make real API calls, we simulate the logic
        # This is a placeholder for where you would implement your API logic
        # For example, checking a government API or news feed
        # Simulated response (this should be replaced with actual API call logic)
        is_leader_changed = False  # Simulate checking the condition

        if is_leader_changed:
            print("recommendation: p2")  # Ceased to be Supreme Leader
        else:
            print("recommendation: p1")  # No change