import os
import math
import threading
import time
import unicodedata
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests


# ============================================================
# AYARLAR
# ============================================================

API_URL = "https://v3.football.api-sports.io"
TIMEZONE = "Europe/Istanbul"

# ============================================================
# PROFESYONEL ARAYÜZ TEMASI
# ============================================================
BG = "#0b1220"
PANEL = "#111c2e"
PANEL_2 = "#16243a"
CARD = "#17263d"
CARD_HOVER = "#1d304d"
TEXT = "#f8fafc"
MUTED = "#94a3b8"
ACCENT = "#38bdf8"
ACCENT_2 = "#22c55e"
WARNING = "#f59e0b"
DANGER = "#ef4444"
BORDER = "#263852"
WHITE = "#ffffff"


def api_anahtari_yukle():
    """Web sürümü için API anahtarını ortam değişkeni veya api_key.txt dosyasından alır.
    Streamlit sunucusunda GUI/Tkinter penceresi açmaz.
    """
    anahtar = (os.getenv("API_FOOTBALL_KEY") or "").strip()
    if anahtar:
        return anahtar

    try:
        dosya = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_key.txt")
        if os.path.exists(dosya):
            with open(dosya, "r", encoding="utf-8-sig") as f:
                anahtar = f.read().strip()
            if anahtar:
                return anahtar
    except Exception:
        pass

    return None


API_KEY = api_anahtari_yukle()

if not API_KEY:
    # Web arayüzü bu durumu kullanıcıya gösterecek; import sırasında uygulamayı kilitleme.
    API_KEY = ""


# ============================================================
# API
# ============================================================

def _anahtar_dosyasi():
    try:
        return os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "api_key.txt"
        )
    except Exception:
        return "api_key.txt"


def _anahtar_oku():
    """Anahtarı ortam değişkeninden veya api_key.txt dosyasından yeniden okur."""
    anahtar = (os.getenv("API_FOOTBALL_KEY") or "").strip()
    if anahtar:
        return anahtar

    try:
        dosya = _anahtar_dosyasi()
        if os.path.exists(dosya):
            with open(dosya, "r", encoding="utf-8-sig") as f:
                return f.read().strip()
    except Exception:
        pass

    return ""


def _anahtar_iste():
    """Web sürümünde Tkinter ile anahtar istemez."""
    return False




def api_get(endpoint, params=None, _anahtar_yenile=True):

    global API_KEY

    # Her çağrıda ortam değişkenini kontrol et. Böylece VS Code terminalinde
    # anahtar sonradan ayarlanmış olsa bile uygulama güncel anahtarı kullanır.
    taze_anahtar = _anahtar_oku()
    if taze_anahtar:
        API_KEY = taze_anahtar

    headers = {
        "x-apisports-key": (API_KEY or "").strip(),
        "Accept": "application/json",
        "User-Agent": "IddaaMacAnalizMerkezi/1.0"
    }

    # API-Football bazen yoğunluk nedeniyle bağlantıyı geç tamamlayabilir.
    # Tek denemede analizi düşürmek yerine kısa bağlantı + daha uzun okuma
    # zaman aşımı ve kontrollü tekrar deniyoruz.
    last_error = None
    for deneme in range(3):
        try:
            response = requests.get(
                API_URL + "/" + endpoint,
                headers=headers,
                params=params or {},
                timeout=(10, 45)
            )
            break
        except (requests.Timeout, requests.ConnectionError, requests.RequestException) as e:
            last_error = e
            if deneme < 2:
                time.sleep(1.5 * (deneme + 1))
                continue
            raise Exception(
                "İnternet/API bağlantı hatası\n\n"
                f"API-Football yanıtı zamanında gelmedi: {e}\n\n"
                "Bağlantı tekrar denendi (3/3). Analiz verileri korunuyor; "
                "lütfen tekrar ANALİZ butonuna basın."
            )

    try:
        data = response.json()
    except Exception:
        raise Exception(
            f"API geçersiz cevap verdi.\n"
            f"HTTP: {response.status_code}"
        )

    errors = data.get("errors") or {}

    # API anahtarı bu işlemde ulaşmadıysa, ortam değişkeni ile GUI/EXE
    # arasındaki farkı gidermek için uygulama içinden bir kez yeni anahtar al.
    if (
        _anahtar_yenile
        and isinstance(errors, dict)
        and any(
            "missing application key" in str(v).lower()
            or "invalid api key" in str(v).lower()
            or "unauthorized" in str(v).lower()
            for v in errors.values()
        )
    ):
        if _anahtar_iste():
            return api_get(
                endpoint,
                params=params,
                _anahtar_yenile=False
            )

    if response.status_code != 200:
        raise Exception(
            f"API HTTP Hatası: {response.status_code}\n"
            f"{errors or data}"
        )

    if errors:
        if isinstance(errors, dict):
            hata = " | ".join(
                f"{k}: {v}"
                for k, v in errors.items()
            )
        else:
            hata = str(errors)

        raise Exception(hata)

    return data.get("response", [])


# ============================================================
# TARİH
# ============================================================

def bugunun_tarihi():

    return datetime.now(
        ZoneInfo(TIMEZONE)
    ).strftime("%Y-%m-%d")


def tarih_gecerli_mi(tarih):

    try:
        datetime.strptime(
            tarih,
            "%Y-%m-%d"
        )
        return True
    except ValueError:
        return False


def tarih_degistir(gun):

    try:

        tarih = datetime.strptime(
            tarih_var.get(),
            "%Y-%m-%d"
        )

        yeni_tarih = tarih + timedelta(
            days=gun
        )

        tarih_var.set(
            yeni_tarih.strftime("%Y-%m-%d")
        )

        tum_maclari_getir()

    except Exception:

        messagebox.showerror(
            "Tarih Hatası",
            "Tarih formatı YYYY-MM-DD olmalı."
        )


def bugun():

    tarih_var.set(
        bugunun_tarihi()
    )

    tum_maclari_getir()


# ============================================================
# TAKIM ARAMA
# ============================================================

def takim_ara():

    isim = takim_ara_var.get().strip()

    if len(isim) < 3:
        messagebox.showwarning(
            "Takım Arama",
            "En az 3 harf yazmalısın."
        )
        return

    arama_butonu.config(state="disabled")

    def normalize(text):
        text = str(text or "").strip().lower()
        return "".join(
            c for c in unicodedata.normalize("NFKD", text)
            if not unicodedata.combining(c)
        )

    def worker():
        try:
            aramalar = [isim]
            sade = normalize(isim)
            if sade and sade != isim:
                aramalar.append(sade)

            bulunan = {}
            for sorgu in aramalar:
                try:
                    takimlar = api_get("teams", {"search": sorgu})
                except Exception:
                    continue
                for item in takimlar:
                    takim = item.get("team", {})
                    takim_id = takim.get("id")
                    takim_adi = takim.get("name")
                    ulke = takim.get("country")
                    if takim_id and takim_adi:
                        bulunan[int(takim_id)] = (
                            f"{takim_adi} | {ulke or 'Bilinmiyor'} | ID: {takim_id}"
                        )

            sonuc = list(bulunan.values())

            def guncelle():
                arama_butonu.config(state="normal")
                takim_combo["values"] = sonuc
                if sonuc:
                    takim_combo.current(0)
                    takim_bilgisi_var.set(f"{len(sonuc)} takım bulundu.")
                else:
                    takim_bilgisi_var.set("Takım bulunamadı.")
                    messagebox.showinfo(
                        "Sonuç",
                        "Bu isimle takım bulunamadı. Takımın resmi İngilizce adını da deneyebilirsin."
                    )

            root.after(0, guncelle)

        except Exception as exc:
            hata_mesaji = str(exc)
            root.after(
                0,
                lambda: (
                    arama_butonu.config(state="normal"),
                    messagebox.showerror("API Hatası", hata_mesaji)
                )
            )

    threading.Thread(target=worker, daemon=True).start()


def secili_takim_id():

    secim = takim_combo.get().strip()

    if not secim:
        return None

    try:

        return int(
            secim.split("ID:")[-1].strip()
        )

    except Exception:

        return None


def secili_takim_adi():

    secim = takim_combo.get().strip()

    if not secim:
        return ""

    try:
        return secim.split("|")[0].strip()
    except Exception:
        return secim


# ============================================================
# SEÇİLEN TAKIMIN SEÇİLEN GÜNDEKİ MAÇLARI
# ============================================================

def takim_maclarini_getir(
    team_id,
    tarih
):

    # Season hatasını önlemek için
    # önce günün tüm maçlarını alıyoruz.

    tum_maclar = api_get(
        "fixtures",
        {
            "date": tarih,
            "timezone": TIMEZONE
        }
    )

    sonuc = []

    for mac in tum_maclar:

        try:

            home_id = mac["teams"]["home"]["id"]
            away_id = mac["teams"]["away"]["id"]

            if (
                home_id == team_id
                or away_id == team_id
            ):

                sonuc.append(mac)

        except Exception:

            continue

    return sonuc


def takim_maclarini_yukle():

    team_id = secili_takim_id()

    if not team_id:

        messagebox.showwarning(
            "Takım Seç",
            "Önce takım arayıp bir takım seç."
        )

        return

    tarih = tarih_var.get()

    if not tarih_gecerli_mi(tarih):

        messagebox.showerror(
            "Tarih Hatası",
            "Tarih YYYY-MM-DD formatında olmalı."
        )

        return

    takim_adi = secili_takim_adi()

    takim_mac_butonu.config(
        state="disabled"
    )

    liste_temizle()

    baslik_var.set(
        f"🔎 {takim_adi} | {tarih}"
    )

    durum_var.set(
        "Takımın maçları aranıyor..."
    )

    def worker():

        try:

            maclar = takim_maclarini_getir(
                team_id,
                tarih
            )

            def guncelle():

                takim_mac_butonu.config(
                    state="normal"
                )

                liste_temizle()

                if not maclar:

                    durum_var.set(
                        "Bu tarihte maç bulunamadı."
                    )

                    return

                durum_var.set(
                    f"{len(maclar)} maç bulundu."
                )

                maclari_listeye_ekle(
                    maclar
                )

            root.after(
                0,
                guncelle
            )

        except Exception as exc:

            hata_mesaji = str(exc)

            def hata():

                takim_mac_butonu.config(
                    state="normal"
                )

                messagebox.showerror(
                    "API Hatası",
                    hata_mesaji
                )

                durum_var.set(
                    "Maçlar alınamadı."
                )

            root.after(
                0,
                hata
            )

    threading.Thread(
        target=worker,
        daemon=True
    ).start()


# ============================================================
# GÜNÜN TÜM MAÇLARI
# ============================================================

def tum_maclari_getir():

    tarih = tarih_var.get()

    if not tarih_gecerli_mi(tarih):

        messagebox.showerror(
            "Tarih Hatası",
            "Tarih YYYY-MM-DD formatında olmalı."
        )

        return

    tarih_getir_butonu.config(
        state="disabled"
    )

    liste_temizle()

    baslik_var.set(
        f"⚽ {tarih} GÜNÜN MAÇLARI"
    )

    durum_var.set(
        "Tüm liglerin maçları getiriliyor..."
    )

    def worker():

        try:

            maclar = api_get(
                "fixtures",
                {
                    "date": tarih,
                    "timezone": TIMEZONE
                }
            )

            def guncelle():

                tarih_getir_butonu.config(
                    state="normal"
                )

                liste_temizle()

                maclari_listeye_ekle(
                    maclar
                )

                durum_var.set(
                    f"{len(maclar)} maç bulundu."
                )

            root.after(
                0,
                guncelle
            )

        except Exception as exc:

            hata_mesaji = str(exc)

            def hata():

                tarih_getir_butonu.config(
                    state="normal"
                )

                messagebox.showerror(
                    "API Hatası",
                    hata_mesaji
                )

                durum_var.set(
                    "Maçlar alınamadı."
                )

            root.after(
                0,
                hata
            )

    threading.Thread(
        target=worker,
        daemon=True
    ).start()


