"""
app.py — Monitor Arbitraje Intradía
=====================================
Bloomberg-style dashboard. Lee CSV desde GitHub en tiempo real.
GITHUB_REPO debe coincidir con tu repositorio.
"""

import time
import json
from datetime import datetime, timezone

import pandas as pd
import requests
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# ★ EDITA ESTE VALOR ★
# ─────────────────────────────────────────────────────────────────────────────
GITHUB_REPO = "CompositeManTrader/Arbitraje-Dashboard"
BRANCH      = "main"
# ─────────────────────────────────────────────────────────────────────────────

BASE_RAW    = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{BRANCH}"
STALE_SECS  = 30   # segundos sin actualización → alerta amarilla
DEAD_SECS   = 120  # segundos sin actualización → alerta roja

st.set_page_config(
    page_title="Arbitraje Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS — Bloomberg Terminal Style
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

*, html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif !important;
    box-sizing: border-box;
}
.stApp {
    background: #070b14 !important;
    color: #d4dce8 !important;
}
.block-container { padding: 1.2rem 1.8rem 2rem 1.8rem !important; max-width: 100% !important; }

/* ── TOP BAR ── */
.topbar {
    display: flex; align-items: center; justify-content: space-between;
    background: #0c1220;
    border: 1px solid #1a2640;
    border-radius: 8px;
    padding: 10px 20px;
    margin-bottom: 16px;
}
.topbar-left { display: flex; align-items: center; gap: 16px; }
.topbar-logo {
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px; font-weight: 600;
    color: #f0a500;
    letter-spacing: 3px;
    background: #1a1200;
    border: 1px solid #3d2800;
    padding: 4px 10px;
    border-radius: 4px;
}
.topbar-title {
    font-size: 15px; font-weight: 600;
    color: #e8eef5; letter-spacing: 0.5px;
}
.topbar-sub {
    font-size: 11px; color: #4a6080; letter-spacing: 1px;
    font-family: 'JetBrains Mono', monospace;
}
.topbar-right { display: flex; align-items: center; gap: 12px; }

/* ── STATUS BADGES ── */
.status-live {
    display: inline-flex; align-items: center; gap: 7px;
    background: #061a0a; border: 1px solid #0d4a1a;
    padding: 5px 14px; border-radius: 20px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px; font-weight: 600; color: #00e676;
    letter-spacing: 1px;
}
.status-warn {
    display: inline-flex; align-items: center; gap: 7px;
    background: #1a1200; border: 1px solid #4d3800;
    padding: 5px 14px; border-radius: 20px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px; font-weight: 600; color: #ffab00;
    letter-spacing: 1px;
}
.status-dead {
    display: inline-flex; align-items: center; gap: 7px;
    background: #1a0608; border: 1px solid #4d0e14;
    padding: 5px 14px; border-radius: 20px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px; font-weight: 600; color: #ff1744;
    letter-spacing: 1px;
}
.dot-live { width:8px; height:8px; border-radius:50%; background:#00e676;
    box-shadow: 0 0 6px #00e676;
    animation: blink 1.4s ease-in-out infinite; }
.dot-warn { width:8px; height:8px; border-radius:50%; background:#ffab00;
    box-shadow: 0 0 6px #ffab00;
    animation: blink 0.7s ease-in-out infinite; }
