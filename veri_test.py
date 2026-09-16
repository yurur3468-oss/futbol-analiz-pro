import os
import requests

TOKEN = os.getenv("FOOTBALL_DATA_TOKEN")

if not TOKEN:
    print("API anahtarı bulunamadı!")
    exit()

url = "https://api.football-data.org/v4/matches"

headers = {
    "X-Auth-Token": TOKEN
}

response = requests.get(
    url,
    headers=headers
)

print("Durum kodu:", response.status_code)

if response.status_code != 200:
    print("API hatası:")
    print(response.text)
    exit()

data = response.json()

maclar = data.get("matches", [])

print()
print("======================================")
print("       API'DEN GELEN MAÇLAR")
print("======================================")
print()

print("Toplam maç:", len(maclar))
print()

for mac in maclar[:20]:

    lig = mac["competition"]["name"]
    ev_sahibi = mac["homeTeam"]["name"]
    deplasman = mac["awayTeam"]["name"]

    print("Lig:", lig)
    print(f"Maç: {ev_sahibi} - {deplasman}")
    print("--------------------------------------")