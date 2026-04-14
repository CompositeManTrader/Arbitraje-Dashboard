"""
app.py — Monitor de Arbitraje Intradía v3
==========================================
Bloomberg-grade terminal. CDMX timezone. Professional design.
"""

import time
import json
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# ★ EDITA ESTE VALOR ★
# ─────────────────────────────────────────────────────────────────────────────
GITHUB_REPO = "CompositeManTrader/Arbitraje-Dashboard"
BRANCH      = "main"
# ─────────────────────────────────────────────────────────────────────────────

BASE_RAW   = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{BRANCH}"
CDMX       = ZoneInfo("America/Mexico_City")
STALE_SECS = 30
DEAD_SECS  = 120

st.set_page_config(
    page_title="ARB · Monitor de Arbitraje",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300&family=Barlow+Condensed:wght@400;500;600;700&family=Fira+Code:wght@400;500;600&display=swap');

:root {
    --bg0:      #04080f;
    --bg1:      #080e1c;
    --bg2:      #0c1528;
    --bg3:      #101c32;
    --border:   #162035;
    --border2:  #1e2e4a;
    --text0:    #eef2f8;
    --text1:    #99adc4;
    --text2:    #4a6280;
    --text3:    #283850;
    --gold:     #e8b84b;
    --gold2:    #f5d07a;
    --blue:     #3d9aff;
    --blue2:    #7abdff;
    --green:    #00d68f;
    --green2:   #5fffcb;
    --red:      #ff4d6a;
    --red2:     #ff8099;
    --amber:    #ffaa00;
    --amber2:   #ffd060;
    --teal:     #00c8d4;
    --purple:   #b060ff;
}

*, html, body, [class*="css"] {
    font-family: 'Barlow', sans-serif !important;
    box-sizing: border-box;
}
.stApp { background: var(--bg0) !important; color: var(--text0) !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }
section[data-testid="stSidebar"] { background: var(--bg1) !important; border-right: 1px solid var(--border) !important; }
#MainMenu, footer, header, .stDeployButton { visibility: hidden; display: none; }

/* ══════════════════════════════════════════════
   NAVBAR
══════════════════════════════════════════════ */
.navbar {
    display: flex; align-items: stretch;
    background: var(--bg1);
    border-bottom: 1px solid var(--border);
    height: 52px;
    padding: 0 24px;
    gap: 0;
}
.nav-brand {
    display: flex; align-items: center; gap: 12px;
    padding-right: 24px;
    border-right: 1px solid var(--border);
}
.nav-logo {
    width: 32px; height: 32px;
    background: linear-gradient(135deg, var(--gold) 0%, #b8860b 100%);
    border-radius: 6px;
    display: flex; align-items: center; justify-content: center;
    font-family: 'Fira Code', monospace;
    font-size: 13px; font-weight: 600; color: #000;
    letter-spacing: -1px;
    box-shadow: 0 0 12px rgba(232,184,75,0.25);
}
.nav-name {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 17px; font-weight: 700;
    color: var(--text0); letter-spacing: 1px;
    text-transform: uppercase;
}
.nav-tagline {
    font-size: 9px; font-weight: 500;
    color: var(--text2); letter-spacing: 2px;
    text-transform: uppercase; margin-top: 1px;
}
.nav-markets {
    display: flex; align-items: center; gap: 0;
    padding: 0 20px;
    border-right: 1px solid var(--border);
}
.nav-market {
    display: flex; flex-direction: column; align-items: center;
    padding: 0 14px;
    border-right: 1px solid var(--border);
    cursor: default;
}
.nav-market:last-child { border-right: none; }
.nm-name { font-family: 'Fira Code', monospace; font-size: 9px; font-weight: 600; color: var(--text2); letter-spacing: 1px; }
.nm-status { font-size: 9px; font-weight: 600; color: var(--green); letter-spacing: 1px; }
.nm-status.closed { color: var(--text3); }
.nav-right {
    display: flex; align-items: center; gap: 16px;
    margin-left: auto;
}
.nav-clock {
    font-family: 'Fira Code', monospace;
    font-size: 13px; font-weight: 500; color: var(--text1);
    letter-spacing: 1px;
}
.nav-tz { font-size: 9px; color: var(--text3); letter-spacing: 1px; }

/* ══════════════════════════════════════════════
   STATUS PILL
══════════════════════════════════════════════ */
.pill {
    display: inline-flex; align-items: center; gap: 7px;
    padding: 5px 14px; border-radius: 4px;
    font-family: 'Fira Code', monospace;
    font-size: 10px; font-weight: 600; letter-spacing: 1.5px;
    text-transform: uppercase;
}
.pill-live   { background: rgba(0,214,143,.08); border: 1px solid rgba(0,214,143,.25); color: var(--green); }
.pill-warn   { background: rgba(255,170,0,.08);  border: 1px solid rgba(255,170,0,.25);  color: var(--amber); }
.pill-dead   { background: rgba(255,77,106,.08); border: 1px solid rgba(255,77,106,.25); color: var(--red); }
.pdot { width:7px; height:7px; border-radius:50%; }
.pdot-live  { background:var(--green); box-shadow:0 0 6px var(--green); animation:blink 1.6s ease infinite; }
.pdot-warn  { background:var(--amber); box-shadow:0 0 6px var(--amber); animation:blink 0.7s ease infinite; }
.pdot-dead  { background:var(--red); }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.15} }

