#!/usr/bin/env python3
import requests
import json
import datetime
import os

# Your API key and channel ID
API_KEY = "AIzaSyBUS5CZsLNM_dBCy-8DLHFdlRyMR4fZ4nI"
CHANNEL_ID = "UC8ZwxRUAvDsaC_dI7azemYw"

# Output file
OUTPUT_FILE = "youtube_stats.json"

def fetch_stats():
    url = f"https://www.googleapis.com/youtube/v3/channels?part=statistics&id={CHANNEL_ID}&key={API_KEY}"
    response = requests.get(url).json()

    if "items" not in response:
        print("Error fetching stats:", response)
        return None

    stats = response["items"][0]["statistics"]
    stats["date"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return stats

def save_stats(stats):
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r") as f:
            data = json.load(f)
    else:
        data = []

    data.append(stats)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=4)

if __name__ == "__main__":
    stats = fetch_stats()
    if stats:
        save_stats(stats)
        print("Saved stats:", stats)

