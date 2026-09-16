import os
import html
from datetime import date
from pathlib import Path
import streamlit as st

# ------------------------------------------------------------
# API ANAHTARINI STREAMLIT SECRETS'TAN AL
# ------------------------------------------------------------
try:
    if "API_FOOTBALL_KEY" in st.secrets and st.secrets["API_FOOTBALL_KEY"]:
        os.environ["API_FOOTBALL_KEY"] = str(st.secrets["API_FOOTBALL_KEY"])
except Exception:
    pass

try:
    from web_core import gunun_maclarini_getir_web, analiz_mac_web, API_KEY
except Exception as exc:
    st.error("Web analiz motoru yüklenemedi.")
    st.exception(exc)
    st.stop()

st.set_page_config(
    page_title="Yarasa Analiz",
    page_icon="⚽",
    layout="wide"
)

# ------------------------------------------------------------
# PROFESYONEL TASARIM
# ------------------------------------------------------------
st.markdown("""
<style>
.stApp {
    background: #070f1d;
    color: #f8fafc;
}

.block-container {
    max-width: 1320px;
    padding-top: 1.0rem;
    padding-bottom: 3rem;
}

/* Ana banner */
.yarasa-banner {
    position: relative;
    width: 100%;
    min-height: 175px;
    overflow: hidden;
    border-radius: 16px;
    border: 1px solid #14532d;
    margin: 0 0 22px 0;
    background:
        radial-gradient(circle at 75% 20%, rgba(20,184,166,.18), transparent 30%),
        linear-gradient(135deg, #02140f 0%, #071c22 45%, #06111d 100%);
    box-shadow: 0 12px 35px rgba(0,0,0,.38);
}

.yarasa-banner:before,
.yarasa-banner:after {
    content: "";
    position: absolute;
    height: 3px;
    width: 48%;
    background: linear-gradient(90deg, transparent, #22c55e, #39ff88);
    transform: rotate(-18deg);
    opacity: .9;
}

.yarasa-banner:before {
    left: -7%;
    top: 38px;
}

.yarasa-banner:after {
    left: -2%;
    top: 88px;
    opacity: .45;
}

.banner-inner {
    position: relative;
    z-index: 2;
    min-height: 175px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 24px;
    padding: 20px 35px;
}

.bat-logo {
    width: 145px;
    min-width: 145px;
    height: 145px;
    display: flex;
    align-items: center;
    justify-content: center;
    filter: drop-shadow(0 0 13px rgba(34,197,94,.35));
}

.banner-text {
    text-align: left;
}

.banner-title {
    margin: 0;
    font-size: 52px;
    line-height: 1;
    font-weight: 950;
    letter-spacing: 1px;
    color: #f8fafc;
    text-transform: uppercase;
}

.banner-title span {
    color: #22e66b;
    text-shadow: 0 0 16px rgba(34,230,107,.18);
}

.banner-subtitle {
    margin-top: 13px;
    font-size: 15px;
    letter-spacing: 5px;
    font-weight: 800;
    color: #e2e8f0;
    text-transform: uppercase;
}

.banner-badge {
    margin-top: 12px;
    display: inline-block;
    padding: 6px 13px;
    border: 1px solid #1f8f68;
    border-radius: 999px;
    background: rgba(5,25,23,.7);
    color: #86efac;
    font-size: 12px;
    font-weight: 800;
}

/* Rapor */
.report-wrap {
    margin-top: 22px;
}

.report-title {
    font-size: 26px;
    font-weight: 900;
    margin: 0 0 16px 0;
    color: #f8fafc;
}

.section-title {
    margin: 24px 0 10px 0;
    padding: 12px 15px;
    background: #101c2f;
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
    grid-template-columns: repeat(auto-fit,minmax(330px,1fr));
    gap: 12px;
    margin: 10px 0 18px 0;
}

.signal-card {
    background: linear-gradient(135deg,#12233b,#0f1b2d);
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
    grid-template-columns: repeat(auto-fit,minmax(260px,1fr));
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

.score-box {
    display: grid;
    grid-template-columns: repeat(auto-fit,minmax(220px,1fr));
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
    .banner-inner {
        min-height: 145px;
        padding: 12px 15px;
        gap: 10px;
    }

    .bat-logo {
        width: 85px;
        min-width: 85px;
        height: 85px;
    }

    .banner-title {
        font-size: 30px;
    }

    .banner-subtitle {
        font-size: 9px;
        letter-spacing: 2px;
    }

    .signal-grid,
    .data-grid,
    .score-box {
        grid-template-columns: 1fr;
    }
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# YARASA ANALİZ ANA BANNER
# Harici resim varsa onu kullanır; yoksa dahili SVG banner gösterir.
# Böylece ekstra logo dosyası olmadan da çalışır.
# ------------------------------------------------------------
logo_candidates = [
    Path("yarasa_analiz_banner.png"),
    Path("Yarasa_Analiz_banner.png"),
    Path("Yarasa_Iddaa_logo_seffaf.png.png"),
    Path("logo.png.png"),
]

banner_image = next((p for p in logo_candidates if p.exists()), None)

if banner_image and banner_image.name.lower() in {
    "yarasa_analiz_banner.png",
    "yarasa_analiz_banner.png"
}:
    st.image(str(banner_image), width="stretch")
else:
    # Dahili, profesyonel SVG banner
    st.markdown("""
    <div class="yarasa-banner">
      <div class="banner-inner">
        <div class="bat-logo">
          <svg viewBox="0 0 180 180" width="145" height="145" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="batg" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0" stop-color="#0f172a"/>
                <stop offset="0.55" stop-color="#111827"/>
                <stop offset="1" stop-color="#020617"/>
              </linearGradient>
              <radialGradient id="ballg">
                <stop offset="0" stop-color="#ffffff"/>
                <stop offset="0.75" stop-color="#dbeafe"/>
                <stop offset="1" stop-color="#94a3b8"/>
              </radialGradient>
            </defs>

            <!-- Bat wings -->
            <path d="M89 53
                     C69 24 42 17 12 25
                     C27 39 27 58 8 72
                     C34 70 46 80 57 94
                     C67 83 76 76 90 72 Z"
                  fill="url(#batg)" stroke="#84cc16" stroke-width="4"/>
            <path d="M91 53
                     C111 24 138 17 168 25
                     C153 39 153 58 172 72
                     C146 70 134 80 123 94
                     C113 83 104 76 90 72 Z"
                  fill="url(#batg)" stroke="#84cc16" stroke-width="4"/>

            <!-- Bat head -->
            <path d="M67 45 L61 24 L77 33 L90 24 L103 33 L119 24 L113 45
                     C121 57 114 73 90 78
                     C66 73 59 57 67 45 Z"
                  fill="#111827" stroke="#a3e635" stroke-width="4"/>

            <!-- Eyes -->
            <path d="M73 49 Q80 44 86 50 Q80 56 73 49Z" fill="#d9f99d"/>
            <path d="M107 49 Q100 44 94 50 Q100 56 107 49Z" fill="#d9f99d"/>

            <!-- Football -->
            <circle cx="90" cy="111" r="38" fill="url(#ballg)" stroke="#0f172a" stroke-width="5"/>
            <path d="M90 84 L101 92 L97 105 L83 105 L79 92 Z" fill="#111827"/>
            <path d="M83 105 L72 112 L76 126 L89 131 L97 121 L97 105" fill="none" stroke="#111827" stroke-width="4"/>
            <path d="M97 105 L108 112 L104 126 L91 131" fill="none" stroke="#111827" stroke-width="4"/>
            <path d="M79 92 L68 99 M101 92 L112 99 M76 126 L68 132 M104 126 L112 132"
                  stroke="#111827" stroke-width="4" stroke-linecap="round"/>

            <!-- Ball base -->
            <path d="M50 148 Q90 166 130 148" fill="none" stroke="#22c55e" stroke-width="5"/>
          </svg>
        </div>

        <div class="banner-text">
          <div class="banner-title">YARASA <span>ANALİZ</span></div>
          <div class="banner-subtitle">PROFESYONEL FUTBOL ANALİZ MERKEZİ</div>
          <div class="banner-badge">⚽ CANLI VERİ • İSTATİSTİK • MODEL ANALİZİ</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------
# API KONTROLÜ
# ------------------------------------------------------------
if not API_KEY:
    st.error(
        "API-Football anahtarı bulunamadı. "
        "Streamlit Secrets içinde API_FOOTBALL_KEY tanımlı olmalı."
    )
    st.stop()

# ------------------------------------------------------------
# OTURUM
# ------------------------------------------------------------
if "matches" not in st.session_state:
    st.session_state.matches = []

if "analysis" not in st.session_state:
    st.session_state.analysis = None

# ------------------------------------------------------------
# MAÇ GETİRME
# ------------------------------------------------------------
col1, col2 = st.columns([1, 2])

with col1:
    selected_date = st.date_input(
        "📅 Maç tarihi",
        value=date.today()
    )

with col2:
    if st.button(
        "🔄 MAÇLARI GETİR",
        use_container_width=True
    ):
        with st.spinner("Maçlar getiriliyor..."):
            st.session_state.matches = gunun_maclarini_getir_web(
                selected_date.isoformat()
            )
            st.session_state.analysis = None

matches = st.session_state.matches

if not matches:
    st.info("Tarih seçip **MAÇLARI GETİR** butonuna bas.")
else:
    st.success(f"{len(matches)} maç bulundu.")

    labels = []

    for m in matches:
        h = m.get("teams", {}).get("home", {}).get(
            "name", "Ev Sahibi"
        )
        a = m.get("teams", {}).get("away", {}).get(
            "name", "Deplasman"
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
        format_func=lambda i: labels[i]
    )

    if st.button(
        "🎯 MAÇI ANALİZ ET",
        type="primary",
        use_container_width=True
    ):
        with st.spinner(
            "Analiz motoru çalışıyor... "
            "form, gol, korner, kart ve ilk yarı verileri hesaplanıyor..."
        ):
            st.session_state.analysis = analiz_mac_web(
                matches[idx]
            )

# ------------------------------------------------------------
# YARDIMCI FONKSİYONLAR
# ------------------------------------------------------------
def esc(s):
    return html.escape(str(s), quote=True)


def render_signal(line, source=None):
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


def render_analysis(text):
    lines = text.splitlines()

    st.markdown(
        '<div class="report-wrap">'
        '<div class="report-title">📊 MAÇ ANALİZ RAPORU</div>',
        unsafe_allow_html=True
    )

    if text.startswith("❌ ANALİZ HATASI"):
        st.error(
            text.replace(
                "❌ ANALİZ HATASI",
                ""
            ).strip()
        )
        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )
        return

    i = 0
    signal_html = []

    while i < len(lines):
        raw = lines[i].strip()

        if not raw or set(raw) <= {"═", "─", "-"}:
            i += 1
            continue

        if raw.startswith(
            "🎯 ÖNE ÇIKAN MODEL SONUÇLARI"
        ):
            st.markdown(
                f'<div class="section-title">'
                f'{esc(raw)}</div>',
                unsafe_allow_html=True
            )

            i += 1

            while i < len(lines):
                r = lines[i].strip()

                if not r:
                    i += 1
                    continue

                if r.startswith(
                    "• Güçlü sinyal sayısı:"
                ):
                    st.markdown(
                        f'<div class="highlight-line">'
                        f'{esc(r)}</div>',
                        unsafe_allow_html=True
                    )
                    i += 1
                    break

                if r.startswith("• "):
                    src = None

                    if (
                        i + 1 < len(lines)
                        and lines[i + 1]
                        .strip()
                        .startswith("↳")
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
                    unsafe_allow_html=True
                )
                signal_html = []

            continue

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
                            r.split(":", 1)[1].strip()
                        )
                    )

                elif r.startswith("⚽ Beklenen gol:"):
                    score_items.append(
                        (
                            "Beklenen gol",
                            r.split(":", 1)[1].strip()
                        )
                    )

                else:
                    break

                i += 1

            st.markdown(
                '<div class="score-box">'
                + "".join(
                    f'<div class="score-item">'
                    f'<div class="score-label">{esc(a)}</div>'
                    f'<div class="score-value">{esc(b)}</div>'
                    f'</div>'
                    for a, b in score_items
                )
                + "</div>",
                unsafe_allow_html=True
            )

            continue

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
                f'<div class="section-title">'
                f'{esc(raw)}</div>',
                unsafe_allow_html=True
            )
            i += 1
            continue

        if (
            raw.startswith(("🏠 ", "✈️ "))
            and len(raw) < 55
        ):
            st.markdown(
                f'<div class="section-sub">'
                f'{esc(raw)}</div>',
                unsafe_allow_html=True
            )
            i += 1
            continue

        if (
            raw.startswith("Not:")
            or raw.startswith("Model:")
        ):
            st.markdown(
                f'<div class="note-line">'
                f'{esc(raw)}</div>',
                unsafe_allow_html=True
            )

        elif raw.startswith("   "):
            st.markdown(
                f'<div class="simple-line">'
                f'{esc(raw.strip())}</div>',
                unsafe_allow_html=True
            )

        elif raw.startswith("• "):
            st.markdown(
                f'<div class="highlight-line">'
                f'{esc(raw)}</div>',
                unsafe_allow_html=True
            )

        else:
            st.markdown(
                f'<div class="simple-line">'
                f'{esc(raw)}</div>',
                unsafe_allow_html=True
            )

        i += 1

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


# ------------------------------------------------------------
# ANALİZİ GÖSTER
# ------------------------------------------------------------
if st.session_state.analysis:
    render_analysis(
        st.session_state.analysis
    )
