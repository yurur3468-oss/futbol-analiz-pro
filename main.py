import os
import math
import requests
import tkinter as tk
from tkinter import ttk, messagebox


# =========================================================
# AYARLAR
# =========================================================

TOKEN = os.getenv("FOOTBALL_DATA_TOKEN")

HEADERS = {
    "X-Auth-Token": TOKEN
}

API_URL = "https://api.football-data.org/v4"

# API'den alınan verileri kısa süreli hafızada tutuyoruz.
# Böylece aynı takımı tekrar tekrar istemiyoruz.
TAKIM_CACHE = {}
PUAN_CACHE = {}


# =========================================================
# API İSTEĞİ
# =========================================================

def api_get(url, params=None):

    if not TOKEN:
        return None

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=20
        )

        if response.status_code != 200:

            print(
                "API Hatası:",
                response.status_code,
                response.text
            )

            return None

        return response.json()

    except Exception as hata:

        print("Bağlantı hatası:", hata)

        return None


# =========================================================
# POISSON
# =========================================================

def poisson(ortalama, gol):

    return (
        math.exp(-ortalama)
        * (ortalama ** gol)
        / math.factorial(gol)
    )


def poisson_analiz(ev_beklenen, dep_beklenen):

    ms1 = 0
    beraberlik = 0
    ms2 = 0

    ust25 = 0
    kg_var = 0

    skorlar = []

    for ev_gol in range(8):

        for dep_gol in range(8):

            olasilik = (
                poisson(ev_beklenen, ev_gol)
                *
                poisson(dep_beklenen, dep_gol)
            )

            skorlar.append(
                (
                    ev_gol,
                    dep_gol,
                    olasilik
                )
            )

            if ev_gol > dep_gol:
                ms1 += olasilik

            elif ev_gol == dep_gol:
                beraberlik += olasilik

            else:
                ms2 += olasilik

            if ev_gol + dep_gol >= 3:
                ust25 += olasilik

            if ev_gol >= 1 and dep_gol >= 1:
                kg_var += olasilik

    toplam = ms1 + beraberlik + ms2

    if toplam > 0:

        ms1 /= toplam
        beraberlik /= toplam
        ms2 /= toplam

    skorlar.sort(
        key=lambda x: x[2],
        reverse=True
    )

    return {
        "MS1": ms1,
        "X": beraberlik,
        "MS2": ms2,
        "Ust25": ust25,
        "Alt25": 1 - ust25,
        "KG_Var": kg_var,
        "KG_Yok": 1 - kg_var,
        "skorlar": skorlar[:5]
    }


# =========================================================
# TAKIM MAÇLARI
# =========================================================

def takim_maclarini_getir(team_id):

    if team_id in TAKIM_CACHE:
        return TAKIM_CACHE[team_id]

    url = f"{API_URL}/teams/{team_id}/matches"

    params = {
        "status": "FINISHED",
        "limit": 10
    }

    data = api_get(url, params)

    if not data:

        return []

    maclar = data.get(
        "matches",
        []
    )

    TAKIM_CACHE[team_id] = maclar

    return maclar


# =========================================================
# MAÇTAN TAKIMIN GOLLERİNİ BUL
# =========================================================

def takim_golleri(mac, team_id):

    skor = mac.get(
        "score",
        {}
    ).get(
        "fullTime",
        {}
    )

    ev_gol = skor.get("home")
    dep_gol = skor.get("away")

    if ev_gol is None or dep_gol is None:
        return None

    if mac.get("homeTeam", {}).get("id") == team_id:

        return ev_gol, dep_gol

    if mac.get("awayTeam", {}).get("id") == team_id:

        return dep_gol, ev_gol

    return None


# =========================================================
# FORM
# =========================================================

