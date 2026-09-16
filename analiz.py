import os
import requests


TOKEN = os.getenv("FOOTBALL_DATA_TOKEN")

headers = {
    "X-Auth-Token": TOKEN
}


def takim_verisi(team_id):

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

    if response.status_code != 200:
        print("API hatası:", response.status_code)
        return None

    maclar = response.json().get("matches", [])

    galibiyet = 0
    beraberlik = 0
    maglubiyet = 0

    atilan = 0
    yenilen = 0

    for mac in maclar:

        ev = mac["homeTeam"]["name"]
        deplasman = mac["awayTeam"]["name"]

        skor = mac["score"]["fullTime"]

        ev_gol = skor["home"]
        deplasman_gol = skor["away"]

        if ev_gol is None or deplasman_gol is None:
            continue

        if ev == mac["homeTeam"]["name"]:

            takim_gol = ev_gol
            rakip_gol = deplasman_gol

        else:

            takim_gol = deplasman_gol
            rakip_gol = ev_gol

        atilan += takim_gol
        yenilen += rakip_gol

        if takim_gol > rakip_gol:
            galibiyet += 1

        elif takim_gol == rakip_gol:
            beraberlik += 1

        else:
            maglubiyet += 1

    toplam = galibiyet + beraberlik + maglubiyet

    if toplam == 0:
        return None

    return {
        "mac": toplam,
        "galibiyet": galibiyet,
        "beraberlik": beraberlik,
        "maglubiyet": maglubiyet,
        "atilan": atilan / toplam,
        "yenilen": yenilen / toplam
    }


def tahmin(ev_sahibi_id, deplasman_id):

    ev = takim_verisi(ev_sahibi_id)
    deplasman = takim_verisi(deplasman_id)

    if not ev or not deplasman:
        print("Yeterli veri bulunamadı.")
        return

    # Basit güç puanı
    ev_guc = (
        ev["galibiyet"] * 3
        + ev["beraberlik"]
        + ev["atilan"] * 2
        - ev["yenilen"]
    )

    deplasman_guc = (
        deplasman["galibiyet"] * 3
        + deplasman["beraberlik"]
        + deplasman["atilan"] * 2
        - deplasman["yenilen"]
    )

    # Ev sahibi avantajı
    ev_guc += 2

    toplam = ev_guc + deplasman_guc

    ev_olasilik = ev_guc / toplam
    deplasman_olasilik = deplasman_guc / toplam

    beraberlik_olasilik = 0.25

    ev_olasilik *= 0.75
    deplasman_olasilik *= 0.75

    print()
    print("======================================")
    print("           MAÇ TAHMİNİ")
    print("======================================")

    print()
    print("Ev sahibi:")
    print("Son 10 maç:", ev["mac"])
    print("Galibiyet:", ev["galibiyet"])
    print("Beraberlik:", ev["beraberlik"])
    print("Mağlubiyet:", ev["maglubiyet"])
    print("Gol ortalaması:", round(ev["atilan"], 2))

    print()
    print("Deplasman:")
    print("Son 10 maç:", deplasman["mac"])
    print("Galibiyet:", deplasman["galibiyet"])
    print("Beraberlik:", deplasman["beraberlik"])
    print("Mağlubiyet:", deplasman["maglubiyet"])
    print("Gol ortalaması:", round(deplasman["atilan"], 2))

    print()
    print("======================================")
    print("           OLASILIKLAR")
    print("======================================")

    print(
        "MS 1:",
        round(ev_olasilik * 100, 1),
        "%"
    )

    print(
        "BERABERLİK:",
        round(beraberlik_olasilik * 100, 1),
        "%"
    )

    print(
        "MS 2:",
        round(deplasman_olasilik * 100, 1),
        "%"
    )


# Arsenal - Chelsea
tahmin(57, 61)