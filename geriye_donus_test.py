
import os
import math
import time
from datetime import datetime

import requests


# ============================================================
# AYARLAR
# ============================================================

API_URL = "https://v3.football.api-sports.io"
API_KEY = os.getenv("API_FOOTBALL_KEY")

# Son tamamlanmış sezon: 2025-26
SEASON = 2025

# İlk testte 3 büyük lig. İstersen daha sonra artırabiliriz.
LEAGUES = {
    39: "Premier League",
    140: "La Liga",
    78: "Bundesliga",
}

MAX_FIXTURES_PER_LEAGUE = 0   # 0 = tamamı
MIN_HISTORY = 5               # Maç öncesi en az 5 geçmiş maç
MAX_HISTORY = 10

if not API_KEY:
    raise SystemExit(
        "API_FOOTBALL_KEY bulunamadı.\n\n"
        'VS Code terminalinde:\n'
        '$env:API_FOOTBALL_KEY="API_ANAHTARIN"'
    )


# ============================================================
# API
# ============================================================

def api_get(endpoint, params=None):
    headers = {"x-apisports-key": API_KEY}

    r = requests.get(
        API_URL + "/" + endpoint,
        headers=headers,
        params=params or {},
        timeout=30
    )

    try:
        data = r.json()
    except Exception:
        raise RuntimeError(f"API JSON cevabı okunamadı. HTTP={r.status_code}")

    if r.status_code != 200:
        raise RuntimeError(
            f"API HTTP={r.status_code}: {data.get('errors', data)}"
        )

    errors = data.get("errors")
    if errors:
        raise RuntimeError(str(errors))

    return data.get("response", [])


# ============================================================
# MATEMATİK
# ============================================================

def poisson_pmf(lam, k):
    if lam < 0:
        lam = 0
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def poisson_model(home_lambda, away_lambda):
    max_goal = 10

    hp = [poisson_pmf(home_lambda, i) for i in range(max_goal + 1)]
    ap = [poisson_pmf(away_lambda, i) for i in range(max_goal + 1)]

    norm = sum(hp) * sum(ap)
    if norm <= 0:
        norm = 1

    p1 = px = p2 = over25 = btts = 0.0

    for h in range(max_goal + 1):
        for a in range(max_goal + 1):
            p = (hp[h] * ap[a]) / norm

            if h > a:
                p1 += p
            elif h == a:
                px += p
            else:
                p2 += p

            if h + a >= 3:
                over25 += p

            if h > 0 and a > 0:
                btts += p

    return {
        "MS1": p1,
        "X": px,
        "MS2": p2,
        "OVER25": over25,
        "KG": btts,
    }


def clamp(x, lo=0.001, hi=0.999):
    return max(lo, min(hi, x))


# ============================================================
# MAÇ ÖNCESİ GEÇMİŞ VERİ
# ============================================================

def match_date(fixture):
    return fixture.get("fixture", {}).get("date", "")


def finished(fixture):
    short = fixture.get("fixture", {}).get("status", {}).get("short", "")
    return short in {"FT", "AET", "PEN"}


def team_view(match, team_id):
    """Takım açısından GF/GA/G-B-M çıkarır."""
    h = match["teams"]["home"]
    a = match["teams"]["away"]
    gh = match.get("goals", {}).get("home")
    ga = match.get("goals", {}).get("away")

    if gh is None or ga is None:
        return None

    if h["id"] == team_id:
        gf, g_a = gh, ga
        home = True
    elif a["id"] == team_id:
        gf, g_a = ga, gh
        home = False
    else:
        return None

    if gf > g_a:
        result = "G"
    elif gf == g_a:
        result = "B"
    else:
        result = "M"

    return {
        "gf": gf,
        "ga": g_a,
        "home": home,
        "result": result,
        "over25": (gh + ga >= 3),
        "btts": (gh > 0 and ga > 0),
    }


def previous_matches(team_matches, before_date):
    eligible = [
        m for m in team_matches
        if finished(m) and match_date(m) < before_date
    ]
    eligible.sort(key=match_date, reverse=True)
    return eligible[:MAX_HISTORY]


def form_stats(matches, team_id):
    if not matches:
        return None

    rows = []
    for m in matches:
        row = team_view(m, team_id)
        if row:
            rows.append(row)

    if not rows:
        return None

    n = len(rows)

    gf = sum(x["gf"] for x in rows) / n
    ga = sum(x["ga"] for x in rows) / n

    wins = sum(x["result"] == "G" for x in rows)
    draws = sum(x["result"] == "B" for x in rows)

    points_pct = (wins * 3 + draws) / (n * 3)

    over25 = sum(x["over25"] for x in rows) / n
    btts = sum(x["btts"] for x in rows) / n

    return {
        "n": n,
        "gf": gf,
        "ga": ga,
        "wins": wins,
        "draws": draws,
        "points_pct": points_pct,
        "over25": over25,
        "btts": btts,
    }


