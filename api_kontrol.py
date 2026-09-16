import os
import requests

TOKEN = os.getenv("FOOTBALL_DATA_TOKEN")

HEADERS = {
    "X-Auth-Token": TOKEN
}

url = "https://api.football-data.org/v4/matches"

params = {
    "status": "FINISHED"
}

response = requests.get(
    url,
    headers=HEADERS,
    params=params
)

print("HTTP DURUMU:", response.status_code)

if response.status_code == 200:

    data = response.json()

    maclar = data.get("matches", [])

    print()
    print("TOPLAM MAÇ:", len(maclar))
    print()

    for mac in maclar:

        ev = mac["homeTeam"].get("name")
        dep = mac["awayTeam"].get("name")

        ev_id = mac["homeTeam"].get("id")
        dep_id = mac["awayTeam"].get("id")

        skor = mac["score"]["fullTime"]

        print(
            ev,
            "(ID:", ev_id, ")",
            "-",
            dep,
            "(ID:", dep_id, ")",
            "|",
            skor.get("home"),
            "-",
            skor.get("away")
        )

else:

    print(response.text)