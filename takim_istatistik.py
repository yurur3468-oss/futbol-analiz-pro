import os
import requests
from datetime import datetime, timedelta


TOKEN = os.getenv("FOOTBALL_DATA_TOKEN")

HEADERS = {
    "X-Auth-Token": TOKEN
}


def takim_maclarini_getir(team_id):

    bugun = datetime.utcnow().date()

    # Son 60 günlük maçları kontrol edeceğiz
    baslangic = bugun - timedelta(days=60)

    tum_takim_maclari = []

    # API en fazla 10 günlük dönem kabul ediyor
    mevcut_baslangic = baslangic

    while mevcut_baslangic < bugun:

        mevcut_bitis = min(
            mevcut_baslangic + timedelta(days=9),
            bugun
        )

        url = "https://api.football-data.org/v4/matches"

        params = {
            "status": "FINISHED",
            "dateFrom": str(mevcut_baslangic),
            "dateTo": str(mevcut_bitis),
            "limit": 100
        }

        print(
            "Veri alınıyor:",
            mevcut_baslangic,
            "->",
            mevcut_bitis
        )

        response = requests.get(
            url,
            headers=HEADERS,
            params=params
        )

        if response.status_code != 200:

            print(
                "API Hatası:",
                response.status_code
            )

            print(response.text)

            mevcut_baslangic = (
                mevcut_bitis +
                timedelta(days=1)
            )

            continue

        maclar = response.json().get(
            "matches",
            []
        )

        for mac in maclar:

            ev_id = mac["homeTeam"].get("id")
            dep_id = mac["awayTeam"].get("id")

            if ev_id == team_id or dep_id == team_id:

                tum_takim_maclari.append(mac)

        mevcut_baslangic = (
            mevcut_bitis +
            timedelta(days=1)
        )

    return tum_takim_maclari


def ev_istatistikleri(team_id):

    maclar = takim_maclarini_getir(team_id)

    ev_maclari = []

    for mac in maclar:

        if mac["homeTeam"].get("id") == team_id:

            skor = mac["score"]["fullTime"]

            ev_gol = skor.get("home")
            dep_gol = skor.get("away")

            if ev_gol is not None and dep_gol is not None:

                ev_maclari.append({
                    "attigi": ev_gol,
                    "yedigi": dep_gol
                })

    return ev_maclari


def deplasman_istatistikleri(team_id):

    maclar = takim_maclarini_getir(team_id)

    deplasman_maclari = []

    for mac in maclar:

        if mac["awayTeam"].get("id") == team_id:

            skor = mac["score"]["fullTime"]

            ev_gol = skor.get("home")
            dep_gol = skor.get("away")

            if ev_gol is not None and dep_gol is not None:

                deplasman_maclari.append({
                    "attigi": dep_gol,
                    "yedigi": ev_gol
                })

    return deplasman_maclari


def ortalamalari_hesapla(maclar):

    if len(maclar) == 0:

        return {
            "mac": 0,
            "attigi": 0,
            "yedigi": 0
        }

    toplam_attigi = sum(
        mac["attigi"]
        for mac in maclar
    )

    toplam_yedigi = sum(
        mac["yedigi"]
        for mac in maclar
    )

    return {
        "mac": len(maclar),
        "attigi": toplam_attigi / len(maclar),
        "yedigi": toplam_yedigi / len(maclar)
    }


# TEST
if __name__ == "__main__":

    # Arsenal = 57

    arsenal_id = 57

    print()
    print("================================")
    print(" ARSENAL EV İSTATİSTİKLERİ")
    print("================================")

    ev = ev_istatistikleri(arsenal_id)

    ev_ort = ortalamalari_hesapla(ev)

    print()
    print("Maç sayısı:", ev_ort["mac"])

    print(
        "Maç başına attığı gol:",
        round(ev_ort["attigi"], 2)
    )

    print(
        "Maç başına yediği gol:",
        round(ev_ort["yedigi"], 2)
    )


    print()
    print("================================")
    print(" ARSENAL DEPLASMAN İSTATİSTİKLERİ")
    print("================================")

    dep = deplasman_istatistikleri(arsenal_id)

    dep_ort = ortalamalari_hesapla(dep)

    print()
    print("Maç sayısı:", dep_ort["mac"])

    print(
        "Maç başına attığı gol:",
        round(dep_ort["attigi"], 2)
    )

    print(
        "Maç başına yediği gol:",
        round(dep_ort["yedigi"], 2)
    )