def form_hesapla(maclar, team_id):

    # En yeni maç önce gelecek şekilde sıralıyoruz.
    maclar = sorted(
        maclar,
        key=lambda x: x.get("utcDate", ""),
        reverse=True
    )

    puan = 0
    mac_sayisi = 0

    galibiyet = 0
    beraberlik = 0
    maglubiyet = 0

    form = []

    for mac in maclar:

        sonuc = takim_golleri(
            mac,
            team_id
        )

        if sonuc is None:
            continue

        attigi, yedigi = sonuc

        mac_sayisi += 1

        if attigi > yedigi:

            puan += 3
            galibiyet += 1
            form.append("G")

        elif attigi == yedigi:

            puan += 1
            beraberlik += 1
            form.append("B")

        else:

            maglubiyet += 1
            form.append("M")

        if mac_sayisi >= 10:
            break

    if mac_sayisi == 0:

        return {
            "puan": 0,
            "oran": 0,
            "galibiyet": 0,
            "beraberlik": 0,
            "maglubiyet": 0,
            "form": []
        }

    oran = puan / (
        mac_sayisi * 3
    )

    return {
        "puan": puan,
        "oran": oran,
        "galibiyet": galibiyet,
        "beraberlik": beraberlik,
        "maglubiyet": maglubiyet,
        "form": form
    }


# =========================================================
# AĞIRLIKLI GOL ORTALAMASI
# =========================================================

def agirlikli_gol_istatistigi(
    maclar,
    team_id,
    sadece_ev=None
):

    maclar = sorted(
        maclar,
        key=lambda x: x.get("utcDate", ""),
        reverse=True
    )

    veriler = []

    for mac in maclar:

        ev_id = mac.get(
            "homeTeam",
            {}
        ).get("id")

        dep_id = mac.get(
            "awayTeam",
            {}
        ).get("id")

        # Ev maçları isteniyorsa
        if sadece_ev is True:

            if ev_id != team_id:
                continue

        # Deplasman maçları isteniyorsa
        elif sadece_ev is False:

            if dep_id != team_id:
                continue

        sonuc = takim_golleri(
            mac,
            team_id
        )

        if sonuc is None:
            continue

        attigi, yedigi = sonuc

        veriler.append(
            (
                attigi,
                yedigi
            )
        )

        if len(veriler) >= 10:
            break

    if not veriler:

        return None

    # Yeni maç daha yüksek ağırlık alır.
    agirliklar = []

    for i in range(len(veriler)):

        agirliklar.append(
            len(veriler) - i
        )

    toplam_agirlik = sum(
        agirliklar
    )

    attigi_toplam = 0
    yedigi_toplam = 0

    for i, (attigi, yedigi) in enumerate(veriler):

        agirlik = agirliklar[i]

        attigi_toplam += (
            attigi * agirlik
        )

        yedigi_toplam += (
            yedigi * agirlik
        )

    return {
        "mac": len(veriler),
        "attigi": (
            attigi_toplam
            /
            toplam_agirlik
        ),
        "yedigi": (
            yedigi_toplam
            /
            toplam_agirlik
        )
    }


# =========================================================
# GOL TRENDİ
# =========================================================

def gol_trendi(maclar, team_id):

    maclar = sorted(
        maclar,
        key=lambda x: x.get("utcDate", ""),
        reverse=True
    )

    son5 = []
    onceki5 = []

    for mac in maclar:

        sonuc = takim_golleri(
            mac,
            team_id
        )

        if sonuc is None:
            continue

        son5.append(sonuc)

        if len(son5) >= 5:
            break

    for mac in maclar[5:]:

        sonuc = takim_golleri(
            mac,
            team_id
        )

        if sonuc is None:
            continue

        onceki5.append(sonuc)

        if len(onceki5) >= 5:
            break

    def ortalama(veriler):

        if not veriler:
            return 0

        return sum(
            x[0] for x in veriler
        ) / len(veriler)

    return {
        "son5_attigi": ortalama(son5),
        "onceki5_attigi": ortalama(onceki5)
    }