.dot-dead { width:8px; height:8px; border-radius:50%; background:#ff1744; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.2} }

/* ── ALERT BANNER ── */
.alert-warn {
    background: #1a1200; border-left: 3px solid #ffab00;
    border-radius: 0 6px 6px 0; padding: 10px 16px;
    margin-bottom: 14px;
    font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #ffab00;
}
.alert-dead {
    background: #1a0608; border-left: 3px solid #ff1744;
    border-radius: 0 6px 6px 0; padding: 10px 16px;
    margin-bottom: 14px;
    font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #ff5252;
}

/* ── STAT CARDS ── */
.cards-row {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 10px;
    margin-bottom: 16px;
}
.card {
    background: #0c1220;
    border: 1px solid #1a2640;
    border-radius: 8px;
    padding: 14px 16px;
    position: relative;
    overflow: hidden;
}
.card::before {
    content: '';
    position: absolute; top:0; left:0; right:0; height:2px;
}
.card.blue::before  { background: linear-gradient(90deg, #0066ff, #00aaff); }
.card.green::before { background: linear-gradient(90deg, #00c853, #69f0ae); }
.card.purple::before{ background: linear-gradient(90deg, #aa00ff, #e040fb); }
.card.gold::before  { background: linear-gradient(90deg, #f0a500, #ffd740); }
.card.teal::before  { background: linear-gradient(90deg, #00bcd4, #80deea); }

.card-label {
    font-size: 9px; font-weight: 600;
    color: #3a5070; letter-spacing: 1.5px;
    text-transform: uppercase; margin-bottom: 8px;
    font-family: 'JetBrains Mono', monospace;
}
.card-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 20px; font-weight: 600; color: #e8eef5;
    line-height: 1;
}
.card-value.blue   { color: #40aaff; }
.card-value.green  { color: #00e676; }
.card-value.purple { color: #e040fb; }
.card-value.gold   { color: #ffd740; }
.card-value.teal   { color: #80deea; }
.card-delta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; color: #3a5070; margin-top: 4px;
}

/* ── SECTION HEADERS ── */
.section-header {
    display: flex; align-items: center; gap: 12px;
    margin: 18px 0 8px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid #1a2640;
}
.section-tag {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; font-weight: 600; letter-spacing: 2px;
    padding: 3px 10px; border-radius: 3px;
}
.tag-compra { background: #001833; color: #40aaff; border: 1px solid #0044aa; }
.tag-venta  { background: #1a0033; color: #e040fb; border: 1px solid #6600aa; }
.section-count {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px; color: #3a5070;
}
.section-total {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px; font-weight: 600; margin-left: auto;
}
.total-green  { color: #00e676; }
.total-purple { color: #e040fb; }

/* ── DATAFRAME OVERRIDES ── */
.stDataFrame { background: transparent !important; }
[data-testid="stDataFrame"] > div {
    border: 1px solid #1a2640 !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}
iframe { background: #0c1220 !important; }

/* ── TIMESTAMP BAR ── */
.ts-bar {
    display: flex; align-items: center; justify-content: space-between;
    margin-top: 14px; padding-top: 10px;
    border-top: 1px solid #0f1a2e;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; color: #2a4060; letter-spacing: 0.5px;
}

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
    background: #080e1a !important;
    border-right: 1px solid #1a2640 !important;
}

/* ── HIDE STREAMLIT UI ── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# DATA FETCHERS
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=4)
def fetch_csv(filename: str):
    url = f"{BASE_RAW}/{filename}?t={int(time.time())}"
    try:
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            from io import StringIO
            return pd.read_csv(StringIO(r.text))
    except Exception:
        pass
    return None

@st.cache_data(ttl=4)
def fetch_meta() -> dict:
    url = f"{BASE_RAW}/data/meta.json?t={int(time.time())}"
    try:
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {}


# ─────────────────────────────────────────────────────────────────────────────
# FORMATTERS
# ─────────────────────────────────────────────────────────────────────────────
def fmt_peso(val):
    try:
        v = float(val)
        return f"${v:,.2f}"
    except: return "—"

def fmt_pct(val):
    try:
        v = float(val)
        arrow = "▲" if v >= 0 else "▼"
        return f"{arrow} {abs(v)*100:.2f}%"
    except: return "—"

def fmt_int(val):
    try: return f"{int(float(val)):,}"
    except: return "—"

def prepare_display(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["#"]            = pd.to_numeric(df["#"], errors="coerce").astype("Int64")
    out["Ticker"]       = df["TICKER"]
    out["Empresa"]      = df["Empresa"]
    out["Operación"]    = df["Operación"]
    out["Títulos"]      = df["Títulos"].apply(fmt_int)
    out["Diferencia"]   = df["Diferencia"].apply(fmt_peso)
    out["Precio Justo"] = df["Justo"].apply(fmt_peso)
    out["Rdto %"]       = df["Rendimiento"].apply(fmt_pct)
    out["Utilidad $"]   = df["Utilidad"].apply(fmt_peso)
    out["Inversión"]    = df["Inversión"].apply(fmt_peso)
    out["País"]         = df["País"].astype(str).str.strip()
    return out


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    refresh_sec = st.slider("Refresco (seg)", 3, 60, 5, 1)
    st.markdown("---")
    st.code(f"Repo:\n{GITHUB_REPO}", language=None)


# ─────────────────────────────────────────────────────────────────────────────
# PLACEHOLDERS
# ─────────────────────────────────────────────────────────────────────────────
topbar_ph  = st.empty()
alert_ph   = st.empty()
cards_ph   = st.empty()
compra_ph  = st.empty()
venta_ph   = st.empty()
ts_ph      = st.empty()

iteration  = 0
prev_compra_util = None
prev_venta_util  = None

# ─────────────────────────────────────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────────────────────────────────────
while True:
    iteration += 1
    now_str = datetime.now().strftime("%H:%M:%S")
    now_full = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    df_c  = fetch_csv("data/compra.csv")
    df_v  = fetch_csv("data/venta.csv")
    meta  = fetch_meta()

    # ── CALCULAR ESTADO DE CONEXIÓN ───────────────────────────────────────────
    last_update = meta.get("last_update", "")
    secs_ago    = 9999
    secs_ago_str = "—"

    if last_update:
        try:
            lu = datetime.strptime(last_update, "%Y-%m-%d %H:%M:%S")
            secs_ago = (datetime.now() - lu).total_seconds()
            if secs_ago < 60:
                secs_ago_str = f"{int(secs_ago)}s"
            else:
                secs_ago_str = f"{int(secs_ago/60)}m {int(secs_ago%60)}s"
        except Exception:
            pass

    if df_c is None or df_v is None:
        conn_status = "no_data"
    elif secs_ago > DEAD_SECS:
        conn_status = "dead"
    elif secs_ago > STALE_SECS:
        conn_status = "warn"
    else:
        conn_status = "live"

    # ── STATUS BADGE HTML ─────────────────────────────────────────────────────
    if conn_status == "live":
        badge = '<span class="status-live"><span class="dot-live"></span>EN VIVO · Bloomberg</span>'
    elif conn_status == "warn":
        badge = f'<span class="status-warn"><span class="dot-warn"></span>SIN CAMBIOS · {secs_ago_str}</span>'
    elif conn_status == "dead":
        badge = f'<span class="status-dead"><span class="dot-dead"></span>DESCONECTADO · {secs_ago_str}</span>'
    else:
        badge = '<span class="status-dead"><span class="dot-dead"></span>SIN DATOS</span>'

    # ── TOPBAR ────────────────────────────────────────────────────────────────
    with topbar_ph.container():
        st.markdown(f"""
        <div class="topbar">
            <div class="topbar-left">
                <div class="topbar-logo">ARB</div>
                <div>
                    <div class="topbar-title">Monitor de Arbitraje Intradía</div>
                    <div class="topbar-sub">BMV &nbsp;·&nbsp; BIVA &nbsp;·&nbsp; NYSE &nbsp;·&nbsp; NASDAQ &nbsp;·&nbsp; Monitor $</div>
                </div>
            </div>
            <div class="topbar-right">
                <div style="font-family:'JetBrains Mono',monospace;font-size:11px;color:#3a5070;">
                    {now_str}
                </div>
                {badge}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── ALERT BANNER ──────────────────────────────────────────────────────────
    with alert_ph.container():
        if conn_status == "warn":
            st.markdown(f"""
            <div class="alert-warn">
                ⚠ &nbsp; Bloomberg dejó de actualizar hace <strong>{secs_ago_str}</strong>.
                Verifica que el Excel esté abierto y el autoguardado activo.
                Último dato: <strong>{last_update}</strong>
            </div>
            """, unsafe_allow_html=True)
        elif conn_status == "dead":
            st.markdown(f"""
            <div class="alert-dead">
                ✖ &nbsp; Conexión perdida hace <strong>{secs_ago_str}</strong>.
                Posibles causas: PC Bloomberg apagada · Internet caído · uploader.py cerrado.
                Último dato recibido: <strong>{last_update}</strong>
            </div>
            """, unsafe_allow_html=True)
        elif conn_status == "no_data":
            st.markdown(f"""
            <div class="alert-dead">
                ✖ &nbsp; No se encontraron datos en GitHub.
                Verifica que <strong>uploader.py</strong> esté corriendo
                en la PC con Bloomberg. Repo: <strong>{GITHUB_REPO}</strong>
            </div>
            """, unsafe_allow_html=True)

    if conn_status == "no_data":
        time.sleep(refresh_sec)
        fetch_csv.clear(); fetch_meta.clear()
        continue

    # ── CALCULAR MÉTRICAS ─────────────────────────────────────────────────────
    util_c    = pd.to_numeric(df_c["Utilidad"],    errors="coerce").sum()
    util_v    = pd.to_numeric(df_v["Utilidad"],    errors="coerce").sum()
    inv_c     = pd.to_numeric(df_c["Inversión"],   errors="coerce").sum()
    rend_max  = pd.to_numeric(df_c["Rendimiento"], errors="coerce").max()

    delta_c = ""
    delta_v = ""
    if prev_compra_util is not None:
        d = util_c - prev_compra_util
        delta_c = f"{'▲' if d>=0 else '▼'} ${abs(d):,.2f} vs anterior"
    if prev_venta_util is not None:
        d = util_v - prev_venta_util
        delta_v = f"{'▲' if d>=0 else '▼'} ${abs(d):,.2f} vs anterior"
    prev_compra_util = util_c
    prev_venta_util  = util_v

    # ── CARDS ─────────────────────────────────────────────────────────────────
    with cards_ph.container():
        st.markdown(f"""
        <div class="cards-row">
            <div class="card blue">
                <div class="card-label">Oportunidades Compra</div>
                <div class="card-value blue">{len(df_c)}</div>
                <div class="card-delta">operaciones activas</div>
            </div>
            <div class="card green">
                <div class="card-label">Utilidad Total Compra</div>
                <div class="card-value green">${util_c:,.2f}</div>
                <div class="card-delta">{delta_c or 'acumulado sesión'}</div>
            </div>
            <div class="card purple">
                <div class="card-label">Utilidad Total Venta</div>
                <div class="card-value purple">${util_v:,.2f}</div>
                <div class="card-delta">{delta_v or 'acumulado sesión'}</div>
            </div>
            <div class="card gold">
                <div class="card-label">Mejor Rendimiento</div>
                <div class="card-value gold">{rend_max*100:.2f}%</div>
                <div class="card-delta">top oportunidad</div>
            </div>
            <div class="card teal">
                <div class="card-label">Capital en Compras</div>
                <div class="card-value teal">${inv_c:,.0f}</div>
                <div class="card-delta">inversión requerida</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    COL_CONFIG = {
        "#":            st.column_config.NumberColumn("#", width=45),
        "Ticker":       st.column_config.TextColumn("Ticker", width=85),
        "Empresa":      st.column_config.TextColumn("Empresa", width=230),
        "Operación":    st.column_config.TextColumn("Operación", width=155),
        "Títulos":      st.column_config.TextColumn("Títulos", width=75),
        "Diferencia":   st.column_config.TextColumn("Diferencia", width=105),
        "Precio Justo": st.column_config.TextColumn("Precio Justo", width=115),
        "Rdto %":       st.column_config.TextColumn("Rdto %", width=100),
        "Utilidad $":   st.column_config.TextColumn("Utilidad $", width=110),
        "Inversión":    st.column_config.TextColumn("Inversión", width=130),
        "País":         st.column_config.TextColumn("País", width=115),
    }

    # ── TABLA COMPRA ──────────────────────────────────────────────────────────
    with compra_ph.container():
        st.markdown(f"""
        <div class="section-header">
            <span class="section-tag tag-compra">▲ COMPRA</span>
            <span class="section-count">{len(df_c)} oportunidades</span>
            <span class="section-total total-green">${util_c:,.2f} utilidad total</span>
        </div>
        """, unsafe_allow_html=True)
        st.dataframe(
            prepare_display(df_c),
            use_container_width=True,
            hide_index=True,
            column_config=COL_CONFIG,
            height=min(35 * len(df_c) + 38, 450),
        )

    # ── TABLA VENTA ───────────────────────────────────────────────────────────
    with venta_ph.container():
        st.markdown(f"""
        <div class="section-header">
            <span class="section-tag tag-venta">▼ VENTA</span>
            <span class="section-count">{len(df_v)} oportunidades</span>
            <span class="section-total total-purple">${util_v:,.2f} utilidad total</span>
        </div>
        """, unsafe_allow_html=True)
        st.dataframe(
            prepare_display(df_v),
            use_container_width=True,
            hide_index=True,
            column_config=COL_CONFIG,
            height=min(35 * len(df_v) + 38, 450),
        )

    # ── TIMESTAMP BAR ─────────────────────────────────────────────────────────
    with ts_ph.container():
        st.markdown(f"""
        <div class="ts-bar">
            <span>APP RECARGADA: {now_full}</span>
            <span>BLOOMBERG ACTUALIZÓ: {last_update or '—'}</span>
            <span>HACE: {secs_ago_str}</span>
            <span>REFRESCO: {refresh_sec}s &nbsp;·&nbsp; ITER #{iteration}</span>
        </div>
        """, unsafe_allow_html=True)

    time.sleep(refresh_sec)
    fetch_csv.clear()
    fetch_meta.clear()