/* ══════════════════════════════════════════════
   ALERT STRIP
══════════════════════════════════════════════ */
.alert-strip {
    display: flex; align-items: center; gap: 12px;
    padding: 9px 24px;
    font-family: 'Fira Code', monospace; font-size: 11px;
    border-bottom: 1px solid;
}
.alert-warn { background: rgba(255,170,0,.05); border-color: rgba(255,170,0,.2); color: var(--amber); }
.alert-dead { background: rgba(255,77,106,.05); border-color: rgba(255,77,106,.2); color: var(--red2); }
.alert-icon { font-size: 14px; }

/* ══════════════════════════════════════════════
   MAIN CONTENT WRAPPER
══════════════════════════════════════════════ */
.content { padding: 20px 24px 32px 24px; }

/* ══════════════════════════════════════════════
   METRIC STRIP
══════════════════════════════════════════════ */
.metric-strip {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 1px;
    background: var(--border);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
    margin-bottom: 24px;
}
.metric-cell {
    background: var(--bg1);
    padding: 16px 20px;
    position: relative;
}
.metric-cell::after {
    content: '';
    position: absolute; bottom: 0; left: 20px; right: 20px; height: 2px;
    border-radius: 2px 2px 0 0;
    opacity: 0.6;
}
.mc-gold::after   { background: linear-gradient(90deg, var(--gold), transparent); }
.mc-green::after  { background: linear-gradient(90deg, var(--green), transparent); }
.mc-blue::after   { background: linear-gradient(90deg, var(--blue), transparent); }
.mc-teal::after   { background: linear-gradient(90deg, var(--teal), transparent); }
.mc-purple::after { background: linear-gradient(90deg, var(--purple), transparent); }

.metric-label {
    font-family: 'Fira Code', monospace;
    font-size: 9px; font-weight: 500;
    color: var(--text3); letter-spacing: 2px;
    text-transform: uppercase; margin-bottom: 10px;
}
.metric-value {
    font-family: 'Fira Code', monospace;
    font-size: 22px; font-weight: 600; line-height: 1;
}
.mv-gold   { color: var(--gold); }
.mv-green  { color: var(--green); }
.mv-blue   { color: var(--blue); }
.mv-teal   { color: var(--teal); }
.mv-purple { color: var(--purple); }
.metric-sub {
    font-size: 10px; color: var(--text2);
    margin-top: 5px; letter-spacing: 0.5px;
}

/* ══════════════════════════════════════════════
   TABLE SECTION
══════════════════════════════════════════════ */
.tbl-header {
    display: flex; align-items: center;
    padding: 0 0 10px 0;
    margin-bottom: 2px;
    border-bottom: 1px solid var(--border);
}
.tbl-tag {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 12px; font-weight: 700;
    letter-spacing: 3px; text-transform: uppercase;
    padding: 3px 12px 3px 10px;
    border-radius: 3px;
    margin-right: 12px;
}
.tag-c { background: rgba(61,154,255,.1); color: var(--blue); border-left: 3px solid var(--blue); }
.tag-v { background: rgba(176,96,255,.1); color: var(--purple); border-left: 3px solid var(--purple); }
.tbl-meta {
    font-family: 'Fira Code', monospace;
    font-size: 10px; color: var(--text2);
}
.tbl-total {
    margin-left: auto;
    font-family: 'Fira Code', monospace;
    font-size: 13px; font-weight: 600;
}
.tt-green  { color: var(--green); }
.tt-purple { color: var(--purple); }

