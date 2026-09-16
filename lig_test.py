import os
import requests

TOKEN = os.getenv("FOOTBALL_DATA_TOKEN")

HEADERS = {
    "X-Auth-Token": TOKEN
}

url = "https://api.football-data.org/v4/competitions/PL/standings"

response = requests.get(
    url,
    headers=HEADERS
)

print("HTTP DURUMU:", response.status_code)

if response.status_code == 200:

    data = response.json()

    print()
    print("LİG:", data.get("competition", {}).get("name"))

    standings = data.get("standings", [])

    print("STANDINGS SAYISI:", len(standings))

    for tablo in standings:

        if tablo.get("type") == "TOTAL":

            print()
            print("TAKIMLAR")
            print("--------------------------------")

            for takim in tablo.get("table", []):

                takim_adi = takim["team"].get("name")
                takim_id = takim["team"].get("id")

                oynanan = takim.get("playedGames")
                galibiyet = takim.get("won")
                beraberlik = takim.get("draw")
                maglubiyet = takim.get("lost")
                attigi = takim.get("goalsFor")
                yedigi = takim.get("goalsAgainst")
                puan = takim.get("points")

                print(
                    takim_adi,
                    "| ID:", takim_id,
                    "| O:", oynanan,
                    "| G:", galibiyet,
                    "| B:", beraberlik,
                    "| M:", maglubiyet,
                    "| AG:", attigi,
                    "| YG:", yedigi,
                    "| P:", puan
                )

else:

    print(response.text)