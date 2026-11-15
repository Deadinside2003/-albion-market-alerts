
import os
import json
import urllib.request
from datetime import datetime, timezone

WEBHOOK = os.environ["DISCORD_WEBHOOK_URL"]

BASE = "https://west.albion-online-data.com"

ITEMS = [
    "T6_MOUNT_HORSE",
    "T6_MOUNT_ARMORED_HORSE",
]

CITIES = [
    "Lymhurst",
    "Bridgewatch",
    "Martlock",
    "Fort Sterling",
    "Thetford",
    "Caerleon",
]

def get_prices():
    url = (
        f"{BASE}/api/v2/stats/prices/"
        f"{','.join(ITEMS)}.json"
        f"?locations={','.join(CITIES)}"
    )

    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)

def send_discord(message):
    payload = json.dumps({
        "username": "Spidey Bot",
        "content": message
    }).encode("utf-8")

    request = urllib.request.Request(
        WEBHOOK,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "AlbionMountScanner/1.0"
        },
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        print("Discord HTTP status:", response.status)

def main():
    print("Starting Albion market scanner")

    prices = get_prices()
    now = datetime.now(timezone.utc)

    lines = ["🐎 **Albion Americas Mount Market**"]

    for item in ITEMS:
        for city in CITIES:
            matches = [
                p for p in prices
                if p["item_id"] == item
                and p["city"] == city
                and p["sell_price_min"] > 0
            ]

            if not matches:
                continue

            p = matches[0]

            try:
                updated = datetime.fromisoformat(
                    p["sell_price_min_date"].replace("Z", "+00:00")
                )

                if updated.tzinfo is None:
                    updated = updated.replace(tzinfo=timezone.utc)

                if (now - updated).total_seconds() > 7200:
                    continue

            except (ValueError, TypeError, AttributeError):
                continue

            lines.append(
                f"**{item}** | {city}: "
                f"{p['sell_price_min']:,} silver"
            )

    if len(lines) == 1:
        lines.append("No fresh mount prices found.")

    send_discord("\n".join(lines[:35]))
    print("Scanner finished successfully")

if __name__ == "__main__":
    main()