# ============================================================
# MAÇ LİSTESİ
# ============================================================

def liste_temizle():

    for widget in mac_frame.winfo_children():
        widget.destroy()


def maclari_listeye_ekle(maclar):

    if not maclar:

        tk.Label(
            mac_frame,
            text="⚽  Bu tarih için maç bulunamadı.",
            bg=BG, fg=MUTED,
            font=("Segoe UI", 12)
        ).pack(pady=40)

        return

    gruplar = {}

    for mac in maclar:

        lig = mac.get(
            "league",
            {}
        )

        ulke = lig.get(
            "country",
            "Bilinmeyen Ülke"
        )

        lig_adi = lig.get(
            "name",
            "Bilinmeyen Lig"
        )

        anahtar = (
            f"{ulke} - {lig_adi}"
        )

        if anahtar not in gruplar:
            gruplar[anahtar] = []

        gruplar[anahtar].append(mac)

    for grup_adi in sorted(
        gruplar.keys()
    ):

        grup_label = tk.Label(
            mac_frame,
            text=f"🌍  {grup_adi.upper()}",
            bg=BG, fg=ACCENT,
            font=("Segoe UI", 10, "bold"),
            anchor="w"
        )

        grup_label.pack(
            fill="x",
            padx=10,
            pady=(12, 5)
        )

        for mac in gruplar[grup_adi]:

            mac_butonu_olustur(
                mac
            )


def mac_saati(mac):

    try:

        tarih = mac["fixture"]["date"]

        dt = datetime.fromisoformat(
            tarih.replace(
                "Z",
                "+00:00"
            )
        )

        dt = dt.astimezone(
            ZoneInfo(TIMEZONE)
        )

        return dt.strftime("%H:%M")

    except Exception:

        return "--:--"


def mac_butonu_olustur(mac):
    home = mac["teams"]["home"]
    away = mac["teams"]["away"]
    home_adi = home.get("name", "Ev Sahibi")
    away_adi = away.get("name", "Deplasman")
    skor_home = mac["goals"].get("home")
    skor_away = mac["goals"].get("away")
    saat = mac_saati(mac)

    if skor_home is not None and skor_away is not None:
        skor = f"{skor_home} - {skor_away}"
        durum = "TAMAMLANDI"
        durum_fg = MUTED
    else:
        skor = "VS"
        durum = "PROGRAMDA"
        durum_fg = ACCENT

    card = tk.Frame(mac_frame, bg=CARD, highlightbackground=BORDER,
                    highlightthickness=1, bd=0)
    card.pack(fill="x", padx=14, pady=5)

    time_box = tk.Frame(card, bg=PANEL_2, width=100)
    time_box.pack(side="left", fill="y", padx=8, pady=8)
    time_box.pack_propagate(False)

    tk.Label(time_box, text=saat, bg=PANEL_2, fg=TEXT,
             font=("Segoe UI", 15, "bold")).pack(pady=(9, 0))
    tk.Label(time_box, text=durum, bg=PANEL_2, fg=durum_fg,
             font=("Segoe UI", 7, "bold")).pack(pady=(2, 8))

    teams_box = tk.Frame(card, bg=CARD)
    teams_box.pack(side="left", fill="both", expand=True, padx=12, pady=10)

    tk.Label(teams_box, text=home_adi, bg=CARD, fg=TEXT,
             font=("Segoe UI", 12, "bold"), anchor="e").grid(
                 row=0, column=0, sticky="e", padx=(0, 18))
    tk.Label(teams_box, text=skor, bg=CARD, fg=ACCENT,
             font=("Segoe UI", 16, "bold"), width=7).grid(
                 row=0, column=1)
    tk.Label(teams_box, text=away_adi, bg=CARD, fg=TEXT,
             font=("Segoe UI", 12, "bold"), anchor="w").grid(
                 row=0, column=2, sticky="w", padx=(18, 0))

    teams_box.grid_columnconfigure(0, weight=1)
    teams_box.grid_columnconfigure(2, weight=1)

    analyze_btn = tk.Button(
        card, text="ANALİZ  →",
        font=("Segoe UI", 10, "bold"),
        bg=ACCENT, fg="#06111f",
        activebackground="#7dd3fc", activeforeground="#06111f",
        relief="flat", bd=0, cursor="hand2",
        padx=18, pady=10,
        command=lambda m=mac: mac_analizi(m)
    )
    analyze_btn.pack(side="right", padx=12, pady=10)

    def hover_on(_event):
        card.configure(bg=CARD_HOVER)
        teams_box.configure(bg=CARD_HOVER)
        for child in teams_box.winfo_children():
            child.configure(bg=CARD_HOVER)

    def hover_off(_event):
        card.configure(bg=CARD)
        teams_box.configure(bg=CARD)
        for child in teams_box.winfo_children():
            child.configure(bg=CARD)

    for widget in (card, teams_box):
        widget.bind("<Enter>", hover_on)
        widget.bind("<Leave>", hover_off)


# ============================================================
# SON 10 MAÇ
# ============================================================

def takim_son_maclari(team_id):
    """Son 10 maçı güvenli şekilde getirir ve aynı analiz içinde tekrar çağırmaz."""
    try:
        team_id = int(team_id)
    except Exception:
        return []

    if team_id in _TEAM_LAST_MATCHES_CACHE:
        return _TEAM_LAST_MATCHES_CACHE[team_id]

    try:
        maclar = api_get(
            "fixtures",
            {
                "team": team_id,
                "last": 10,
                "timezone": TIMEZONE
            }
        )
        maclar = maclar or []
        _TEAM_LAST_MATCHES_CACHE[team_id] = maclar
        return maclar
    except Exception:
        # Ağ geçici olarak cevap vermiyorsa burada sessizce boş veri dönmek
        # yerine üst katmanın anlamlı hata mesajı göstermesine izin ver.
        raise


def takim_form(team_id):

    maclar = takim_son_maclari(team_id)

    galibiyet = beraberlik = maglubiyet = 0
    atilan = yenilen = 0
    kg = over15 = over25 = 0

    agirlikli_kg = agirlikli_over15 = agirlikli_over25 = 0.0
    agirlikli_gf = agirlikli_ga = 0.0
    agirlikli_fh_over05 = agirlikli_fh_over15 = 0.0
    agirlikli_fh_gf = agirlikli_fh_ga = 0.0
    fh_gf = fh_ga = fh_over05 = fh_over15 = 0
    fh_oynanan = 0
    agirlik_toplam = 0.0
    oynanan = 0

    for sira, mac in enumerate(maclar):
        home_id = mac["teams"]["home"]["id"]
        away_id = mac["teams"]["away"]["id"]

        gh = mac["goals"].get("home")
        ga = mac["goals"].get("away")

        if gh is None or ga is None:
            continue

        oynanan += 1

        if home_id == team_id:
            gf, gk = gh, ga
            if gh > ga:
                galibiyet += 1
            elif gh == ga:
                beraberlik += 1
            else:
                maglubiyet += 1
        else:
            gf, gk = ga, gh
            if ga > gh:
                galibiyet += 1
            elif ga == gh:
                beraberlik += 1
            else:
                maglubiyet += 1

        atilan += gf
        yenilen += gk

        # API genellikle en yeni maçı ilk sırada verir.
        # Son maçlara daha fazla ağırlık veriyoruz.
        agirlik = 1.0 + max(0, 9 - min(sira, 9)) * 0.10
        agirlik_toplam += agirlik
        agirlikli_gf += gf * agirlik
        agirlikli_ga += gk * agirlik

        if gh > 0 and ga > 0:
            kg += 1
            agirlikli_kg += agirlik

        if gh + ga >= 2:
            over15 += 1
            agirlikli_over15 += agirlik

        if gh + ga >= 3:
            over25 += 1
            agirlikli_over25 += agirlik

        # İlk yarı gol verisi API-Football fixture cevabındaki halftime alanından gelir.
        # Veri yoksa maçı ilk yarı örneklemine dahil etmiyoruz; 0 kabul etmiyoruz.
        ht = mac.get("goals", {}).get("halftime", {}) or {}
        hth = ht.get("home")
        hta = ht.get("away")
        if hth is not None and hta is not None:
            fh_oynanan += 1
            if home_id == team_id:
                fh_gf += hth
                fh_ga += hta
            else:
                fh_gf += hta
                fh_ga += hth
            fh_total = hth + hta
            if fh_total >= 1:
                fh_over05 += 1
                agirlikli_fh_over05 += agirlik
            if fh_total >= 2:
                fh_over15 += 1
                agirlikli_fh_over15 += agirlik
            agirlikli_fh_gf += (hth if home_id == team_id else hta) * agirlik
            agirlikli_fh_ga += (hta if home_id == team_id else hth) * agirlik

    if oynanan == 0:
        return {
            "mac": 0, "G": 0, "B": 0, "M": 0,
            "GF": 0, "GA": 0, "AVG_GF": 0, "AVG_GA": 0,
            "W_AVG_GF": 0, "W_AVG_GA": 0,
            "KG": 0, "OVER15": 0, "OVER25": 0,
            "W_KG": 0, "W_OVER15": 0, "W_OVER25": 0,
            "FH_MAC": 0, "FH_AVG_GF": 0, "FH_AVG_GA": 0,
            "FH_OVER05": 0, "FH_OVER15": 0,
            "W_FH_AVG_GF": 0, "W_FH_AVG_GA": 0,
            "W_FH_OVER05": 0, "W_FH_OVER15": 0
        }

    return {
        "mac": oynanan,
        "G": galibiyet,
        "B": beraberlik,
        "M": maglubiyet,
        "GF": atilan,
        "GA": yenilen,
        "AVG_GF": atilan / oynanan,
        "AVG_GA": yenilen / oynanan,
        "W_AVG_GF": (agirlikli_gf / agirlik_toplam) if agirlik_toplam else atilan / oynanan,
        "W_AVG_GA": (agirlikli_ga / agirlik_toplam) if agirlik_toplam else yenilen / oynanan,
        "KG": kg / oynanan * 100,
        "OVER15": over15 / oynanan * 100,
        "OVER25": over25 / oynanan * 100,
        "W_KG": (agirlikli_kg / agirlik_toplam * 100) if agirlik_toplam else 0,
        "W_OVER15": (agirlikli_over15 / agirlik_toplam * 100) if agirlik_toplam else 0,
        "W_OVER25": (agirlikli_over25 / agirlik_toplam * 100) if agirlik_toplam else 0,
        "FH_MAC": fh_oynanan,
        "FH_AVG_GF": (fh_gf / fh_oynanan) if fh_oynanan else 0,
        "FH_AVG_GA": (fh_ga / fh_oynanan) if fh_oynanan else 0,
        "FH_OVER05": (fh_over05 / fh_oynanan * 100) if fh_oynanan else 0,
        "FH_OVER15": (fh_over15 / fh_oynanan * 100) if fh_oynanan else 0,
        "W_FH_AVG_GF": (agirlikli_fh_gf / agirlik_toplam) if fh_oynanan and agirlik_toplam else 0,
        "W_FH_AVG_GA": (agirlikli_fh_ga / agirlik_toplam) if fh_oynanan and agirlik_toplam else 0,
        "W_FH_OVER05": (agirlikli_fh_over05 / agirlik_toplam * 100) if fh_oynanan and agirlik_toplam else 0,
        "W_FH_OVER15": (agirlikli_fh_over15 / agirlik_toplam * 100) if fh_oynanan and agirlik_toplam else 0
    }

