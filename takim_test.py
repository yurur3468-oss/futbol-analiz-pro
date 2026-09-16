import os
import requests

TOKEN = os.getenv("FOOTBALL_DATA_TOKEN")

if not TOKEN:
    print("API anahtarı bulunamadı!")
    exit()

headers = {
    "X-Auth-Token": TOKEN
}

# Örnek olarak Arsenal takımını test ediyoruz
team_id = 57

url = f"https://api.football-data.org/v4/teams/{team_id}/matches"

params = {
    "status": "FINISHED",
    "limit": 10
}

response = requests.get(
    url,
    headers=headers,
    params=params
)

print("Durum kodu:", response.status_code)

if response.status_code != 200:
    print(response.text)
    exit()

data = response.json()

maclar = data.get("matches", [])

print()
print("SON 10 MAÇ")
print("==============================")

for mac in maclar:

    tarih = mac["utcDate"][:10]

    ev = mac["homeTeam"]["name"]

    deplasman = mac["awayTeam"]["name"]

    skor = mac["score"]["fullTime"]

    ev_gol = skor["home"]

    deplasman_gol = skor["away"]

    print()
    print(tarih)
    print(f"{ev} {ev_gol} - {deplasman_gol} {deplasman}")