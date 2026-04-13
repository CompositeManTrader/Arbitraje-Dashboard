"""
app.py — Sube a Streamlit Cloud
================================
Lee los CSV desde GitHub y muestra el Monitor de Arbitraje en tiempo real.
"""

import time
import json
from datetime import datetime

import pandas as pd
import requests
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# ★ EDITA ESTE VALOR ★
# ─────────────────────────────────────────────────────────────────────────────
GITHUB_REPO = "CompositeManTrader/Arbitraje-Dashboard"  # igual que en uploader.py
BRANCH      = "main"
# ─────────────────────────────────────────────────────────────────────────────

BASE_RAW = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{BRANCH}"

st.set_page_config(
    page_title="Monitor Arbitraje",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    background-color: #0a0e1a;
    color: #c8d0e0;
}
.stApp { background-color: #0a0e1a; }

.monitor-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 12px 0 18px 0;
    border-bottom: 1px solid #1e2d4a;
    margin-bottom: 20px;
}
.monitor-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 22px; font-weight: 600;
    color: #4fc3f7; letter-spacing: 2px;
}
.monitor-subtitle { font-size: 12px; color: #546e8a; letter-spacing: 1px; }
.live-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: #0d1f0d; border: 1px solid #1b5e20;
    padding: 4px 12px; border-radius: 20px;
    font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: #4caf50;
}
.live-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: #4caf50;
    animation: pulse 1.4s ease-in-out infinite;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }

.section-badge {
    display: inline-block; padding: 4px 16px; border-radius: 3px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px; font-weight: 600; letter-spacing: 2px; margin-bottom: 10px;
}
.badge-compra { background:#0d2137; color:#4fc3f7; border-left:3px solid #4fc3f7; }
.badge-venta  { background:#1a0d24; color:#ce93d8; border-left:3px solid #ce93d8; }

.stat-row { display: flex; gap: 12px; margin-bottom: 20px; }
.stat-card {
    flex: 1; background: #0f1729; border: 1px solid #1e2d4a;
    border-radius: 6px; padding: 12px 16px;
}
.stat-label { font-size: 10px; color: #546e8a; letter-spacing: 1px; text-transform: uppercase; }
.stat-value { font-family:'IBM Plex Mono',monospace; font-size:22px; font-weight:600; color:#e0e8f0; }
.stat-value.green  { color: #4caf50; }
.stat-value.purple { color: #ce93d8; }
.stat-value.blue   { color: #4fc3f7; }

.ts { font-family:'IBM Plex Mono',monospace; font-size:11px; color:#546e8a; }
.err-box {
    background:#1a0808; border:1px solid #5c1010; border-radius:6px;
    padding:16px; margin:20px 0;
    font-family:'IBM Plex Mono',monospace; font-size:12px; color:#ef9a9a;
}
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# FETCH desde GitHub raw (con cache corto)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=4)
def fetch_csv(filename: str) -> pd.DataFrame | None:
    url = f"{BASE_RAW}/{filename}"
    try:
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            from io import StringIO
            return pd.read_csv(StringIO(r.text))
        return None
    except Exception:
        return None

@st.cache_data(ttl=4)
def fetch_meta() -> dict:
    url = f"{BASE_RAW}/data/meta.json"
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
    if pd.isna(val): return "—"
    return f"${val:,.2f}"

def fmt_pct(val):
    if pd.isna(val): return "—"
    return f"{val*100:.2f}%"

def fmt_int(val):
    if pd.isna(val): return "—"
    try: return f"{int(val):,}"
    except: return str(val)

def prepare_display(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["#"]           = pd.to_numeric(df["#"], errors="coerce").astype("Int64")
    out["Ticker"]      = df["TICKER"]
    out["Empresa"]     = df["Empresa"]
    out["Operación"]   = df["Operación"]
    out["Títulos"]     = df["Títulos"].apply(fmt_int)
    out["Diferencia"]  = df["Diferencia"].apply(fmt_peso)
    out["Justo"]       = df["Justo"].apply(fmt_peso)
    out["Rendimiento"] = df["Rendimiento"].apply(fmt_pct)
    out["Utilidad $"]  = df["Utilidad"].apply(fmt_peso)
    out["Inversión"]   = df["Inversión"].apply(fmt_peso)
    out["País"]        = df["País"].astype(str).str.strip()
    return out


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    st.markdown("---")
    refresh_sec = st.slider("Refresco (seg)", 3, 60, 5, 1)
    st.markdown("---")
    st.markdown(f"**Fuente de datos**")
    st.code(f"github.com/{GITHUB_REPO}", language=None)
    st.markdown("---")
    meta_ph = st.empty()


# ─────────────────────────────────────────────────────────────────────────────
# PLACEHOLDERS
# ─────────────────────────────────────────────────────────────────────────────
header_ph  = st.empty()
stats_ph   = st.empty()
compra_ph  = st.empty()
venta_ph   = st.empty()
ts_ph      = st.empty()

iteration = 0

while True:
    iteration += 1
    now = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")

    df_compra = fetch_csv("data/compra.csv")
    df_venta  = fetch_csv("data/venta.csv")
    meta      = fetch_meta()

    # ── HEADER ────────────────────────────────────────────────────────────────
    with header_ph.container():
        st.markdown(f"""
        <div class="monitor-header">
            <div>
                <div class="monitor-title">◈ MONITOR ARBITRAJE INTRADÍA</div>
                <div class="monitor-subtitle">BMV · BIVA · NYSE · NASDAQ — Monitor $</div>
            </div>
            <div>
                <span class="live-badge">
                    <span class="live-dot"></span>
                    EN VIVO · Bloomberg → GitHub
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── ERROR ─────────────────────────────────────────────────────────────────
    if df_compra is None or df_venta is None:
        with stats_ph.container():
            st.markdown(f"""
            <div class="err-box">
                ⚠ No se encontraron datos en GitHub.<br><br>
                Verifica que el <strong>uploader.py</strong> esté corriendo
                en la PC con Bloomberg y que el repositorio sea:<br>
                <strong>{GITHUB_REPO}</strong>
            </div>
            """, unsafe_allow_html=True)
        time.sleep(refresh_sec)
        fetch_csv.clear()
        fetch_meta.clear()
        continue

    # ── SIDEBAR META ──────────────────────────────────────────────────────────
    with meta_ph.container():
        if meta:
            st.markdown(f"""
            **Última actualización Bloomberg:**  
            `{meta.get('last_update','—')}`  
            Compras: `{meta.get('rows_compra','—')}` · Ventas: `{meta.get('rows_venta','—')}`
            """)

    # ── STATS CARDS ───────────────────────────────────────────────────────────
    util_compra = pd.to_numeric(df_compra["Utilidad"], errors="coerce").sum()
    util_venta  = pd.to_numeric(df_venta["Utilidad"],  errors="coerce").sum()
    rend_max    = pd.to_numeric(df_compra["Rendimiento"], errors="coerce").max()

    with stats_ph.container():
        st.markdown(f"""
        <div class="stat-row">
            <div class="stat-card">
                <div class="stat-label">Oportunidades Compra</div>
                <div class="stat-value blue">{len(df_compra)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Utilidad Total Compra</div>
                <div class="stat-value green">${util_compra:,.2f}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Oportunidades Venta</div>
                <div class="stat-value purple">{len(df_venta)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Utilidad Total Venta</div>
                <div class="stat-value purple">${util_venta:,.2f}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Mejor Rendimiento</div>
                <div class="stat-value green">{rend_max*100:.2f}%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    COL_CONFIG = {
        "#":          st.column_config.NumberColumn("#", width=40),
        "Ticker":     st.column_config.TextColumn("TICKER", width=90),
        "Empresa":    st.column_config.TextColumn("Empresa", width=230),
        "Operación":  st.column_config.TextColumn("Operación", width=155),
        "Títulos":    st.column_config.TextColumn("Títulos", width=80),
        "Diferencia": st.column_config.TextColumn("Diferencia", width=105),
        "Justo":      st.column_config.TextColumn("Justo", width=115),
        "Rendimiento":st.column_config.TextColumn("Rendimiento", width=105),
        "Utilidad $": st.column_config.TextColumn("Utilidad $", width=115),
        "Inversión":  st.column_config.TextColumn("Inversión", width=135),
        "País":       st.column_config.TextColumn("País", width=120),
    }

    # ── TABLA COMPRA ──────────────────────────────────────────────────────────
    with compra_ph.container():
        st.markdown('<span class="section-badge badge-compra">▲ COMPRA</span>', unsafe_allow_html=True)
        st.dataframe(prepare_display(df_compra), use_container_width=True,
                     hide_index=True, column_config=COL_CONFIG)

    # ── TABLA VENTA ───────────────────────────────────────────────────────────
    with venta_ph.container():
        st.markdown('<span class="section-badge badge-venta">▼ VENTA</span>', unsafe_allow_html=True)
        st.dataframe(prepare_display(df_venta), use_container_width=True,
                     hide_index=True, column_config=COL_CONFIG)

    # ── TIMESTAMP ─────────────────────────────────────────────────────────────
    with ts_ph.container():
        bbg_ts = meta.get("last_update", "—")
        st.markdown(
            f'<div class="ts">⟳ App recargada: {now} &nbsp;|&nbsp; '
            f'Bloomberg actualizó: {bbg_ts} &nbsp;|&nbsp; Iter #{iteration}</div>',
            unsafe_allow_html=True
        )

    time.sleep(refresh_sec)
    fetch_csv.clear()
    fetch_meta.clear()
