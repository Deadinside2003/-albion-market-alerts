
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
HOME_CITY = "Lymhurst"
TRAVEL_PROFIT_THRESHOLD = 30000
TRANSPORT_COST_PER_HORSE = 0
CITIES = [
    "Lymhurst",
    "Bridgewatch",
    "Martlock",
    "Fort Sterling",
    "Thetford",
    "Caerleon",
]
RIDING_CRAFT_COST = 0
ARMORED_CRAFT_COST = 0

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
    print("Scanning T6 horse markets...")
    prices = get_prices()

    names = {
        "T6_MOUNT_HORSE": "T6 Riding Horse",
        "T6_MOUNT_ARMORED_HORSE": "T6 Armored Horse",
    }

    craft_costs = {
        "T6_MOUNT_HORSE": RIDING_CRAFT_COST,
        "T6_MOUNT_ARMORED_HORSE": ARMORED_CRAFT_COST,
    }

    # Estimates only; adjust for your actual market fees.
    MARKET_FEE_RATE = 0.065

    messages = ["🐎 **Spidey Bot - T6 Horse Farm Report**"]
    candidates = []

    for item in ITEMS:
        city_prices = {}

        for entry in prices:
            if entry.get("item_id") != item:
                continue

            city = entry.get("city")
            price = entry.get("sell_price_min", 0)

            if city in CITIES and price > 0:
                city_prices[city] = price

        messages.append(f"\n**{names[item]}**")

        if HOME_CITY not in city_prices:
            messages.append(
                "⚠️ No Lymhurst listing available. "
                "Cannot evaluate travel threshold."
            )
            continue

        craft_cost = craft_costs[item]

        def net_return(city):
            price = city_prices[city]
            fees = round(price * MARKET_FEE_RATE)
            transport = (
                0 if city == HOME_CITY
                else TRANSPORT_COST_PER_HORSE
            )
            return price - fees - craft_cost - transport

        home_net = net_return(HOME_CITY)
        best_city = max(city_prices, key=net_return)
        best_net = net_return(best_city)
        extra = best_net - home_net

        if (
            best_city != HOME_CITY
            and extra >= TRAVEL_PROFIT_THRESHOLD
        ):
            chosen_city = best_city
            chosen_net = best_net
            travel_note = (
                f"🚚 Travel opportunity: +{extra:,} "
                "silver over Lymhurst"
            )
        else:
            chosen_city = HOME_CITY
            chosen_net = home_net
            travel_note = "🏡 Stay in Lymhurst"

        messages.append(
            f"🏡 Lymhurst listing: "
            f"{city_prices[HOME_CITY]:,} silver\n"
            f"📍 Recommended city: {chosen_city}\n"
            f"💰 Estimated net proceeds: "
            f"{chosen_net:,} silver\n"
            f"{travel_note}"
        )

        candidates.append(
            (chosen_net, names[item], chosen_city)
        )

    if candidates:
        best = max(candidates)
        messages.append(
            f"\n🏆 **Best mount: {best[1]}**\n"
            f"📍 Sell in: {best[2]}\n"
            f"💰 Estimated net proceeds: "
            f"{best[0]:,} silver"
        )
    else:
        messages.append(
            "\n⚠️ Insufficient Lymhurst market data."
        )

    messages.append(
        "\n⚠️ Estimates use listed asking prices, "
        "not guaranteed sales. Crafting and transport "
        "costs are currently placeholders."
    )

    now = datetime.now(timezone.utc)
    messages.append(
        "\n🕒 Scan: "
        + now.strftime("%Y-%m-%d %H:%M UTC")
    )

    send_discord("\n".join(messages))



if __name__ == "__main__":
    main()
