"""Finds scheduled and live YouTube streams on the channels below and saves them to links.json.
The website (index.html) reads links.json and attaches each stream to the matching tournament day.
Needs one secret: YOUTUBE_API_KEY (free, from Google Cloud). No extra Python packages."""
import datetime
import json
import os
import sys
import urllib.parse
import urllib.request

KEY = os.environ.get("YOUTUBE_API_KEY")

# Channel IDs start with UC. To double-check one: open the channel on YouTube,
# click the description / About, then "Share channel" -> "Copy channel ID".
CHANNELS = {
    "PUBG MOBILE Esports": "UCmeeY9kzNswUpbYyJntb3Aw",
    "PUBG MOBILE Esports South Asia": "UCMus-ap67HdQVz_QMHtaxXw",
    "KRAFTON INDIA ESPORTS": "UCugG6-k5QGbq_iDEPAnG4NQ",
}

# Also ask YouTube's search for "upcoming" and "live" streams. Each search costs 100 quota units,
# so 3 channels x 2 searches x 12 runs a day = about 7,200 of the free 10,000 daily units.
SEARCH_STREAMS = True
KEEP_PAST_DAYS = 3     # keep streams that started up to 3 days ago
KEEP_FUTURE_DAYS = 45  # and streams scheduled up to 45 days ahead
OUT_FILE = "links.json"


def api(path, **params):
    params["key"] = KEY
    url = "https://www.googleapis.com/youtube/v3/" + path + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.load(resp)


def candidate_ids(channel_id):
    ids = set()
    try:  # cheap: the channel's uploads playlist (1 quota unit)
        data = api("playlistItems", part="contentDetails", playlistId="UU" + channel_id[2:], maxResults=50)
        ids.update(i["contentDetails"]["videoId"] for i in data.get("items", []))
    except Exception as err:
        print("  playlist lookup failed:", err)
    if SEARCH_STREAMS:
        for kind in ("upcoming", "live"):
            try:
                data = api("search", part="id", channelId=channel_id, eventType=kind, type="video", maxResults=50)
                found = [i["id"]["videoId"] for i in data.get("items", [])]
                print("  %s streams found: %d" % (kind, len(found)))
                ids.update(found)
            except Exception as err:
                print("  %s search failed: %s" % (kind, err))
    return ids


def video_details(ids):
    ids = sorted(ids)
    items = []
    for i in range(0, len(ids), 50):
        data = api("videos", part="snippet,liveStreamingDetails", id=",".join(ids[i:i + 50]))
        items.extend(data.get("items", []))
    return items


def main():
    if not KEY:
        sys.exit("YOUTUBE_API_KEY is not set.")
    now = datetime.datetime.now(datetime.timezone.utc)
    low = now - datetime.timedelta(days=KEEP_PAST_DAYS)
    high = now + datetime.timedelta(days=KEEP_FUTURE_DAYS)
    entries, ok_channels = [], 0
    for name, cid in CHANNELS.items():
        print("Checking", name)
        try:
            ids = candidate_ids(cid)
            for v in video_details(ids):
                live = v.get("liveStreamingDetails") or {}
                start = live.get("scheduledStartTime") or live.get("actualStartTime")
                if not start:
                    continue
                when = datetime.datetime.fromisoformat(start.replace("Z", "+00:00"))
                if not (low <= when <= high):
                    continue
                print("  +", v["snippet"]["title"], "|", start)
                entries.append({
                    "videoId": v["id"],
                    "title": v["snippet"]["title"],
                    "channel": name,
                    "url": "https://www.youtube.com/watch?v=" + v["id"],
                    "scheduledStart": start,
                    "state": v["snippet"].get("liveBroadcastContent", "none"),
                })
            ok_channels += 1
        except Exception as err:
            print("  failed:", err)
    if ok_channels == 0:
        sys.exit("No channel could be read. Keeping the old links.json.")
    entries.sort(key=lambda e: e["scheduledStart"])
    try:
        with open(OUT_FILE, encoding="utf-8") as f:
            old = json.load(f).get("videos", [])
    except Exception:
        old = []
    if old == entries:
        print("No changes.")
        return
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump({"updated": now.isoformat(timespec="seconds"), "videos": entries}, f, indent=2, ensure_ascii=False)
    print("Saved", len(entries), "streams to", OUT_FILE)


if __name__ == "__main__":
    main()