# =========================================================
# EV İSTATİSTİĞİ
# =========================================================

def ev_istatistikleri(team_id):

    maclar = takim_maclarini_getir(
        team_id
    )

    return agirlikli_gol_istatistigi(
        maclar,
        team_id,
        True
    )


# =========================================================
# DEPLASMAN İSTATİSTİĞİ
# =========================================================

def deplasman_istatistikleri(team_id):

    maclar = takim_maclarini_getir(
        team_id
    )

    return agirlikli_gol_istatistigi(
        maclar,
        team_id,
        False
    )


# =========================================================
# LİG PUAN DURUMU
# =========================================================

def lig_puan_durumu(competition_code):

    if not competition_code:
        return {}

    if competition_code in PUAN_CACHE:
        return PUAN_CACHE[competition_code]

    url = (
        f"{API_URL}/competitions/"
        f"{competition_code}/standings"
    )

    data = api_get(url)

    if not data:
        return {}

    takimlar = {}

    standings = data.get(
        "standings",
        []
    )

    for tablo in standings:

        if tablo.get("type") != "TOTAL":
            continue

        for satir in tablo.get(
            "table",
            []
        ):

            team = satir.get(
                "team",
                {}
            )

            team_id = team.get(
                "id"
            )

            if team_id is None:
                continue

            takimlar[team_id] = {
                "sira": satir.get(
                    "position",
                    0
                ),
                "puan": satir.get(
                    "points",
                    0
                )
            }

        break

    PUAN_CACHE[competition_code] = takimlar

    return takimlar


# =========================================================
# RAKİP GÜCÜ
# =========================================================

def rakip_gucu(maclar, team_id):

    toplam = 0
    sayi = 0

    for mac in maclar:

        if mac.get(
            "homeTeam",
            {}
        ).get("id") == team_id:

            rakip_id = mac.get(
                "awayTeam",
                {}
            ).get("id")

        elif mac.get(
            "awayTeam",
            {}
        ).get("id") == team_id:

            rakip_id = mac.get(
                "homeTeam",
                {}
            ).get("id")

        else:

            continue

        competition = mac.get(
            "competition",
            {}
        )

        code = competition.get(
            "code"
        )

        tablo = lig_puan_durumu(
            code
        )

        if rakip_id not in tablo:
            continue

        rakip = tablo[
            rakip_id
        ]

        sira = rakip.get(
            "sira",
            0
        )

        if sira <= 0:
            continue

        # İlk sıradaki rakip daha güçlü kabul edilir.
        # Etkiyi sınırlıyoruz.
        guc = max(
            0.75,
            min(
                1.25,
                1.25
                -
                ((sira - 1) * 0.02)
            )
        )

        toplam += guc
        sayi += 1

    if sayi == 0:
        return 1.0

    return toplam / sayi


# =========================================================
# YÜZDE
# =========================================================

def yuzde(orani):

    return f"%{orani * 100:.1f}"


# =========================================================
# GERÇEK ANALİZ
# =========================================================