# ============================================================
# EV / DEPLASMAN FORMU
# ============================================================

def venue_form(
    team_id,
    home=True
):

    maclar = takim_son_maclari(
        team_id
    )

    ilgili = []

    for mac in maclar:

        home_id = mac["teams"]["home"]["id"]
        away_id = mac["teams"]["away"]["id"]

        if home and home_id == team_id:
            ilgili.append(mac)

        elif not home and away_id == team_id:
            ilgili.append(mac)

    G = 0
    B = 0
    M = 0
    GF = 0
    GA = 0

    oynanan = 0

    for mac in ilgili:

        gh = mac["goals"].get("home")
        ga = mac["goals"].get("away")

        if gh is None or ga is None:
            continue

        oynanan += 1

        if home:

            GF += gh
            GA += ga

            if gh > ga:
                G += 1
            elif gh == ga:
                B += 1
            else:
                M += 1

        else:

            GF += ga
            GA += gh

            if ga > gh:
                G += 1
            elif ga == gh:
                B += 1
            else:
                M += 1

    return {
        "mac": oynanan,
        "G": G,
        "B": B,
        "M": M,
        "GF": GF,
        "GA": GA
    }


# ============================================================
# KORNER VERİSİ
# ============================================================

_FIXTURE_DETAILS_CACHE = {}
_TEAM_LAST_MATCHES_CACHE = {}

def fixture_istatistiklerini_getir(fixture_ids):
    """Fixture ayrıntılarını getirir; aynı fixture için tekrar API çağrısını önler."""
    if not fixture_ids:
        return []
    temiz_ids = []
    for fid in fixture_ids:
        try:
            fid = int(fid)
        except Exception:
            continue
        if fid not in temiz_ids:
            temiz_ids.append(fid)
    eksik_ids = [fid for fid in temiz_ids if fid not in _FIXTURE_DETAILS_CACHE]
    for i in range(0, len(eksik_ids), 10):
        grup = eksik_ids[i:i + 10]
        ids = "-".join(str(x) for x in grup)
        try:
            veriler = api_get("fixtures", {"ids": ids})
            for veri in veriler:
                try:
                    fid = int(veri.get("fixture", {}).get("id"))
                    _FIXTURE_DETAILS_CACHE[fid] = veri
                except Exception:
                    pass
        except Exception:
            continue
    return [_FIXTURE_DETAILS_CACHE[fid] for fid in temiz_ids if fid in _FIXTURE_DETAILS_CACHE]


def takim_korner_analizi(
    team_id,
    maclar
):

    if not maclar:

        return {
            "mac": 0,
            "korner_for": 0,
            "korner_against": 0,
            "toplam": 0,
            "over85": 0,
            "over95": 0,
            "over105": 0,
            "over115": 0
        }

    fixture_ids = []

    for mac in maclar:

        fixture_id = mac.get(
            "fixture",
            {}
        ).get("id")

        if fixture_id:

            fixture_ids.append(
                fixture_id
            )

    detaylar = fixture_istatistiklerini_getir(
        fixture_ids
    )

    toplam_mac = 0

    korner_for = 0
    korner_against = 0

    over85 = 0
    over95 = 0
    over105 = 0
    over115 = 0

    for mac in detaylar:

        try:

            home_id = mac["teams"]["home"]["id"]
            away_id = mac["teams"]["away"]["id"]

            home_corners = None
            away_corners = None

            istatistikler = mac.get(
                "statistics",
                []
            )

            for takim_istatistik in istatistikler:

                team_id_mac = (
                    takim_istatistik
                    .get("team", {})
                    .get("id")
                )

                for stat in (
                    takim_istatistik
                    .get(
                        "statistics",
                        []
                    )
                ):

                    if stat.get(
                        "type"
                    ) != "Corner Kicks":
                        continue

                    value = stat.get(
                        "value"
                    )

                    if value is None:
                        continue

                    try:
                        value = int(value)
                    except Exception:
                        continue

                    if team_id_mac == home_id:

                        home_corners = value

                    elif team_id_mac == away_id:

                        away_corners = value

            if (
                home_corners is None
                or away_corners is None
            ):
                continue

            if team_id == home_id:

                takim_korner = home_corners
                rakip_korner = away_corners

            elif team_id == away_id:

                takim_korner = away_corners
                rakip_korner = home_corners

            else:

                continue

            toplam_korner = (
                takim_korner
                + rakip_korner
            )

            toplam_mac += 1

            korner_for += takim_korner
            korner_against += rakip_korner

            if toplam_korner >= 9:
                over85 += 1

            if toplam_korner >= 10:
                over95 += 1

            if toplam_korner >= 11:
                over105 += 1

            if toplam_korner >= 12:
                over115 += 1

        except Exception:

            continue

    if toplam_mac == 0:

        return {
            "mac": 0,
            "korner_for": 0,
            "korner_against": 0,
            "toplam": 0,
            "over85": 0,
            "over95": 0,
            "over105": 0,
            "over115": 0
        }

    return {
        "mac": toplam_mac,

        "korner_for":
            korner_for / toplam_mac,

        "korner_against":
            korner_against / toplam_mac,

        "toplam":
            (
                korner_for
                + korner_against
            ) / toplam_mac,

        "over85":
            over85 / toplam_mac * 100,

        "over95":
            over95 / toplam_mac * 100,

        "over105":
            over105 / toplam_mac * 100,

        "over115":
            over115 / toplam_mac * 100
    }


# ============================================================
# KART VERİSİ VE KART MODELİ
# ============================================================