def venue_stats(matches, team_id, home_required):
    rows = []

    for m in matches:
        row = team_view(m, team_id)
        if row and row["home"] == home_required:
            rows.append(row)

    if not rows:
        return None

    n = len(rows)

    return {
        "n": n,
        "gf": sum(x["gf"] for x in rows) / n,
        "ga": sum(x["ga"] for x in rows) / n,
        "win": sum(x["result"] == "G" for x in rows) / n,
        "over25": sum(x["over25"] for x in rows) / n,
        "btts": sum(x["btts"] for x in rows) / n,
    }


# ============================================================
# MAÇ İÇİN ÖZELLİKLER
# ============================================================

def build_features(fixture, home_history, away_history):
    home_id = fixture["teams"]["home"]["id"]
    away_id = fixture["teams"]["away"]["id"]

    hf = form_stats(home_history, home_id)
    af = form_stats(away_history, away_id)

    if not hf or not af:
        return None

    hv = venue_stats(home_history, home_id, True)
    av = venue_stats(away_history, away_id, False)

    # Saha verisi yoksa genel form kullanılır.
    h_gf = hv["gf"] if hv else hf["gf"]
    h_ga = hv["ga"] if hv else hf["ga"]
    a_gf = av["gf"] if av else af["gf"]
    a_ga = av["ga"] if av else af["ga"]

    # V4'teki Poisson mantığına yakın, ancak geriye dönük test için
    # sadece maç öncesinde mevcut olan bilgiler kullanılır.
    home_lambda = (0.60 * hf["gf"] + 0.40 * h_gf)
    away_lambda = (0.60 * af["gf"] + 0.40 * a_gf)

    home_lambda = 0.65 * home_lambda + 0.35 * af["ga"]
    away_lambda = 0.65 * away_lambda + 0.35 * hf["ga"]

    home_lambda = max(0.15, min(home_lambda, 4.50))
    away_lambda = max(0.15, min(away_lambda, 4.50))

    pois = poisson_model(home_lambda, away_lambda)

    # Form sinyali: puan gücünü 1X2'ye dağıt.
    form_total = hf["points_pct"] + af["points_pct"]
    if form_total > 0:
        form_home = hf["points_pct"] / form_total
        form_away = af["points_pct"] / form_total
    else:
        form_home = form_away = 0.5

    # Beraberlik için form sinyalini nötr tutuyoruz.
    form_signal = {
        "MS1": form_home,
        "X": 1.0 / 3.0,
        "MS2": form_away,
    }

    # Saha galibiyet sinyali.
    if hv and av and (hv["win"] + av["win"]) > 0:
        venue_home = hv["win"] / (hv["win"] + av["win"])
        venue_away = av["win"] / (hv["win"] + av["win"])
        venue_signal = {
            "MS1": venue_home,
            "X": 1.0 / 3.0,
            "MS2": venue_away,
        }
    else:
        venue_signal = None

    return {
        "pois": pois,
        "form": form_signal,
        "venue": venue_signal,
        "hf": hf,
        "af": af,
        "hv": hv,
        "av": av,
    }


# ============================================================
# MODEL KOMBİNASYONU
# ============================================================

def ensemble_1x2(features, wf, wv):
    wp = 1.0 - wf - wv

    raw = {}
    for k in ("MS1", "X", "MS2"):
        value = wp * features["pois"][k]
        value += wf * features["form"][k]

        if features["venue"]:
            value += wv * features["venue"][k]
        else:
            # Saha verisi yoksa ağırlığı Poisson'a geri ver.
            value += wv * features["pois"][k]

        raw[k] = max(0.000001, value)

    total = sum(raw.values())
    return {k: raw[k] / total for k in raw}


def ensemble_market(features, market, w_emp):
    """Poisson + geçmiş empirik oran."""
    p = features["pois"][market]

    if market == "OVER25":
        empirical = (features["hf"]["over25"] + features["af"]["over25"]) / 2
    else:
        empirical = (features["hf"]["btts"] + features["af"]["btts"]) / 2

    return (1.0 - w_emp) * p + w_emp * empirical


# ============================================================
# PUANLAMA
# ============================================================

def brier_binary(prob, actual):
    return (prob - actual) ** 2


def brier_multiclass(pred, actual_key):
    score = 0.0
    for key in ("MS1", "X", "MS2"):
        actual = 1.0 if key == actual_key else 0.0
        score += (pred[key] - actual) ** 2
    return score


def actual_1x2(fixture):
    gh = fixture["goals"].get("home")
    ga = fixture["goals"].get("away")

    if gh > ga:
        return "MS1"
    if gh == ga:
        return "X"
    return "MS2"


