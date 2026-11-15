
import os
import json
import urllib.request
from urllib.parse import urlencode
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
    items = ",".join(ITEMS)
    params = urlencode({
        "locations": ",".join(CITIES)
    })
    url = (
        f"{BASE}/api/v2/stats/prices/"
        f"{items}.json?{params}"
    )

    with urllib.request.urlopen(
        url, timeout=30
    ) as response:
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
            "User-Agent": "AlbionMountScanner"
        },
        method="POST"
    )

    with urllib.request.urlopen(
        request, timeout=30
    ) as response:
        print("Discord status:", response.status)


def main():
    print("Scanning Albion mount markets...")
    prices = get_prices()

    names = {
        "T6_MOUNT_HORSE": "T6 Riding Horse",
        "T6_MOUNT_ARMORED_HORSE": "T6 Armored Horse"
    }

    messages = ["🐎 **Albion Mount Trading Scanner**"]

    for item in ITEMS:
        buy_options = []
        sell_options = []

        for entry in prices:
            if entry["item_id"] != item:
                continue

            city = entry["city"]
            sell_price = entry.get("sell_price_min", 0)
            buy_order = entry.get("buy_price_max", 0)

            if sell_price > 0:
                buy_options.append(
                    (sell_price, city)
                )

            if buy_order > 0:
                sell_options.append(
                    (buy_order, city)
                )

        messages.append(
            f"\n**{names[item]}**"
        )

        if not buy_options or not sell_options:
            messages.append(
                "Not enough market data."
            )
            continue

        cheapest = min(buy_options)
        highest = max(sell_options)

        buy_price, buy_city = cheapest
        sell_price, sell_city = highest

        gross_profit = sell_price - buy_price

        messages.append(
            f"🟢 Buy: {buy_city} — "
            f"{buy_price:,} silver\n"
            f"🔴 Sell: {sell_city} — "
            f"{sell_price:,} silver\n"
            f"💰 Gross spread: "
            f"{gross_profit:,} silver"
        )

        if gross_profit <= 0:
            messages.append(
                "⚠️ No positive spread found."
            )

    now = datetime.now(timezone.utc)
    messages.append(
        "\n🕒 Scan: "
        + now.strftime("%Y-%m-%d %H:%M UTC")
    )

    send_discord("\n".join(messages))


if __name__ == "__main__":
    main()