def gercek_analiz(mac):

    if not TOKEN:

        messagebox.showerror(
            "API Anahtarı",
            "FOOTBALL_DATA_TOKEN bulunamadı."
        )

        return

    ev_id = mac["homeTeam"]["id"]
    dep_id = mac["awayTeam"]["id"]

    ev_adi = mac["homeTeam"]["name"]
    dep_adi = mac["awayTeam"]["name"]

    pencere.config(
        cursor="watch"
    )

    pencere.update()

    try:

        ev_maclar = takim_maclarini_getir(
            ev_id
        )

        dep_maclar = takim_maclarini_getir(
            dep_id
        )

        if not ev_maclar:

            messagebox.showwarning(
                "Veri",
                f"{ev_adi} için maç verisi bulunamadı."
            )

            return

        if not dep_maclar:

            messagebox.showwarning(
                "Veri",
                f"{dep_adi} için maç verisi bulunamadı."
            )

            return

        # =================================================
        # FORM
        # =================================================

        ev_form = form_hesapla(
            ev_maclar,
            ev_id
        )

        dep_form = form_hesapla(
            dep_maclar,
            dep_id
        )

        # =================================================
        # GENEL AĞIRLIKLI GOL
        # =================================================

        ev_genel = agirlikli_gol_istatistigi(
            ev_maclar,
            ev_id,
            None
        )

        dep_genel = agirlikli_gol_istatistigi(
            dep_maclar,
            dep_id,
            None
        )

        # =================================================
        # EV / DEPLASMAN
        # =================================================

        ev = ev_istatistikleri(
            ev_id
        )

        dep = deplasman_istatistikleri(
            dep_id
        )

        # =================================================
        # EV TAKIMININ EV VERİSİ YOKSA GENEL VERİ
        # =================================================

        if ev is None:
            ev = ev_genel

        if dep is None:
            dep = dep_genel

        if ev is None or dep is None:

            messagebox.showwarning(
                "Veri",
                "Yeterli maç verisi bulunamadı."
            )

            return

        # =================================================
        # GOL TRENDİ
        # =================================================

        ev_trend = gol_trendi(
            ev_maclar,
            ev_id
        )

        dep_trend = gol_trendi(
            dep_maclar,
            dep_id
        )

        # =================================================
        # TEMEL BEKLENEN GOL
        # =================================================

        beklenen_ev = (
            ev["attigi"]
            +
            dep["yedigi"]
        ) / 2

        beklenen_dep = (
            dep["attigi"]
            +
            ev["yedigi"]
        ) / 2

        # =================================================
        # FORM ETKİSİ
        # =================================================

        ev_form_etki = (
            0.90
            +
            ev_form["oran"]
            * 0.20
        )

        dep_form_etki = (
            0.90
            +
            dep_form["oran"]
            * 0.20
        )

        beklenen_ev *= ev_form_etki
        beklenen_dep *= dep_form_etki

        # =================================================
        # SON 5 MAÇ GOL TRENDİ
        # =================================================

        if ev_trend["onceki5_attigi"] > 0:

            fark = (
                ev_trend["son5_attigi"]
                -
                ev_trend["onceki5_attigi"]
            )

            fark = max(
                -0.30,
                min(
                    0.30,
                    fark
                )
            )

            beklenen_ev *= (
                1 + fark * 0.08
            )

        if dep_trend["onceki5_attigi"] > 0:

            fark = (
                dep_trend["son5_attigi"]
                -
                dep_trend["onceki5_attigi"]
            )

            fark = max(
                -0.30,
                min(
                    0.30,
                    fark
                )
            )

            beklenen_dep *= (
                1 + fark * 0.08
            )

        # =================================================
        # RAKİP GÜCÜ
        # =================================================

        ev_rakip_gucu = rakip_gucu(
            ev_maclar,
            ev_id
        )

        dep_rakip_gucu = rakip_gucu(
            dep_maclar,
            dep_id
        )

        # Güçlü rakiplere karşı alınan sonuçların
        # etkisini biraz artırıyoruz.
        beklenen_ev *= (
            0.96
            +
            ev_rakip_gucu * 0.04
        )

        beklenen_dep *= (
            0.96
            +
            dep_rakip_gucu * 0.04
        )

        # =================================================
        # MAKSİMUM SINIR
        # =================================================

        beklenen_ev = max(
            0.15,
            min(
                5.0,
                beklenen_ev
            )
        )

        beklenen_dep = max(
            0.15,
            min(
                5.0,
                beklenen_dep
            )
        )

        # =================================================
        # POISSON
        # =================================================

        sonuc = poisson_analiz(
            beklenen_ev,
            beklenen_dep
        )

    finally:

        pencere.config(
            cursor=""
        )

        pencere.update()

    # =====================================================
    # SONUÇ PENCERESİ
    # =====================================================

    sonuc_penceresi = tk.Toplevel(
        pencere
    )

    sonuc_penceresi.title(
        f"Gerçek Analiz - {ev_adi} vs {dep_adi}"
    )

    sonuc_penceresi.geometry(
        "900x950"
    )

    sonuc_penceresi.resizable(
        False,
        False
    )

    # =====================================================
    # BAŞLIK
    # =====================================================

    tk.Label(
        sonuc_penceresi,
        text=f"⚽ {ev_adi} - {dep_adi}",
        font=("Arial", 21, "bold")
    ).pack(
        pady=18
    )

    # =====================================================
    # İSTATİSTİK KUTUSU
    # =====================================================

    istatistik = tk.Frame(
        sonuc_penceresi
    )

    istatistik.pack(
        fill="x",
        padx=20
    )

    tk.Label(
        istatistik,
        text="EV SAHİBİ",
        font=("Arial", 13, "bold")
    ).grid(
        row=0,
        column=0,
        padx=100
    )

    tk.Label(
        istatistik,
        text="DEPLASMAN",
        font=("Arial", 13, "bold")
    ).grid(
        row=0,
        column=1,
        padx=100
    )

    ev_form_metni = "".join(
        ev_form["form"]
    )

    dep_form_metni = "".join(
        dep_form["form"]
    )

    ev_metni = (
        f"Genel maç: {ev_genel['mac']}\n"
        f"Ev maçları: {ev['mac']}\n"
        f"Galibiyet: {ev_form['galibiyet']}\n"
        f"Beraberlik: {ev_form['beraberlik']}\n"
        f"Mağlubiyet: {ev_form['maglubiyet']}\n"
        f"Attığı gol: {ev_genel['attigi']:.2f}\n"
        f"Yediği gol: {ev_genel['yedigi']:.2f}\n\n"
        f"FORM: {ev_form_metni}\n"
        f"FORM PUANI: {ev_form['puan']}\n"
        f"FORM: %{ev_form['oran'] * 100:.1f}\n\n"
        f"Rakip gücü: {ev_rakip_gucu:.2f}"
    )

    dep_metni = (
        f"Genel maç: {dep_genel['mac']}\n"
        f"Deplasman maçları: {dep['mac']}\n"
        f"Galibiyet: {dep_form['galibiyet']}\n"
        f"Beraberlik: {dep_form['beraberlik']}\n"
        f"Mağlubiyet: {dep_form['maglubiyet']}\n"
        f"Attığı gol: {dep_genel['attigi']:.2f}\n"
        f"Yediği gol: {dep_genel['yedigi']:.2f}\n\n"
        f"FORM: {dep_form_metni}\n"
        f"FORM PUANI: {dep_form['puan']}\n"
        f"FORM: %{dep_form['oran'] * 100:.1f}\n\n"
        f"Rakip gücü: {dep_rakip_gucu:.2f}"
    )

    tk.Label(
        istatistik,
        text=ev_metni,
        font=("Arial", 10),
        justify="center"
    ).grid(
        row=1,
        column=0,
        pady=10
    )

    tk.Label(
        istatistik,
        text=dep_metni,
        font=("Arial", 10),
        justify="center"
    ).grid(
        row=1,
        column=1,
        pady=10
    )

    # =====================================================
    # FORM TRENDİ
    # =====================================================

    ttk.Separator(
        sonuc_penceresi,
        orient="horizontal"
    ).pack(
        fill="x",
        padx=30,
        pady=8
    )

    tk.Label(
        sonuc_penceresi,
        text="📈 GOL TRENDİ",
        font=("Arial", 16, "bold")
    ).pack(
        pady=6
    )

    tk.Label(
        sonuc_penceresi,
        text=(
            f"{ev_adi} son 5 gol ort.: "
            f"{ev_trend['son5_attigi']:.2f}"
            f"     |     "
            f"{dep_adi} son 5 gol ort.: "
            f"{dep_trend['son5_attigi']:.2f}"
        ),
        font=("Arial", 11)
    ).pack(
        pady=3
    )

    # =====================================================
    # BEKLENEN GOL
    # =====================================================

    ttk.Separator(
        sonuc_penceresi,
        orient="horizontal"
    ).pack(
        fill="x",
        padx=30,
        pady=8
    )

    tk.Label(
        sonuc_penceresi,
        text="⚽ BEKLENEN GOL",
        font=("Arial", 16, "bold")
    ).pack(
        pady=7
    )

    tk.Label(
        sonuc_penceresi,
        text=(
            f"{ev_adi}: {beklenen_ev:.2f}"
            f"     |     "
            f"{dep_adi}: {beklenen_dep:.2f}"
        ),
        font=("Arial", 14)
    ).pack(
        pady=5
    )

    # =====================================================
    # MAÇ SONUCU
    # =====================================================

    tk.Label(
        sonuc_penceresi,
        text="🏆 MAÇ SONUCU OLASILIKLARI",
        font=("Arial", 16, "bold")
    ).pack(
        pady=10
    )

    tk.Label(
        sonuc_penceresi,
        text=f"MS 1       {yuzde(sonuc['MS1'])}",
        font=("Arial", 14)
    ).pack(
        pady=3
    )

    tk.Label(
        sonuc_penceresi,
        text=f"BERABERLİK       {yuzde(sonuc['X'])}",
        font=("Arial", 14)
    ).pack(
        pady=3
    )

    tk.Label(
        sonuc_penceresi,
        text=f"MS 2       {yuzde(sonuc['MS2'])}",
        font=("Arial", 14)
    ).pack(
        pady=3
    )

    # =====================================================
    # GOL ANALİZİ
    # =====================================================

    ttk.Separator(
        sonuc_penceresi,
        orient="horizontal"
    ).pack(
        fill="x",
        padx=30,
        pady=8
    )

    tk.Label(
        sonuc_penceresi,
        text="🥅 GOL ANALİZİ",
        font=("Arial", 16, "bold")
    ).pack(
        pady=7
    )

    tk.Label(
        sonuc_penceresi,
        text=f"2.5 ÜST       {yuzde(sonuc['Ust25'])}",
        font=("Arial", 13)
    ).pack(
        pady=3
    )

    tk.Label(
        sonuc_penceresi,
        text=f"2.5 ALT       {yuzde(sonuc['Alt25'])}",
        font=("Arial", 13)
    ).pack(
        pady=3
    )

    tk.Label(
        sonuc_penceresi,
        text=f"KG VAR       {yuzde(sonuc['KG_Var'])}",
        font=("Arial", 13)
    ).pack(
        pady=3
    )

    tk.Label(
        sonuc_penceresi,
        text=f"KG YOK       {yuzde(sonuc['KG_Yok'])}",
        font=("Arial", 13)
    ).pack(
        pady=3
    )

    # =====================================================
    # EN OLASI SKORLAR
    # =====================================================

    ttk.Separator(
        sonuc_penceresi,
        orient="horizontal"
    ).pack(
        fill="x",
        padx=30,
        pady=8
    )

    tk.Label(
        sonuc_penceresi,
        text="🎯 EN OLASI 5 SKOR",
        font=("Arial", 16, "bold")
    ).pack(
        pady=7
    )

    for ev_gol, dep_gol, olasilik in sonuc["skorlar"]:

        tk.Label(
            sonuc_penceresi,
            text=(
                f"{ev_gol} - {dep_gol}"
                f"     %{olasilik * 100:.2f}"
            ),
            font=("Arial", 12)
        ).pack(
            pady=2
        )

    # =====================================================
    # UYARI
    # =====================================================

    tk.Label(
        sonuc_penceresi,
        text=(
            "Bu sonuçlar istatistiksel model çıktılarıdır; "
            "kesin maç sonucu veya garanti değildir."
        ),
        font=("Arial", 9)
    ).pack(
        pady=15
    )