# ============================================================
# VERİYİ ÇEK
# ============================================================

def load_league(league_id, league_name):
    print(f"\n📥 {league_name} ({SEASON}) verisi alınıyor...")

    fixtures = api_get(
        "fixtures",
        {
            "league": league_id,
            "season": SEASON,
        }
    )

    fixtures = [
        f for f in fixtures
        if finished(f)
        and f.get("teams", {}).get("home", {}).get("id")
        and f.get("teams", {}).get("away", {}).get("id")
        and f.get("goals", {}).get("home") is not None
        and f.get("goals", {}).get("away") is not None
    ]

    fixtures.sort(key=match_date)

    if MAX_FIXTURES_PER_LEAGUE:
        fixtures = fixtures[:MAX_FIXTURES_PER_LEAGUE]

    print(f"   ✅ {len(fixtures)} tamamlanmış maç")

    return fixtures


def group_team_matches(fixtures):
    grouped = {}

    for f in fixtures:
        for side in ("home", "away"):
            tid = f["teams"][side]["id"]
            grouped.setdefault(tid, []).append(f)

    for tid in grouped:
        grouped[tid].sort(key=match_date)

    return grouped


# ============================================================
# GERİYE DÖNÜK TEST
# ============================================================

def prepare_cases(fixtures):
    grouped = group_team_matches(fixtures)

    cases = []

    for f in fixtures:
        dt = match_date(f)

        hid = f["teams"]["home"]["id"]
        aid = f["teams"]["away"]["id"]

        hh = previous_matches(grouped.get(hid, []), dt)
        ah = previous_matches(grouped.get(aid, []), dt)

        if len(hh) < MIN_HISTORY or len(ah) < MIN_HISTORY:
            continue

        features = build_features(f, hh, ah)
        if not features:
            continue

        cases.append({
            "fixture": f,
            "features": features,
            "actual": actual_1x2(f),
            "actual_over25": (
                1.0 if
                f["goals"]["home"] + f["goals"]["away"] >= 3
                else 0.0
            ),
            "actual_kg": (
                1.0 if
                f["goals"]["home"] > 0 and f["goals"]["away"] > 0
                else 0.0
            ),
        })

    return cases


def evaluate_1x2(cases, wf, wv):
    total = 0.0
    correct = 0
    n = 0

    for c in cases:
        pred = ensemble_1x2(c["features"], wf, wv)
        total += brier_multiclass(pred, c["actual"])

        if max(pred, key=pred.get) == c["actual"]:
            correct += 1

        n += 1

    if n == 0:
        return None

    return {
        "brier": total / n,
        "accuracy": correct / n,
        "n": n,
    }


def evaluate_market(cases, market, w_emp):
    total = 0.0
    correct = 0
    n = 0

    actual_key = "actual_over25" if market == "OVER25" else "actual_kg"

    for c in cases:
        p = ensemble_market(c["features"], market, w_emp)
        actual = c[actual_key]

        total += brier_binary(p, actual)

        if (p >= 0.50 and actual == 1.0) or (p < 0.50 and actual == 0.0):
            correct += 1

        n += 1

    if n == 0:
        return None

    return {
        "brier": total / n,
        "accuracy": correct / n,
        "n": n,
    }


def optimize_1x2(cases):
    best = None

    # Form + saha ağırlığını tarıyoruz.
    for wf_i in range(0, 31, 2):
        wf = wf_i / 100

        for wv_i in range(0, 21, 2):
            wv = wv_i / 100

            if wf + wv > 0.45:
                continue

            result = evaluate_1x2(cases, wf, wv)

            if result is None:
                continue

            if best is None or result["brier"] < best["brier"]:
                best = {
                    "wf": wf,
                    "wv": wv,
                    **result,
                }

    return best


def optimize_market(cases, market):
    best = None

    for wi in range(0, 81, 5):
        w = wi / 100
        result = evaluate_market(cases, market, w)

        if result is None:
            continue

        if best is None or result["brier"] < best["brier"]:
            best = {
                "w_emp": w,
                **result,
            }

    return best


