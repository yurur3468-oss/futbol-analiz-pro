import math


def poisson(ortalama, gol):
    """
    Poisson dağılımı:
    Belirli bir gol sayısının gerçekleşme olasılığını hesaplar.
    """
    return (math.exp(-ortalama) * (ortalama ** gol)) / math.factorial(gol)


def mac_analizi(ev_sahibi_gol, deplasman_gol):
    """
    Beklenen gol değerlerinden maç olasılıklarını hesaplar.
    """

    ev_kazanir = 0
    beraberlik = 0
    deplasman_kazanir = 0

    ust_25 = 0
    kg_var = 0

    skorlar = []

    # 0-6 gol arası tüm skorları hesapla
    for ev_gol in range(7):
        for dep_gol in range(7):

            olasilik_ev = poisson(ev_sahibi_gol, ev_gol)
            olasilik_dep = poisson(deplasman_gol, dep_gol)

            olasilik = olasilik_ev * olasilik_dep

            skorlar.append(
                (ev_gol, dep_gol, olasilik)
            )

            # Maç sonucu
            if ev_gol > dep_gol:
                ev_kazanir += olasilik

            elif ev_gol == dep_gol:
                beraberlik += olasilik

            else:
                deplasman_kazanir += olasilik

            # 2.5 ÜST
            if ev_gol + dep_gol >= 3:
                ust_25 += olasilik

            # KG VAR
            if ev_gol >= 1 and dep_gol >= 1:
                kg_var += olasilik

    # En yüksek ihtimalli skor
    skorlar.sort(
        key=lambda x: x[2],
        reverse=True
    )

    en_olasi_skor = skorlar[0]

    return {
        "MS1": ev_kazanir,
        "X": beraberlik,
        "MS2": deplasman_kazanir,
        "Ust25": ust_25,
        "Alt25": 1 - ust_25,
        "KG_Var": kg_var,
        "KG_Yok": 1 - kg_var,
        "En_Olası_Skor": en_olasi_skor
    }


# TEST
if __name__ == "__main__":

    # Örnek:
    # Ev sahibi 1.70 gol bekleniyor
    # Deplasman 1.10 gol bekleniyor

    sonuc = mac_analizi(1.70, 1.10)

    print("\n--- POISSON ANALİZİ ---")

    print(
        "MS1:",
        round(sonuc["MS1"] * 100, 2),
        "%"
    )

    print(
        "Beraberlik:",
        round(sonuc["X"] * 100, 2),
        "%"
    )

    print(
        "MS2:",
        round(sonuc["MS2"] * 100, 2),
        "%"
    )

    print(
        "2.5 ÜST:",
        round(sonuc["Ust25"] * 100, 2),
        "%"
    )

    print(
        "2.5 ALT:",
        round(sonuc["Alt25"] * 100, 2),
        "%"
    )

    print(
        "KG VAR:",
        round(sonuc["KG_Var"] * 100, 2),
        "%"
    )

    print(
        "KG YOK:",
        round(sonuc["KG_Yok"] * 100, 2),
        "%"
    )

    skor = sonuc["En_Olası_Skor"]

    print(
        "En olası skor:",
        skor[0],
        "-",
        skor[1],
        "(",
        round(skor[2] * 100, 2),
        "%)"
    )