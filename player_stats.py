import requests
import json
import time
import os
import sys
import logging

# player_stats.py
# Fetch user lite info for IDs in player_ids.json and count players by level.

ENTRY_URL = "https://api2.warera.io/trpc/user.getUserLite"
HEADERS = {"Content-Type": "application/json"}
DELAY = 0.2  # seconds between requests
RETRY_429 = 30  # seconds to wait on 429

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('debug.log'),
              logging.StreamHandler()])


def load_ids(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_stats(path, stats):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)


def append_player_data(path, player_data):
    """Append individual player data to JSON file"""
    data = []
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    data.append(player_data)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def fetch_user_data(user_id):
    params = {"input": json.dumps({"userId": user_id})}
    while True:
        r = requests.get(ENTRY_URL, params=params, headers=HEADERS, timeout=30)
        if r.status_code == 200:
            try:
                j = r.json()
            except ValueError:
                return None
            data = j.get("result", {}).get("data", {})
            return data
        elif r.status_code == 429:
            logging.warning(f"Rate limited, waiting {RETRY_429}s")
            time.sleep(RETRY_429)
        else:
            return None


def main():
    try:
        base_dir = os.path.dirname(__file__)
    except NameError:
        base_dir = os.getcwd()

    ids_file = os.path.join(base_dir, "player_ids.json")
    out_file = os.path.join(base_dir, "player_stats.json")

    if not os.path.isfile(ids_file):
        logging.error(f"Missing input file: {ids_file}")
        sys.exit(1)

    try:
        user_ids = load_ids(ids_file)
    except Exception as e:
        logging.error(f"Failed to read ids: {e}")
        sys.exit(1)

    logging.info(f"Loaded {len(user_ids)} player IDs")

    # Clear output file
    write_stats(out_file, [])

    failed = 0
    processed = 0

    for uid in user_ids:
        data = fetch_user_data(uid)
        processed += 1

        if data is None:
            failed += 1
            logging.warning(f"Failed to fetch data for user {uid}")
        else:
            player = {}
            player[uid] = data
            print(f"player data fetched. {processed}")
            append_player_data(out_file, data)
            #logging.info(f"[{processed}/{len(user_ids)}] User {uid} - Level {data.get("leveling", "N/A").get("level")}")

        time.sleep(DELAY)

    logging.info(
        f"Processing complete: {processed} processed, {failed} failed")


if __name__ == "__main__":
    main()
