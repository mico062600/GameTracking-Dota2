import os
import requests

# --- CONFIGURATION ---
# Both players are now added directly into this list!
PLAYER_IDS = ["183768181", "199551113"]
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def get_last_match_id(player_id):
    """Reads the last known match ID for a specific player's data file."""
    cache_file = f"last_match_{player_id}.txt"
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            return f.read().strip()
    return None

def save_last_match_id(player_id, match_id):
    """Saves the newest match ID for a specific player's data file."""
    cache_file = f"last_match_{player_id}.txt"
    with open(cache_file, "w") as f:
        f.write(str(match_id))

def check_player_matches(player_id):
    url = f"https://opendota.com{player_id}/recentMatches"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"API Error for {player_id}: {response.status_code}")
            return

        matches = response.json()
        if not matches or not isinstance(matches, list):
            print(f"No match history format found for {player_id}.")
            return

        latest_match = matches[0]
        latest_match_id = str(latest_match["match_id"])
        saved_match_id = get_last_match_id(player_id)

        if saved_match_id is None:
            print(f"First run setup: Baselining player {player_id} to match {latest_match_id}")
            save_last_match_id(player_id, latest_match_id)
            return

        if latest_match_id != saved_match_id:
            print(f"New match found for player {player_id}! ID: {latest_match_id}")
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
                    "title": f"Player {player_id} just finished a game!",
                    "description": f"**Result:** {result}\n**KDA:** {kills}/{deaths}/{assists}",
                    "color": 3066993 if "WON" in result else 15158332,
                    "fields": [{"name": "Links", "value": f"[Dotabuff](https://dotabuff.com{latest_match_id}) | [OpenDota](https://opendota.com{latest_match_id})"}]
                }]
            }
            requests.post(DISCORD_WEBHOOK_URL, json=payload)
            save_last_match_id(player_id, latest_match_id)
        else:
            print(f"Player {player_id} checked. No new matches.")

    except Exception as e:
        print(f"Error checking player {player_id}: {e}")

if __name__ == "__main__":
    # Loop over every player ID configured in the list above
    for pid in PLAYER_IDS:
        check_player_matches(pid)
