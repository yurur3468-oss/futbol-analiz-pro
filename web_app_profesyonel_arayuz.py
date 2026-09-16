import os
import html
from datetime import date
from pathlib import Path

import streamlit as st

# ============================================================
# STREAMLIT SECRET
# ============================================================

try:
    if "API_FOOTBALL_KEY" in st.secrets and st.secrets["API_FOOTBALL_KEY"]:
        os.environ["API_FOOTBALL_KEY"] = str(st.secrets["API_FOOTBALL_KEY"])
except Exception:
    pass


# ============================================================
# WEB CORE
# ============================================================

try:
    from web_core import (
        gunun_maclarini_getir_web,
        analiz_mac_web,
        API_KEY,
    )
except Exception as exc:
    st.error("Web analiz motoru yüklenemedi.")
    st.exception(exc)
    st.stop()


# ============================================================
# SAYFA AYARLARI
# ============================================================

st.set_page_config(
    page_title="Yarasa İddaa | Futbol Analiz Pro",
    page_icon="⚽",
    layout="wide",
)


# ============================================================
# TASARIM
# ============================================================

st.markdown(
    """
<style>
.stApp {
    background: #07101d;
    color: #f8fafc;
}

.block-container {
    max-width: 1250px;
    padding-top: 1.2rem;
    padding-bottom: 3rem;
}

/* Logo alanı */
.logo-wrap {
    background: #091525;
    border: 1px solid #1d3855;
    border-radius: 16px;
    padding: 10px;
    margin-bottom: 18px;
    box-shadow: 0 8px 30px rgba(0,0,0,.20);
}

.logo-wrap img {
    display: block;
    width: 100%;
    max-height: 300px;
    object-fit: contain;
    border-radius: 12px;
}

/* Üst başlık */
.hero {
    background: linear-gradient(135deg, #0d1c30, #101d31);
    border: 1px solid #263852;
    padding: 20px 24px;
    border-radius: 14px;
    margin-bottom: 18px;
}

.hero h1 {
    margin: 0;
    font-size: 32px;
    color: #f8fafc;
    font-weight: 900;
}

.sub {
    color: #94a3b8;
    margin-top: 6px;
    font-size: 15px;
}

/* Analiz raporu */
.report-wrap {
    margin-top: 20px;
}

.report-title {
    font-size: 25px;
    font-weight: 900;
    margin: 0 0 16px 0;
    color: #f8fafc;
}

.section-title {
    margin: 24px 0 10px 0;
    padding: 12px 15px;
    background: #101d31;
    border: 1px solid #263852;
    border-left: 4px solid #20b8ff;
    border-radius: 9px;
    color: #eaf4ff;
    font-size: 18px;
    font-weight: 800;
}

.section-sub {
    margin: 10px 0 8px 0;
    color: #7dd3fc;
    font-weight: 700;
    font-size: 15px;
}

.signal-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(330px, 1fr));
    gap: 12px;
    margin: 10px 0 18px 0;
}

.signal-card {
    background: linear-gradient(135deg, #12233b, #0f1b2d);
    border: 1px solid #2c4565;
    border-radius: 11px;
    padding: 15px 17px;
    min-height: 86px;
    box-shadow: 0 4px 15px rgba(0,0,0,.16);
}

.signal-name {
    color: #f8fafc;
    font-size: 16px;
    font-weight: 800;
    margin-bottom: 7px;
}

.signal-prob {
    color: #22c55e;
    font-size: 18px;
    font-weight: 900;
}

.signal-level {
    color: #86efac;
    font-size: 13px;
    font-weight: 700;
    margin-left: 6px;
}

.signal-source {
    color: #94a3b8;
    font-size: 12px;
    margin-top: 7px;
    line-height: 1.45;
}

.data-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 10px;
    margin: 10px 0 16px 0;
}

.data-card {
    background: #101b2c;
    border: 1px solid #253b57;
    border-radius: 10px;
    padding: 12px 14px;
}

.data-label {
    color: #94a3b8;
    font-size: 12px;
    margin-bottom: 4px;
}

.data-value {
    color: #f8fafc;
    font-size: 15px;
    font-weight: 700;
    line-height: 1.45;
}

.simple-line {
    background: #0f1a2b;
    border: 1px solid #1f334d;
    border-radius: 8px;
    padding: 9px 12px;
    margin: 7px 0;
    color: #dbeafe;
    line-height: 1.5;
}

.highlight-line {
    background: #10263a;
    border: 1px solid #275b78;
    border-radius: 9px;
    padding: 12px 14px;
    margin: 8px 0;
    color: #f8fafc;
    font-weight: 700;
}

.note-line {
    color: #94a3b8;
    font-size: 13px;
    padding: 7px 2px;
    line-height: 1.5;
}

.divider {
    height: 1px;
    background: #263852;
    margin: 20px 0;
}

.score-box {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 12px;
    margin: 12px 0 18px 0;
}

.score-item {
    background: #111f33;
    border: 1px solid #2a4564;
    border-radius: 10px;
    padding: 14px;
}

.score-label {
    color: #94a3b8;
    font-size: 12px;
}

.score-value {
    color: #f8fafc;
    font-size: 21px;
    font-weight: 900;
    margin-top: 4px;
}

@media (max-width: 700px) {
    .hero h1 {
        font-size: 27px;
    }

    .signal-grid,
    .data-grid,
    .score-box {
        grid-template-columns: 1fr;
    }
}
</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# LOGO
# ============================================================

logo_path = Path(__file__).resolve().parent / "yarasa_banner.png"

if logo_path.exists():
    st.markdown('<div class="logo-wrap">', unsafe_allow_html=True)
    st.image(str(logo_path), width="stretch")
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.warning(
        "yarasa_banner.png bulunamadı. Logo dosyasını web_app_profesyonel_arayuz.py ile aynı klasöre koy."
    )

st.markdown(
    """
<div class="hero">
    <h1>⚽ YARASA İDDAA</h1>
    <div class="sub">Profesyonel Futbol Analiz Merkezi</div>
</div>
""",
    unsafe_allow_html=True,
)


# ============================================================
# API KONTROLÜ
# ============================================================

if not API_KEY:
    st.error(
        "API-Football anahtarı bulunamadı. Streamlit Secrets veya "
        "API_FOOTBALL_KEY ortam değişkeni gerekli."
    )
    st.stop()


# ============================================================
# SESSION STATE
# ============================================================

if "matches" not in st.session_state:
    st.session_state.matches = []

if "analysis" not in st.session_state:
    st.session_state.analysis = None


# ============================================================
# MAÇLARI GETİR
# ============================================================

col1, col2 = st.columns([1, 2])

with col1:
    selected_date = st.date_input(
        "📅 Maç tarihi",
        value=date.today(),
    )

with col2:
    if st.button(
        "🔄 MAÇLARI GETİR",
        use_container_width=True,
    ):
        with st.spinner("Maçlar getiriliyor..."):
            st.session_state.matches = gunun_maclarini_getir_web(
                selected_date.isoformat()
            )
            st.session_state.analysis = None


matches = st.session_state.matches


# ============================================================
# MAÇ SEÇİMİ
# ============================================================

if not matches:
    st.info("Tarih seçip **MAÇLARI GETİR** butonuna bas.")

else:
    st.success(f"{len(matches)} maç bulundu.")

    labels = []

    for m in matches:
        h = (
            m.get("teams", {})
            .get("home", {})
            .get("name", "Ev Sahibi")
        )

        a = (
            m.get("teams", {})
            .get("away", {})
            .get("name", "Deplasman")
        )

        league = m.get("league", {}).get("name", "")

        dt = m.get("fixture", {}).get("date", "")

        labels.append(
            f"{h} — {a} | {league} | "
            f"{dt[11:16] if len(dt) >= 16 else ''}"
        )

    idx = st.selectbox(
        "⚽ Analiz edilecek maç",
        range(len(labels)),
        format_func=lambda i: labels[i],
    )

    if st.button(
        "🎯 MAÇI ANALİZ ET",
        type="primary",
        use_container_width=True,
    ):
        with st.spinner(
            "Analiz motoru çalışıyor... form, gol, korner, kart ve ilk yarı verileri hesaplanıyor..."
        ):
            st.session_state.analysis = analiz_mac_web(
                matches[idx]
            )


# ============================================================
# YARDIMCI FONKSİYONLAR
# ============================================================

def esc(s):
    return html.escape(str(s), quote=True)


def render_signal(line, source=None):
    # "• Pazar: %xx.x | GÜÇ" formatını güvenli biçimde ayırır.
    text = line.strip().lstrip("•").strip()

    prob = ""
    level = ""
    name = text

    if ":" in text:
        name, rest = text.split(":", 1)
        rest = rest.strip()

        if "|" in rest:
            prob, level = [
                x.strip()
                for x in rest.split("|", 1)
            ]
        else:
            prob = rest

    elif "|" in text:
        name, rest = [
            x.strip()
            for x in text.split("|", 1)
        ]
        prob = rest

    src = source or "Model çıktısı"

    return f"""
    <div class="signal-card">
        <div class="signal-name">{esc(name)}</div>
        <div>
            <span class="signal-prob">{esc(prob)}</span>
            <span class="signal-level">{esc(level)}</span>
        </div>
        <div class="signal-source">↳ {esc(src)}</div>
    </div>
    """


# ============================================================
# ANALİZ RAPORU
# ============================================================

def render_analysis(text):
    lines = text.splitlines()

    st.markdown(
        '<div class="report-wrap">'
        '<div class="report-title">📊 MAÇ ANALİZ RAPORU</div>',
        unsafe_allow_html=True,
    )

    # Hata durumu
    if text.startswith("❌ ANALİZ HATASI"):
        st.error(
            text.replace("❌ ANALİZ HATASI", "").strip()
        )
        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )
        return

    i = 0
    signal_html = []

    while i < len(lines):
        raw = lines[i].strip()

        if not raw or set(raw) <= {"═", "─", "-"}:
            i += 1
            continue

        # ----------------------------------------------------
        # ÖNE ÇIKAN MODEL SONUÇLARI
        # ----------------------------------------------------

        if raw.startswith("🎯 ÖNE ÇIKAN MODEL SONUÇLARI"):
            st.markdown(
                f'<div class="section-title">{esc(raw)}</div>',
                unsafe_allow_html=True,
            )

            i += 1

            while i < len(lines):
                r = lines[i].strip()

                if not r:
                    i += 1
                    continue

                if r.startswith("• Güçlü sinyal sayısı:"):
                    st.markdown(
                        f'<div class="highlight-line">{esc(r)}</div>',
                        unsafe_allow_html=True,
                    )
                    i += 1
                    break

                if r.startswith("• "):
                    src = None

                    if (
                        i + 1 < len(lines)
                        and lines[i + 1].strip().startswith("↳")
                    ):
                        src = (
                            lines[i + 1]
                            .strip()
                            .lstrip("↳")
                            .strip()
                        )
                        i += 1

                    signal_html.append(
                        render_signal(r, src)
                    )

                else:
                    break

                i += 1

            if signal_html:
                st.markdown(
                    '<div class="signal-grid">'
                    + "".join(signal_html)
                    + "</div>",
                    unsafe_allow_html=True,
                )
                signal_html = []

            continue

        # ----------------------------------------------------
        # TAHMİNİ SKOR / BEKLENEN GOL
        # ----------------------------------------------------

        if (
            raw.startswith("🥅 Tahmini skor:")
            or raw.startswith("⚽ Beklenen gol:")
        ):
            score_items = []

            while i < len(lines):
                r = lines[i].strip()

                if r.startswith("🥅 Tahmini skor:"):
                    score_items.append(
                        (
                            "Tahmini skor",
                            r.split(":", 1)[1].strip(),
                        )
                    )

                elif r.startswith("⚽ Beklenen gol:"):
                    score_items.append(
                        (
                            "Beklenen gol",
                            r.split(":", 1)[1].strip(),
                        )
                    )

                else:
                    break

                i += 1

            st.markdown(
                '<div class="score-box">'
                + "".join(
                    f"""
                    <div class="score-item">
                        <div class="score-label">{esc(a)}</div>
                        <div class="score-value">{esc(b)}</div>
                    </div>
                    """
                    for a, b in score_items
                )
                + "</div>",
                unsafe_allow_html=True,
            )

            continue

        # ----------------------------------------------------
        # BÜYÜK BÖLÜM BAŞLIKLARI
        # ----------------------------------------------------

        if (
            len(raw) < 70
            and (
                raw.isupper()
                or raw.startswith(
                    (
                        "🏠 ",
                        "✈️ ",
                        "🏟 ",
                        "🚩 ",
                        "🟨 ",
                        "🟥 ",
                        "⏱️ ",
                        "🎯 ",
                        "⚽ ",
                        "📊 ",
                    )
                )
            )
        ):
            st.markdown(
                f'<div class="section-title">{esc(raw)}</div>',
                unsafe_allow_html=True,
            )
            i += 1
            continue

        # ----------------------------------------------------
        # TAKIM ALT BAŞLIKLARI
        # ----------------------------------------------------

        if raw.startswith(("🏠 ", "✈️ ")) and len(raw) < 55:
            st.markdown(
                f'<div class="section-sub">{esc(raw)}</div>',
                unsafe_allow_html=True,
            )
            i += 1
            continue

        # ----------------------------------------------------
        # NOT / MODEL
        # ----------------------------------------------------

        if raw.startswith("Not:") or raw.startswith("Model:"):
            st.markdown(
                f'<div class="note-line">{esc(raw)}</div>',
                unsafe_allow_html=True,
            )

        elif raw.startswith("   "):
            st.markdown(
                f'<div class="simple-line">{esc(raw.strip())}</div>',
                unsafe_allow_html=True,
            )

        elif raw.startswith("• "):
            st.markdown(
                f'<div class="highlight-line">{esc(raw)}</div>',
                unsafe_allow_html=True,
            )

        else:
            st.markdown(
                f'<div class="simple-line">{esc(raw)}</div>',
                unsafe_allow_html=True,
            )

        i += 1

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


# ============================================================
# ANALİZİ GÖSTER
# ============================================================

if st.session_state.analysis:
    render_analysis(
        st.session_state.analysis
    )
