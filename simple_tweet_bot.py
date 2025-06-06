#!/usr/bin/env python3
"""
A simple bot to fetch LLM Oracle predictions and print demo tweets for new items.
Continuously checks the API every minute, querying from the last known end time.
Can optionally post tweets live if configured and run with --live-mode.
"""
import json
import time
import os
import argparse
from datetime import datetime, timedelta
import urllib.request
import urllib.parse
from typing import Optional, Tuple, Dict, Any
import random
from dotenv import load_dotenv

load_dotenv()

try:
    import tweepy
except ImportError:
    print("Tweepy library not found. Please install it: pip3 install tweepy")
    print("Live tweeting functionality will be disabled.")
    tweepy = None

HISTORY_FILE = "simple_tweet_history.json"
API_BASE_URL = "https://api.ai.uma.xyz"
API_ENDPOINT = "/advanced-query"
CHECK_INTERVAL_SECONDS = 300
DEFAULT_LOOKBACK_DAYS = 1/12

def load_history() -> Tuple[set, int]:
    """Loads tweeted item IDs and the next start timestamp from the history file."""
    default_start_timestamp = int((datetime.now() - timedelta(days=DEFAULT_LOOKBACK_DAYS)).timestamp())
    try:
        with open(HISTORY_FILE, 'r') as f:
            data = json.load(f)
            tweeted_ids = set(data.get("tweeted_ids", []))
            next_start_timestamp = data.get("next_start_timestamp", default_start_timestamp)
            if not isinstance(next_start_timestamp, int):
                print(f"Warning: next_start_timestamp in history is not an int. Defaulting.")
                next_start_timestamp = default_start_timestamp
        print(f"Loaded {len(tweeted_ids)} IDs and next_start_timestamp: {datetime.fromtimestamp(next_start_timestamp)} from {HISTORY_FILE}")
        return tweeted_ids, next_start_timestamp
    except FileNotFoundError:
        print(f"History file '{HISTORY_FILE}' not found. Starting with lookback of {DEFAULT_LOOKBACK_DAYS} days.")
        return set(), default_start_timestamp
    except json.JSONDecodeError:
        print(f"Error decoding JSON from '{HISTORY_FILE}'. Starting fresh.")
        return set(), default_start_timestamp
    except Exception as e:
        print(f"Unexpected error loading history: {e}. Starting fresh.")
        return set(), default_start_timestamp

def save_history(history_set: set, new_next_start_timestamp: int):
    """Saves tweeted item IDs and the new next start timestamp to the history file."""
    try:
        with open(HISTORY_FILE, 'w') as f:
            data_to_save = {
                "tweeted_ids": list(history_set),
                "next_start_timestamp": new_next_start_timestamp
            }
            json.dump(data_to_save, f, indent=2)
        print(f"Saved {len(history_set)} IDs. Next query will start from: {datetime.fromtimestamp(new_next_start_timestamp)}")
    except Exception as e:
        print(f"An error occurred saving history: {e}")

def get_item_id(item: dict) -> Optional[str]:
    """Extracts a unique ID from an API result item."""
    if not isinstance(item, dict): return None
    for key in ["query_id"]:
        if item.get(key):
            return str(item[key])
    print(f"Warning: Could not find a primary ID for item: {str(item)[:200]}...")
    return None

def get_item_title(item: dict) -> str:
    """Extracts a title from an API result item's ancillary_data."""
    if not isinstance(item, dict): return "Unknown Prediction"
    try:
        ancillary_data_str = item.get("proposal_metadata", {}).get("ancillary_data", "")
        if not ancillary_data_str or not isinstance(ancillary_data_str, str):
            raise ValueError("Ancillary data is missing or not a string")
        title_marker = "title:"
        title_start_index = ancillary_data_str.lower().find(title_marker)
        if title_start_index != -1:
            title_start_index += len(title_marker)
            terminators = [",", "\n", "description:"] 
            title_end_index = len(ancillary_data_str)
            for term in terminators:
                current_term_index = ancillary_data_str.find(term, title_start_index)
                if current_term_index != -1:
                    title_end_index = min(title_end_index, current_term_index)
            title = ancillary_data_str[title_start_index:title_end_index].strip()
            if title:
                if title.lower().startswith("q:"): title = title[2:].lstrip()
                return title if len(title) < 200 else title[:197] + "..."
    except Exception as e:
        print(f"Error extracting title: {e}. Ancillary data: '{str(ancillary_data_str)[:100]}...'")
    item_id_for_fallback = get_item_id(item)
    return f"Prediction {item_id_for_fallback}" if item_id_for_fallback else "Unknown Prediction"

