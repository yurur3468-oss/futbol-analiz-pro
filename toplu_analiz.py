import os
import time
import math
import threading
import requests
import tkinter as tk
from tkinter import ttk, messagebox

# =========================================================
# AYARLAR
# =========================================================

TOKEN = os.getenv("FOOTBALL_DATA_TOKEN")

BASE_URL = "https://api.football-data.org/v4"

# API'yi fazla sık kullanmamak için
MIN_REQUEST_INTERVAL = 6.5

# Takım verilerini hafızada tut
TAKIM_CACHE = {}

# Son API isteğinin zamanı
SON_ISTEK_ZAMANI = 0

# =========================================================
# API İSTEĞİ
# =========================================================

def api_get(endpoint, params=None):
    global SON_ISTEK_ZAMANI

    if not TOKEN:
        raise Exception("API anahtarı bulunamadı.")

    # İki API isteği arasında bekle
    simdi = time.time()
    gecen = simdi - SON_ISTEK_ZAMANI

    if gecen < MIN_REQUEST_INTERVAL:
        bekle = MIN_REQUEST_INTERVAL - gecen
        time.sleep(bekle)

    headers = {
        "X-Auth-Token": TOKEN
    }

    url = BASE_URL + endpoint

    for deneme in range(2):

        try:
            SON_ISTEK_ZAMANI = time.time()

            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=30
            )

            # Başarılı
            if response.status_code == 200:
                return response.json()

            # 429 = API limiti
            if response.status_code == 429:

                retry_after = response.headers.get("Retry-After")

                if retry_after:
                    try:
                        bekleme = int(retry_after)
                    except:
                        bekleme = 30
                else:
                    bekleme = 30

                durum_yaz(
                    f"⚠ API limiti doldu. {bekleme} saniye bekleniyor..."
                )

                time.sleep(bekleme)

                continue

            # 403
            if response.status_code == 403:
                raise Exception(
                    "API 403 hatası: API anahtarı veya erişim yetkisi reddedildi."
                )

            # 400
            if response.status_code == 400:
                raise Exception(
                    "API 400 hatası: İstek geçersiz."
                )

            raise Exception(
                f"API Hatası: {response.status_code}\n"
                f"{response.text[:300]}"
            )

        except requests.exceptions.Timeout:
            if deneme == 0:
                durum_yaz("⚠ API zaman aşımı. Tekrar deneniyor...")
                time.sleep(5)
            else:
                raise Exception("API bağlantısı zaman aşımına uğradı.")

        except requests.exceptions.RequestException as e:
            raise Exception(f"İnternet/API bağlantı hatası:\n{e}")

    raise Exception("API isteği başarısız oldu.")


# =========================================================
# TAKIM MAÇLARI
# =========================================================

def takim_maclari(team_id):

    # Daha önce alınmışsa tekrar API'ye gitme
    if team_id in TAKIM_CACHE:
        return TAKIM_CACHE[team_id]

    durum_yaz(f"Takım verisi alınıyor: {team_id}")

    data = api_get(
        f"/teams/{team_id}/matches",
        {
            "status": "FINISHED",
            "limit": 10
        }
    )

    matches = data.get("matches", [])

    TAKIM_CACHE[team_id] = matches

    return matches


# =========================================================
# TAKIM İSTATİSTİKLERİ
# =========================================================

