import os
from datetime import date
import streamlit as st

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

st.set_page_config(page_title="Futbol Analiz Pro", page_icon="⚽", layout="wide")

st.markdown("""
<style>
.stApp { background:#0b1220; color:#f8fafc; }
.block-container { max-width:1250px; padding-top:2rem; }
.hero { background:#111c2e; border:1px solid #263852; padding:24px; border-radius:12px; margin-bottom:18px; }
.hero h1 { margin:0; font-size:34px; }
.sub { color:#94a3b8; margin-top:6px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>⚽ FUTBOL ANALİZ PRO</h1><div class="sub">Profesyonel maç analiz ve istatistik sistemi</div></div>', unsafe_allow_html=True)

if not API_KEY:
    st.error("API-Football anahtarı bulunamadı. Yerelde proje klasöründe api_key.txt veya API_FOOTBALL_KEY ortam değişkeni gerekli.")
    st.stop()

if "matches" not in st.session_state:
    st.session_state.matches = []
if "analysis" not in st.session_state:
    st.session_state.analysis = None

col1, col2 = st.columns([1, 2])
with col1:
    selected_date = st.date_input("📅 Maç tarihi", value=date.today())
with col2:
    if st.button("🔄 MAÇLARI GETİR", use_container_width=True):
        with st.spinner("Maçlar getiriliyor..."):
            st.session_state.matches = gunun_maclarini_getir_web(selected_date.isoformat())
            st.session_state.analysis = None

matches = st.session_state.matches

if not matches:
    st.info("Tarih seçip **MAÇLARI GETİR** butonuna bas.")
else:
    st.success(f"{len(matches)} maç bulundu.")
    labels=[]
    for m in matches:
        h=m.get('teams',{}).get('home',{}).get('name','Ev Sahibi')
        a=m.get('teams',{}).get('away',{}).get('name','Deplasman')
        league=m.get('league',{}).get('name','')
        dt=m.get('fixture',{}).get('date','')
        labels.append(f"{h} — {a} | {league} | {dt[11:16] if len(dt)>=16 else ''}")
    idx=st.selectbox("⚽ Analiz edilecek maç", range(len(labels)), format_func=lambda i: labels[i])
    if st.button("🎯 MAÇI ANALİZ ET", type="primary", use_container_width=True):
        with st.spinner("Analiz motoru çalışıyor... form, gol, korner, kart ve ilk yarı verileri hesaplanıyor..."):
            st.session_state.analysis = analiz_mac_web(matches[idx])
    if st.session_state.analysis:
        st.markdown("### 📊 MAÇ ANALİZ RAPORU")
        st.text(st.session_state.analysis)