def get_recommendation_text(item: dict, recommendation_type: str = "resolved") -> str:
    """Converts recommendation code to text using resultMapping if available.
    Args:
        item: The full item dictionary
        recommendation_type: Either "resolved" or "proposed" to specify which outcome to get
    """
    if not isinstance(item, dict): return "Unknown"
    
    # Get recommendation based on type
    if recommendation_type == "resolved":
        recommendation = item.get("result", {}).get("recommendation")
    else:  # proposed
        recommendation = item.get("proposed_price_outcome")
    
    # Get the result mapping if available
    result_mapping = item.get("resultMapping", {})
    
    print(f"Result mapping: {result_mapping}")
    print(f"Recommendation ({recommendation_type}): {recommendation}")
    
    if result_mapping and recommendation in result_mapping:
        print(f"Text: {result_mapping[recommendation]}")
        return result_mapping[recommendation]
    
    # Fallback mapping for p1-p3 if resultMapping is not available
    fallback_mapping = {"p1": "p1", "p2": "p2", "p3": "Uncertain"}
    return fallback_mapping.get(str(recommendation), "Unknown")

def get_item_query_link(item: dict) -> str:
    """Constructs a URL to the query page for the given item."""
    item_id = get_item_id(item)
    if item_id:
        # Assuming the frontend URL structure based on API_BASE_URL
        # API_BASE_URL is "https://api.ai.uma.xyz", so frontend might be "https://ai.uma.xyz"
        return f"https://ai.uma.xyz/query.html?query_id={item_id}"
    return ""

def has_tags(item: dict) -> bool:
    """Checks if an item has any tags in either proposal_metadata or market_data."""
    if not isinstance(item, dict):
        return False
    
    # Check tags in proposal_metadata
    proposal_tags = item.get("proposal_metadata", {}).get("tags", [])
    if isinstance(proposal_tags, list) and proposal_tags:
        return True
        
    # Check tags in market_data
    market_tags = item.get("market_data", {}).get("tags", [])
    if isinstance(market_tags, list) and market_tags:
        return True
        
    return False

def is_sports_event(item: dict) -> bool:
    """Checks if an event has sports-related tags."""
    if not isinstance(item, dict):
        return False
    
    # Get tags from proposal_metadata
    tags = item.get("proposal_metadata", {}).get("tags", [])
    if not isinstance(tags, list):
        return False
    
    # Check for sports-related tags
    sports_tags = {"Sports", "Soccer", "Football", "Basketball", "Baseball", "Hockey", 
                  "Tennis", "Golf", "Racing", "Olympics", "World Cup", "Championship"}
    
    return any(tag in sports_tags for tag in tags)

def fetch_oracle_data(start_timestamp_for_query: int) -> Tuple[Optional[list], int]:
    """Fetches data from the Oracle API using urllib. Returns (api_data, end_timestamp_of_query)."""
    current_unix = int(time.time())
    
    # Always look back 2 hours from current time
    two_hours_ago = current_unix - (36 * 60 * 60)  # 24 hours in seconds
    
    params_dict = {
        "start_timestamp": two_hours_ago,
        "end_timestamp": current_unix,
        "limit": 100,
        "full": "true" 
    }
    
    query_string = urllib.parse.urlencode(params_dict)
    full_url = f"{API_BASE_URL}{API_ENDPOINT}?{query_string}"
    
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Fetching data from: {full_url}")
    print(f"Query window: {datetime.fromtimestamp(two_hours_ago)} to {datetime.fromtimestamp(current_unix)}")
    
    try:
        req = urllib.request.Request(full_url)
        req.add_header('User-Agent', 'SimpleTweetBot/0.1 Python urllib')
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.getcode() != 200:
                print(f"API request failed: HTTP {response.getcode()} {response.reason}")
                try:
                    error_body = response.read().decode('utf-8', 'ignore')
                    print(f"Error response body: {error_body[:500]}...")
                except Exception as read_err:
                    print(f"Could not read error response body: {read_err}")
                return None, current_unix
            
            response_data_bytes = response.read()
            response_data_str = response_data_bytes.decode('utf-8')
            print(f"API Response status: {response.getcode()}, Data length: {len(response_data_bytes)} bytes")
            return json.loads(response_data_str), current_unix
            
    except Exception as e: 
        print(f"An error occurred during API fetch: {type(e).__name__} - {e}")
        return None, current_unix