def takim_istatistik(team_id):

    matches = takim_maclari(team_id)

    if not matches:
        return {
            "gf": 1.0,
            "ga": 1.0,
            "form": 0.5,
            "over": 0.5,
            "btts": 0.5
        }

    toplam_gol = 0
    toplam_yenilen = 0

    puan = 0
    over_sayisi = 0
    btts_sayisi = 0

    sayi = 0

    for mac in matches:

        home = mac.get("homeTeam", {})
        away = mac.get("awayTeam", {})

        score = mac.get("score", {})
        full = score.get("fullTime", {})

        hg = full.get("home")
        ag = full.get("away")

        if hg is None or ag is None:
            continue

        hg = int(hg)
        ag = int(ag)

        team_id_mac = team_id

        if home.get("id") == team_id_mac:

            attigi = hg
            yedigi = ag

            if hg > ag:
                puan += 3
            elif hg == ag:
                puan += 1

        else:

            attigi = ag
            yedigi = hg

            if ag > hg:
                puan += 3
            elif ag == hg:
                puan += 1

        toplam_gol += attigi
        toplam_yenilen += yedigi

        if hg + ag > 2:
            over_sayisi += 1

        if hg > 0 and ag > 0:
            btts_sayisi += 1

        sayi += 1

    if sayi == 0:
        return {
            "gf": 1.0,
            "ga": 1.0,
            "form": 0.5,
            "over": 0.5,
            "btts": 0.5
        }

    return {
        "gf": toplam_gol / sayi,
        "ga": toplam_yenilen / sayi,
        "form": puan / (sayi * 3),
        "over": over_sayisi / sayi,
        "btts": btts_sayisi / sayi
    }


# =========================================================
# EV / DEPLASMAN İSTATİSTİĞİ
# =========================================================

def ev_deplasman_istatistik(team_id, ev_mi):

    matches = takim_maclari(team_id)

    gf = 0
    ga = 0
    sayi = 0

    for mac in matches:

        home = mac.get("homeTeam", {})
        away = mac.get("awayTeam", {})

        score = mac.get("score", {})
        full = score.get("fullTime", {})

        hg = full.get("home")
        ag = full.get("away")

        if hg is None or ag is None:
            continue

        if ev_mi:

            if home.get("id") != team_id:
                continue

            gf += hg
            ga += ag

        else:

            if away.get("id") != team_id:
                continue

            gf += ag
            ga += hg

        sayi += 1

    if sayi == 0:

        # Ev/deplasman verisi yoksa genel ortalamayı kullan
        genel = takim_istatistik(team_id)

        return {
            "gf": genel["gf"],
            "ga": genel["ga"]
        }

    return {
        "gf": gf / sayi,
        "ga": ga / sayi
    }


# =========================================================
# POISSON
# =========================================================

def poisson(k, lamb):

    return (
        math.exp(-lamb)
        * (lamb ** k)
        / math.factorial(k)
    )


# =========================================================
# MAÇ ANALİZİ
# =========================================================

def mac_analiz(mac):

    home = mac.get("homeTeam", {})
    away = mac.get("awayTeam", {})

    home_id = home.get("id")
    away_id = away.get("id")

    home_name = home.get("name", "Ev Sahibi")
    away_name = away.get("name", "Deplasman")

    # Takım istatistikleri
    ev = takim_istatistik(home_id)
    dep = takim_istatistik(away_id)

    # Ev / deplasman
    ev_saha = ev_deplasman_istatistik(
        home_id,
        True
    )

    dep_saha = ev_deplasman_istatistik(
        away_id,
        False
    )

    # Beklenen goller
    ev_gol = (
        ev_saha["gf"] * 0.55
        + dep_saha["ga"] * 0.45
    )

    dep_gol = (
        dep_saha["gf"] * 0.55
        + ev_saha["ga"] * 0.45
    )

    # Form etkisi
    ev_gol *= (
        0.85
        + ev["form"] * 0.30
    )

    dep_gol *= (
        0.85
        + dep["form"] * 0.30
    )

    # Aşırı uçları sınırla
    ev_gol = max(0.2, min(ev_gol, 4.0))
    dep_gol = max(0.2, min(dep_gol, 4.0))

    # Olasılıklar
    ms1 = 0
    beraberlik = 0
    ms2 = 0

    ust25 = 0
    kg = 0

    skorlar = []

    for i in range(7):

        p_home = poisson(i, ev_gol)

        for j in range(7):

            p_away = poisson(j, dep_gol)

            p = p_home * p_away

            if i > j:
                ms1 += p

            elif i == j:
                beraberlik += p

            else:
                ms2 += p

            if i + j >= 3:
                ust25 += p

            if i > 0 and j > 0:
                kg += p

            skorlar.append(
                (
                    p,
                    f"{i}-{j}"
                )
            )

    skorlar.sort(
        reverse=True,
        key=lambda x: x[0]
    )

    en_iyi_skor = skorlar[0][1]

    # Yüzdeye çevir
    ms1 *= 100
    beraberlik *= 100
    ms2 *= 100
    ust25 *= 100
    kg *= 100

    return {
        "home": home_name,
        "away": away_name,
        "home_goals": ev_gol,
        "away_goals": dep_gol,
        "ms1": ms1,
        "x": beraberlik,
        "ms2": ms2,
        "over25": ust25,
        "btts": kg,
        "score": en_iyi_skor
    }