# =========================================================
# MAÇLARI GETİR
# =========================================================

def maclari_getir():

    if not TOKEN:

        messagebox.showerror(
            "API Anahtarı",
            "FOOTBALL_DATA_TOKEN bulunamadı."
        )

        return

    url = f"{API_URL}/matches"

    data = api_get(url)

    if not data:

        messagebox.showerror(
            "API Hatası",
            "Maç verileri alınamadı."
        )

        return

    maclar = data.get(
        "matches",
        []
    )

    for widget in mac_listesi.winfo_children():

        widget.destroy()

    if not maclar:

        tk.Label(
            mac_listesi,
            text="Maç bulunamadı.",
            font=("Arial", 13)
        ).pack(
            pady=20
        )

        return

    for mac in maclar:

        lig = mac.get(
            "competition",
            {}
        ).get(
            "name",
            "Bilinmeyen Lig"
        )

        ev = mac.get(
            "homeTeam",
            {}
        ).get(
            "name",
            "?"
        )

        dep = mac.get(
            "awayTeam",
            {}
        ).get(
            "name",
            "?"
        )

        kart = tk.Frame(
            mac_listesi,
            bd=2,
            relief="groove",
            padx=15,
            pady=12
        )

        kart.pack(
            fill="x",
            padx=20,
            pady=8
        )

        tk.Label(
            kart,
            text=lig,
            font=("Arial", 10, "bold")
        ).pack()

        tk.Label(
            kart,
            text=f"{ev}  -  {dep}",
            font=("Arial", 15, "bold")
        ).pack(
            pady=6
        )

        tk.Button(
            kart,
            text="🔍 GERÇEK ANALİZ ET",
            font=("Arial", 10, "bold"),
            command=lambda m=mac: gercek_analiz(m)
        ).pack()


