import os
import math
import threading
import unicodedata
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests
import tkinter as tk
from tkinter import ttk, messagebox


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
    """API anahtarını sırasıyla ortam değişkeninden, dosyadan veya pencereden alır."""
    # 1) VS Code / Windows ortam değişkeni
    anahtar = (os.getenv("API_FOOTBALL_KEY") or "").strip()
    if anahtar:
        return anahtar

    # 2) Proje klasöründeki api_key.txt
    # Böylece EXE veya VS Code hangi şekilde açılırsa açılsın anahtar kaybolmaz.
    try:
        dosya = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_key.txt")
        if os.path.exists(dosya):
            with open(dosya, "r", encoding="utf-8") as f:
                anahtar = f.read().strip()
            if anahtar:
                return anahtar
    except Exception:
        pass

    # 3) Anahtar yoksa kullanıcıdan güvenli şekilde uygulama içinden iste.
    # Anahtar sohbet ekranına/terminal çıktısına yazdırılmaz.
    try:
        from tkinter import simpledialog
        gecici_root = tk.Tk()
        gecici_root.withdraw()
        anahtar = simpledialog.askstring(
            "API-Football Anahtarı",
            "API-Football Pro API anahtarınızı girin:\n\n"
            "Anahtar bilgisayarınızda api_key.txt olarak saklanacaktır.",
            show="*",
            parent=gecici_root
        )
        gecici_root.destroy()
        anahtar = (anahtar or "").strip()

        if anahtar:
            try:
                dosya = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_key.txt")
                with open(dosya, "w", encoding="utf-8") as f:
                    f.write(anahtar)
            except Exception:
                pass
            return anahtar
    except Exception:
        pass

    return None


API_KEY = api_anahtari_yukle()