# =========================================================
# MAÇLARI GETİR
# =========================================================

def maclari_getir():

    try:

        durum_yaz("Maçlar getiriliyor...")

        data = api_get(
            "/matches",
            {
                "status": "SCHEDULED"
            }
        )

        matches = data.get("matches", [])

        # Listeyi temizle
        liste.delete(
            0,
            tk.END
        )

        for mac in matches:

            home = mac.get(
                "homeTeam",
                {}
            ).get(
                "name",
                "?"
            )

            away = mac.get(
                "awayTeam",
                {}
            ).get(
                "name",
                "?"
            )

            competition = mac.get(
                "competition",
                {}
            ).get(
                "name",
                "?"
            )

            liste.insert(
                tk.END,
                f"{competition} | {home} - {away}"
            )

        global MACLAR
        MACLAR = matches

        durum_yaz(
            f"{len(matches)} maç bulundu."
        )

    except Exception as e:

        messagebox.showerror(
            "API Hatası",
            str(e)
        )

        durum_yaz(
            "Maçlar alınamadı."
        )


# =========================================================
# TOPLU ANALİZ
# =========================================================

def toplu_analiz():

    if not MACLAR:

        messagebox.showwarning(
            "Uyarı",
            "Önce MAÇLARI GETİR butonuna bas."
        )

        return

    buton_analiz.config(
        state="disabled"
    )

    buton_getir.config(
        state="disabled"
    )

    tablo.delete(
        *tablo.get_children()
    )

    def calistir():

        try:

            toplam = len(MACLAR)

            # =================================================
            # 1. ADIM
            # Benzersiz takımları bul
            # =================================================

            takimlar = {}

            for mac in MACLAR:

                home_id = mac.get(
                    "homeTeam",
                    {}
                ).get("id")

                away_id = mac.get(
                    "awayTeam",
                    {}
                ).get("id")

                if home_id:
                    takimlar[home_id] = True

                if away_id:
                    takimlar[away_id] = True

            takim_listesi = list(
                takimlar.keys()
            )

            toplam_takim = len(
                takim_listesi
            )

            durum_yaz(
                f"{toplam} maç / {toplam_takim} takım hazırlanıyor..."
            )

            # =================================================
            # 2. ADIM
            # Takım verilerini bir kere çek
            # =================================================

            for sira, team_id in enumerate(
                takim_listesi,
                start=1
            ):

                try:

                    takim_maclari(team_id)

                    yuzde = (
                        sira
                        / toplam_takim
                        * 100
                    )

                    progress["value"] = yuzde

                    durum_yaz(
                        f"Takım verileri: "
                        f"{sira}/{toplam_takim}"
                    )

                    pencere.update_idletasks()

                except Exception as e:

                    durum_yaz(
                        f"⚠ Takım verisi alınamadı: "
                        f"{team_id}"
                    )

            # =================================================
            # 3. ADIM
            # Maç analizleri
            # =================================================

            durum_yaz(
                "Maç analizleri başlıyor..."
            )

            for sira, mac in enumerate(
                MACLAR,
                start=1
            ):

                try:

                    sonuc = mac_analiz(mac)

                    competition = mac.get(
                        "competition",
                        {}
                    ).get(
                        "name",
                        "?"
                    )

                    tablo.insert(
                        "",
                        tk.END,
                        values=(
                            competition,
                            f"{sonuc['home']} - {sonuc['away']}",
                            f"%{sonuc['ms1']:.1f}",
                            f"%{sonuc['x']:.1f}",
                            f"%{sonuc['ms2']:.1f}",
                            f"%{sonuc['over25']:.1f}",
                            f"%{sonuc['btts']:.1f}",
                            sonuc["score"]
                        )
                    )

                    progress["value"] = (
                        sira
                        / toplam
                        * 100
                    )

                    durum_yaz(
                        f"Maç analiz ediliyor: "
                        f"{sira}/{toplam}"
                    )

                    pencere.update_idletasks()

                except Exception as e:

                    durum_yaz(
                        f"⚠ Maç analiz hatası: {e}"
                    )

            durum_yaz(
                f"✅ Tamamlandı: {toplam} maç analiz edildi."
            )

            messagebox.showinfo(
                "Tamamlandı",
                f"{toplam} maç analiz edildi."
            )

        except Exception as e:

            messagebox.showerror(
                "Hata",
                str(e)
            )

        finally:

            buton_analiz.config(
                state="normal"
            )

            buton_getir.config(
                state="normal"
            )

    threading.Thread(
        target=calistir,
        daemon=True
    ).start()


