import os
import requests

print("=" * 60)
print("API-FOOTBALL BAĞLANTI TESTİ")
print("=" * 60)

api_key = os.getenv("API_FOOTBALL_KEY", "").strip()

print("API anahtarı kontrol ediliyor...")

if not api_key:
    print("❌ API_FOOTBALL_KEY BULUNAMADI!")
    input("Çıkmak için Enter...")
    raise SystemExit

print(f"✅ API anahtarı bulundu. Uzunluk: {len(api_key)}")
print("🔄 API-FOOTBALL'a bağlanılıyor...")

url = "https://v3.football.api-sports.io/fixtures"

headers = {
    "x-apisports-key": api_key,
    "Accept": "application/json"
}

params = {
    "date": "2026-09-16",
    "timezone": "Europe/Istanbul"
}

try:
    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=30
    )

    print()
    print("HTTP:", response.status_code)
    print("-" * 60)

    data = response.json()

    print("API GET:", data.get("get"))
    print("SONUÇ SAYISI:", data.get("results"))
    print("HATALAR:", data.get("errors"))

    if response.status_code == 200 and not data.get("errors"):
        print()
        print("✅✅✅ API BAĞLANTISI BAŞARILI! ✅✅✅")
        print()
        print(f"Bugün {data.get('results', 0)} maç bulundu.")

        maclar = data.get("response", [])

        for mac in maclar[:10]:
            home = mac.get("teams", {}).get("home", {}).get("name", "?")
            away = mac.get("teams", {}).get("away", {}).get("name", "?")

            print(f"⚽ {home} - {away}")

    else:
        print()
        print("❌ API BAĞLANTISINDA HATA VAR.")
        print()
        print("API'nin gönderdiği hata:")
        print(data.get("errors"))

except requests.exceptions.RequestException as e:
    print()
    print("❌ INTERNET/API BAĞLANTI HATASI:")
    print(e)

except Exception as e:
    print()
    print("❌ BEKLENMEYEN HATA:")
    print(e)

print()
input("Çıkmak için Enter...")