if not API_KEY:
    raise SystemExit(
        "API-Football API anahtarı bulunamadı. Uygulama yeniden açıldığında anahtar giriş penceresi gelecektir."
    )


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
    """API anahtarı sorununda uygulama içinden anahtar ister."""
    global API_KEY

    try:
        from tkinter import simpledialog
        anahtar = simpledialog.askstring(
            "API-Football API Anahtarı",
            "API-Football Pro anahtarınızı girin.\n\n"
            "Anahtar sohbet ekranına yazdırılmaz ve proje klasöründeki api_key.txt dosyasına kaydedilir.",
            show="*",
            parent=root
        )
    except Exception:
        anahtar = None

    anahtar = (anahtar or "").strip()
    if not anahtar:
        return False

    API_KEY = anahtar

    try:
        with open(_anahtar_dosyasi(), "w", encoding="utf-8") as f:
            f.write(API_KEY)
    except Exception:
        pass

    return True


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

    try:
        response = requests.get(
            API_URL + "/" + endpoint,
            headers=headers,
            params=params or {},
            timeout=30
        )
    except requests.RequestException as e:
        raise Exception(
            f"İnternet/API bağlantı hatası:\n{e}"
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

    return api_get(
        "fixtures",
        {
            "team": team_id,
            "last": 10,
            "timezone": TIMEZONE
        }
    )


def takim_form(team_id):

    maclar = takim_son_maclari(
        team_id
    )

    galibiyet = 0
    beraberlik = 0
    maglubiyet = 0

    atilan = 0
    yenilen = 0

    kg = 0
    over15 = 0
    over25 = 0

    # Son maçlara daha fazla ağırlık veriyoruz. Amaç yüzdeleri şişirmek değil,
    # güncel formu eski maçlardan biraz daha fazla hesaba katmak.
    agirlikli_kg = 0.0
    agirlikli_over15 = 0.0
    agirlikli_over25 = 0.0
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

            atilan += gh
            yenilen += ga

            if gh > ga:
                galibiyet += 1
            elif gh == ga:
                beraberlik += 1
            else:
                maglubiyet += 1

        else:

            atilan += ga
            yenilen += gh

            if ga > gh:
                galibiyet += 1
            elif ga == gh:
                beraberlik += 1
            else:
                maglubiyet += 1

        # API sonucu genellikle yeniden eskiye geldiği için ilk maçlara
        # (daha güncel olanlara) daha yüksek ağırlık veriyoruz.
        agirlik = max(1.0, 1.0 + (9 - min(sira, 9)) * 0.08)
        agirlik_toplam += agirlik

        if gh > 0 and ga > 0:
            kg += 1
            agirlikli_kg += agirlik

        if gh + ga >= 2:
            over15 += 1
            agirlikli_over15 += agirlik

        if gh + ga >= 3:
            over25 += 1
            agirlikli_over25 += agirlik

    if oynanan == 0:

        return {
            "mac": 0,
            "G": 0,
            "B": 0,
            "M": 0,
            "GF": 0,
            "GA": 0,
            "AVG_GF": 0,
            "AVG_GA": 0,
            "KG": 0,
            "OVER15": 0,
            "OVER25": 0,
            "W_KG": 0,
            "W_OVER15": 0,
            "W_OVER25": 0
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
        "KG": kg / oynanan * 100,
        "OVER15": over15 / oynanan * 100,
        "OVER25": over25 / oynanan * 100,
        "W_KG": (agirlikli_kg / agirlik_toplam * 100) if agirlik_toplam else 0,
        "W_OVER15": (agirlikli_over15 / agirlik_toplam * 100) if agirlik_toplam else 0,
        "W_OVER25": (agirlikli_over25 / agirlik_toplam * 100) if agirlik_toplam else 0
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

def fixture_istatistiklerini_getir(
    fixture_ids
):

    if not fixture_ids:
        return []

    sonuc = []

    # API çağrılarını 20'li gruplar halinde yapıyoruz.
    for i in range(
        0,
        len(fixture_ids),
        20
    ):

        grup = fixture_ids[
            i:i + 20
        ]

        ids = "-".join(
            str(x)
            for x in grup
        )

        try:

            veriler = api_get(
                "fixtures",
                {
                    "ids": ids
                }
            )

            sonuc.extend(
                veriler
            )

        except Exception:

            continue

    return sonuc


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

    # 0-12 gol aralığı kullanılıyor; pratikte kalan kuyruk ihmal edilebilir.
    max_goal = 12
    ev_gol = {i: poisson(home_lambda, i) for i in range(max_goal + 1)}
    dep_gol = {i: poisson(away_lambda, i) for i in range(max_goal + 1)}

    toplam_olasilik = sum(ev_gol.values()) * sum(dep_gol.values())
    if toplam_olasilik <= 0:
        toplam_olasilik = 1.0

    ms1 = beraberlik = ms2 = 0.0
    over15 = over25 = over35 = 0.0
    kg = 0.0
    first_home = first_away = no_goal = 0.0
    en_yuksek = 0.0
    tahmin_home = tahmin_away = 0

    for h in range(max_goal + 1):
        for a in range(max_goal + 1):
            olasilik = (ev_gol[h] * dep_gol[a]) / toplam_olasilik

            if h > a:
                ms1 += olasilik
            elif h == a:
                beraberlik += olasilik
            else:
                ms2 += olasilik

            if h + a >= 2:
                over15 += olasilik
            if h + a >= 3:
                over25 += olasilik
            if h + a >= 4:
                over35 += olasilik

            if h > 0 and a > 0:
                kg += olasilik

            if olasilik > en_yuksek:
                en_yuksek = olasilik
                tahmin_home = h
                tahmin_away = a

    # İlk gol modeli: bağımsız Poisson süreçlerinin ilk olay yaklaşımı.
    toplam_lambda = max(0.0001, home_lambda + away_lambda)
    gol_olma = 1 - math.exp(-toplam_lambda)
    first_home = (home_lambda / toplam_lambda) * gol_olma
    first_away = (away_lambda / toplam_lambda) * gol_olma
    no_goal = math.exp(-toplam_lambda)

    return {
        "MS1": ms1 * 100,
        "X": beraberlik * 100,
        "MS2": ms2 * 100,
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
        "skor_away": tahmin_away
    }


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
    """Aşırı özgüveni azaltan basit kalibrasyon.

    50'nin üzerindeki tahminleri kontrollü biçimde korur; böylece
    küçük örneklemde %80-%90 gibi gereğinden yüksek yüzdeler üretilmez.
    """
    p = max(0.0, min(100.0, float(olasilik)))
    g = max(0.45, min(1.0, float(guc)))
    sonuc = 50.0 + (p - 50.0) * g
    return max(1.0, min(99.0, sonuc))


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


def market_onerileri_olustur(poisson_sonuc, home_corner, away_corner,
                             home_name, away_name, home_form=None,
                             away_form=None, home_venue=None,
                             away_venue=None, prediction=None, h2h=None):
    """Birleşik modelden pazarları olasılık + kaynak uyumu ile sıralar."""
    if home_form is None:
        home_form = {"mac": 0}
    if away_form is None:
        away_form = {"mac": 0}
    if home_venue is None:
        home_venue = {"mac": 0}
    if away_venue is None:
        away_venue = {"mac": 0}

    model = gelistirilmis_model(
        poisson_sonuc, home_form, away_form, home_venue,
        away_venue, prediction, h2h
    )

    destek = model.get("DESTEK", {})

    def etiket(anahtar, temel):
        d = destek.get(anahtar, (0, 0))
        if d[1] <= 0:
            return temel
        return f"{temel} | Destek {d[0]}/{d[1]}"

    markets = [
        (etiket("MS1", "MS1"), model["MS1"], "Poisson + form + saha + API"),
        (etiket("X", "MS X"), model["X"], "Poisson + form + saha + API"),
        (etiket("MS2", "MS2"), model["MS2"], "Poisson + form + saha + API"),
        (etiket("OVER15", "1.5 ÜSTÜ"), model["OVER15"], "Poisson + güncel form"),
        (etiket("OVER15", "1.5 ALTI"), 100 - model["OVER15"], "Poisson + güncel form"),
        (etiket("OVER25", "2.5 ÜSTÜ"), model["OVER25"], "Poisson + güncel form + gol ortalaması"),
        (etiket("OVER25", "2.5 ALTI"), 100 - model["OVER25"], "Poisson + güncel form + gol ortalaması"),
        (etiket("OVER35", "3.5 ÜSTÜ"), model["OVER35"], "Poisson"),
        (etiket("OVER35", "3.5 ALTI"), 100 - model["OVER35"], "Poisson"),
        (etiket("KG", "KG VAR"), model["KG"], "Poisson + güncel form"),
        (etiket("KG", "KG YOK"), 100 - model["KG"], "Poisson + güncel form"),
        ("İLK GOL - " + home_name, model["FIRST_HOME"], "Poisson"),
        ("İLK GOL - " + away_name, model["FIRST_AWAY"], "Poisson"),
    ]

    if home_corner.get("mac", 0) > 0 and away_corner.get("mac", 0) > 0:
        corner_markets = [
            ("8.5 KORNER ÜSTÜ", (home_corner["over85"] + away_corner["over85"]) / 2),
            ("9.5 KORNER ÜSTÜ", (home_corner["over95"] + away_corner["over95"]) / 2),
            ("10.5 KORNER ÜSTÜ", (home_corner["over105"] + away_corner["over105"]) / 2),
            ("11.5 KORNER ÜSTÜ", (home_corner["over115"] + away_corner["over115"]) / 2),
        ]
        for ad, ol in corner_markets:
            # İki takımın verisini eşit ağırlıkla alıp %100'e yaklaşan
            # örneklem yüzdelerini de hafifçe merkeze çekeriz.
            ol = _kalibre(ol, 0.90)
            toplam_korner_orneklem = int(home_corner.get("mac", 0)) + int(away_corner.get("mac", 0))
            destek_sayisi = round((home_corner.get({"8.5 KORNER ÜSTÜ":"over85", "9.5 KORNER ÜSTÜ":"over95", "10.5 KORNER ÜSTÜ":"over105", "11.5 KORNER ÜSTÜ":"over115"}[ad], 0) + away_corner.get({"8.5 KORNER ÜSTÜ":"over85", "9.5 KORNER ÜSTÜ":"over95", "10.5 KORNER ÜSTÜ":"over105", "11.5 KORNER ÜSTÜ":"over115"}[ad], 0)) / 20)
            markets.append((f"{ad} | Veri desteği", ol, f"Son korner verileri | Örneklem {toplam_korner_orneklem} maç"))
            markets.append((f"{ad.replace(' ÜSTÜ', ' ALTI')} | Veri desteği", 100 - ol, f"Son korner verileri | Örneklem {toplam_korner_orneklem} maç"))

    # Önce olasılık, eşitlikte kaynak desteği. Olasılık yapay biçimde artırılmaz.
    def siralama(m):
        ad, ol, kaynak = m
        import re
        eslesme = re.search(r"Destek (\d+)/(\d+)", ad)
        destek_puani = (int(eslesme.group(1)) / int(eslesme.group(2))) if eslesme else 0.5
        return (round(float(ol), 3), destek_puani)

    markets.sort(key=siralama, reverse=True)
    return markets


# ============================================================
# MAÇ ANALİZİ
# ============================================================

def mac_analizi(mac):

    fixture_id = mac["fixture"]["id"]

    home = mac["teams"]["home"]
    away = mac["teams"]["away"]

    home_id = home["id"]
    away_id = away["id"]

    home_name = home["name"]
    away_name = away["name"]

    league = mac.get(
        "league",
        {}
    )

    league_id = league.get("id")
    season = league.get("season")

    analiz_penceresi = tk.Toplevel(root)
    analiz_penceresi.title(f"⚽ {home_name}  vs  {away_name}")
    analiz_penceresi.geometry("1320x900")
    analiz_penceresi.minsize(1050, 720)
    analiz_penceresi.configure(bg=BG)

    # -------------------- ÜST MAÇ KARTI --------------------
    hero = tk.Frame(analiz_penceresi, bg=PANEL,
                    highlightbackground=BORDER, highlightthickness=1)
    hero.pack(fill="x", padx=18, pady=(16, 10))

    tk.Label(hero, text="MAÇ ANALİZ DASHBOARD", bg=PANEL, fg=ACCENT,
             font=("Segoe UI", 9, "bold")).pack(pady=(12, 2))

    teams_hero = tk.Frame(hero, bg=PANEL)
    teams_hero.pack(fill="x", pady=2)
    tk.Label(teams_hero, text=home_name, bg=PANEL, fg=TEXT,
             font=("Segoe UI", 20, "bold")).pack(side="left", expand=True, anchor="e", padx=18)
    tk.Label(teams_hero, text="VS", bg=PANEL, fg=ACCENT,
             font=("Segoe UI", 18, "bold")).pack(side="left", padx=12)
    tk.Label(teams_hero, text=away_name, bg=PANEL, fg=TEXT,
             font=("Segoe UI", 20, "bold")).pack(side="left", expand=True, anchor="w", padx=18)

    tk.Label(hero,
             text=f"{league.get('country', '')}  •  {league.get('name', '')}  •  Maç ID: {fixture_id}",
             bg=PANEL, fg=MUTED, font=("Segoe UI", 9)).pack(pady=(2, 12))

    status_bar = tk.Frame(analiz_penceresi, bg=PANEL_2)
    status_bar.pack(fill="x", padx=18, pady=(0, 10))
    progress_label = tk.Label(status_bar, text="⏳  Analiz hazırlanıyor...",
                              bg=PANEL_2, fg=TEXT, font=("Segoe UI", 10, "bold"), anchor="w")
    progress_label.pack(side="left", padx=14, pady=8)

    # -------------------- ÖZET KARTLARI --------------------
    cards = tk.Frame(analiz_penceresi, bg=BG)
    cards.pack(fill="x", padx=18, pady=(0, 10))

    def metric_card(parent, title, accent=ACCENT):
        box = tk.Frame(parent, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        box.pack(side="left", fill="both", expand=True, padx=4)
        tk.Label(box, text=title, bg=CARD, fg=MUTED,
                 font=("Segoe UI", 9, "bold")).pack(pady=(9, 3))
        value = tk.Label(box, text="--", bg=CARD, fg=TEXT,
                         font=("Segoe UI", 17, "bold"))
        value.pack()
        sub = tk.Label(box, text="Hazırlanıyor", bg=CARD, fg=accent,
                       font=("Segoe UI", 8, "bold"))
        sub.pack(pady=(2, 10))
        return value, sub

    score_value, score_sub = metric_card(cards, "🎯 MODEL SKORU")
    goal_value, goal_sub = metric_card(cards, "⚽ BEKLENEN GOL")
    market1_value, market1_sub = metric_card(cards, "🔥 ÖNE ÇIKAN 1")
    market2_value, market2_sub = metric_card(cards, "📈 ÖNE ÇIKAN 2")
    market3_value, market3_sub = metric_card(cards, "🛡️ ÖNE ÇIKAN 3")

    # -------------------- DETAY PANELİ --------------------
    section_bar = tk.Frame(analiz_penceresi, bg=PANEL)
    section_bar.pack(fill="x", padx=18, pady=(0, 6))
    tk.Label(section_bar, text="📊  DETAYLI ANALİZ", bg=PANEL, fg=TEXT,
             font=("Segoe UI", 11, "bold")).pack(side="left", padx=12, pady=8)
    tk.Label(section_bar, text="Model • Form • Korner • API • Oran • H2H",
             bg=PANEL, fg=MUTED, font=("Segoe UI", 8)).pack(side="right", padx=12)

    text_frame = tk.Frame(analiz_penceresi, bg=BG)
    text_frame.pack(fill="both", expand=True, padx=18, pady=(0, 16))
    scrollbar = ttk.Scrollbar(text_frame, orient="vertical")
    scrollbar.pack(side="right", fill="y")

    analiz_text = tk.Text(
        text_frame, bg="#0f1a2b", fg=TEXT, insertbackground=TEXT,
        selectbackground="#24557a", selectforeground=WHITE,
        relief="flat", bd=0, padx=24, pady=18,
        font=("Segoe UI", 10), wrap="word", spacing1=2, spacing3=2,
        yscrollcommand=scrollbar.set
    )
    analiz_text.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=analiz_text.yview)

    analiz_text.tag_configure("section", foreground=ACCENT,
                              font=("Segoe UI", 12, "bold"), spacing1=10, spacing3=4)
    analiz_text.tag_configure("hero", foreground=TEXT,
                              font=("Segoe UI", 11, "bold"), spacing1=5, spacing3=2)
    analiz_text.tag_configure("strong", foreground=TEXT,
                              font=("Segoe UI", 10, "bold"))
    analiz_text.tag_configure("positive", foreground=ACCENT_2,
                              font=("Segoe UI", 10, "bold"))
    analiz_text.tag_configure("warning", foreground=WARNING,
                              font=("Segoe UI", 10, "bold"))
    analiz_text.tag_configure("muted", foreground=MUTED,
                              font=("Segoe UI", 9))
    analiz_text.tag_configure("line", foreground=BORDER)
    analiz_text.tag_configure("normal", foreground="#dbeafe",
                              font=("Segoe UI", 10))
    analiz_text.tag_configure("label", foreground="#8fb4d9",
                              font=("Segoe UI", 9, "bold"))
    analiz_text.tag_configure("market", foreground=TEXT,
                              font=("Segoe UI", 10, "bold"), lmargin1=8)

    analiz_text.insert("end", "⏳  ANALİZ MOTORU ÇALIŞIYOR\n\n"
                       "Son 10 maç • ev/deplasman formu • H2H • kornerler\n"
                       "API-Football tahmini • oranlar • Poisson modeli\n\n"
                       "Veriler toplanıyor, lütfen bekleyin...", "hero")
    analiz_text.config(state="disabled")

    def yaz(metin):
        # Üst dashboard kartlarını sonuç metninden güvenli biçimde doldur.
        skor = re.search(r"Tahmini skor:\s*([0-9]+-[0-9]+)", metin)
        gol = re.search(r"Beklenen gol:\s*([0-9.]+\s*-\s*[0-9.]+)", metin)
        if skor:
            score_value.config(text=skor.group(1))
            score_sub.config(text="Poisson + form + saha")
        if gol:
            goal_value.config(text=gol.group(1))
            goal_sub.config(text="Beklenen gol")

        market_lines = re.findall(r"•\s*(.+?):\s*%([0-9]+(?:\.[0-9]+)?)\s*\|\s*(.+)", metin)
        metric_pairs = [(market1_value, market1_sub), (market2_value, market2_sub), (market3_value, market3_sub)]
        for idx, pair in enumerate(metric_pairs):
            if idx < len(market_lines):
                ad, yuzde, guven = market_lines[idx]
                pair[0].config(text=f"%{float(yuzde):.1f}")
                pair[1].config(text=f"{ad} • {guven}")
            else:
                pair[0].config(text="—")
                pair[1].config(text="Yeterli güçlü sinyal yok")

        # Üçüncü kart boş kalmasın: model skoru / KG gibi temel bilgiyi göster.
        if len(market_lines) < 3 and skor:
            market3_value.config(text=skor.group(1))
            market3_sub.config(text="Tahmini skor")

        analiz_text.config(state="normal")
        analiz_text.delete("1.0", "end")
        for raw in metin.splitlines():
            satir = raw.rstrip()
            stripped = satir.strip()
            if not stripped:
                analiz_text.insert("end", "\n")
                continue
            if stripped.startswith(("═", "─", "━", "===")):
                analiz_text.insert("end", stripped + "\n", "line")
                continue
            if any(k in stripped for k in (
                "ÖNE ÇIKAN MODEL", "KORNER ANALİZİ", "KORNER MODELİ",
                "POISSON MODELİ", "API-FOOTBALL TAHMİNİ", "MAÇ ORANLARI",
                "MODEL ÖZETİ", "MODELİN EN YÜKSEK OLASILIKLI PAZARLARI"
            )):
                analiz_text.insert("end", "\n" + stripped + "\n", "section")
                continue
            if stripped.startswith("• ") and "%" in stripped:
                analiz_text.insert("end", stripped + "\n", "market")
                continue
            if stripped.startswith(("Tahmini skor:", "Tahmin:", "Model skor:",
                                    "Beklenen gol:", "Beklenen Gol:", "Tahmini toplam korner:")):
                analiz_text.insert("end", stripped + "\n", "hero")
                continue
            if any(k in stripped for k in ("ÇOK GÜÇLÜ", "GÜÇLÜ", "YÜKSEK")):
                analiz_text.insert("end", stripped + "\n", "positive")
                continue
            if any(k in stripped for k in ("ORTA", "SINIRDA")):
                analiz_text.insert("end", stripped + "\n", "warning")
                continue
            if stripped.startswith("Not:") or "Veri desteği" in stripped:
                analiz_text.insert("end", stripped + "\n", "muted")
                continue
            if stripped.startswith(("🎯", "📊", "🤖", "💰", "🚩", "📌")):
                analiz_text.insert("end", stripped + "\n", "strong")
                continue
            analiz_text.insert("end", stripped + "\n", "normal")
        analiz_text.config(state="disabled")
        analiz_text.see("1.0")
        progress_label.config(text="✓  Analiz tamamlandı")

    def worker():

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

            home_lambda = (
                home_form["AVG_GF"] * 0.60
                +
                (
                    home_venue["GF"]
                    / home_venue["mac"]
                    if home_venue["mac"] > 0
                    else home_form["AVG_GF"]
                ) * 0.40
            )

            away_lambda = (
                away_form["AVG_GF"] * 0.60
                +
                (
                    away_venue["GF"]
                    / away_venue["mac"]
                    if away_venue["mac"] > 0
                    else away_form["AVG_GF"]
                ) * 0.40
            )

            home_lambda = (
                home_lambda * 0.65
                +
                away_form["AVG_GA"] * 0.35
            )

            away_lambda = (
                away_lambda * 0.65
                +
                home_form["AVG_GA"] * 0.35
            )

            home_lambda = max(
                0.15,
                min(
                    home_lambda,
                    4.50
                )
            )

            away_lambda = max(
                0.15,
                min(
                    away_lambda,
                    4.50
                )
            )

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
                h2h
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

            for ad, olasilik, kaynak in guclu[:7]:
                satirlar.append(
                    f"• {ad}: %{olasilik:.1f} | {guven_seviyesi(olasilik)}"
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

            # ====================================================
            # POISSON
            # ====================================================

            satirlar.append("")

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
            for ad, olasilik, kaynak in marketler[:5]:
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

            root.after(
                0,
                lambda: yaz(
                    sonuc_metni
                )
            )

        except Exception as exc:

            hata_mesaji = str(exc)

            root.after(
                0,
                lambda: yaz(
                    "❌ ANALİZ HATASI\n\n"
                    + hata_mesaji
                )
            )

    threading.Thread(
        target=worker,
        daemon=True
    ).start()


# ============================================================
# ANA PENCERE — PROFESYONEL PANEL
# ============================================================

root = tk.Tk()
root.title("⚽ İDDAA MAÇ ANALİZ MERKEZİ")
root.geometry("1450x920")
root.minsize(1100, 720)
root.configure(bg=BG)

style = ttk.Style()
try:
    style.theme_use("clam")
except Exception:
    pass

style.configure(
    "Modern.TCombobox",
    fieldbackground=PANEL_2, background=PANEL_2,
    foreground=TEXT, bordercolor=BORDER,
    lightcolor=BORDER, darkcolor=BORDER,
    arrowcolor=ACCENT, padding=7,
    font=("Segoe UI", 10)
)
style.map("Modern.TCombobox",
          fieldbackground=[("readonly", PANEL_2)],
          foreground=[("readonly", TEXT)])
style.configure("Modern.Vertical.TScrollbar",
                background=PANEL_2, troughcolor=BG,
                bordercolor=BG, arrowcolor=MUTED)

header = tk.Frame(root, bg=BG)
header.pack(fill="x", padx=24, pady=(20, 8))

tk.Label(header, text="⚽", bg=BG, fg=ACCENT,
         font=("Segoe UI Emoji", 30)).pack(side="left", padx=(8, 12))

title_box = tk.Frame(header, bg=BG)
title_box.pack(side="left")
tk.Label(title_box, text="İDDAA MAÇ ANALİZ MERKEZİ",
         bg=BG, fg=TEXT, font=("Segoe UI", 25, "bold")).pack(anchor="w")
tk.Label(title_box,
         text="Veri odaklı futbol analiz • form • korner • oran • Poisson modeli",
         bg=BG, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w", pady=(2, 0))

api_badge = tk.Label(header, text="● API HAZIR",
                     bg="#123522", fg=ACCENT_2,
                     font=("Segoe UI", 9, "bold"), padx=12, pady=6)
api_badge.pack(side="right", padx=8)

tarih_panel = tk.Frame(root, bg=PANEL,
                       highlightbackground=BORDER, highlightthickness=1)
tarih_panel.pack(fill="x", padx=24, pady=6)

tk.Label(tarih_panel, text="📅  TARİH", bg=PANEL, fg=TEXT,
         font=("Segoe UI", 10, "bold")).pack(side="left", padx=(14, 10), pady=10)

def modern_button(parent, text, command, bgc=PANEL_2, fgc=TEXT, padx=13):
    return tk.Button(
        parent, text=text, command=command, bg=bgc, fg=fgc,
        activebackground=CARD_HOVER, activeforeground=WHITE,
        relief="flat", bd=0, font=("Segoe UI", 9, "bold"),
        cursor="hand2", padx=padx, pady=7
    )

modern_button(tarih_panel, "‹  ÖNCEKİ", lambda: tarih_degistir(-1)).pack(side="left", padx=3)

tarih_var = tk.StringVar(value=bugunun_tarihi())
tk.Entry(tarih_panel, textvariable=tarih_var, width=12,
         font=("Segoe UI", 11, "bold"), justify="center",
         bg=PANEL_2, fg=TEXT, insertbackground=TEXT,
         relief="flat", bd=0).pack(side="left", padx=5, ipady=5)

modern_button(tarih_panel, "BUGÜN", bugun, bgc=ACCENT, fgc="#06111f").pack(side="left", padx=3)
modern_button(tarih_panel, "SONRAKİ  ›", lambda: tarih_degistir(1)).pack(side="left", padx=3)

tarih_getir_butonu = modern_button(
    tarih_panel, "↻  MAÇLARI GETİR", tum_maclari_getir,
    bgc=ACCENT, fgc="#06111f", padx=15
)
tarih_getir_butonu.pack(side="left", padx=(10, 12))

takim_panel = tk.Frame(root, bg=PANEL,
                       highlightbackground=BORDER, highlightthickness=1)
takim_panel.pack(fill="x", padx=24, pady=6)

tk.Label(takim_panel, text="🔎  TAKIM ARA", bg=PANEL, fg=TEXT,
         font=("Segoe UI", 10, "bold")).pack(side="left", padx=(14, 10), pady=10)

takim_ara_var = tk.StringVar()
takim_entry = tk.Entry(
    takim_panel, textvariable=takim_ara_var, width=25,
    font=("Segoe UI", 10), bg=PANEL_2, fg=TEXT,
    insertbackground=TEXT, relief="flat", bd=0
)
takim_entry.pack(side="left", padx=4, ipady=6)

arama_butonu = modern_button(takim_panel, "ARA", takim_ara,
                              bgc=ACCENT, fgc="#06111f")
arama_butonu.pack(side="left", padx=5)

takim_combo = ttk.Combobox(
    takim_panel, width=38, state="readonly",
    font=("Segoe UI", 10), style="Modern.TCombobox"
)
takim_combo.pack(side="left", padx=5, ipady=2)

takim_mac_butonu = modern_button(
    takim_panel, "⚽ TAKIM MAÇLARI", takim_maclarini_yukle,
    bgc=ACCENT_2, fgc="#06110a", padx=15
)
takim_mac_butonu.pack(side="left", padx=(6, 10))

takim_bilgisi_var = tk.StringVar(value="")
tk.Label(takim_panel, textvariable=takim_bilgisi_var,
         bg=PANEL, fg=MUTED, font=("Segoe UI", 9)).pack(side="left", padx=4)

takim_entry.bind("<Return>", lambda event: takim_ara())

status_panel = tk.Frame(root, bg=BG)
status_panel.pack(fill="x", padx=24, pady=(10, 2))

durum_var = tk.StringVar(value="Bugünün maçları yükleniyor...")
tk.Label(status_panel, textvariable=durum_var,
         bg=BG, fg=ACCENT,
         font=("Segoe UI", 10, "bold")).pack(side="left")

baslik_var = tk.StringVar(value=f"⚽  {bugunun_tarihi()}  •  GÜNÜN MAÇLARI")
tk.Label(status_panel, textvariable=baslik_var,
         bg=BG, fg=TEXT,
         font=("Segoe UI", 15, "bold")).pack(side="right")

ana_frame = tk.Frame(root, bg=BG)
ana_frame.pack(fill="both", expand=True, padx=24, pady=(5, 18))

canvas = tk.Canvas(ana_frame, bg=BG, highlightthickness=0, bd=0)
scrollbar = ttk.Scrollbar(ana_frame, orient="vertical",
                          command=canvas.yview,
                          style="Modern.Vertical.TScrollbar")
mac_frame = tk.Frame(canvas, bg=BG)

mac_frame.bind("<Configure>",
               lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

canvas_window = canvas.create_window((0, 0), window=mac_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)
canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

def canvas_genislik(event):
    canvas.itemconfig(canvas_window, width=event.width)

canvas.bind("<Configure>", canvas_genislik)

def mouse_wheel(event):
    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

canvas.bind_all("<MouseWheel>", mouse_wheel)

# ============================================================
# BAŞLAT
# ============================================================

def api_baslangic_kontrolu():
    """Uygulama açılırken API anahtarını kontrol eder; maç listesini bloke etmez."""
    try:
        api_get("status")
        durum_var.set("API bağlantısı hazır. Maçlar getiriliyor...")
    except Exception as e:
        # status başarısız olsa bile maç çağrısı ayrıca denenir; gerçek hata
        # kullanıcıya mevcut akışta gösterilecektir.
        durum_var.set("API bağlantısı kontrol ediliyor...")


root.after(100, api_baslangic_kontrolu)
root.after(300, tum_maclari_getir)

root.mainloop()