# =========================================================
# DURUM YAZISI
# =========================================================

def durum_yaz(mesaj):

    pencere.after(
        0,
        lambda: durum.config(
            text=mesaj
        )
    )


# =========================================================
# ARAYÜZ
# =========================================================

MACLAR = []

pencere = tk.Tk()

pencere.title(
    "İddaa Analiz - Toplu Maç Analizi"
)

pencere.geometry(
    "1250x700"
)

pencere.minsize(
    1000,
    600
)

# ---------------------------------------------------------
# ÜST BUTONLAR
# ---------------------------------------------------------

ust = tk.Frame(
    pencere
)

ust.pack(
    pady=15
)

buton_getir = tk.Button(
    ust,
    text="🔄 MAÇLARI GETİR",
    font=("Arial", 12, "bold"),
    command=maclari_getir,
    width=20
)

buton_getir.pack(
    side="left",
    padx=10
)

buton_analiz = tk.Button(
    ust,
    text="🚀 TÜM MAÇLARI ANALİZ ET",
    font=("Arial", 12, "bold"),
    command=toplu_analiz,
    width=25
)

buton_analiz.pack(
    side="left",
    padx=10
)

# ---------------------------------------------------------
# İLERLEME ÇUBUĞU
# ---------------------------------------------------------

progress = ttk.Progressbar(
    pencere,
    orient="horizontal",
    length=900,
    mode="determinate"
)

progress.pack(
    pady=10
)

# ---------------------------------------------------------
# DURUM
# ---------------------------------------------------------

durum = tk.Label(
    pencere,
    text="Hazır.",
    font=("Arial", 11)
)

durum.pack(
    pady=5
)

# ---------------------------------------------------------
# MAÇ LİSTESİ
# ---------------------------------------------------------

liste = tk.Listbox(
    pencere,
    height=8,
    font=("Arial", 10)
)

liste.pack(
    fill="x",
    padx=20,
    pady=10
)

# ---------------------------------------------------------
# TABLO
# ---------------------------------------------------------

kolonlar = (
    "Lig",
    "Maç",
    "MS1",
    "X",
    "MS2",
    "Üst2.5",
    "KG",
    "Skor"
)

tablo = ttk.Treeview(
    pencere,
    columns=kolonlar,
    show="headings",
    height=18
)

for kolon in kolonlar:

    tablo.heading(
        kolon,
        text=kolon
    )

    if kolon == "Maç":
        tablo.column(
            kolon,
            width=300
        )

    elif kolon == "Lig":
        tablo.column(
            kolon,
            width=180
        )

    else:
        tablo.column(
            kolon,
            width=90,
            anchor="center"
        )

tablo.pack(
    fill="both",
    expand=True,
    padx=20,
    pady=10
)

# ---------------------------------------------------------
# BAŞLAT
# ---------------------------------------------------------

pencere.mainloop()