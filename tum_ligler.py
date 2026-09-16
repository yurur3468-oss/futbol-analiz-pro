import os
import time
import requests
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta, timezone
import threading

# =========================================================
# AYARLAR
# =========================================================

TOKEN = os.getenv("FOOTBALL_DATA_TOKEN")

BASE_URL = "https://api.football-data.org/v4"

MIN_REQUEST_INTERVAL = 6.5
SON_ISTEK = 0

MACLAR = []


# =========================================================
# API
# =========================================================

def api_get(endpoint, params=None):

    global SON_ISTEK

    if not TOKEN:
        raise Exception(
            "API anahtarı bulunamadı."
        )

    gecen = time.time() - SON_ISTEK

    if gecen < MIN_REQUEST_INTERVAL:
        time.sleep(
            MIN_REQUEST_INTERVAL - gecen
        )

    headers = {
        "X-Auth-Token": TOKEN
    }

    url = BASE_URL + endpoint

    for deneme in range(2):

        SON_ISTEK = time.time()

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=30
        )

        if response.status_code == 200:
            return response.json()

        if response.status_code == 429:

            retry_after = response.headers.get(
                "Retry-After"
            )

            try:
                bekle = int(retry_after)
            except:
                bekle = 30

            durum.config(
                text=f"⚠ API limiti. {bekle} saniye bekleniyor..."
            )

            pencere.update_idletasks()

            time.sleep(bekle)

            continue

        raise Exception(
            f"API Hatası: {response.status_code}\n\n"
            f"{response.text[:500]}"
        )

    raise Exception(
        "API isteği başarısız oldu."
    )


# =========================================================
# TARİHLER
# =========================================================

def tarihleri_hesapla():

    bugun = datetime.now(
        timezone.utc
    ).date()

    baslangic = bugun

    bitis = bugun + timedelta(
        days=7
    )

    return (
        baslangic.isoformat(),
        bitis.isoformat()
    )


# =========================================================
# LİGLER
# =========================================================

def ligleri_getir():

    data = api_get(
        "/competitions"
    )

    return data.get(
        "competitions",
        []
    )


# =========================================================
# TÜM LİGLERDEN MAÇLARI GETİR
# =========================================================

def maclari_topla():

    buton.config(
        state="disabled"
    )

    liste.delete(
        0,
        tk.END
    )

    MACLAR.clear()

    def calistir():

        try:

            # ---------------------------------------------
            # TARİH ARALIĞI
            # ---------------------------------------------

            baslangic, bitis = tarihleri_hesapla()

            durum.config(
                text=(
                    f"Maçlar aranıyor: "
                    f"{baslangic} → {bitis}"
                )
            )

            pencere.update_idletasks()

            # ---------------------------------------------
            # LİGLER
            # ---------------------------------------------

            competitions = ligleri_getir()

            toplam_lig = len(
                competitions
            )

            if toplam_lig == 0:

                raise Exception(
                    "Erişilebilir lig bulunamadı."
                )

            durum.config(
                text=f"{toplam_lig} lig bulundu."
            )

            pencere.update_idletasks()

            # ---------------------------------------------
            # MAÇLARI TEKRARSIZ TOPLA
            # ---------------------------------------------

            tum_maclar = {}

            for sira, lig in enumerate(
                competitions,
                start=1
            ):

                code = lig.get(
                    "code"
                )

                lig_adi = lig.get(
                    "name",
                    "Bilinmeyen Lig"
                )

                if not code:
                    continue

                durum.config(
                    text=(
                        f"Lig {sira}/{toplam_lig}: "
                        f"{lig_adi}"
                    )
                )

                pencere.update_idletasks()

                try:

                    data = api_get(
                        "/matches",
                        {
                            "competitions": code,
                            "dateFrom": baslangic,
                            "dateTo": bitis
                        }
                    )

                    matches = data.get(
                        "matches",
                        []
                    )

                    for mac in matches:

                        mac_id = mac.get(
                            "id"
                        )

                        if mac_id:
                            tum_maclar[
                                mac_id
                            ] = mac

                except Exception as e:

                    print(
                        f"{lig_adi} hatası:",
                        e
                    )

                    continue

            # ---------------------------------------------
            # SIRALA
            # ---------------------------------------------

            MACLAR.extend(
                tum_maclar.values()
            )

            MACLAR.sort(
                key=lambda x: x.get(
                    "utcDate",
                    ""
                )
            )

            # ---------------------------------------------
            # EKRANA YAZ
            # ---------------------------------------------

            for mac in MACLAR:

                competition = mac.get(
                    "competition",
                    {}
                ).get(
                    "name",
                    "?"
                )

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

                tarih = mac.get(
                    "utcDate",
                    ""
                )

                # Tarihi daha okunabilir yap
                try:

                    dt = datetime.fromisoformat(
                        tarih.replace(
                            "Z",
                            "+00:00"
                        )
                    )

                    tarih_goster = dt.strftime(
                        "%d.%m.%Y %H:%M"
                    )

                except:

                    tarih_goster = tarih

                satir = (
                    f"{tarih_goster} | "
                    f"{competition} | "
                    f"{home} - {away}"
                )

                liste.insert(
                    tk.END,
                    satir
                )

            # ---------------------------------------------
            # SONUÇ
            # ---------------------------------------------

            durum.config(
                text=(
                    f"✅ {toplam_lig} lig tarandı. "
                    f"{len(MACLAR)} maç bulundu."
                )
            )

            messagebox.showinfo(
                "Maçlar Hazır",
                (
                    f"{toplam_lig} lig tarandı.\n\n"
                    f"Tarih aralığı:\n"
                    f"{baslangic} → {bitis}\n\n"
                    f"Bulunan maç: {len(MACLAR)}"
                )
            )

        except Exception as e:

            messagebox.showerror(
                "Hata",
                str(e)
            )

            durum.config(
                text="Hata oluştu."

            )

        finally:

            buton.config(
                state="normal"
            )

    threading.Thread(
        target=calistir,
        daemon=True
    ).start()


# =========================================================
# ARAYÜZ
# =========================================================

pencere = tk.Tk()

pencere.title(
    "İddaa Analiz - Tüm Ligler"
)

pencere.geometry(
    "1150x700"
)

# =========================================================
# BAŞLIK
# =========================================================

baslik = tk.Label(
    pencere,
    text="🌍 TÜM LİGLER - 7 GÜNLÜK MAÇ TARAMA",
    font=("Arial", 18, "bold")
)

baslik.pack(
    pady=20
)

# =========================================================
# BUTON
# =========================================================

buton = tk.Button(
    pencere,
    text="🔄 MAÇLARI GETİR",
    font=("Arial", 13, "bold"),
    command=maclari_topla,
    width=30,
    height=2
)

buton.pack(
    pady=10
)

# =========================================================
# DURUM
# =========================================================

durum = tk.Label(
    pencere,
    text="Hazır.",
    font=("Arial", 11)
)

durum.pack(
    pady=10
)

# =========================================================
# İLERLEME
# =========================================================

progress = ttk.Progressbar(
    pencere,
    orient="horizontal",
    length=850,
    mode="indeterminate"
)

progress.pack(
    pady=5
)

# =========================================================
# MAÇ LİSTESİ
# =========================================================

liste = tk.Listbox(
    pencere,
    font=("Arial", 10)
)

liste.pack(
    fill="both",
    expand=True,
    padx=20,
    pady=20
)

# =========================================================
# BAŞLAT
# =========================================================

pencere.mainloop()