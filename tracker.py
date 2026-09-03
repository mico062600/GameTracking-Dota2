import os
import requests

STEAM_32_ID = "183768181"
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
CACHE_FILE = "last_match_id.txt"

def get_last_match_id():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return f.read().strip()
    return None

def save_last_match_id(match_id):
    with open(CACHE_FILE, "w") as f:
        f.write(str(match_id))

def check_matches():
    url = f"https://opendota.com{STEAM_32_ID}/recentMatches"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"API Error: {response.status_code}")
            return

        matches = response.json()
        if not matches or not isinstance(matches, list):
            print("No matches or invalid API response format.")
            return

        latest_match = matches[0]
        latest_match_id = str(latest_match["match_id"])
        saved_match_id = get_last_match_id()

        if saved_match_id is None:
            print(f"First run setup: Baselining match ID to {latest_match_id}")
            save_last_match_id(latest_match_id)
            return

        if latest_match_id != saved_match_id:
            print(f"New match found! ID: {latest_match_id}")
            kills = latest_match.get("kills", 0)
            deaths = latest_match.get("deaths", 0)
            assists = latest_match.get("assists", 0)

            player_slot = latest_match.get("player_slot", 0)
            is_radiant = player_slot < 128
            radiant_win = latest_match.get("radiant_win", True)
            result = "🏆 WON" if (is_radiant == radiant_win) else "❌ LOST"

            payload = {
                "username": "Dota 2 Match Tracker",
                "avatar_url": "https://dotabuff.com",
                "embeds": [{
                    "title": f"Player {STEAM_32_ID} just finished a game!",
                    "description": f"**Result:** {result}\n**KDA:** {kills}/{deaths}/{assists}",
                    "color": 3066993 if "WON" in result else 15158332,
                    "fields": [{"name": "Match Link", "value": f"[Dotabuff](https://dotabuff.com{latest_match_id})"}]
                }]
            }
            requests.post(DISCORD_WEBHOOK_URL, json=payload)
            save_last_match_id(latest_match_id)
        else:
            print("Checked. No new matches played since last check.")

    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    check_matches()