/* ══════════════════════════════════════════════
   FOOTER
══════════════════════════════════════════════ */
.footer-bar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 24px;
    border-top: 1px solid var(--border);
    background: var(--bg1);
    font-family: 'Fira Code', monospace;
    font-size: 9px; color: var(--text3);
    letter-spacing: 0.8px;
    margin-top: 16px;
}
.footer-item { display: flex; flex-direction: column; gap: 2px; }
.fi-label { color: var(--text3); }
.fi-value { color: var(--text2); }

/* ══════════════════════════════════════════════
   STREAMLIT DATAFRAME OVERRIDE
══════════════════════════════════════════════ */
[data-testid="stDataFrame"] {
    border-radius: 6px !important;
    overflow: hidden !important;
}
[data-testid="stDataFrame"] > div {
    border: 1px solid var(--border2) !important;
    border-radius: 6px !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=4)
def fetch_csv(filename):
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
def fetch_meta():
    url = f"{BASE_RAW}/data/meta.json?t={int(time.time())}"
    try:
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {}

def cdmx_now():
    return datetime.now(CDMX)

def fmt_peso(v):
    try: return f"${float(v):>12,.2f}"
    except: return "—"

def fmt_pct(v):
    try:
        f = float(v)
        sym = "▲" if f >= 0 else "▼"
        return f"{sym} {abs(f)*100:.3f}%"
    except: return "—"

def fmt_int(v):
    try: return f"{int(float(v)):,}"
    except: return "—"

def prepare(df):
    out = pd.DataFrame()
    out["#"]            = pd.to_numeric(df["#"], errors="coerce").astype("Int64")
    out["Ticker"]       = df["TICKER"]
    out["Empresa"]      = df["Empresa"]
    out["Operación"]    = df["Operación"]
    out["Títulos"]      = df["Títulos"].apply(fmt_int)
    out["Diferencia"]   = df["Diferencia"].apply(fmt_peso)
    out["Precio Justo"] = df["Justo"].apply(fmt_peso)
    out["Rdto"]         = df["Rendimiento"].apply(fmt_pct)
    out["Utilidad"]     = df["Utilidad"].apply(fmt_peso)
    out["Inversión"]    = df["Inversión"].apply(fmt_peso)
    out["País"]         = df["País"].astype(str).str.strip()
    out["ISIN"]         = df["ISIN"].astype(str).str.strip()
    return out


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Parámetros")
    refresh_sec = st.slider("Refresco (seg)", 3, 60, 5, 1)
    st.markdown("---")
    st.caption(f"Repositorio\n`{GITHUB_REPO}`")
    st.caption("Zona horaria: **America/Mexico_City**")
    st.caption("Delay estimado Bloomberg→Pantalla: **~10 seg**")


# ─────────────────────────────────────────────────────────────────────────────
# PLACEHOLDERS
# ─────────────────────────────────────────────────────────────────────────────
nav_ph    = st.empty()
alert_ph  = st.empty()
body_ph   = st.empty()
foot_ph   = st.empty()

iteration = 0
prev_uc = prev_uv = None

COL_CONFIG = {
    "#":            st.column_config.NumberColumn("#",            width=45),
    "Ticker":       st.column_config.TextColumn("Ticker",         width=80),
    "Empresa":      st.column_config.TextColumn("Empresa",        width=240),
    "Operación":    st.column_config.TextColumn("Operación",      width=160),
    "Títulos":      st.column_config.TextColumn("Títulos",        width=80),
    "Diferencia":   st.column_config.TextColumn("Diferencia",     width=120),
    "Precio Justo": st.column_config.TextColumn("Precio Justo",   width=125),
    "Rdto":         st.column_config.TextColumn("Rdto %",         width=105),
    "Utilidad":     st.column_config.TextColumn("Utilidad $",     width=120),
    "Inversión":    st.column_config.TextColumn("Inversión",      width=135),
    "País":         st.column_config.TextColumn("País",           width=130),
    "ISIN":         st.column_config.TextColumn("ISIN",           width=135),
}