# =========================================================
# ANA PENCERE
# =========================================================

pencere = tk.Tk()

pencere.title(
    "İddaa Maç Analiz Merkezi"
)

pencere.geometry(
    "1000x750"
)

pencere.minsize(
    850,
    600
)


tk.Label(
    pencere,
    text="⚽ İDDAA MAÇ ANALİZ MERKEZİ",
    font=("Arial", 24, "bold")
).pack(
    pady=20
)

tk.Label(
    pencere,
    text=(
        "Form + Ev/Deplasman + Gol Trendi "
        "+ Rakip Gücü + Poisson"
    ),
    font=("Arial", 12)
).pack()


tk.Button(
    pencere,
    text="🔄 MAÇLARI GETİR",
    font=("Arial", 13, "bold"),
    padx=20,
    pady=10,
    command=maclari_getir
).pack(
    pady=20
)


# =========================================================
# KAYDIRILABİLİR MAÇ LİSTESİ
# =========================================================

cerceve = tk.Frame(
    pencere
)

cerceve.pack(
    fill="both",
    expand=True,
    padx=30,
    pady=10
)

canvas = tk.Canvas(
    cerceve
)

kaydirma = ttk.Scrollbar(
    cerceve,
    orient="vertical",
    command=canvas.yview
)

mac_listesi = tk.Frame(
    canvas
)

mac_listesi.bind(
    "<Configure>",
    lambda e: canvas.configure(
        scrollregion=canvas.bbox("all")
    )
)

canvas.create_window(
    (0, 0),
    window=mac_listesi,
    anchor="nw"
)

canvas.configure(
    yscrollcommand=kaydirma.set
)

canvas.pack(
    side="left",
    fill="both",
    expand=True
)

kaydirma.pack(
    side="right",
    fill="y"
)


# =========================================================
# BAŞLAT
# =========================================================

pencere.mainloop()