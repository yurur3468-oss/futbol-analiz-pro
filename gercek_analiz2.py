import os
import math
import threading
import unicodedata
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests
import tkinter as tk
from tkinter import ttk, messagebox


# ============================================================
# AYARLAR
# ============================================================

API_URL = "https://v3.football.api-sports.io"
API_KEY = os.getenv("API_FOOTBALL_KEY")
TIMEZONE = "Europe/Istanbul"


if not API_KEY:
    raise SystemExit(
        "API_FOOTBALL_KEY bulunamadı.\n\n"
        "VS Code terminalinde:\n\n"
        '$env:API_FOOTBALL_KEY="API_ANAHTARIN"'
    )


# ============================================================
# API
# ============================================================

def api_get(endpoint, params=None):

    headers = {
        "x-apisports-key": API_KEY
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

    if response.status_code != 200:
        raise Exception(
            f"API HTTP Hatası: {response.status_code}\n"
            f"{data.get('errors', data)}"
        )

    errors = data.get("errors")

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

        except Exception as e:
            root.after(
                0,
                lambda: (
                    arama_butonu.config(state="normal"),
                    messagebox.showerror("API Hatası", str(e))
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

        except Exception as e:

            hata_mesaji = str(e)

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

        except Exception as e:

            hata_mesaji = str(e)

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

        ttk.Label(
            mac_frame,
            text="Maç bulunamadı.",
            font=("Arial", 12)
        ).pack(
            pady=30
        )

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
            text=f"🌍 {grup_adi}",
            font=("Arial", 12, "bold"),
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

    home_adi = home.get(
        "name",
        "Ev Sahibi"
    )

    away_adi = away.get(
        "name",
        "Deplasman"
    )

    skor_home = mac["goals"].get("home")
    skor_away = mac["goals"].get("away")

    saat = mac_saati(mac)

    if (
        skor_home is not None
        and skor_away is not None
    ):

        skor = (
            f"{skor_home} - "
            f"{skor_away}"
        )

    else:

        skor = "vs"

    frame = tk.Frame(
        mac_frame,
        bd=1,
        relief="solid"
    )

    frame.pack(
        fill="x",
        padx=10,
        pady=3
    )

    tk.Label(
        frame,
        text=(
            f"⚽ {saat}   "
            f"{home_adi}  "
            f"{skor}  "
            f"{away_adi}"
        ),
        font=("Arial", 11),
        anchor="w"
    ).pack(
        side="left",
        padx=8,
        pady=8
    )

    tk.Button(
        frame,
        text="📊 ANALİZ ET",
        font=("Arial", 10, "bold"),
        command=lambda m=mac: mac_analizi(m)
    ).pack(
        side="right",
        padx=8
    )


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
    over25 = 0

    oynanan = 0

    for mac in maclar:

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

        if gh > 0 and ga > 0:
            kg += 1

        if gh + ga > 2.5:
            over25 += 1

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
            "OVER25": 0
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
        "OVER25": over25 / oynanan * 100
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
            (over85 + 1) / (toplam_mac + 2) * 100,

        "over95":
            (over95 + 1) / (toplam_mac + 2) * 100,

        "over105":
            (over105 + 1) / (toplam_mac + 2) * 100,

        "over115":
            (over115 + 1) / (toplam_mac + 2) * 100
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
    if olasilik >= 65:
        return "YÜKSEK"
    if olasilik >= 55:
        return "ORTA"
    if olasilik >= 50:
        return "SINIRDA"
    return "DÜŞÜK"


# ============================================================
# GELİŞMİŞ ENSEMBLE MODELİ
# ============================================================

def clamp_olasilik(deger, alt=1.0, ust=99.0):
    try:
        return max(alt, min(ust, float(deger)))
    except Exception:
        return alt


def guvenilirlik_agirligi(mac_sayisi, hedef=10):
    """Örneklem büyüklüğüne göre veri ağırlığı. Az veri modeli şişirmez."""
    try:
        n = max(0, int(mac_sayisi))
    except Exception:
        n = 0
    return min(1.0, n / float(hedef))


def yuzde_empirik(maclar, olay):
    """Son maçlardan olay gerçekleşme yüzdesini döndürür."""
    toplam = 0
    basarili = 0

    for mac in maclar or []:
        try:
            gh = mac["goals"].get("home")
            ga = mac["goals"].get("away")
            if gh is None or ga is None:
                continue
            toplam += 1
            if olay(gh, ga, mac):
                basarili += 1
        except Exception:
            continue

    if toplam == 0:
        return None, 0

    # Küçük örneklemlerde %0/%100 gibi aşırı değerleri yumuşat.
    # Laplace düzeltmesi: (başarı + 1) / (toplam + 2)
    duzeltilmis = ((basarili + 1) / (toplam + 2)) * 100
    return duzeltilmis, toplam


def h2h_istatistikleri(h2h, home_id, away_id):
    """H2H sonuçlarından ev sahibi bakış açısıyla temel yüzdeleri çıkarır."""
    toplam = 0
    ms1 = 0
    beraberlik = 0
    ms2 = 0
    over25 = 0
    kg = 0

    for mac in h2h or []:
        try:
            gh = mac["goals"].get("home")
            ga = mac["goals"].get("away")
            hid = mac["teams"]["home"]["id"]
            aid = mac["teams"]["away"]["id"]

            if gh is None or ga is None:
                continue

            # H2H farklı saha sırasıyla gelebilir; sonucu bu maçın
            # gerçek ev/deplasman takımlarına göre değerlendiriyoruz.
            toplam += 1

            if hid == home_id and aid == away_id:
                if gh > ga:
                    ms1 += 1
                elif gh == ga:
                    beraberlik += 1
                else:
                    ms2 += 1
            elif hid == away_id and aid == home_id:
                if ga > gh:
                    ms1 += 1
                elif ga == gh:
                    beraberlik += 1
                else:
                    ms2 += 1

            if gh + ga >= 3:
                over25 += 1
            if gh > 0 and ga > 0:
                kg += 1
        except Exception:
            continue

    if toplam == 0:
        return None

    return {
        "MS1": ms1 / toplam * 100,
        "X": beraberlik / toplam * 100,
        "MS2": ms2 / toplam * 100,
        "OVER25": over25 / toplam * 100,
        "UNDER25": 100 - (over25 / toplam * 100),
        "KG": kg / toplam * 100,
        "KG_YOK": 100 - (kg / toplam * 100),
        "mac": toplam
    }


def gelismis_model_hesapla(
    poisson_sonuc,
    home_form,
    away_form,
    home_venue,
    away_venue,
    h2h,
    prediction
):
    """
    Poisson + son form + saha formu + H2H + API tahminini
    kontrollü şekilde birleştirir.

    Amaç olasılığı yapay olarak yükseltmek değil;
    aynı sonucu destekleyen bağımsız sinyalleri bir araya getirmektir.
    """
    sonuc = dict(poisson_sonuc)

    # ------------------------------------------------------------
    # Form puanı: galibiyet 3, beraberlik 1.
    # Örneklem küçükse ağırlık otomatik düşer.
    # ------------------------------------------------------------
    def form_puani(form):
        mac = max(0, form.get("mac", 0))
        if mac <= 0:
            return None, 0
        puan = (
            form.get("G", 0) * 3
            + form.get("B", 0)
        )
        return (puan / (mac * 3)) * 100, mac

    home_form_pct, home_n = form_puani(home_form)
    away_form_pct, away_n = form_puani(away_form)

    # Ev/deplasman galibiyet oranları
    home_venue_win = (
        home_venue["G"] / home_venue["mac"] * 100
        if home_venue.get("mac", 0) > 0 else None
    )
    away_venue_win = (
        away_venue["G"] / away_venue["mac"] * 100
        if away_venue.get("mac", 0) > 0 else None
    )

    # ------------------------------------------------------------
    # Empirik toplam gol ve KG yüzdeleri
    # ------------------------------------------------------------
    home_over25, hn = yuzde_empirik(
        globals().get("_MODEL_HOME_MATCHES", []),
        lambda gh, ga, m: gh + ga >= 3
    )
    away_over25, an = yuzde_empirik(
        globals().get("_MODEL_AWAY_MATCHES", []),
        lambda gh, ga, m: gh + ga >= 3
    )

    home_kg, _ = yuzde_empirik(
        globals().get("_MODEL_HOME_MATCHES", []),
        lambda gh, ga, m: gh > 0 and ga > 0
    )
    away_kg, _ = yuzde_empirik(
        globals().get("_MODEL_AWAY_MATCHES", []),
        lambda gh, ga, m: gh > 0 and ga > 0
    )

    h2h_stats = h2h_istatistikleri(
        h2h,
        globals().get("_MODEL_HOME_ID"),
        globals().get("_MODEL_AWAY_ID")
    )

    # ------------------------------------------------------------
    # MS 1 / X / MS 2
    # Poisson ana modeldir. Diğer kaynaklar sınırlı ağırlıktadır.
    # ------------------------------------------------------------
    api_home = api_draw = api_away = None
    if prediction:
        pred = prediction.get("predictions", {})
        percent = pred.get("percent", {})
        try:
            api_home = float(str(percent.get("home", "")).replace("%", ""))
        except Exception:
            pass
        try:
            api_draw = float(str(percent.get("draw", "")).replace("%", ""))
        except Exception:
            pass
        try:
            api_away = float(str(percent.get("away", "")).replace("%", ""))
        except Exception:
            pass

    # API değerleri toplam 100 değilse normalize et.
    if all(x is not None for x in (api_home, api_draw, api_away)):
        api_toplam = api_home + api_draw + api_away
        if api_toplam > 0:
            api_home = api_home / api_toplam * 100
            api_draw = api_draw / api_toplam * 100
            api_away = api_away / api_toplam * 100

    # Form karşılaştırmasını 3 sonuca dağıtıyoruz.
    form_signal_home = None
    form_signal_away = None
    if home_form_pct is not None and away_form_pct is not None:
        form_signal_home = home_form_pct / max(1, home_form_pct + away_form_pct) * 100
        form_signal_away = away_form_pct / max(1, home_form_pct + away_form_pct) * 100

    # Saha sinyali
    venue_signal_home = venue_signal_away = None
    if home_venue_win is not None and away_venue_win is not None:
        toplam = home_venue_win + away_venue_win
        if toplam > 0:
            venue_signal_home = home_venue_win / toplam * 100
            venue_signal_away = away_venue_win / toplam * 100

    # Veri ağırlıkları
    form_weight = min(
        0.16,
        0.16 * min(guvenilirlik_agirligi(home_n), guvenilirlik_agirligi(away_n))
    )
    venue_weight = min(
        0.12,
        0.12 * min(
            guvenilirlik_agirligi(home_venue.get("mac", 0)),
            guvenilirlik_agirligi(away_venue.get("mac", 0))
        )
    )
    h2h_weight = 0.08 if h2h_stats and h2h_stats["mac"] >= 5 else 0.0
    api_weight = 0.15 if all(x is not None for x in (api_home, api_draw, api_away)) else 0.0
    poisson_weight = 1.0 - form_weight - venue_weight - h2h_weight - api_weight

    def blend(ms_key, form_signal, venue_signal, api_signal):
        degerler = [(poisson_sonuc[ms_key], poisson_weight)]
        if form_signal is not None:
            degerler.append((form_signal, form_weight))
        if venue_signal is not None:
            degerler.append((venue_signal, venue_weight))
        if h2h_stats:
            degerler.append((h2h_stats[ms_key], h2h_weight))
        if api_signal is not None:
            degerler.append((api_signal, api_weight))

        agirlik_toplam = sum(w for _, w in degerler)
        return sum(v * w for v, w in degerler) / agirlik_toplam

    sonuc["MS1"] = blend("MS1", form_signal_home, venue_signal_home, api_home)
    sonuc["X"] = blend(
        "X",
        None,
        None,
        api_draw
    )
    sonuc["MS2"] = blend("MS2", form_signal_away, venue_signal_away, api_away)

    # ------------------------------------------------------------
    # Toplam gol / KG:
    # Poisson + iki takımın son maçları + H2H.
    # ------------------------------------------------------------
    def blend_market(poisson_value, empirical_values, h2h_value=None):
        parcalar = [(poisson_value, 0.65)]
        for value, n in empirical_values:
            if value is not None:
                w = 0.175 * guvenilirlik_agirligi(n)
                parcalar.append((value, w))
        if h2h_value is not None and h2h_stats and h2h_stats["mac"] >= 5:
            parcalar.append((h2h_value, 0.10))
        toplam_w = sum(w for _, w in parcalar)
        return sum(v * w for v, w in parcalar) / toplam_w

    sonuc["OVER25"] = blend_market(
        poisson_sonuc["OVER25"],
        [(home_over25, hn), (away_over25, an)],
        h2h_stats["OVER25"] if h2h_stats else None
    )
    sonuc["UNDER25"] = 100 - sonuc["OVER25"]

    sonuc["KG"] = blend_market(
        poisson_sonuc["KG"],
        [(home_kg, home_n), (away_kg, away_n)],
        h2h_stats["KG"] if h2h_stats else None
    )
    sonuc["KG_YOK"] = 100 - sonuc["KG"]

    # 1.5 ve 3.5 Poisson sonuçlarını koruyoruz; 2.5 ana toplam-gol
    # sinyali olarak geliştirilmiş modelden geliyor.
    sonuc["OVER15"] = clamp_olasilik(sonuc["OVER15"])
    sonuc["UNDER15"] = 100 - sonuc["OVER15"]
    sonuc["OVER25"] = clamp_olasilik(sonuc["OVER25"])
    sonuc["UNDER25"] = 100 - sonuc["OVER25"]
    sonuc["OVER35"] = clamp_olasilik(sonuc["OVER35"])
    sonuc["UNDER35"] = 100 - sonuc["OVER35"]
    sonuc["KG"] = clamp_olasilik(sonuc["KG"])
    sonuc["KG_YOK"] = 100 - sonuc["KG"]

    # MS yüzdeleri birlikte 100'e ölçeklenir.
    ms_toplam = sonuc["MS1"] + sonuc["X"] + sonuc["MS2"]
    if ms_toplam > 0:
        sonuc["MS1"] = sonuc["MS1"] / ms_toplam * 100
        sonuc["X"] = sonuc["X"] / ms_toplam * 100
        sonuc["MS2"] = sonuc["MS2"] / ms_toplam * 100

    # Modelin destek gücü: bağımsız kaynaklar aynı tarafa yakınsa yükselir.
    ms_values = [sonuc["MS1"], sonuc["X"], sonuc["MS2"]]
    sonuc["MODEL_GUVEN"] = max(ms_values)
    sonuc["VERI_SAYISI"] = home_n + away_n
    sonuc["H2H_SAYISI"] = h2h_stats["mac"] if h2h_stats else 0

    return sonuc


def market_onerileri_olustur(poisson_sonuc, home_corner, away_corner, home_name, away_name):
    """Model olasılıklarını tek ekranda okunabilir piyasa çıktısına dönüştürür."""
    markets = [
        ("MS1", poisson_sonuc["MS1"], "Poisson maç sonucu modeli"),
        ("MS X", poisson_sonuc["X"], "Poisson maç sonucu modeli"),
        ("MS2", poisson_sonuc["MS2"], "Poisson maç sonucu modeli"),
        ("1.5 ÜSTÜ", poisson_sonuc["OVER15"], "Poisson toplam gol modeli"),
        ("2.5 ÜSTÜ", poisson_sonuc["OVER25"], "Poisson toplam gol modeli"),
        ("2.5 ALTI", poisson_sonuc["UNDER25"], "Poisson toplam gol modeli"),
        ("3.5 ÜSTÜ", poisson_sonuc["OVER35"], "Poisson toplam gol modeli"),
        ("3.5 ALTI", poisson_sonuc["UNDER35"], "Poisson toplam gol modeli"),
        ("KG VAR", poisson_sonuc["KG"], "Poisson karşılıklı gol modeli"),
        ("KG YOK", poisson_sonuc["KG_YOK"], "Poisson karşılıklı gol modeli"),
        (f"İLK GOL - {home_name}", poisson_sonuc["FIRST_HOME"], "İlk gol Poisson yaklaşımı"),
        (f"İLK GOL - {away_name}", poisson_sonuc["FIRST_AWAY"], "İlk gol Poisson yaklaşımı"),
    ]

    if home_corner.get("mac", 0) > 0 and away_corner.get("mac", 0) > 0:
        corner_markets = [
            ("8.5 KORNER ÜSTÜ", (home_corner["over85"] + away_corner["over85"]) / 2),
            ("9.5 KORNER ÜSTÜ", (home_corner["over95"] + away_corner["over95"]) / 2),
            ("10.5 KORNER ÜSTÜ", (home_corner["over105"] + away_corner["over105"]) / 2),
            ("11.5 KORNER ÜSTÜ", (home_corner["over115"] + away_corner["over115"]) / 2),
        ]
        for ad, ol in corner_markets:
            markets.append((ad, ol, "İki takımın geçmiş korner verilerinin ortalaması"))
            markets.append((ad.replace(" ÜSTÜ", " ALTI"), 100 - ol, "İki takımın geçmiş korner verilerinin ortalaması"))

    markets.sort(key=lambda x: x[1], reverse=True)
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

    analiz_penceresi = tk.Toplevel(
        root
    )

    analiz_penceresi.title(
        f"📊 {home_name} - {away_name}"
    )

    analiz_penceresi.geometry(
        "1100x850"
    )

    analiz_penceresi.minsize(
        900,
        650
    )

    baslik = tk.Label(
        analiz_penceresi,
        text=(
            f"⚽ {home_name}  vs  "
            f"{away_name}"
        ),
        font=("Arial", 20, "bold")
    )

    baslik.pack(
        pady=(15, 5)
    )

    alt = tk.Label(
        analiz_penceresi,
        text=(
            f"{league.get('country', '')} | "
            f"{league.get('name', '')} | "
            f"Maç ID: {fixture_id}"
        ),
        font=("Arial", 10)
    )

    alt.pack(
        pady=(0, 10)
    )

    text_frame = tk.Frame(
        analiz_penceresi
    )

    text_frame.pack(
        fill="both",
        expand=True,
        padx=15,
        pady=10
    )

    scrollbar = tk.Scrollbar(
        text_frame
    )

    scrollbar.pack(
        side="right",
        fill="y"
    )

    analiz_text = tk.Text(
        text_frame,
        font=("Consolas", 10),
        wrap="word",
        yscrollcommand=scrollbar.set
    )

    analiz_text.pack(
        side="left",
        fill="both",
        expand=True
    )

    scrollbar.config(
        command=analiz_text.yview
    )

    analiz_text.insert(
        "end",
        "⏳ MAÇ ANALİZİ HAZIRLANIYOR...\n\n"
        "Son 10 maçlar,\n"
        "ev/deplasman formu,\n"
        "korner istatistikleri,\n"
        "H2H, puan durumu,\n"
        "API tahmini, oranlar\n"
        "ve Poisson modeli hesaplanıyor..."
    )

    analiz_text.config(
        state="disabled"
    )

    def yaz(metin):

        analiz_text.config(
            state="normal"
        )

        analiz_text.delete(
            "1.0",
            "end"
        )

        analiz_text.insert(
            "end",
            metin
        )

        analiz_text.config(
            state="disabled"
        )

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

            # Gelişmiş ensemble model için maç verilerini açıkça aktar.
            globals()["_MODEL_HOME_MATCHES"] = home_last_matches
            globals()["_MODEL_AWAY_MATCHES"] = away_last_matches
            globals()["_MODEL_HOME_ID"] = home_id
            globals()["_MODEL_AWAY_ID"] = away_id

            gelismis_sonuc = gelismis_model_hesapla(
                poisson_sonuc,
                home_form,
                away_form,
                home_venue,
                away_venue,
                h2h,
                prediction
            )

            marketler = market_onerileri_olustur(
                gelismis_sonuc,
                home_corner,
                away_corner,
                home_name,
                away_name
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

            for ad, olasilik, kaynak in marketler[:7]:
                satirlar.append(
                    f"• {ad}: %{olasilik:.1f} | {guven_seviyesi(olasilik)}"
                )

            satirlar.append("")
            satirlar.append(
                f"🥅 Tahmini skor: {poisson_sonuc['skor_home']}-{poisson_sonuc['skor_away']}"
            )
            satirlar.append(
                f"⚽ Beklenen gol: {home_lambda:.2f} - {away_lambda:.2f}"
            )
            satirlar.append(
                "Not: Bu bölüm istatistiksel model çıktısıdır; kesin sonuç veya garanti değildir."
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
                f"{gelismis_sonuc['MS1']:.1f}%"
            )

            satirlar.append(
                f"MS X:  "
                f"{gelismis_sonuc['X']:.1f}%"
            )

            satirlar.append(
                f"MS 2:  "
                f"{gelismis_sonuc['MS2']:.1f}%"
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
                f"2.5 ÜST: {gelismis_sonuc['OVER25']:.1f}% | 2.5 ALT: {gelismis_sonuc['UNDER25']:.1f}%"
            )
            satirlar.append(
                f"3.5 ÜST: {poisson_sonuc['OVER35']:.1f}% | 3.5 ALT: {poisson_sonuc['UNDER35']:.1f}%"
            )
            satirlar.append(
                f"KG VAR: {gelismis_sonuc['KG']:.1f}% | KG YOK: {gelismis_sonuc['KG_YOK']:.1f}%"
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
                gelismis_sonuc["MS1"],
                gelismis_sonuc["X"],
                gelismis_sonuc["MS2"]
            )

            if en_yuksek_ms == gelismis_sonuc["MS1"]:

                model_ms = "MS1"

            elif en_yuksek_ms == gelismis_sonuc["X"]:

                model_ms = "MS X"

            else:

                model_ms = "MS2"

            satirlar.append(
                f"Model MS sonucu: "
                f"{model_ms}"
            )

            satirlar.append(
                f"Model MS olasılıkları: MS1 %{gelismis_sonuc['MS1']:.1f} | "
                f"X %{gelismis_sonuc['X']:.1f} | MS2 %{gelismis_sonuc['MS2']:.1f}"
            )

            satirlar.append(
                f"Model veri gücü: %{gelismis_sonuc['MODEL_GUVEN']:.1f} | "
                f"Son maç örneklemi: {gelismis_sonuc['VERI_SAYISI']}"
            )

            satirlar.append(
                f"Model skor: "
                f"{poisson_sonuc['skor_home']}-"
                f"{poisson_sonuc['skor_away']}"
            )

            satirlar.append(
                f"2.5 ÜST olasılığı: {gelismis_sonuc['OVER25']:.1f}% | 2.5 ALT: {gelismis_sonuc['UNDER25']:.1f}%"
            )

            satirlar.append(
                f"KG VAR olasılığı: {gelismis_sonuc['KG']:.1f}% | KG YOK: {gelismis_sonuc['KG_YOK']:.1f}%"
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
                f"📚 Veri kapsamı: Son maç verisi {gelismis_sonuc['VERI_SAYISI']} | "
                f"H2H {gelismis_sonuc['H2H_SAYISI']}"
            )
            satirlar.append(
                "🧠 Model: Poisson + form + saha formu + H2H + API tahmini"
            )
            satirlar.append(
                "⚠️ Yüzdeler yapay olarak yükseltilmez; veri azsa ilgili sinyalin ağırlığı düşürülür."
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

        except Exception as e:

            hata_mesaji = str(e)

            root.after(
                0,
                lambda mesaj=hata_mesaji: yaz(
                    "❌ ANALİZ HATASI\n\n"
                    + mesaj
                )
            )

    threading.Thread(
        target=worker,
        daemon=True
    ).start()


# ============================================================
# ANA PENCERE
# ============================================================

root = tk.Tk()

root.title(
    "⚽ İDDAA MAÇ ANALİZ MERKEZİ"
)

root.geometry(
    "1380x900"
)

root.minsize(
    1050,
    700
)


# ============================================================
# BAŞLIK
# ============================================================

baslik = tk.Label(
    root,
    text="⚽ İDDAA MAÇ ANALİZ MERKEZİ",
    font=("Arial", 27, "bold")
)

baslik.pack(
    pady=(25, 3)
)

alt_baslik = tk.Label(
    root,
    text="Tarih seç • Takım ara • Maçı bul • Analiz et",
    font=("Arial", 13)
)

alt_baslik.pack(
    pady=(0, 15)
)


# ============================================================
# TARİH PANELİ
# ============================================================

tarih_panel = tk.Frame(
    root,
    bd=1,
    relief="solid"
)

tarih_panel.pack(
    fill="x",
    padx=10,
    pady=5
)

tk.Label(
    tarih_panel,
    text="📅 TARİH:",
    font=("Arial", 12, "bold")
).pack(
    side="left",
    padx=8,
    pady=10
)

tk.Button(
    tarih_panel,
    text="◀ ÖNCEKİ GÜN",
    command=lambda: tarih_degistir(-1)
).pack(
    side="left",
    padx=5
)

tarih_var = tk.StringVar(
    value=bugunun_tarihi()
)

tk.Entry(
    tarih_panel,
    textvariable=tarih_var,
    width=14,
    font=("Arial", 12, "bold"),
    justify="center"
).pack(
    side="left",
    padx=5
)

tk.Button(
    tarih_panel,
    text="BUGÜN",
    command=bugun
).pack(
    side="left",
    padx=5
)

tk.Button(
    tarih_panel,
    text="SONRAKİ GÜN ▶",
    command=lambda: tarih_degistir(1)
).pack(
    side="left",
    padx=5
)

tarih_getir_butonu = tk.Button(
    tarih_panel,
    text="📅 TARİHİ GETİR",
    command=tum_maclari_getir
)

tarih_getir_butonu.pack(
    side="left",
    padx=10
)


# ============================================================
# TAKIM ARAMA PANELİ
# ============================================================

takim_panel = tk.Frame(
    root,
    bd=1,
    relief="solid"
)

takim_panel.pack(
    fill="x",
    padx=10,
    pady=5
)

tk.Label(
    takim_panel,
    text="🔎 TAKIM ARA:",
    font=("Arial", 12, "bold")
).pack(
    side="left",
    padx=8,
    pady=10
)

takim_ara_var = tk.StringVar()

takim_entry = tk.Entry(
    takim_panel,
    textvariable=takim_ara_var,
    width=28,
    font=("Arial", 11)
)

takim_entry.pack(
    side="left",
    padx=5
)

arama_butonu = tk.Button(
    takim_panel,
    text="🔎 ARA",
    command=takim_ara
)

arama_butonu.pack(
    side="left",
    padx=5
)

takim_combo = ttk.Combobox(
    takim_panel,
    width=42,
    state="readonly",
    font=("Arial", 10)
)

takim_combo.pack(
    side="left",
    padx=5
)

takim_mac_butonu = tk.Button(
    takim_panel,
    text="⚽ TAKIM MAÇLARINI GETİR",
    command=takim_maclarini_yukle
)

takim_mac_butonu.pack(
    side="left",
    padx=8
)

takim_bilgisi_var = tk.StringVar(
    value=""
)

tk.Label(
    takim_panel,
    textvariable=takim_bilgisi_var
).pack(
    side="left",
    padx=5
)


# Enter ile takım arama
takim_entry.bind(
    "<Return>",
    lambda event: takim_ara()
)


# ============================================================
# DURUM
# ============================================================

durum_var = tk.StringVar(
    value="Bugünün maçları yükleniyor..."
)

tk.Label(
    root,
    textvariable=durum_var,
    font=("Arial", 11, "bold")
).pack(
    pady=5
)

baslik_var = tk.StringVar(
    value=(
        f"⚽ {bugunun_tarihi()} "
        "GÜNÜN MAÇLARI"
    )
)

tk.Label(
    root,
    textvariable=baslik_var,
    font=("Arial", 15, "bold")
).pack(
    pady=5
)


# ============================================================
# MAÇ LİSTESİ SCROLL ALANI
# ============================================================

ana_frame = tk.Frame(
    root
)

ana_frame.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=5
)

canvas = tk.Canvas(
    ana_frame
)

scrollbar = ttk.Scrollbar(
    ana_frame,
    orient="vertical",
    command=canvas.yview
)

mac_frame = tk.Frame(
    canvas
)

mac_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(
        scrollregion=canvas.bbox("all")
    )
)

canvas_window = canvas.create_window(
    (0, 0),
    window=mac_frame,
    anchor="nw"
)

canvas.configure(
    yscrollcommand=scrollbar.set
)

canvas.pack(
    side="left",
    fill="both",
    expand=True
)

scrollbar.pack(
    side="right",
    fill="y"
)


def canvas_genislik(event):

    canvas.itemconfig(
        canvas_window,
        width=event.width
    )


canvas.bind(
    "<Configure>",
    canvas_genislik
)


# ============================================================
# MOUSE TEKERLEĞİ
# ============================================================

def mouse_wheel(event):

    canvas.yview_scroll(
        int(
            -1 * (event.delta / 120)
        ),
        "units"
    )


canvas.bind_all(
    "<MouseWheel>",
    mouse_wheel
)


# ============================================================
# BAŞLAT
# ============================================================

root.after(
    300,
    tum_maclari_getir
)

root.mainloop()