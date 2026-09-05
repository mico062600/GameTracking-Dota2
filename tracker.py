import os
import requests

# --- CONFIGURATION ---
PLAYER_MAP = {
    "183768181": "Killua 射殺",
    "199551113": "Sol Engot"
}
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def get_last_match_id(player_id):
    cache_file = f"last_match_{player_id}.txt"
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r") as f:
                return f.read().strip()
        except Exception:
            return None
    return None

def save_last_match_id(player_id, match_id):
    cache_file = f"last_match_{player_id}.txt"
    try:
        with open(cache_file, "w") as f:
            f.write(str(match_id))
    except Exception as e:
        print(f"Failed to write cache file: {e}")

def check_player_matches(player_id, player_name):
    url = f"https://api.opendota.com/api/players/{player_id}/recentMatches"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        response = requests.get(url, headers=headers, timeout=(5, 5))
        if response.status_code != 200:
            print(f"API Error for {player_name}: Status {response.status_code}")
            return

        matches = response.json()
        if not matches or not isinstance(matches, list):
            print(f"No match history array found for {player_name}.")
            return

        saved_match_id = get_last_match_id(player_id)

        # Baseline setup on absolute first execution tracker run
        if saved_match_id is None:
            latest_match_id = str(matches[0].get("match_id", ""))
            print(f"First run setup: Baselining {player_name} to match {latest_match_id}")
            save_last_match_id(player_id, latest_match_id)
            return

        # Identify all new matches that occurred since the last saved ID
        new_matches = []
        for match in matches:
            m_id = str(match.get("match_id", ""))
            if m_id == saved_match_id:
                break
            new_matches.append(match)

        if not new_matches:
            print(f"{player_name} checked. No new matches.")
            return

        # Reverse the array loop to post them chronologically from oldest to newest
        new_matches.reverse()
        print(f"Found {len(new_matches)} new match(es) for {player_name}!")

        for idx, current_match in enumerate(new_matches):
            current_match_id = str(current_match.get("match_id", ""))
            kills = current_match.get("kills", 0)
            deaths = current_match.get("deaths", 0)
            assists = current_match.get("assists", 0)

            player_slot = current_match.get("player_slot", 0)
            is_radiant = player_slot < 128
            radiant_win = current_match.get("radiant_win", True)
            result = "🏆 WON" if (is_radiant == radiant_win) else "❌ LOST"

            payload = {
                "username": "Dota 2 Match Tracker",
                "avatar_url": "https://dotabuff.com",
                "embeds": [{
                    "title": f"👤 {player_name} just finished a game!",
                    "description": f"**Result:** {result}\n**KDA:** {kills}/{deaths}/{assists}",
                    "color": 3066993 if "WON" in result else 15158332,
                    "fields": [{"name": "Links", "value": f"[Dotabuff](https://dotabuff.com{player_id}) | [OpenDota](https://opendota.com{current_match_id})"}]
                }]
            }
            
            if DISCORD_WEBHOOK_URL:
                requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
            
            # Progressively update the txt cache file so network drops don't lose queue order
            save_last_match_id(player_id, current_match_id)

    except Exception as e:
        print(f"Error checking {player_name}: {e}")

if __name__ == "__main__":
    for pid, name in PLAYER_MAP.items():
        check_player_matches(pid, name)