def create_tweepy_client():
    """Creates and authenticates a Tweepy API v2 client using environment variables."""
    if not tweepy:
        print("Tweepy library not imported, cannot create client.")
        return None
        
    api_key = os.getenv("TWITTER_API_KEY")
    api_secret = os.getenv("TWITTER_API_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

    if not all([api_key, api_secret, access_token, access_token_secret]):
        print("Warning: Twitter API credentials not fully found in environment variables.")
        print("Required: TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET")
        print("Live tweeting will be disabled.")
        return None

    try:
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )
        # Test authentication (optional but recommended)
        me_response = client.get_me()
        print(f"Successfully authenticated with Twitter as user: @{me_response.data.username} (ID: {me_response.data.id})")
        return client
    except tweepy.errors.TweepyException as e:
        print(f"Error authenticating with Twitter API: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred creating Twitter client: {e}")
        return None

def main():
    """Main function for the simple tweet bot."""
    parser = argparse.ArgumentParser(description="Simple LLM Oracle Tweet Bot")
    parser.add_argument("--live-mode", action="store_true", 
                        help="Enable actual tweeting (requires Twitter API credentials as environment variables)")
    parser.add_argument("--no-ai", action="store_true",
                        help="Disable AI-generated tweets and use simple format instead")
    args = parser.parse_args()

    print(f"--- Simple Tweet Bot Starting ({'LIVE MODE' if args.live_mode else 'DEMO MODE'}, "
          f"AI Tweets: {'Disabled' if args.no_ai else 'Enabled'}, runs continuously, Ctrl+C to stop) ---")
    
    twitter_client = None
    if args.live_mode:
        print("Live mode enabled. Attempting to authenticate with Twitter...")
        twitter_client = create_tweepy_client()
        if twitter_client is None:
            print("Twitter client authentication failed or credentials missing. Will proceed in demo mode.")
    else:
        print("Running in demo mode. Tweets will be printed to console.")

    tweeted_history, next_start_ts = load_history()
    
    try:
        while True:
            print(f"\n--- Cycle starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. Querying from {datetime.fromtimestamp(next_start_ts)} ---")
            
            api_data, query_ended_at_ts = fetch_oracle_data(next_start_ts)
            current_cycle_max_item_ts = 0

            if api_data is None:
                print("No data fetched from API or an error occurred during this cycle.")
            elif not isinstance(api_data, list):
                print(f"API data is not a list as expected. Type: {type(api_data)}. Content: {str(api_data)[:500]}...")
            else:
                print(f"Fetched {len(api_data)} items from the API this cycle.")
                if api_data: # Log the first item for debugging
                    try:
                        print(f"DEBUG: First item from API response: {json.dumps(api_data[0], indent=2)}")
                    except Exception as e:
                        print(f"DEBUG: Could not serialize first item for logging: {e}")

                new_items_processed_this_cycle = 0

                for i, item in enumerate(api_data):
                    print(f"\n--- Processing API Item {i+1}/{len(api_data)} ---")
                    if not isinstance(item, dict):
                        print(f"Skipping item, not a dictionary: {str(item)[:200]}...")
                        continue
                    
                    try:
                        item_ts = item.get("last_updated_timestamp") or item.get("request_timestamp_s")
                        if item_ts and isinstance(item_ts, int):
                            current_cycle_max_item_ts = max(current_cycle_max_item_ts, item_ts)
                    except Exception as e:
                         print(f"    Warning: Could not parse timestamp from item: {e}")

                    item_id = get_item_id(item)
                    if not item_id:
                        print(f"Skipping item due to missing or un-extractable ID.")
                        continue

                    if item_id not in tweeted_history:
                        # Skip items with no tags
                        if not has_tags(item):
                            print(f"  Skipping item with no tags: {item_id}")
                            continue
                            
                        # Check if it's a sports event and randomly decide whether to post
                        if is_sports_event(item):
                            if random.random() > 0.5:  # 50% chance to skip
                                print(f"  Skipping sports event (random 50% filter): {item_id}")
                                continue
                            print(f"  Sports event selected for posting (random 50% filter): {item_id}")
                        
                        title = get_item_title(item)
                        
                        resolved_price_outcome_code = item.get("result", {}).get("recommendation")
                        proposed_price_outcome_code = item.get("proposed_price_outcome")

                        # Skip items with uncertain or cannot be determined recommendations (case insensitive)
                        if resolved_price_outcome_code and resolved_price_outcome_code.lower() in ["p3", "p4"]:
                            print(f"  Skipping item with uncertain/cannot be determined recommendation ({resolved_price_outcome_code}): {item_id}")
                            continue

                        # Convert outcome codes to text using the existing helper.
                        # Pass the entire item to get access to resultMapping
                        resolved_outcome_str = get_recommendation_text(item, "resolved") if resolved_price_outcome_code else "N/A"
                        proposed_outcome_str = get_recommendation_text(item, "proposed") if proposed_price_outcome_code else "N/A"
                        
                        query_link = get_item_query_link(item)
                        
                        # Construct the tweet text with proposed and resolved outcomes
                        tweet_text = f"Market: {title}\n\nProposed Answer: {proposed_outcome_str}\nAI Answer: {resolved_outcome_str}"
                        
                        if query_link:
                            tweet_text += f"\n\nLink: {query_link}"
                        # Ensure it's not too long
                        if len(tweet_text) > 280:
                             tweet_text = tweet_text[:277] + "..."
                        
                        processed_successfully = False
                        if args.live_mode and twitter_client:
                            print(f"Attempting to post tweet for ID: {item_id}...")
                            try:
                                response = twitter_client.create_tweet(text=tweet_text)
                                print(f"Tweet posted successfully! Tweet ID: {response.data['id']}")
                                processed_successfully = True
                            except tweepy.errors.TweepyException as e:
                                print(f"Error posting tweet for ID {item_id}: {e}")
                            except Exception as e:
                                print(f"An unexpected error occurred during tweeting for ID {item_id}: {e}")
                        else:
                            # Demo mode or client failed
                            print("\n============================================================")
                            print(f"DEMO TWEET ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}):")
                            print("------------------------------------------------------------")
                            print(tweet_text)
                            print(f"(Reference ID: {item_id})")
                            print("============================================================\n")
                            processed_successfully = True # Mark as processed in demo mode

                        if processed_successfully:
                            tweeted_history.add(item_id)
                            new_items_processed_this_cycle += 1
                            time.sleep(1) # Small delay after processing an item
                        else:
                             print(f"Failed to process item ID {item_id} (live tweet failed). It will be retried next cycle.")
                    else:
                        print(f"  Item ID '{item_id}' already processed. Skipping.")

                if new_items_processed_this_cycle > 0:
                    print(f"Successfully processed {new_items_processed_this_cycle} new items this cycle.")
                else:
                    print("No new items to process this cycle (all fetched items were either processed or in history).")
            
            # Determine the next start timestamp
            if current_cycle_max_item_ts > 0:
                next_start_ts = current_cycle_max_item_ts + 1 
            else:
                # If no item timestamps found, advance based on query end time
                next_start_ts = query_ended_at_ts 
            # Ensure window doesn't go backward, always advance at least to end of last query
            next_start_ts = max(next_start_ts, query_ended_at_ts) 
            
            save_history(tweeted_history, next_start_ts)
            
            print(f"--- Cycle finished. Waiting for {CHECK_INTERVAL_SECONDS} seconds... ---")
            time.sleep(CHECK_INTERVAL_SECONDS)
            
    except KeyboardInterrupt:
        print("\n--- KeyboardInterrupt received. Shutting down simple tweet bot gracefully... ---")
    finally:
        final_ts_to_save = None
        if 'next_start_ts' in locals():
             final_ts_to_save = next_start_ts
        else:
             _, final_ts_to_save = load_history() 
        
        if 'tweeted_history' in locals():
             save_history(tweeted_history, final_ts_to_save)
        print("--- Simple Tweet Bot Finished ---")

if __name__ == "__main__":
    main() 