# ─────────────────────────────────────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────────────────────────────────────
while True:
    iteration += 1
    now        = cdmx_now()
    now_time   = now.strftime("%H:%M:%S")
    now_full   = now.strftime("%Y-%m-%d %H:%M:%S")
    now_date   = now.strftime("%d %b %Y").upper()

    df_c  = fetch_csv("data/compra.csv")
    df_v  = fetch_csv("data/venta.csv")
    meta  = fetch_meta()

    # ── Calcular estado ───────────────────────────────────────────────────────
    last_update = meta.get("last_update", "")
    secs_ago    = 9999
    secs_str    = "—"
    if last_update:
        try:
            lu       = datetime.strptime(last_update, "%Y-%m-%d %H:%M:%S")
            # uploader corre en hora local de la PC Bloomberg (CDMX)
            lu_cdmx  = lu.replace(tzinfo=CDMX)
            secs_ago = (now - lu_cdmx).total_seconds()
            if secs_ago < 60:
                secs_str = f"{int(secs_ago)}s ago"
            else:
                secs_str = f"{int(secs_ago/60)}m {int(secs_ago%60)}s ago"
        except Exception:
            pass

    if df_c is None or df_v is None:
        status = "nodata"
    elif secs_ago > DEAD_SECS:
        status = "dead"
    elif secs_ago > STALE_SECS:
        status = "warn"
    else:
        status = "live"

    # ── Market hours (CDMX) ───────────────────────────────────────────────────
    hour = now.hour
    bmv_open  = 8 <= hour < 15
    biva_open = 8 <= hour < 15
    nyse_open = 8 <= hour < 15   # NYSE abre 9:30 ET = 8:30 CDMX aprox

    def mkt(open_):
        cls = "" if open_ else " closed"
        txt = "ABIERTO" if open_ else "CERRADO"
        return cls, txt

    # ── Status badge ─────────────────────────────────────────────────────────
    if status == "live":
        badge = '<span class="pill pill-live"><span class="pdot pdot-live"></span>EN VIVO</span>'
    elif status == "warn":
        badge = f'<span class="pill pill-warn"><span class="pdot pdot-warn"></span>SIN CAMBIOS · {secs_str}</span>'
    else:
        badge = f'<span class="pill pill-dead"><span class="pdot pdot-dead"></span>DESCONECTADO · {secs_str}</span>'

    # ── NAVBAR ────────────────────────────────────────────────────────────────
    c1, c2, c3 = mkt(bmv_open), mkt(biva_open), mkt(nyse_open)
    with nav_ph.container():
        st.markdown(f"""
        <div class="navbar">
            <div class="nav-brand">
                <div class="nav-logo">ARB</div>
                <div>
                    <div class="nav-name">Composite Man</div>
                    <div class="nav-tagline">Arbitrage Intelligence Platform</div>
                </div>
            </div>
            <div class="nav-markets">
                <div class="nav-market">
                    <div class="nm-name">BMV</div>
                    <div class="nm-status{c1[0]}">{c1[1]}</div>
                </div>
                <div class="nav-market">
                    <div class="nm-name">BIVA</div>
                    <div class="nm-status{c2[0]}">{c2[1]}</div>
                </div>
                <div class="nav-market">
                    <div class="nm-name">NYSE</div>
                    <div class="nm-status{c3[0]}">{c3[1]}</div>
                </div>
                <div class="nav-market">
                    <div class="nm-name">NASDAQ</div>
                    <div class="nm-status{c3[0]}">{c3[1]}</div>
                </div>
            </div>
            <div class="nav-right">
                <div>
                    <div class="nav-clock">{now_time}</div>
                    <div class="nav-tz">CDMX · {now_date}</div>
                </div>
                {badge}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── ALERT ─────────────────────────────────────────────────────────────────
    with alert_ph.container():
        if status == "warn":
            st.markdown(f"""
            <div class="alert-strip alert-warn">
                <span class="alert-icon">⚠</span>
                Bloomberg dejó de actualizar hace <strong>{secs_str}</strong>.
                Verifica que el Excel esté abierto y el autoguardado activo.
                Último dato recibido: <strong>{last_update} CDMX</strong>
            </div>""", unsafe_allow_html=True)
        elif status in ("dead", "nodata"):
            cause = "PC Bloomberg apagada &nbsp;·&nbsp; Internet caído &nbsp;·&nbsp; uploader.py cerrado"
            last  = f"Último dato: <strong>{last_update} CDMX</strong>" if last_update else "Sin datos previos"
            st.markdown(f"""
            <div class="alert-strip alert-dead">
                <span class="alert-icon">✖</span>
                Conexión perdida hace <strong>{secs_str}</strong> &nbsp;—&nbsp; {cause}
                &nbsp;·&nbsp; {last}
            </div>""", unsafe_allow_html=True)

    if status == "nodata":
        time.sleep(refresh_sec)
        fetch_csv.clear(); fetch_meta.clear()
        continue

    # ── Métricas ──────────────────────────────────────────────────────────────
    uc   = pd.to_numeric(df_c["Utilidad"],    errors="coerce").sum()
    uv   = pd.to_numeric(df_v["Utilidad"],    errors="coerce").sum()
    inv  = pd.to_numeric(df_c["Inversión"],   errors="coerce").sum()
    rmax = pd.to_numeric(df_c["Rendimiento"], errors="coerce").max()
    nc, nv = len(df_c), len(df_v)

    delta_c = f"{'▲' if uc>=(prev_uc or uc) else '▼'} ${abs(uc-(prev_uc or uc)):,.2f} vs ant." if prev_uc is not None else "sesión actual"
    delta_v = f"{'▲' if uv>=(prev_uv or uv) else '▼'} ${abs(uv-(prev_uv or uv)):,.2f} vs ant." if prev_uv is not None else "sesión actual"
    prev_uc, prev_uv = uc, uv

    # ── BODY ──────────────────────────────────────────────────────────────────
    with body_ph.container():
        st.markdown('<div class="content">', unsafe_allow_html=True)

        # Metric strip
        st.markdown(f"""
        <div class="metric-strip">
            <div class="metric-cell mc-gold">
                <div class="metric-label">Utilidad Compra</div>
                <div class="metric-value mv-gold">${uc:,.2f}</div>
                <div class="metric-sub">{delta_c}</div>
            </div>
            <div class="metric-cell mc-purple">
                <div class="metric-label">Utilidad Venta</div>
                <div class="metric-value mv-purple">${uv:,.2f}</div>
                <div class="metric-sub">{delta_v}</div>
            </div>
            <div class="metric-cell mc-green">
                <div class="metric-label">Mejor Rendimiento</div>
                <div class="metric-value mv-green">{rmax*100:.3f}%</div>
                <div class="metric-sub">top oportunidad compra</div>
            </div>
            <div class="metric-cell mc-teal">
                <div class="metric-label">Capital Requerido</div>
                <div class="metric-value mv-teal">${inv:,.0f}</div>
                <div class="metric-sub">inversión compras activas</div>
            </div>
            <div class="metric-cell mc-blue">
                <div class="metric-label">Oportunidades</div>
                <div class="metric-value mv-blue">{nc + nv}</div>
                <div class="metric-sub">{nc} compra · {nv} venta</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Tabla Compra ──────────────────────────────────────────────────────
        st.markdown(f"""
        <div class="tbl-header">
            <span class="tbl-tag tag-c">▲ Compra</span>
            <span class="tbl-meta">{nc} oportunidades activas</span>
            <span class="tbl-total tt-green">${uc:,.2f} utilidad total</span>
        </div>
        """, unsafe_allow_html=True)
        st.dataframe(
            prepare(df_c),
            use_container_width=True,
            hide_index=True,
            column_config=COL_CONFIG,
            height=min(38 * nc + 42, 480),
        )

        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

        # ── Tabla Venta ───────────────────────────────────────────────────────
        st.markdown(f"""
        <div class="tbl-header">
            <span class="tbl-tag tag-v">▼ Venta</span>
            <span class="tbl-meta">{nv} oportunidades activas</span>
            <span class="tbl-total tt-purple">${uv:,.2f} utilidad total</span>
        </div>
        """, unsafe_allow_html=True)
        st.dataframe(
            prepare(df_v),
            use_container_width=True,
            hide_index=True,
            column_config=COL_CONFIG,
            height=min(38 * nv + 42, 480),
        )

        st.markdown('</div>', unsafe_allow_html=True)

    # ── FOOTER ────────────────────────────────────────────────────────────────
    with foot_ph.container():
        st.markdown(f"""
        <div class="footer-bar">
            <div class="footer-item">
                <span class="fi-label">PLATAFORMA</span>
                <span class="fi-value">Composite Man · Arbitrage Intelligence</span>
            </div>
            <div class="footer-item">
                <span class="fi-label">APP RECARGADA</span>
                <span class="fi-value">{now_full} CDMX</span>
            </div>
            <div class="footer-item">
                <span class="fi-label">BLOOMBERG ACTUALIZÓ</span>
                <span class="fi-value">{last_update or '—'} CDMX</span>
            </div>
            <div class="footer-item">
                <span class="fi-label">DELAY ESTIMADO</span>
                <span class="fi-value">~10 seg Bloomberg → Pantalla</span>
            </div>
            <div class="footer-item">
                <span class="fi-label">REFRESCO / ITER</span>
                <span class="fi-value">{refresh_sec}s · #{iteration}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    time.sleep(refresh_sec)
    fetch_csv.clear()
    fetch_meta.clear()