def _istatistik_sayisi(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace("%", "")
    if not text or text.lower() in ("null", "none", "-", "n/a"):
        return None
    try:
        return float(text)
    except Exception:
        return None


def takim_kart_analizi(team_id, maclar):
    """Son maçlardan sarı/kırmızı kart profilini çıkarır."""
    bos = {"mac": 0, "yellow_for": 0.0, "yellow_against": 0.0, "red_for": 0.0,
           "red_against": 0.0, "red_total": 0.0, "total_cards": 0.0,
           "over25": 0.0, "over35": 0.0, "over45": 0.0, "over55": 0.0, "over65": 0.0,
           "red_match_pct": 0.0}
    if not maclar:
        return bos
    ids = [m.get("fixture", {}).get("id") for m in maclar if m.get("fixture", {}).get("id")]
    details = fixture_istatistiklerini_getir(ids)
    records = []
    for match in details:
        try:
            home_id = match.get("teams", {}).get("home", {}).get("id")
            away_id = match.get("teams", {}).get("away", {}).get("id")
            if team_id not in (home_id, away_id):
                continue
            vals = {home_id: {"y": None, "r": None}, away_id: {"y": None, "r": None}}
            for block in match.get("statistics", []) or []:
                tid = block.get("team", {}).get("id")
                if tid not in vals:
                    continue
                for stat in block.get("statistics", []) or []:
                    typ = str(stat.get("type", "")).strip().lower()
                    val = _istatistik_sayisi(stat.get("value"))
                    if typ == "yellow cards":
                        vals[tid]["y"] = val
                    elif typ == "red cards":
                        vals[tid]["r"] = val
            if all(vals[t]["y"] is None and vals[t]["r"] is None for t in vals):
                continue
            hy, hr = max(0.0, vals[home_id]["y"] or 0.0), max(0.0, vals[home_id]["r"] or 0.0)
            ay, ar = max(0.0, vals[away_id]["y"] or 0.0), max(0.0, vals[away_id]["r"] or 0.0)
            if team_id == home_id:
                yf, ya, rf, ra = hy, ay, hr, ar
            else:
                yf, ya, rf, ra = ay, hy, ar, hr
            records.append({"yf": yf, "ya": ya, "rf": rf, "ra": ra, "total": yf + ya + rf + ra, "red": rf + ra})
        except Exception:
            continue
    n = len(records)
    if n == 0:
        return bos
    weights = list(range(1, n + 1))
    wsum = float(sum(weights))
    def wavg(key):
        return sum(r[key] * w for r, w in zip(records, weights)) / wsum
    def pct(th):
        return sum(w for r, w in zip(records, weights) if r["total"] >= th) / wsum * 100
    return {"mac": n, "yellow_for": wavg("yf"), "yellow_against": wavg("ya"),
            "red_for": wavg("rf"), "red_against": wavg("ra"), "red_total": wavg("red"),
            "total_cards": wavg("total"), "over25": pct(3), "over35": pct(4), "over45": pct(5),
            "over55": pct(6), "over65": pct(7),
            "red_match_pct": sum(w for r, w in zip(records, weights) if r["red"] >= 1) / wsum * 100}


def kart_modeli(home_cards, away_cards):
    """Kart toplamı ve takım kartlarını Poisson + geçmiş oranlarıyla birleştirir."""
    hn, an = int(home_cards.get("mac", 0) or 0), int(away_cards.get("mac", 0) or 0)
    if hn <= 0 or an <= 0:
        return None
    home_expected = (float(home_cards.get("yellow_for", 0)) * 0.55 + float(away_cards.get("yellow_against", 0)) * 0.45 +
                     float(home_cards.get("red_for", 0)) * 0.35 + float(away_cards.get("red_against", 0)) * 0.15)
    away_expected = (float(away_cards.get("yellow_for", 0)) * 0.55 + float(home_cards.get("yellow_against", 0)) * 0.45 +
                     float(away_cards.get("red_for", 0)) * 0.35 + float(home_cards.get("red_against", 0)) * 0.15)
    observed_total = (float(home_cards.get("total_cards", 0)) + float(away_cards.get("total_cards", 0))) / 2.0
    predicted_total = max(1.5, min(9.0, (home_expected + away_expected) * 0.78 + observed_total * 0.22))
    lines = {}
    sample = hn + an
    for key, minimum in (("over25", 3), ("over35", 4), ("over45", 5), ("over55", 6), ("over65", 7)):
        model_pct = overdispersed_poisson_tail(predicted_total, minimum) * 100
        empirical = (float(home_cards.get(key, 0)) + float(away_cards.get(key, 0))) / 2.0
        lines[key] = bayes_oran(empirical, model_pct, sample, prior_strength=10.0)
    team_lines = {}
    for side, expected in (("home", home_expected), ("away", away_expected)):
        for suffix, minimum in (("05", 1), ("15", 2), ("25", 3)):
            team_lines[side + suffix] = overdispersed_poisson_tail(expected, minimum) * 100
    red_lambda = max(0.005, float(home_cards.get("red_total", 0)) + float(away_cards.get("red_total", 0)))
    red_emp = (float(home_cards.get("red_match_pct", 0)) + float(away_cards.get("red_match_pct", 0))) / 2.0
    red_model = (1 - math.exp(-red_lambda)) * 100
    return {"mac": sample, "home_expected": home_expected, "away_expected": away_expected,
            "predicted_total": predicted_total, "lines": lines, "team_lines": team_lines,
            "red_over05": bayes_oran(red_emp, red_model, sample, prior_strength=18.0)}


# ============================================================
# H2H
# ============================================================

def h2h_getir(
    home_id,
    away_id
):

    return api_get(
        "fixtures/headtohead",
        {
            "h2h": f"{home_id}-{away_id}",
            "last": 10
        }
    )


# ============================================================
# PUAN DURUMU
# ============================================================

def standings_getir(
    league_id,
    season
):

    try:

        return api_get(
            "standings",
            {
                "league": league_id,
                "season": season
            }
        )

    except Exception:

        return []


# ============================================================
# API TAHMİNİ
# ============================================================

def api_prediction_getir(
    fixture_id
):

    try:

        sonuc = api_get(
            "predictions",
            {
                "fixture": fixture_id
            }
        )

        if sonuc:
            return sonuc[0]

    except Exception:

        pass

    return None


# ============================================================
# ORANLAR
# ============================================================

def odds_getir(
    fixture_id
):

    try:

        return api_get(
            "odds",
            {
                "fixture": fixture_id
            }
        )

    except Exception:

        return []



def turkcelestir(metin):
    if not metin:
        return ""
    metin = str(metin)
    replacements = {
        "Both Teams To Score": "Karşılıklı Gol",
        "Both Teams Score": "Karşılıklı Gol",
        "Over 1.5": "1.5 Üstü",
        "Over 2.5": "2.5 Üstü",
        "Over 3.5": "3.5 Üstü",
        "Under 1.5": "1.5 Altı",
        "Under 2.5": "2.5 Altı",
        "Under 3.5": "3.5 Altı",
        "Home Win": "Ev Sahibi Kazanır",
        "Away Win": "Deplasman Kazanır",
        "Draw": "Beraberlik",
        "Home or Draw": "Ev Sahibi veya Beraberlik",
        "Away or Draw": "Deplasman veya Beraberlik",
        "Clean Sheet": "Gol Yemeden",
        "First Half": "İlk Yarı",
        "Second Half": "İkinci Yarı",
        "Corners": "Kornerler",
        "Goals": "Goller",
        "Form": "Form Durumu",
        "Head to Head": "İkili Rekabet",
        "Prediction": "Tahmin",
        "Probability": "Olasılık",
        "Expected Goals": "Beklenen Goller",
        "Home": "Ev Sahibi",
        "Away": "Deplasman",
    }
    for eski, yeni in replacements.items():
        metin = metin.replace(eski, yeni)
    return metin

def oranlari_parse(
    odds
):

    sonuc = {}

    for item in odds:

        for bookmaker in item.get(
            "bookmakers",
            []
        ):

            for bet in bookmaker.get(
                "bets",
                []
            ):

                bet_name = bet.get(
                    "name",
                    ""
                )

                values = bet.get(
                    "values",
                    []
                )

                if bet_name not in sonuc:
                    sonuc[bet_name] = []

                for value in values:

                    sonuc[bet_name].append(
                        {
                            "value":
                                value.get(
                                    "value"
                                ),
                            "odd":
                                value.get(
                                    "odd"
                                )
                        }
                    )

    return sonuc


# ============================================================
# POISSON
# ============================================================

def poisson(
    lam,
    k
):

    if lam < 0:
        lam = 0

    return (
        math.exp(-lam)
        * (lam ** k)
        / math.factorial(k)
    )


def poisson_mac_tahmini(home_lambda, away_lambda):

    max_goal = 15
    ev_gol = {i: poisson(home_lambda, i) for i in range(max_goal + 1)}
    dep_gol = {i: poisson(away_lambda, i) for i in range(max_goal + 1)}

    norm = sum(ev_gol.values()) * sum(dep_gol.values())
    norm = norm if norm > 0 else 1.0

    ms1 = beraberlik = ms2 = 0.0
    over05 = over15 = over25 = over35 = 0.0
    kg = 0.0
    score_probs = {}

    for h in range(max_goal + 1):
        for a in range(max_goal + 1):
            ol = (ev_gol[h] * dep_gol[a]) / norm
            score_probs[(h, a)] = ol

            if h > a:
                ms1 += ol
            elif h == a:
                beraberlik += ol
            else:
                ms2 += ol

            total = h + a
            if total >= 1:
                over05 += ol
            if total >= 2:
                over15 += ol
            if total >= 3:
                over25 += ol
            if total >= 4:
                over35 += ol

            if h > 0 and a > 0:
                kg += ol

    total_lambda = max(0.0001, home_lambda + away_lambda)
    gol_olma = 1 - math.exp(-total_lambda)

    first_home = home_lambda / total_lambda * gol_olma
    first_away = away_lambda / total_lambda * gol_olma
    no_goal = math.exp(-total_lambda)

    tahmin_home, tahmin_away = max(
        score_probs,
        key=score_probs.get
    )

    # En olası 3 skor senaryosu
    top_scores = sorted(
        score_probs.items(),
        key=lambda x: x[1],
        reverse=True
    )[:3]

    return {
        "MS1": ms1 * 100,
        "X": beraberlik * 100,
        "MS2": ms2 * 100,
        "OVER05": over05 * 100,
        "UNDER05": 100 - over05 * 100,
        "OVER15": over15 * 100,
        "UNDER15": 100 - over15 * 100,
        "OVER25": over25 * 100,
        "UNDER25": 100 - over25 * 100,
        "OVER35": over35 * 100,
        "UNDER35": 100 - over35 * 100,
        "KG": kg * 100,
        "KG_YOK": 100 - kg * 100,
        "FIRST_HOME": first_home * 100,
        "FIRST_AWAY": first_away * 100,
        "NO_GOAL": no_goal * 100,
        "skor_home": tahmin_home,
        "skor_away": tahmin_away,
        "TOP_SKORLAR": [
            (h, a, p * 100) for (h, a), p in top_scores
        ],
        "TOTAL_LAMBDA": total_lambda,
        "HOME_LAMBDA": float(home_lambda),
        "AWAY_LAMBDA": float(away_lambda)
    }


def poisson_tail(lam, minimum):
    """P(X >= minimum) için sayısal olarak güvenli Poisson kuyruğu."""
    lam = max(0.01, float(lam))
    minimum = max(0, int(minimum))
    k_max = max(30, int(lam + 12 * math.sqrt(lam + 1) + 20))
    probs = []
    for k in range(k_max + 1):
        probs.append(poisson(lam, k))
    return max(0.0, min(1.0, 1.0 - sum(probs[:minimum])))


def overdispersed_poisson_tail(lam, minimum):
    """Korner gibi değişkenliği yüksek bir pazar için 3 senaryolu Poisson karışımı."""
    lam = max(0.05, float(lam))
    # Aynı ortalamayı korurken varyansı biraz artırır.
    senaryolar = (
        (lam * 0.72, 0.20),
        (lam, 0.60),
        (lam * 1.28, 0.20),
    )
    return sum(
        agirlik * poisson_tail(l, minimum)
        for l, agirlik in senaryolar
    )


def bayes_oran(empirical, model, sample_size, prior_strength=8.0):
    """Küçük örneklemde %0/%100 uçlarını yumuşatır."""
    n = max(0.0, float(sample_size))
    e = max(0.0, min(100.0, float(empirical)))
    m = max(0.0, min(100.0, float(model)))

    empirical_weight = n / (n + prior_strength)
    return empirical_weight * e + (1 - empirical_weight) * m


def gelismis_korner_model(home_corner, away_corner):
    """Kornerleri yalnızca geçmiş yüzdesiyle değil, beklenen toplam ve dağılımla hesaplar."""

    hn = int(home_corner.get("mac", 0) or 0)
    an = int(away_corner.get("mac", 0) or 0)

    if hn <= 0 or an <= 0:
        return None

    h_for = float(home_corner.get("korner_for", 0) or 0)
    h_against = float(home_corner.get("korner_against", 0) or 0)
    a_for = float(away_corner.get("korner_for", 0) or 0)
    a_against = float(away_corner.get("korner_against", 0) or 0)

    # Hücum gücü + rakibin verdiği korner + takımın toplam korner seviyesi.
    home_expected = (h_for * 0.55) + (a_against * 0.45)
    away_expected = (a_for * 0.55) + (h_against * 0.45)

    observed_total = (
        float(home_corner.get("toplam", 0) or 0) +
        float(away_corner.get("toplam", 0) or 0)
    ) / 2.0

    predicted_total = (
        (home_expected + away_expected) * 0.82
        + observed_total * 0.18
    )

    # Sonuçları makul aralıkta tut.
    predicted_total = max(5.5, min(15.5, predicted_total))

    thresholds = {
        "over75": 8,
        "over85": 9,
        "over95": 10,
        "over105": 11,
        "over115": 12,
        "over125": 13,
    }

    sample = hn + an
    result = {
        "mac": sample,
        "home_expected": home_expected,
        "away_expected": away_expected,
        "predicted_total": predicted_total,
        "lines": {}
    }

    key_map = {
        8: "over75",
        9: "over85",
        10: "over95",
        11: "over105",
        12: "over115",
        13: "over125",
    }

    for minimum, key in key_map.items():
        model_pct = overdispersed_poisson_tail(
            predicted_total,
            minimum
        ) * 100

        empirical_values = []
        if key in home_corner:
            empirical_values.append(float(home_corner[key]))
        if key in away_corner:
            empirical_values.append(float(away_corner[key]))

        empirical_pct = (
            sum(empirical_values) / len(empirical_values)
            if empirical_values else model_pct
        )

        # Model ağırlığı örneklem arttıkça azalır; böylece gerçek veri
        # yeterliyse geçmiş maçlar daha fazla söz sahibi olur.
        pct = bayes_oran(
            empirical_pct,
            model_pct,
            sample,
            prior_strength=10
        )

        result["lines"][key] = max(1.0, min(99.0, pct))

    return result

def guven_seviyesi(olasilik):
    """Olasılığı şişirmek yerine model desteğine göre güven seviyesi verir."""
    if olasilik >= 70:
        return "ÇOK GÜÇLÜ"
    if olasilik >= 62:
        return "GÜÇLÜ"
    if olasilik >= 55:
        return "ORTA"
    if olasilik >= 50:
        return "SINIRDA"
    return "DÜŞÜK"


def _yuzde_sayi(deger):
    """API-Football yüzde alanlarını güvenli şekilde sayıya çevirir."""
    if deger is None:
        return None
    try:
        metin = str(deger).replace("%", "").replace(",", ".").strip()
        return float(metin)
    except Exception:
        return None


def _kalibre(olasilik, guc=1.0):
    """Aşırı özgüveni kontrollü biçimde azaltır.

    Yüksek olasılıkları otomatik olarak 100'e taşımaz; model ile gerçek veri
    arasındaki fark büyüdükçe daha muhafazakâr davranır.
    """
    try:
        p = float(olasilik)
    except Exception:
        return 50.0
    p = max(0.1, min(99.9, p))
    g = max(0.45, min(1.0, float(guc)))

    # Logit benzeri sıkıştırma: uçlara yaklaşmayı zorlaştırır.
    if p <= 50.0:
        sonuc = 50.0 - (50.0 - p) * g
    else:
        sonuc = 50.0 + (p - 50.0) * g

    # Son güvenlik tavanı: veri/model hiçbir durumda yapay %100 üretmesin.
    return max(1.0, min(98.5, sonuc))


def _monotonik_gol_olasiliklari(poisson_sonuc):
    """Toplam gol üst çizgilerini aynı dağılımdan ve monoton biçimde üretir."""
    o05 = _kalibre(poisson_sonuc.get("OVER05", 50.0), 0.92)
    o15 = _kalibre(poisson_sonuc.get("OVER15", 50.0), 0.90)
    o25 = _kalibre(poisson_sonuc.get("OVER25", 50.0), 0.88)
    o35 = _kalibre(poisson_sonuc.get("OVER35", 50.0), 0.82)

    # Mantıksal sıra: P(T>0) >= P(T>1) >= P(T>2) >= P(T>3).
    o15 = min(o15, o05 - 0.5)
    o25 = min(o25, o15 - 0.5)
    o35 = min(o35, o25 - 0.5)

    o35 = max(1.0, o35)
    o25 = max(o35 + 0.5, o25)
    o15 = max(o25 + 0.5, o15)
    o05 = max(o15 + 0.5, o05)

    return {
        "OVER05": min(98.5, o05),
        "OVER15": min(98.5, o15),
        "OVER25": min(98.5, o25),
        "OVER35": min(98.5, o35),
    }

def gelistirilmis_model(poisson_sonuc, home_form, away_form,
                        home_venue, away_venue, prediction, h2h):
    """Çok kaynaklı ve adaptif maç modeli.

    Model olasılıkları yapay biçimde yükseltmez. Bunun yerine:
    - Poisson ana omurgayı oluşturur.
    - Son form ve saha formu güncel veriyi ekler.
    - API-Football tahmini bağımsız doğrulama olarak kullanılır.
    - Kaynaklar birbirinden çok ayrışıyorsa sonuç 50'ye doğru kalibre edilir.
    - Kaynaklar birbirine yakınsa modelin güçlü sinyali daha fazla korunur.
    """
    p = dict(poisson_sonuc)

    def oran(veri, anahtar, varsayilan=None):
        deger = veri.get(anahtar)
        if deger is None:
            return varsayilan
        try:
            return float(deger)
        except Exception:
            return varsayilan

    def ortalama_gecerli(degerler, varsayilan):
        temiz = [float(x) for x in degerler if x is not None]
        return sum(temiz) / len(temiz) if temiz else varsayilan

    def uyum_kalibrasyonu(kaynaklar):
        """Kaynaklar arasındaki fark büyüdükçe güveni azaltır."""
        temiz = [float(x) for x in kaynaklar if x is not None]
        if len(temiz) < 2:
            return 0.88
        fark = max(temiz) - min(temiz)
        if fark <= 6:
            return 0.96
        if fark <= 12:
            return 0.93
        if fark <= 20:
            return 0.88
        if fark <= 30:
            return 0.82
        return 0.74

    # ========================================================
    # MAÇ SONUCU: POISSON + SAHA + FORM + API
    # ========================================================
    hv_games = max(0, int(home_venue.get("mac", 0) or 0))
    av_games = max(0, int(away_venue.get("mac", 0) or 0))
    hf_games = max(0, int(home_form.get("mac", 0) or 0))
    af_games = max(0, int(away_form.get("mac", 0) or 0))

    hv_win = oran(home_venue, "G", 0) / hv_games * 100 if hv_games else None
    hv_draw = oran(home_venue, "B", 0) / hv_games * 100 if hv_games else None
    hv_loss = oran(home_venue, "M", 0) / hv_games * 100 if hv_games else None
    av_win = oran(away_venue, "G", 0) / av_games * 100 if av_games else None
    av_draw = oran(away_venue, "B", 0) / av_games * 100 if av_games else None
    av_loss = oran(away_venue, "M", 0) / av_games * 100 if av_games else None

    hf_win = oran(home_form, "G", 0) / hf_games * 100 if hf_games else None
    hf_draw = oran(home_form, "B", 0) / hf_games * 100 if hf_games else None
    hf_loss = oran(home_form, "M", 0) / hf_games * 100 if hf_games else None
    af_win = oran(away_form, "G", 0) / af_games * 100 if af_games else None
    af_draw = oran(away_form, "B", 0) / af_games * 100 if af_games else None
    af_loss = oran(away_form, "M", 0) / af_games * 100 if af_games else None

    ms1_sources = [p["MS1"]]
    msx_sources = [p["X"]]
    ms2_sources = [p["MS2"]]

    for hedef, degerler in (
        (ms1_sources, [hv_win, av_loss, hf_win, af_loss]),
        (msx_sources, [hv_draw, av_draw, hf_draw, af_draw]),
        (ms2_sources, [hv_loss, av_win, hf_loss, af_win]),
    ):
        hedef.extend(x for x in degerler if x is not None)

    # Form tarafına son maçların ağırlıklı oranı da dahil edilir.
    if hf_games and af_games:
        ms1_sources.append(ortalama_gecerli([
            home_form.get("W_RESULT_HOME"),
            away_form.get("W_RESULT_AWAY")
        ], (hf_win or p["MS1"])))

    ms1 = sum(ms1_sources) / len(ms1_sources)
    msx = sum(msx_sources) / len(msx_sources)
    ms2 = sum(ms2_sources) / len(ms2_sources)

    if prediction:
        pred = prediction.get("predictions", {}) or {}
        percent = pred.get("percent", {}) or {}
        api_home = _yuzde_sayi(percent.get("home"))
        api_draw = _yuzde_sayi(percent.get("draw"))
        api_away = _yuzde_sayi(percent.get("away"))
        api_agirlik = 0.18
        if api_home is not None:
            ms1_sources.append(api_home)
            ms1 = ms1 * (1 - api_agirlik) + api_home * api_agirlik
        if api_draw is not None:
            msx_sources.append(api_draw)
            msx = msx * (1 - api_agirlik) + api_draw * api_agirlik
        if api_away is not None:
            ms2_sources.append(api_away)
            ms2 = ms2 * (1 - api_agirlik) + api_away * api_agirlik

    ms_toplam = max(0.001, ms1 + msx + ms2)
    ms1 = ms1 / ms_toplam * 100
    msx = msx / ms_toplam * 100
    ms2 = ms2 / ms_toplam * 100

    # ========================================================
    # GOL PAZARLARI: GÜNCEL FORM + POISSON
    # ========================================================
    kg_emp = ortalama_gecerli([
        home_form.get("W_KG"), away_form.get("W_KG"),
        home_form.get("KG"), away_form.get("KG")
    ], p["KG"])
    over15_emp = ortalama_gecerli([
        home_form.get("W_OVER15"), away_form.get("W_OVER15"),
        home_form.get("OVER15"), away_form.get("OVER15")
    ], p["OVER15"])
    over25_emp = ortalama_gecerli([
        home_form.get("W_OVER25"), away_form.get("W_OVER25"),
        home_form.get("OVER25"), away_form.get("OVER25")
    ], p["OVER25"])

    # Ev/deplasman gol ortalamalarını da küçük bir doğrulama sinyali yap.
    gol_form_15 = None
    gol_form_25 = None
    if hf_games and af_games:
        toplam_gol_ort = (
            float(home_form.get("AVG_GF", 0)) + float(home_form.get("AVG_GA", 0)) +
            float(away_form.get("AVG_GF", 0)) + float(away_form.get("AVG_GA", 0))
        ) / 2.0
        # Basit ampirik dönüşüm: yüksek toplam gol ortalaması üst pazarını destekler.
        gol_form_15 = max(35.0, min(95.0, 50.0 + (toplam_gol_ort - 2.0) * 18.0))
        gol_form_25 = max(30.0, min(90.0, 50.0 + (toplam_gol_ort - 2.2) * 16.0))

    over15_sources = [p["OVER15"], over15_emp]
    if gol_form_15 is not None:
        over15_sources.append(gol_form_15)
    over25_sources = [p["OVER25"], over25_emp]
    if gol_form_25 is not None:
        over25_sources.append(gol_form_25)
    kg_sources = [p["KG"], kg_emp]

    p["MS1"] = _kalibre(ms1, uyum_kalibrasyonu(ms1_sources))
    p["X"] = _kalibre(msx, uyum_kalibrasyonu(msx_sources))
    p["MS2"] = _kalibre(ms2, uyum_kalibrasyonu(ms2_sources))

    over15_mix = sum(over15_sources) / len(over15_sources)
    over25_mix = sum(over25_sources) / len(over25_sources)
    kg_mix = sum(kg_sources) / len(kg_sources)

    p["OVER15"] = _kalibre(over15_mix, uyum_kalibrasyonu(over15_sources))
    p["UNDER15"] = 100 - p["OVER15"]
    p["OVER25"] = _kalibre(over25_mix, uyum_kalibrasyonu(over25_sources))
    p["UNDER25"] = 100 - p["OVER25"]
    p["KG"] = _kalibre(kg_mix, uyum_kalibrasyonu(kg_sources))
    p["KG_YOK"] = 100 - p["KG"]

    # 3.5 üstte yalnızca Poisson kullanılır; yüksek skor senaryolarını abartmamak için
    # daha sıkı kalibrasyon uygulanır.
    p["OVER35"] = _kalibre(p["OVER35"], 0.80)
    p["UNDER35"] = 100 - p["OVER35"]
    p["FIRST_HOME"] = _kalibre(p["FIRST_HOME"], 0.82)
    p["FIRST_AWAY"] = _kalibre(p["FIRST_AWAY"], 0.82)
    p["NO_GOAL"] = _kalibre(p["NO_GOAL"], 0.82)

    # Toplam gol çizgilerini aynı dağılım mantığıyla tutarlı hale getir.
    gol_cizgileri = _monotonik_gol_olasiliklari(p)
    p.update(gol_cizgileri)
    p["UNDER05"] = 100 - p["OVER05"]
    p["UNDER15"] = 100 - p["OVER15"]
    p["UNDER25"] = 100 - p["OVER25"]
    p["UNDER35"] = 100 - p["OVER35"]

    # MS yüzdelerini tekrar 100'e normalize et.
    ms_sum = p["MS1"] + p["X"] + p["MS2"]
    if ms_sum > 0:
        p["MS1"] = p["MS1"] / ms_sum * 100
        p["X"] = p["X"] / ms_sum * 100
        p["MS2"] = p["MS2"] / ms_sum * 100

    # Kaynakların aynı yönde olup olmadığını ayrıca sakla.
    # Bu değer olasılığı şişirmek için değil, sinyal kalitesini ölçmek içindir.
    def destek(veriler, hedef):
        temiz = [float(x) for x in veriler if x is not None]
        if not temiz:
            return (0, 0)
        if hedef >= 50:
            return (sum(1 for x in temiz if x >= 50), len(temiz))
        return (sum(1 for x in temiz if x < 50), len(temiz))

    p["DESTEK"] = {
        "MS1": destek(ms1_sources, p["MS1"]),
        "X": destek(msx_sources, p["X"]),
        "MS2": destek(ms2_sources, p["MS2"]),
        "OVER15": destek(over15_sources, p["OVER15"]),
        "OVER25": destek(over25_sources, p["OVER25"]),
        "KG": destek(kg_sources, p["KG"]),
        "OVER35": (1, 1),
        "FIRST_HOME": (1, 1),
        "FIRST_AWAY": (1, 1),
    }

    return p


def ilk_yari_gol_modeli(home_form, away_form, home_lambda, away_lambda):
    """İlk yarı toplam golü için ayrı, tutarlı bir model.

    0.5 ve 1.5 çizgileri aynı dağılımdan üretildiği için:
    FH 0.5 ÜST >= FH 1.5 ÜST ve alt olasılıkları matematiksel olarak tutarlı kalır.
    Geçmiş ilk yarı verisi yoksa tam maç beklenen golünden muhafazakâr pay kullanılır.
    """
    hf_n = int(home_form.get("FH_MAC", 0) or 0)
    af_n = int(away_form.get("FH_MAC", 0) or 0)

    full_total = max(0.30, float(home_lambda) + float(away_lambda))

    # Takımların ilk yarı hücum/savunma ortalamaları.
    hgf = float(home_form.get("W_FH_AVG_GF", 0) or 0)
    hga = float(home_form.get("W_FH_AVG_GA", 0) or 0)
    agf = float(away_form.get("W_FH_AVG_GF", 0) or 0)
    aga = float(away_form.get("W_FH_AVG_GA", 0) or 0)

    data_h = hf_n > 0 and (hgf + hga) > 0
    data_a = af_n > 0 and (agf + aga) > 0

    if data_h:
        home_fh = (hgf * 0.58) + (aga * 0.42)
    else:
        home_fh = float(home_lambda) * 0.45

    if data_a:
        away_fh = (agf * 0.58) + (hga * 0.42)
    else:
        away_fh = float(away_lambda) * 0.45

    raw_total = max(0.15, home_fh + away_fh)

    # Tam maç modelinin ilk yarı payıyla aşırı sapmayı engelle.
    baseline = full_total * 0.46
    confidence = min(1.0, (hf_n + af_n) / 20.0)
    fh_total = raw_total * confidence + baseline * (1.0 - confidence)
    fh_total = max(0.15, min(2.60, fh_total))

    # İlk yarı ev/deplasman gol dağılımını toplam lambda ile uyumlu tut.
    share_h = home_fh / max(0.001, raw_total)
    share_h = max(0.20, min(0.80, share_h))
    fh_home_lambda = fh_total * share_h
    fh_away_lambda = fh_total * (1.0 - share_h)

    over05 = 1.0 - math.exp(-fh_total)
    over15 = 1.0 - math.exp(-fh_total) * (1.0 + fh_total)
    under05 = 1.0 - over05
    under15 = 1.0 - over15

    no_goal = under05
    fh_home_score = (1.0 - math.exp(-fh_home_lambda)) * 100.0
    fh_away_score = (1.0 - math.exp(-fh_away_lambda)) * 100.0

    return {
        "FH_LAMBDA_HOME": fh_home_lambda,
        "FH_LAMBDA_AWAY": fh_away_lambda,
        "FH_TOTAL_LAMBDA": fh_total,
        "FH_OVER05": over05 * 100.0,
        "FH_UNDER05": under05 * 100.0,
        "FH_OVER15": over15 * 100.0,
        "FH_UNDER15": under15 * 100.0,
        "FH_NO_GOAL": no_goal * 100.0,
        "FH_HOME_GOAL": fh_home_score,
        "FH_AWAY_GOAL": fh_away_score,
        "FH_DATA_MATCHES": hf_n + af_n
    }


def market_onerileri_olustur(poisson_sonuc, home_corner, away_corner,
                             home_name, away_name, home_form=None,
                             away_form=None, home_venue=None,
                             away_venue=None, prediction=None, h2h=None, home_cards=None, away_cards=None):
    """Tüm pazarları çoklu veri kaynağı + model uyumu ile sıralar."""

    home_form = home_form or {"mac": 0}
    away_form = away_form or {"mac": 0}
    home_venue = home_venue or {"mac": 0}
    away_venue = away_venue or {"mac": 0}

    model = gelistirilmis_model(
        poisson_sonuc, home_form, away_form, home_venue,
        away_venue, prediction, h2h
    )

    destek = model.get("DESTEK", {})

    def destek_orani(key):
        d = destek.get(key, (0, 0))
        return (d[0] / d[1]) if d[1] else 0.5

    markets = [
        ("MS1", model["MS1"], "Poisson + form + saha + API", "MS1"),
        ("MS X", model["X"], "Poisson + form + saha + API", "X"),
        ("MS2", model["MS2"], "Poisson + form + saha + API", "MS2"),

        ("0.5 ÜSTÜ", model.get("OVER05", 0), "Poisson gol modeli", "OVER15"),
        ("1.5 ÜSTÜ", model["OVER15"], "Poisson + güncel form", "OVER15"),
        ("1.5 ALTI", model["UNDER15"], "Poisson + güncel form", "OVER15"),
        ("2.5 ÜSTÜ", model["OVER25"], "Poisson + form + gol ortalaması", "OVER25"),
        ("2.5 ALTI", model["UNDER25"], "Poisson + form + gol ortalaması", "OVER25"),
        ("3.5 ÜSTÜ", model["OVER35"], "Poisson", "OVER35"),
        ("3.5 ALTI", model["UNDER35"], "Poisson", "OVER35"),

        ("KG VAR", model["KG"], "Poisson + güncel form", "KG"),
        ("KG YOK", model["KG_YOK"], "Poisson + güncel form", "KG"),

        (f"İLK GOL - {home_name}", model["FIRST_HOME"], "İlk olay Poisson modeli", "FIRST_HOME"),
        (f"İLK GOL - {away_name}", model["FIRST_AWAY"], "İlk olay Poisson modeli", "FIRST_AWAY"),
    ]

    fh_model = ilk_yari_gol_modeli(
        home_form, away_form,
        poisson_sonuc.get("HOME_LAMBDA", poisson_sonuc.get("TOTAL_LAMBDA", 2.0) * 0.55),
        poisson_sonuc.get("AWAY_LAMBDA", poisson_sonuc.get("TOTAL_LAMBDA", 2.0) * 0.45)
    )
    markets.extend([
        ("İLK YARI 0.5 ÜSTÜ", fh_model["FH_OVER05"], "İlk yarı Poisson + son ilk yarı verileri", "FH_GOALS"),
        ("İLK YARI 0.5 ALTI", fh_model["FH_UNDER05"], "İlk yarı Poisson + son ilk yarı verileri", "FH_GOALS"),
        ("İLK YARI 1.5 ÜSTÜ", fh_model["FH_OVER15"], "İlk yarı Poisson + son ilk yarı verileri", "FH_GOALS"),
        ("İLK YARI 1.5 ALTI", fh_model["FH_UNDER15"], "İlk yarı Poisson + son ilk yarı verileri", "FH_GOALS"),
    ])

    corner_model = gelismis_korner_model(
        home_corner, away_corner
    )

    if corner_model:
        for key, label in (
            ("over75", "7.5 KORNER ÜSTÜ"),
            ("over85", "8.5 KORNER ÜSTÜ"),
            ("over95", "9.5 KORNER ÜSTÜ"),
            ("over105", "10.5 KORNER ÜSTÜ"),
            ("over115", "11.5 KORNER ÜSTÜ"),
            ("over125", "12.5 KORNER ÜSTÜ"),
        ):
            pct = corner_model["lines"][key]
            markets.append((
                label,
                pct,
                f"Gelişmiş korner dağılımı | {corner_model['mac']} maç",
                "CORNER"
            ))
            markets.append((
                label.replace("ÜSTÜ", "ALTI"),
                100 - pct,
                f"Gelişmiş korner dağılımı | {corner_model['mac']} maç",
                "CORNER"
            ))

    card_model = kart_modeli(home_cards, away_cards) if home_cards and away_cards else None
    if card_model:
        for key, label in (("over25", "3.0 KART ÜSTÜ"), ("over35", "3.5 KART ÜSTÜ"), ("over45", "4.5 KART ÜSTÜ"),
                           ("over55", "5.5 KART ÜSTÜ"), ("over65", "6.5 KART ÜSTÜ")):
            pct = card_model["lines"][key]
            markets.append((label, pct, f"Kart dağılımı + son form | {card_model['mac']} maç", "CARDS"))
            markets.append((label.replace("ÜSTÜ", "ALTI"), 100 - pct, f"Kart dağılımı + son form | {card_model['mac']} maç", "CARDS"))
        for key, label in (("home05", f"{home_name} 0.5 KART ÜSTÜ"), ("home15", f"{home_name} 1.5 KART ÜSTÜ"), ("home25", f"{home_name} 2.5 KART ÜSTÜ"),
                           ("away05", f"{away_name} 0.5 KART ÜSTÜ"), ("away15", f"{away_name} 1.5 KART ÜSTÜ"), ("away25", f"{away_name} 2.5 KART ÜSTÜ")):
            pct = card_model["team_lines"][key]
            markets.append((label, pct, "Takım kart modeli + rakip kart profili", "CARDS"))
            markets.append((label.replace("ÜSTÜ", "ALTI"), 100 - pct, "Takım kart modeli + rakip kart profili", "CARDS"))
        markets.append(("0.5 KIRMIZI KART ÜSTÜ", card_model["red_over05"], "Kırmızı kart geçmişi + Poisson", "CARDS"))
        markets.append(("0.5 KIRMIZI KART ALTI", 100 - card_model["red_over05"], "Kırmızı kart geçmişi + Poisson", "CARDS"))

    # 50'nin altında kalan pazarlar da gösterilebilir; sıralama tamamen
    # olasılık ve veri desteğine göre yapılır.
    markets.sort(
        key=lambda x: (round(float(x[1]), 3), destek_orani(x[3])),
        reverse=True
    )

    return markets


# ============================================================
# MAÇ ANALİZİ
# ============================================================



def analiz_mac_web(mac):
    """V3 analiz motorunu Tkinter penceresi olmadan çalıştırır."""
    fixture_id = mac["fixture"]["id"]
    home = mac["teams"]["home"]
    away = mac["teams"]["away"]
    home_id = home["id"]
    away_id = away["id"]
    home_name = home["name"]
    away_name = away["name"]
    league = mac.get("league", {})
    league_id = league.get("id")
    season = league.get("season")

    try:

        # ====================================================
        # SON 10 MAÇ
        # ====================================================

        home_last_matches = (
            takim_son_maclari(
                home_id
            )
        )

        away_last_matches = (
            takim_son_maclari(
                away_id
            )
        )

        home_form = takim_form(
            home_id
        )

        away_form = takim_form(
            away_id
        )

        # ====================================================
        # EV / DEPLASMAN
        # ====================================================

        home_venue = venue_form(
            home_id,
            home=True
        )

        away_venue = venue_form(
            away_id,
            home=False
        )

        # ====================================================
        # KORNER
        # ====================================================

        home_corner = (
            takim_korner_analizi(
                home_id,
                home_last_matches
            )
        )

        away_corner = (
            takim_korner_analizi(
                away_id,
                away_last_matches
            )
        )

        # ====================================================
        # KART ANALİZİ
        # ====================================================
        home_cards = takim_kart_analizi(home_id, home_last_matches)
        away_cards = takim_kart_analizi(away_id, away_last_matches)

        # ====================================================
        # H2H
        # ====================================================

        h2h = h2h_getir(
            home_id,
            away_id
        )

        # ====================================================
        # PUAN DURUMU
        # ====================================================

        standings = []

        if league_id and season:

            standings = standings_getir(
                league_id,
                season
            )

        # ====================================================
        # API TAHMİNİ
        # ====================================================

        prediction = (
            api_prediction_getir(
                fixture_id
            )
        )

        # ====================================================
        # ORANLAR
        # ====================================================

        odds = odds_getir(
            fixture_id
        )

        odds_parsed = oranlari_parse(
            odds
        )

        # ====================================================
        # POISSON
        # ====================================================

        # ====================================================
        # GELİŞMİŞ BEKLENEN GOL MODELİ
        # Hücum + rakip savunması + ev/deplasman + son form
        # ====================================================

        home_recent_gf = float(
            home_form.get("W_AVG_GF", home_form.get("AVG_GF", 0))
            or 0
        )
        home_recent_ga = float(
            home_form.get("W_AVG_GA", home_form.get("AVG_GA", 0))
            or 0
        )
        away_recent_gf = float(
            away_form.get("W_AVG_GF", away_form.get("AVG_GF", 0))
            or 0
        )
        away_recent_ga = float(
            away_form.get("W_AVG_GA", away_form.get("AVG_GA", 0))
            or 0
        )

        home_venue_gf = (
            home_venue["GF"] / home_venue["mac"]
            if home_venue["mac"] > 0 else home_recent_gf
        )
        home_venue_ga = (
            home_venue["GA"] / home_venue["mac"]
            if home_venue["mac"] > 0 else home_recent_ga
        )
        away_venue_gf = (
            away_venue["GF"] / away_venue["mac"]
            if away_venue["mac"] > 0 else away_recent_gf
        )
        away_venue_ga = (
            away_venue["GA"] / away_venue["mac"]
            if away_venue["mac"] > 0 else away_recent_ga
        )

        # Ev sahibinin üretimi; deplasmanın savunma zaafı da dahil.
        home_lambda = (
            home_recent_gf * 0.42
            + home_venue_gf * 0.28
            + away_recent_ga * 0.20
            + away_venue_ga * 0.10
        )

        # Deplasmanın üretimi; ev sahibinin savunması da dahil.
        away_lambda = (
            away_recent_gf * 0.42
            + away_venue_gf * 0.28
            + home_recent_ga * 0.20
            + home_venue_ga * 0.10
        )

        # Aşırı uçları sınırlandır.
        home_lambda = max(0.15, min(home_lambda, 4.20))
        away_lambda = max(0.15, min(away_lambda, 4.20))

        poisson_sonuc = (
            poisson_mac_tahmini(
                home_lambda,
                away_lambda
            )
        )

        marketler = market_onerileri_olustur(
            poisson_sonuc,
            home_corner,
            away_corner,
            home_name,
            away_name,
            home_form,
            away_form,
            home_venue,
            away_venue,
            prediction,
            h2h,
            home_cards,
            away_cards
        )

        # Ekranda gösterilen Poisson değerleri de birleşik model ile
        # aynı olsun; böylece üstteki özet ile alttaki bölüm çelişmez.
        poisson_sonuc = gelistirilmis_model(
            poisson_sonuc, home_form, away_form, home_venue,
            away_venue, prediction, h2h
        )

        # ====================================================
        # METİN
        # ====================================================

        satirlar = []

        satirlar.append(
            "══════════════════════════════════════════════"
        )

        satirlar.append(
            "              KENDİ ANALİZ MOTORUMUZ"
        )

        satirlar.append(
            "══════════════════════════════════════════════"
        )

        satirlar.append("")

        # ====================================================
        # PROFESYONEL MODEL ÖZETİ
        # ====================================================

        satirlar.append(
            "🎯 ÖNE ÇIKAN MODEL SONUÇLARI"
        )
        satirlar.append(
            "──────────────────────────────────────────────"
        )

        # Aynı maçta birbirine çok yakın pazarları şişirmek yerine,
        # sadece yüksek olasılık + güçlü veri desteği taşıyanları öne çıkar.
        guclu = [m for m in marketler if m[1] >= 62]
        if not guclu:
            guclu = [m for m in marketler if m[1] >= 55]

        for market in guclu[:7]:
            ad = market[0]
            olasilik = market[1]
            kaynak = market[2]
            satirlar.append(
                f"• {ad}: %{olasilik:.1f} | {guven_seviyesi(olasilik)}"
            )
            satirlar.append(
                f"  ↳ {kaynak}"
            )

        satirlar.append(
            f"• Güçlü sinyal sayısı: {len(guclu)} | Eşik: %62"
        )

        satirlar.append("")
        satirlar.append(
            f"🥅 Tahmini skor: {poisson_sonuc['skor_home']}-{poisson_sonuc['skor_away']}"
        )
        satirlar.append(
            f"⚽ Beklenen gol: {home_lambda:.2f} - {away_lambda:.2f}"
        )
        satirlar.append(
            "Model: Poisson + son form + saha formu + API tahmini + H2H + kalibrasyon"
        )
        satirlar.append(
            "Not: Yüksek yüzde garanti değildir; model özellikle aşırı yüksek tahminleri kalibre eder."
        )
        satirlar.append("")

        # ====================================================
        # EV SAHİBİ
        # ====================================================

        satirlar.append(
            f"🏠 {home_name}"
        )

        satirlar.append(
            f"   Son 10: "
            f"{home_form['G']}G "
            f"{home_form['B']}B "
            f"{home_form['M']}M"
        )

        satirlar.append(
            f"   Goller: "
            f"{home_form['GF']}-"
            f"{home_form['GA']}"
        )

        satirlar.append(
            f"   Maç başı gol: "
            f"{home_form['AVG_GF']:.2f}"
        )

        satirlar.append(
            f"   Maç başı yenen: "
            f"{home_form['AVG_GA']:.2f}"
        )

        satirlar.append(
            f"   KG Var: "
            f"{home_form['KG']:.1f}%"
        )

        satirlar.append(
            f"   2.5 Üst: "
            f"{home_form['OVER25']:.1f}%"
        )

        satirlar.append("")

        satirlar.append(
            "🏟 EV FORMU"
        )

        satirlar.append(
            f"   {home_venue['mac']} maç | "
            f"{home_venue['G']}G "
            f"{home_venue['B']}B "
            f"{home_venue['M']}M | "
            f"{home_venue['GF']}-"
            f"{home_venue['GA']}"
        )

        satirlar.append("")

        # ====================================================
        # DEPLASMAN
        # ====================================================

        satirlar.append(
            f"✈️ {away_name}"
        )

        satirlar.append(
            f"   Son 10: "
            f"{away_form['G']}G "
            f"{away_form['B']}B "
            f"{away_form['M']}M"
        )

        satirlar.append(
            f"   Goller: "
            f"{away_form['GF']}-"
            f"{away_form['GA']}"
        )

        satirlar.append(
            f"   Maç başı gol: "
            f"{away_form['AVG_GF']:.2f}"
        )

        satirlar.append(
            f"   Maç başı yenen: "
            f"{away_form['AVG_GA']:.2f}"
        )

        satirlar.append(
            f"   KG Var: "
            f"{away_form['KG']:.1f}%"
        )

        satirlar.append(
            f"   2.5 Üst: "
            f"{away_form['OVER25']:.1f}%"
        )

        satirlar.append("")

        satirlar.append(
            "✈️ DEPLASMAN FORMU"
        )

        satirlar.append(
            f"   {away_venue['mac']} maç | "
            f"{away_venue['G']}G "
            f"{away_venue['B']}B "
            f"{away_venue['M']}M | "
            f"{away_venue['GF']}-"
            f"{away_venue['GA']}"
        )

        # ====================================================
        # KORNER ANALİZİ
        # ====================================================

        satirlar.append("")

        satirlar.append(
            "══════════════════════════════════════════════"
        )

        satirlar.append(
            "🚩 KORNER ANALİZİ"
        )

        satirlar.append(
            "══════════════════════════════════════════════"
        )

        if home_corner["mac"] > 0:

            satirlar.append(
                f"🏠 {home_name} - "
                f"Son {home_corner['mac']} maç"
            )

            satirlar.append(
                f"   Kazandığı korner: "
                f"{home_corner['korner_for']:.2f}"
            )

            satirlar.append(
                f"   Rakibe verdiği korner: "
                f"{home_corner['korner_against']:.2f}"
            )

            satirlar.append(
                f"   Toplam korner: "
                f"{home_corner['toplam']:.2f}"
            )

            satirlar.append(
                f"   8.5 Üst: "
                f"{home_corner['over85']:.1f}%"
            )

            satirlar.append(
                f"   9.5 Üst: "
                f"{home_corner['over95']:.1f}%"
            )

            satirlar.append(
                f"   10.5 Üst: "
                f"{home_corner['over105']:.1f}%"
            )

            satirlar.append(
                f"   11.5 Üst: "
                f"{home_corner['over115']:.1f}%"
            )

        else:

            satirlar.append(
                f"🏠 {home_name}: "
                "Korner verisi bulunamadı."
            )

        satirlar.append("")

        if away_corner["mac"] > 0:

            satirlar.append(
                f"✈️ {away_name} - "
                f"Son {away_corner['mac']} maç"
            )

            satirlar.append(
                f"   Kazandığı korner: "
                f"{away_corner['korner_for']:.2f}"
            )

            satirlar.append(
                f"   Rakibe verdiği korner: "
                f"{away_corner['korner_against']:.2f}"
            )

            satirlar.append(
                f"   Toplam korner: "
                f"{away_corner['toplam']:.2f}"
            )

            satirlar.append(
                f"   8.5 Üst: "
                f"{away_corner['over85']:.1f}%"
            )

            satirlar.append(
                f"   9.5 Üst: "
                f"{away_corner['over95']:.1f}%"
            )

            satirlar.append(
                f"   10.5 Üst: "
                f"{away_corner['over105']:.1f}%"
            )

            satirlar.append(
                f"   11.5 Üst: "
                f"{away_corner['over115']:.1f}%"
            )

        else:

            satirlar.append(
                f"✈️ {away_name}: "
                "Korner verisi bulunamadı."
            )

        # ====================================================
        # KORNER MODELİ
        # ====================================================

        if (
            home_corner["mac"] > 0
            and away_corner["mac"] > 0
        ):

            tahmini_home_corner = (
                home_corner["korner_for"]
                +
                away_corner["korner_against"]
            ) / 2

            tahmini_away_corner = (
                away_corner["korner_for"]
                +
                home_corner["korner_against"]
            ) / 2

            tahmini_toplam_corner = (
                tahmini_home_corner
                +
                tahmini_away_corner
            )

            satirlar.append("")

            satirlar.append(
                "🔮 KORNER MODELİ"
            )

            satirlar.append(
                f"   Tahmini ev korneri: "
                f"{tahmini_home_corner:.1f}"
            )

            satirlar.append(
                f"   Tahmini deplasman korneri: "
                f"{tahmini_away_corner:.1f}"
            )

            satirlar.append(
                f"   🔥 Tahmini toplam korner: "
                f"{tahmini_toplam_corner:.1f}"
            )

            ileri_korner = gelismis_korner_model(
                home_corner, away_corner
            )

            if ileri_korner:
                satirlar.append("")
                satirlar.append(
                    "   GELİŞMİŞ KORNER OLASILIKLARI"
                )
                satirlar.append(
                    f"   7.5 Üst: {ileri_korner['lines']['over75']:.1f}%"
                )
                satirlar.append(
                    f"   8.5 Üst: {ileri_korner['lines']['over85']:.1f}%"
                )
                satirlar.append(
                    f"   9.5 Üst: {ileri_korner['lines']['over95']:.1f}%"
                )
                satirlar.append(
                    f"   10.5 Üst: {ileri_korner['lines']['over105']:.1f}%"
                )
                satirlar.append(
                    f"   11.5 Üst: {ileri_korner['lines']['over115']:.1f}%"
                )
                satirlar.append(
                    f"   12.5 Üst: {ileri_korner['lines']['over125']:.1f}%"
                )

        # ====================================================
        # KART ANALİZİ
        # ====================================================
        satirlar.append("")
        satirlar.append("══════════════════════════════════════════════")
        satirlar.append("🟨 KART ANALİZİ")
        satirlar.append("══════════════════════════════════════════════")
        if home_cards.get("mac", 0) > 0 and away_cards.get("mac", 0) > 0:
            ileri_kart = kart_modeli(home_cards, away_cards)
            satirlar.append(f"   Veri: {home_cards['mac']} + {away_cards['mac']} maç | Tahmini toplam: {ileri_kart['predicted_total']:.2f} kart")
            satirlar.append(f"   🏠 {home_name}: {home_cards['total_cards']:.2f} kart | sarı {home_cards['yellow_for']:.2f}")
            satirlar.append(f"   ✈️ {away_name}: {away_cards['total_cards']:.2f} kart | sarı {away_cards['yellow_for']:.2f}")
            satirlar.append(f"   3.0 ÜST: %{ileri_kart['lines']['over25']:.1f} | 3.5 ÜST: %{ileri_kart['lines']['over35']:.1f}")
            satirlar.append(f"   4.5 ÜST: %{ileri_kart['lines']['over45']:.1f} | 5.5 ÜST: %{ileri_kart['lines']['over55']:.1f} | 6.5 ÜST: %{ileri_kart['lines']['over65']:.1f}")
            satirlar.append(f"   🏠 {home_name} 1.5 ÜST: %{ileri_kart['team_lines']['home15']:.1f} | ✈️ {away_name} 1.5 ÜST: %{ileri_kart['team_lines']['away15']:.1f}")
            satirlar.append(f"   🔴 0.5 Kırmızı Kart ÜST: %{ileri_kart['red_over05']:.1f}")
        else:
            satirlar.append("   Kart istatistiği yeterli değil.")

        # ====================================================
        # POISSON
        # ====================================================

        satirlar.append(
            "──────────────────────────────────────────────"
        )


        satirlar.append(
            "📊 POISSON MODELİ"
        )

        satirlar.append(
            "──────────────────────────────────────────────"
        )

        satirlar.append(
            f"MS 1:  "
            f"{poisson_sonuc['MS1']:.1f}%"
        )

        satirlar.append(
            f"MS X:  "
            f"{poisson_sonuc['X']:.1f}%"
        )

        satirlar.append(
            f"MS 2:  "
            f"{poisson_sonuc['MS2']:.1f}%"
        )

        satirlar.append("")

        satirlar.append(
            f"Model beklenen gol: "
            f"{home_lambda:.2f} - "
            f"{away_lambda:.2f}"
        )

        satirlar.append(
            f"Model skor: "
            f"{poisson_sonuc['skor_home']}-"
            f"{poisson_sonuc['skor_away']}"
        )

        satirlar.append("")

        satirlar.append(
            f"1.5 ÜST: {poisson_sonuc['OVER15']:.1f}% | 1.5 ALT: {poisson_sonuc['UNDER15']:.1f}%"
        )
        satirlar.append(
            f"2.5 ÜST: {poisson_sonuc['OVER25']:.1f}% | 2.5 ALT: {poisson_sonuc['UNDER25']:.1f}%"
        )
        satirlar.append(
            f"3.5 ÜST: {poisson_sonuc['OVER35']:.1f}% | 3.5 ALT: {poisson_sonuc['UNDER35']:.1f}%"
        )
        satirlar.append(
            f"KG VAR: {poisson_sonuc['KG']:.1f}% | KG YOK: {poisson_sonuc['KG_YOK']:.1f}%"
        )
        satirlar.append(
            f"İlk gol: {home_name} %{poisson_sonuc['FIRST_HOME']:.1f} | {away_name} %{poisson_sonuc['FIRST_AWAY']:.1f} | Maçta gol yok %{poisson_sonuc['NO_GOAL']:.1f}"
        )

        # ====================================================
        # İLK YARI GOL MODELİ
        # ====================================================
        ilk_yari_model = ilk_yari_gol_modeli(
            home_form, away_form,
            home_lambda, away_lambda
        )
        satirlar.append("")
        satirlar.append("⏱️ İLK YARI GOL ANALİZİ")
        satirlar.append(
            f"   İlk yarı beklenen gol: {ilk_yari_model['FH_TOTAL_LAMBDA']:.2f}"
        )
        satirlar.append(
            f"   0.5 ÜST: {ilk_yari_model['FH_OVER05']:.1f}% | 0.5 ALT: {ilk_yari_model['FH_UNDER05']:.1f}%"
        )
        satirlar.append(
            f"   1.5 ÜST: {ilk_yari_model['FH_OVER15']:.1f}% | 1.5 ALT: {ilk_yari_model['FH_UNDER15']:.1f}%"
        )
        satirlar.append(
            f"   İlk yarıda gol yok: {ilk_yari_model['FH_NO_GOAL']:.1f}% | Veri: {ilk_yari_model['FH_DATA_MATCHES']} maç"
        )

        # ====================================================
        # H2H
        # ====================================================

        satirlar.append("")

        satirlar.append(
            "──────────────────────────────────────────────"
        )

        satirlar.append(
            "🤝 SON H2H MAÇLARI"
        )

        satirlar.append(
            "──────────────────────────────────────────────"
        )

        if h2h:

            for h in h2h[:10]:

                hh = h["teams"]["home"]["name"]
                aa = h["teams"]["away"]["name"]

                gh = h["goals"].get("home")
                ga = h["goals"].get("away")

                satirlar.append(
                    f"{hh} {gh}-{ga} {aa}"
                )

        else:

            satirlar.append(
                "H2H verisi bulunamadı."
            )

        # ====================================================
        # PUAN DURUMU
        # ====================================================

        satirlar.append("")

        satirlar.append(
            "──────────────────────────────────────────────"
        )

        satirlar.append(
            "🏆 PUAN DURUMU"
        )

        satirlar.append(
            "──────────────────────────────────────────────"
        )

        puan_home = None
        puan_away = None

        if standings:

            try:

                groups = (
                    standings[0]
                    .get("league", {})
                    .get(
                        "standings",
                        []
                    )
                )

                for group in groups:

                    for row in group:

                        team = row.get(
                            "team",
                            {}
                        )

                        if team.get("id") == home_id:

                            puan_home = row

                        if team.get("id") == away_id:

                            puan_away = row

            except Exception:

                pass

        if puan_home:

            satirlar.append(
                f"{home_name}: "
                f"{puan_home.get('rank')}."
                f" sıra | "
                f"{puan_home.get('points')} puan | "
                f"Form: "
                f"{puan_home.get('form', '-')}"
            )

        else:

            satirlar.append(
                f"{home_name}: "
                "Puan durumu verisi yok."
            )

        if puan_away:

            satirlar.append(
                f"{away_name}: "
                f"{puan_away.get('rank')}."
                f" sıra | "
                f"{puan_away.get('points')} puan | "
                f"Form: "
                f"{puan_away.get('form', '-')}"
            )

        else:

            satirlar.append(
                f"{away_name}: "
                "Puan durumu verisi yok."
            )

        # ====================================================
        # API TAHMİNİ
        # ====================================================

        satirlar.append("")

        satirlar.append(
            "──────────────────────────────────────────────"
        )

        satirlar.append(
            "🤖 API-FOOTBALL TAHMİNİ"
        )

        satirlar.append(
            "──────────────────────────────────────────────"
        )

        if prediction:

            pred = prediction.get(
                "predictions",
                {}
            )

            winner = pred.get(
                "winner",
                {}
            )

            percent = pred.get(
                "percent",
                {}
            )

            advice = pred.get(
                "advice"
            )

            satirlar.append(
                f"Tahmin: "
                f"{winner.get('name', '-')}"
            )

            satirlar.append(
                f"MS1: "
                f"{percent.get('home', '-')}"
            )

            satirlar.append(
                f"X: "
                f"{percent.get('draw', '-')}"
            )

            satirlar.append(
                f"MS2: "
                f"{percent.get('away', '-')}"
            )

            if advice:

                satirlar.append(
                    f"API Tavsiyesi: "
                    f"{turkcelestir(advice)}"
                )

        else:

            satirlar.append(
                "API tahmini mevcut değil."
            )

        # ====================================================
        # ORANLAR
        # ====================================================

        satirlar.append("")

        satirlar.append(
            "──────────────────────────────────────────────"
        )

        satirlar.append(
            "💰 MAÇ ORANLARI"
        )

        satirlar.append(
            "──────────────────────────────────────────────"
        )

        if odds_parsed:

            for bet_name, values in list(
                odds_parsed.items()
            )[:5]:

                satirlar.append(
                    f"\n{turkcelestir(bet_name)}:"
                )

                for value in values[:8]:

                    satirlar.append(
                        f"   "
                        f"{turkcelestir(value['value'])} "
                        f"→ {value['odd']}"
                    )

        else:

            satirlar.append(
                "Bu maç için oran verisi bulunamadı."
            )

        # ====================================================
        # ÖZET
        # ====================================================

        satirlar.append("")

        satirlar.append(
            "══════════════════════════════════════════════"
        )

        satirlar.append(
            "📌 MODEL ÖZETİ"
        )

        satirlar.append(
            "══════════════════════════════════════════════"
        )

        en_yuksek_ms = max(
            poisson_sonuc["MS1"],
            poisson_sonuc["X"],
            poisson_sonuc["MS2"]
        )

        if en_yuksek_ms == poisson_sonuc["MS1"]:

            model_ms = "MS1"

        elif en_yuksek_ms == poisson_sonuc["X"]:

            model_ms = "MS X"

        else:

            model_ms = "MS2"

        satirlar.append(
            f"Model MS sonucu: "
            f"{model_ms}"
        )

        satirlar.append(
            f"Model skor: "
            f"{poisson_sonuc['skor_home']}-"
            f"{poisson_sonuc['skor_away']}"
        )

        satirlar.append(
            f"2.5 ÜST olasılığı: {poisson_sonuc['OVER25']:.1f}% | 2.5 ALT: {poisson_sonuc['UNDER25']:.1f}%"
        )

        satirlar.append(
            f"KG VAR olasılığı: {poisson_sonuc['KG']:.1f}% | KG YOK: {poisson_sonuc['KG_YOK']:.1f}%"
        )

        satirlar.append("")
        satirlar.append("🎯 MODELİN EN YÜKSEK OLASILIKLI PAZARLARI")
        for ad, olasilik, kaynak, *_ in marketler[:5]:
            satirlar.append(
                f"   {ad}: %{olasilik:.1f} ({guven_seviyesi(olasilik)})"
            )

        if (
            home_corner["mac"] > 0
            and away_corner["mac"] > 0
        ):

            satirlar.append(
                f"Tahmini toplam korner: "
                f"{tahmini_toplam_corner:.1f}"
            )

        satirlar.append("")

        satirlar.append(
            "Not: Model sonuçları istatistiksel "
            "verilere dayanır ve kesin sonuç değildir."
        )

        sonuc_metni = "\n".join(
            satirlar
        )

        return sonuc_metni

    except Exception as exc:

        hata_mesaji = str(exc)

        return "❌ ANALİZ HATASI\n\n" + hata_mesaji


def gunun_maclarini_getir_web(tarih):
    return api_get("fixtures", {"date": tarih, "timezone": TIMEZONE})
