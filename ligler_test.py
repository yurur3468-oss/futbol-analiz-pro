import os
import requests

TOKEN = os.getenv("FOOTBALL_DATA_TOKEN")

if not TOKEN:
    print("API ANAHTARI BULUNAMADI!")
    input("Kapatmak için Enter'a bas...")
    exit()

headers = {
    "X-Auth-Token": TOKEN
}

url = "https://api.football-data.org/v4/competitions"

try:

    response = requests.get(
        url,
        headers=headers,
        timeout=30
    )

    print("API DURUMU:", response.status_code)
    print()

    if response.status_code != 200:
        print("API HATASI:")
        print(response.text)
    else:

        data = response.json()

        competitions = data.get(
            "competitions",
            []
        )

        print(
            "HESABINDA ERİŞİLEBİLEN LİGLER:"
        )
        print("=" * 60)

        for lig in competitions:

            name = lig.get(
                "name",
                "?"
            )

            country = lig.get(
                "area",
                {}
            ).get(
                "name",
                "?"
            )

            code = lig.get(
                "code",
                "?"
            )

            print(
                f"{country:<25} | "
                f"{name:<35} | "
                f"{code}"
            )

        print("=" * 60)

        print(
            f"Toplam erişilebilir lig: "
            f"{len(competitions)}"
        )

except Exception as e:

    print("HATA:")
    print(e)

input()