def reliability_bucket(cases, market, threshold):
    rows = []

    for c in cases:
        if market == "1X2":
            p = ensemble_1x2(c["features"], 0.10, 0.08)
            prob = max(p.values())
            actual = 1.0 if max(p, key=p.get) == c["actual"] else 0.0
        else:
            p = ensemble_market(
                c["features"],
                market,
                threshold
            )
            prob = max(p, 1 - p)
            actual = (
                c["actual_over25"] if market == "OVER25"
                else c["actual_kg"]
            )
            actual = 1.0 if (p >= 0.50) == (actual == 1.0) else 0.0

        rows.append((prob, actual))

    buckets = [
        (0.50, 0.55),
        (0.55, 0.60),
        (0.60, 0.65),
        (0.65, 0.70),
        (0.70, 0.75),
        (0.75, 1.01),
    ]

    out = []

    for lo, hi in buckets:
        selected = [x for x in rows if lo <= x[0] < hi]

        if not selected:
            continue

        out.append({
            "range": f"%{lo*100:.0f}-{min(100, hi*100):.0f}",
            "n": len(selected),
            "accuracy": sum(x[1] for x in selected) / len(selected),
        })

    return out


# ============================================================
# RAPOR
# ============================================================

def main():
    print("=" * 70)
    print("📊 İDDAA ANALİZ MOTORU — GERİYE DÖNÜK TEST")
    print("=" * 70)
    print(f"Sezon: {SEASON}")
    print("Amaç: geçmiş maçlarda model kalibrasyonunu ölçmek.")
    print("Not: Bu test geçmiş performansı ölçer; gelecekte garanti sağlamaz.")

    all_cases = []

    for league_id, league_name in LEAGUES.items():
        try:
            fixtures = load_league(league_id, league_name)
            cases = prepare_cases(fixtures)

            print(f"   🧪 Teste uygun maç: {len(cases)}")

            all_cases.extend(cases)

            # API'yi gereksiz zorlamamak için ligler arasında kısa bekleme.
            time.sleep(1)

        except Exception as e:
            print(f"   ❌ {league_name}: {e}")

    if not all_cases:
        print("\n❌ Test için yeterli veri oluşmadı.")
        return

    print("\n" + "=" * 70)
    print(f"TOPLAM TEST MAÇI: {len(all_cases)}")
    print("=" * 70)

    # --------------------------------------------------------
    # 1X2 ağırlık optimizasyonu
    # --------------------------------------------------------
    best_1x2 = optimize_1x2(all_cases)

    print("\n🏆 1X2 AĞIRLIK TESTİ")
    print("-" * 70)
    print(
        f"Form ağırlığı : %{best_1x2['wf']*100:.0f}\n"
        f"Saha ağırlığı : %{best_1x2['wv']*100:.0f}\n"
        f"Poisson       : %{(1-best_1x2['wf']-best_1x2['wv'])*100:.0f}\n"
        f"İsabet        : %{best_1x2['accuracy']*100:.2f}\n"
        f"Brier skoru   : {best_1x2['brier']:.4f}"
    )

    # --------------------------------------------------------
    # 2.5 ÜST
    # --------------------------------------------------------
    best_over = optimize_market(all_cases, "OVER25")

    print("\n⚽ 2.5 ÜST AĞIRLIK TESTİ")
    print("-" * 70)
    print(
        f"Empirik veri ağırlığı : %{best_over['w_emp']*100:.0f}\n"
        f"Poisson ağırlığı      : %{(1-best_over['w_emp'])*100:.0f}\n"
        f"İsabet                : %{best_over['accuracy']*100:.2f}\n"
        f"Brier skoru           : {best_over['brier']:.4f}"
    )

    # --------------------------------------------------------
    # KG VAR
    # --------------------------------------------------------
    best_kg = optimize_market(all_cases, "KG")

    print("\n🥅 KG VAR AĞIRLIK TESTİ")
    print("-" * 70)
    print(
        f"Empirik veri ağırlığı : %{best_kg['w_emp']*100:.0f}\n"
        f"Poisson ağırlığı      : %{(1-best_kg['w_emp'])*100:.0f}\n"
        f"İsabet                : %{best_kg['accuracy']*100:.2f}\n"
        f"Brier skoru           : {best_kg['brier']:.4f}"
    )

    # --------------------------------------------------------
    # Lig bazında kaba dağılım
    # --------------------------------------------------------
    print("\n📈 YÜKSEK MODEL OLASILIKLARININ GEÇMİŞ İSABETİ")
    print("-" * 70)

    for market, w in (
        ("OVER25", best_over["w_emp"]),
        ("KG", best_kg["w_emp"]),
    ):
        buckets = reliability_bucket(all_cases, market, w)

        print(f"\n{market}:")
        for row in buckets:
            print(
                f"  {row['range']:>9}  | "
                f"{row['n']:>4} maç | "
                f"gerçekleşme/isabet %{row['accuracy']*100:>6.2f}"
            )

    print("\n" + "=" * 70)
    print("✅ TEST TAMAMLANDI")
    print("=" * 70)
    print(
        "\nBu sonuçlardan sonra gercek_analiz.py içindeki ağırlıkları "
        "geçmiş veride ölçülen değerlere göre güncelleyebiliriz."
    )


if __name__ == "__main__":
    main()
