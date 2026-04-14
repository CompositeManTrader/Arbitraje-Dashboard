"""
app.py — Monitor de Arbitraje Intradía v4
==========================================
Tablas 100% HTML custom — ajuste perfecto a pantalla, diseño premium.
"""

import time
import json
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

# ─────────────────────────────────────────────────────────────────────────────
GITHUB_REPO = "CompositeManTrader/Arbitraje-Dashboard"
BRANCH      = "main"
# ─────────────────────────────────────────────────────────────────────────────

BASE_RAW   = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{BRANCH}"
CDMX       = ZoneInfo("America/Mexico_City")
STALE_SECS = 30
DEAD_SECS  = 120

st.set_page_config(
    page_title="ARB · Composite Man",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow:wght@300;400;500;600;700&family=Barlow+Condensed:wght@500;600;700&family=Fira+Code:wght@400;500;600&display=swap');

:root {
    --bg0:#04080f; --bg1:#080e1c; --bg2:#0c1528; --bg3:#111d35;
    --border:#162035; --border2:#1e2e4a;
    --text0:#eef2f8; --text1:#99adc4; --text2:#4a6280; --text3:#283850;
    --gold:#e8b84b; --gold2:#f5d07a;
    --blue:#3d9aff; --blue2:#7abdff;
    --green:#00d68f; --green2:#5fffcb;
    --red:#ff4d6a; --amber:#ffaa00;
    --teal:#00c8d4; --purple:#b060ff;
}
*, html, body, [class*="css"] { font-family:'Barlow',sans-serif !important; box-sizing:border-box; }
.stApp { background:var(--bg0) !important; color:var(--text0) !important; }
.block-container { padding:0 !important; max-width:100% !important; }
section[data-testid="stSidebar"] { background:var(--bg1) !important; border-right:1px solid var(--border) !important; }
#MainMenu,footer,header,.stDeployButton { visibility:hidden; display:none; }

/* NAVBAR */
.navbar {
    display:flex; align-items:stretch;
    background:var(--bg1); border-bottom:1px solid var(--border);
    height:54px; padding:0 24px; gap:0; position:sticky; top:0; z-index:100;
}
.nav-brand { display:flex; align-items:center; gap:12px; padding-right:24px; border-right:1px solid var(--border); }
.nav-logo {
    width:34px; height:34px;
    background:linear-gradient(135deg,var(--gold) 0%,#9a6800 100%);
    border-radius:6px; display:flex; align-items:center; justify-content:center;
    font-family:'Fira Code',monospace; font-size:12px; font-weight:700; color:#000;
    box-shadow:0 0 14px rgba(232,184,75,.3);
}
.nav-name { font-family:'Barlow Condensed',sans-serif; font-size:17px; font-weight:700; color:var(--text0); letter-spacing:1px; text-transform:uppercase; }
.nav-tagline { font-size:9px; color:var(--text2); letter-spacing:2px; text-transform:uppercase; }
.nav-markets { display:flex; align-items:center; padding:0 4px; border-right:1px solid var(--border); }
.nav-market { display:flex; flex-direction:column; align-items:center; padding:0 14px; border-right:1px solid var(--border); }
.nav-market:last-child { border-right:none; }
.nm-name { font-family:'Fira Code',monospace; font-size:9px; font-weight:600; color:var(--text2); letter-spacing:1px; }
.nm-open { font-size:9px; font-weight:700; color:var(--green); letter-spacing:1px; }
.nm-closed { font-size:9px; font-weight:600; color:var(--text3); letter-spacing:1px; }
.nav-right { display:flex; align-items:center; gap:16px; margin-left:auto; }
.nav-clock { font-family:'Fira Code',monospace; font-size:14px; font-weight:500; color:var(--text1); }
.nav-tz { font-size:9px; color:var(--text3); letter-spacing:1px; text-align:right; }

/* PILLS */
.pill { display:inline-flex; align-items:center; gap:7px; padding:5px 14px; border-radius:4px; font-family:'Fira Code',monospace; font-size:10px; font-weight:600; letter-spacing:1.5px; }
.pill-live   { background:rgba(0,214,143,.08);  border:1px solid rgba(0,214,143,.3);  color:var(--green); }
.pill-warn   { background:rgba(255,170,0,.08);  border:1px solid rgba(255,170,0,.3);  color:var(--amber); }
.pill-dead   { background:rgba(255,77,106,.08); border:1px solid rgba(255,77,106,.3); color:var(--red); }
.pdot { width:7px; height:7px; border-radius:50%; }
.pdot-live  { background:var(--green); box-shadow:0 0 7px var(--green); animation:blink 1.6s ease infinite; }
.pdot-warn  { background:var(--amber); box-shadow:0 0 7px var(--amber); animation:blink .7s ease infinite; }
.pdot-dead  { background:var(--red); }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.1} }

/* ALERT */
.alert-strip { display:flex; align-items:center; gap:12px; padding:9px 24px; font-family:'Fira Code',monospace; font-size:11px; border-bottom:1px solid; }
.alert-warn { background:rgba(255,170,0,.05); border-color:rgba(255,170,0,.2); color:var(--amber); }
.alert-dead { background:rgba(255,77,106,.05); border-color:rgba(255,77,106,.2); color:var(--red); }

/* CONTENT */
.content { padding:18px 24px 28px 24px; }

/* METRICS */
.metric-strip { display:grid; grid-template-columns:repeat(5,1fr); gap:1px; background:var(--border); border:1px solid var(--border); border-radius:8px; overflow:hidden; margin-bottom:22px; }
.metric-cell { background:var(--bg1); padding:14px 18px; position:relative; }
.metric-cell::after { content:''; position:absolute; bottom:0; left:18px; right:18px; height:2px; border-radius:2px 2px 0 0; opacity:.7; }
.mc-gold::after   { background:linear-gradient(90deg,var(--gold),transparent); }
.mc-purple::after { background:linear-gradient(90deg,var(--purple),transparent); }
.mc-green::after  { background:linear-gradient(90deg,var(--green),transparent); }
.mc-teal::after   { background:linear-gradient(90deg,var(--teal),transparent); }
.mc-blue::after   { background:linear-gradient(90deg,var(--blue),transparent); }
.metric-label { font-family:'Fira Code',monospace; font-size:9px; font-weight:500; color:var(--text3); letter-spacing:2px; text-transform:uppercase; margin-bottom:8px; }
.metric-value { font-family:'Fira Code',monospace; font-size:21px; font-weight:600; line-height:1; }
.mv-gold{color:var(--gold)} .mv-green{color:var(--green)} .mv-blue{color:var(--blue)} .mv-teal{color:var(--teal)} .mv-purple{color:var(--purple)}
.metric-sub { font-size:10px; color:var(--text2); margin-top:5px; }

/* SECTION HEADER */
.tbl-header { display:flex; align-items:center; padding:0 0 10px 0; margin-bottom:0; border-bottom:1px solid var(--border); }
.tbl-tag { font-family:'Barlow Condensed',sans-serif; font-size:12px; font-weight:700; letter-spacing:3px; text-transform:uppercase; padding:3px 12px 3px 10px; border-radius:3px; margin-right:12px; }
.tag-c { background:rgba(61,154,255,.1); color:var(--blue); border-left:3px solid var(--blue); }
.tag-v { background:rgba(176,96,255,.1); color:var(--purple); border-left:3px solid var(--purple); }
.tbl-meta { font-family:'Fira Code',monospace; font-size:10px; color:var(--text2); }
.tbl-total { margin-left:auto; font-family:'Fira Code',monospace; font-size:13px; font-weight:600; }
.tt-green{color:var(--green)} .tt-purple{color:var(--purple)}

/* FOOTER */
.footer-bar { display:flex; align-items:center; justify-content:space-between; padding:10px 24px; border-top:1px solid var(--border); background:var(--bg1); font-family:'Fira Code',monospace; font-size:9px; color:var(--text3); letter-spacing:.8px; margin-top:12px; }
.footer-item { display:flex; flex-direction:column; gap:2px; }
.fi-label{color:var(--text3)} .fi-value{color:var(--text2)}
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

def fp(v):
    try: return f"${float(v):,.2f}"
    except: return "—"

def fpct(v):
    try:
        f = float(v)
        sym = "▲" if f >= 0 else "▼"
        cls = "pct-up" if f >= 0 else "pct-dn"
        return f'<span class="{cls}">{sym} {abs(f)*100:.3f}%</span>'
    except: return "<span>—</span>"

def fi(v):
    try: return f"{int(float(v)):,}"
    except: return "—"

def fu(v):
    try:
        f = float(v)
        cls = "util-pos" if f >= 0 else "util-neg"
        return f'<span class="{cls}">{fp(v)}</span>'
    except: return "<span>—</span>"


# ─────────────────────────────────────────────────────────────────────────────
# HTML TABLE BUILDER
# ─────────────────────────────────────────────────────────────────────────────
def build_table_html(df: pd.DataFrame, tipo: str) -> str:
    accent = "#3d9aff" if tipo == "compra" else "#b060ff"

    rows_html = ""
    for _, row in df.iterrows():
        op = str(row.get("Operación", ""))
        if "BIVA" in op and "BMV" in op:
            op_badge = '<span class="badge badge-both">BMV+BIVA</span>'
        elif "BIVA" in op:
            op_badge = '<span class="badge badge-biva">BIVA</span>'
        else:
            op_badge = '<span class="badge badge-bmv">BMV</span>'

        rows_html += f"""
        <tr>
            <td class="td-num">{int(float(row.get('#', 0)))}</td>
            <td class="td-ticker">{row.get('TICKER','')}</td>
            <td class="td-empresa">{row.get('Empresa','')}</td>
            <td class="td-op">{op_badge}</td>
            <td class="td-r">{fi(row.get('Títulos'))}</td>
            <td class="td-r mono">{fp(row.get('Diferencia'))}</td>
            <td class="td-r mono">{fp(row.get('Justo'))}</td>
            <td class="td-r">{fpct(row.get('Rendimiento'))}</td>
            <td class="td-r mono">{fu(row.get('Utilidad'))}</td>
            <td class="td-r mono dim">{fp(row.get('Inversión'))}</td>
            <td class="td-pais">{str(row.get('País','')).strip()}</td>
        </tr>"""

    return f"""
    <style>
    .arb-table-wrap {{
        width: 100%;
        overflow-x: auto;
        border-radius: 8px;
        border: 1px solid #162035;
        background: #080e1c;
        margin-bottom: 4px;
    }}
    .arb-table {{
        width: 100%;
        border-collapse: collapse;
        font-family: 'Barlow', sans-serif;
        font-size: 13px;
        table-layout: fixed;
    }}
    .arb-table thead tr {{
        background: #0c1528;
        border-bottom: 2px solid {accent}22;
    }}
    .arb-table thead th {{
        padding: 10px 12px;
        font-family: 'Fira Code', monospace;
        font-size: 9px;
        font-weight: 600;
        color: #4a6280;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        white-space: nowrap;
        border-bottom: 1px solid #162035;
    }}
    .arb-table thead th.th-accent {{
        color: {accent};
        border-bottom: 2px solid {accent};
    }}
    .arb-table thead th.r {{ text-align: right; }}
    .arb-table tbody tr {{
        border-bottom: 1px solid #0f1828;
        transition: background .15s;
    }}
    .arb-table tbody tr:hover {{ background: #0e1930; }}
    .arb-table tbody tr:last-child {{ border-bottom: none; }}
    .arb-table td {{
        padding: 9px 12px;
        color: #c8d8e8;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        vertical-align: middle;
    }}
    .td-num {{
        width: 42px;
        font-family: 'Fira Code', monospace;
        font-size: 11px;
        color: #283850;
        text-align: center;
    }}
    .td-ticker {{
        width: 90px;
        font-family: 'Fira Code', monospace;
        font-size: 13px;
        font-weight: 600;
        color: {accent};
        letter-spacing: .5px;
    }}
    .td-empresa {{
        width: auto;
        font-size: 12px;
        font-weight: 500;
        color: #99adc4;
    }}
    .td-op {{ width: 110px; }}
    .td-r {{ text-align: right; width: 110px; }}
    .td-pais {{
        width: 130px;
        font-size: 11px;
        color: #4a6280;
        font-weight: 500;
    }}
    .mono {{ font-family: 'Fira Code', monospace; font-size: 12px; }}
    .dim  {{ color: #3a5272 !important; }}

    /* Badges */
    .badge {{
        display: inline-block;
        padding: 2px 8px;
        border-radius: 3px;
        font-family: 'Fira Code', monospace;
        font-size: 9px; font-weight: 600;
        letter-spacing: 1px;
    }}
    .badge-bmv  {{ background: rgba(61,154,255,.12); color: #3d9aff; border: 1px solid rgba(61,154,255,.2); }}
    .badge-biva {{ background: rgba(0,200,212,.12);  color: #00c8d4; border: 1px solid rgba(0,200,212,.2); }}
    .badge-both {{ background: rgba(232,184,75,.12); color: #e8b84b; border: 1px solid rgba(232,184,75,.2); }}

    /* Pct colors */
    .pct-up {{ color: #00d68f; font-family:'Fira Code',monospace; font-size:12px; font-weight:600; }}
    .pct-dn {{ color: #ff4d6a; font-family:'Fira Code',monospace; font-size:12px; font-weight:600; }}
    .util-pos {{ color: #00d68f; font-family:'Fira Code',monospace; font-size:12px; font-weight:600; }}
    .util-neg {{ color: #ff4d6a; font-family:'Fira Code',monospace; font-size:12px; }}

    /* Column widths */
    .arb-table colgroup col:nth-child(1)  {{ width: 42px; }}
    .arb-table colgroup col:nth-child(2)  {{ width: 88px; }}
    .arb-table colgroup col:nth-child(3)  {{ width: auto; min-width:180px; }}
    .arb-table colgroup col:nth-child(4)  {{ width: 110px; }}
    .arb-table colgroup col:nth-child(5)  {{ width: 75px; }}
    .arb-table colgroup col:nth-child(6)  {{ width: 110px; }}
    .arb-table colgroup col:nth-child(7)  {{ width: 120px; }}
    .arb-table colgroup col:nth-child(8)  {{ width: 110px; }}
    .arb-table colgroup col:nth-child(9)  {{ width: 115px; }}
    .arb-table colgroup col:nth-child(10) {{ width: 120px; }}
    .arb-table colgroup col:nth-child(11) {{ width: 130px; }}
    </style>

    <div class="arb-table-wrap">
      <table class="arb-table">
        <colgroup>
          <col><col><col><col><col><col><col><col><col><col><col>
        </colgroup>
        <thead>
          <tr>
            <th>#</th>
            <th>Ticker</th>
            <th>Empresa</th>
            <th>Bolsa</th>
            <th class="r">Títulos</th>
            <th class="r">Diferencia</th>
            <th class="r">Precio Justo</th>
            <th class="r th-accent">Rdto %</th>
            <th class="r th-accent">Utilidad $</th>
            <th class="r">Inversión</th>
            <th>País</th>
          </tr>
        </thead>
        <tbody>
          {rows_html}
        </tbody>
      </table>
    </div>
    """


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Parámetros")
    refresh_sec = st.slider("Refresco (seg)", 3, 60, 5, 1)
    st.markdown("---")
    st.caption(f"Repo: `{GITHUB_REPO}`")
    st.caption("Zona horaria: **CDMX**")
    st.caption("Delay Bloomberg→Pantalla: **~10 seg**")


# ─────────────────────────────────────────────────────────────────────────────
# PLACEHOLDERS
# ─────────────────────────────────────────────────────────────────────────────
nav_ph   = st.empty()
alert_ph = st.empty()
body_ph  = st.empty()
foot_ph  = st.empty()

iteration = 0
prev_uc = prev_uv = None

# ─────────────────────────────────────────────────────────────────────────────
# LOOP
# ─────────────────────────────────────────────────────────────────────────────
while True:
    iteration += 1
    now      = cdmx_now()
    now_time = now.strftime("%H:%M:%S")
    now_full = now.strftime("%Y-%m-%d %H:%M:%S")
    now_date = now.strftime("%d %b %Y").upper()

    df_c = fetch_csv("data/compra.csv")
    df_v = fetch_csv("data/venta.csv")
    meta = fetch_meta()

    # ── Estado conexión ───────────────────────────────────────────────────────
    last_update = meta.get("last_update", "")
    secs_ago = 9999
    secs_str = "—"
    if last_update:
        try:
            lu = datetime.strptime(last_update, "%Y-%m-%d %H:%M:%S").replace(tzinfo=CDMX)
            secs_ago = (now - lu).total_seconds()
            secs_str = f"{int(secs_ago)}s" if secs_ago < 60 else f"{int(secs_ago/60)}m {int(secs_ago%60)}s"
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

    # ── Mercados ──────────────────────────────────────────────────────────────
    h = now.hour
    mkts = {
        "BMV":    8 <= h < 15,
        "BIVA":   8 <= h < 15,
        "NYSE":   8 <= h < 15,
        "NASDAQ": 8 <= h < 15,
    }
    mkt_html = "".join([
        f'<div class="nav-market"><div class="nm-name">{k}</div>'
        f'<div class="{"nm-open" if v else "nm-closed"}">{"ABIERTO" if v else "CERRADO"}</div></div>'
        for k, v in mkts.items()
    ])

    # ── Badge ─────────────────────────────────────────────────────────────────
    if status == "live":
        badge = '<span class="pill pill-live"><span class="pdot pdot-live"></span>EN VIVO</span>'
    elif status == "warn":
        badge = f'<span class="pill pill-warn"><span class="pdot pdot-warn"></span>SIN CAMBIOS · {secs_str}</span>'
    else:
        badge = f'<span class="pill pill-dead"><span class="pdot pdot-dead"></span>DESCONECTADO · {secs_str}</span>'

    # ── NAVBAR ────────────────────────────────────────────────────────────────
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
          <div class="nav-markets">{mkt_html}</div>
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
            st.markdown(f'<div class="alert-strip alert-warn">⚠ &nbsp; Bloomberg sin cambios hace <strong>{secs_str}</strong> · Último dato: <strong>{last_update} CDMX</strong> · Verifica que el Excel esté abierto y autoguardado activo.</div>', unsafe_allow_html=True)
        elif status in ("dead", "nodata"):
            st.markdown(f'<div class="alert-strip alert-dead">✖ &nbsp; Conexión perdida hace <strong>{secs_str}</strong> · Causas posibles: PC Bloomberg apagada · Internet caído · uploader.py cerrado · Último dato: <strong>{last_update or "—"} CDMX</strong></div>', unsafe_allow_html=True)

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

    d_c = f"{'▲' if prev_uc is None or uc>=prev_uc else '▼'} ${abs(uc-(prev_uc or uc)):,.2f} vs ant." if prev_uc is not None else "sesión actual"
    d_v = f"{'▲' if prev_uv is None or uv>=prev_uv else '▼'} ${abs(uv-(prev_uv or uv)):,.2f} vs ant." if prev_uv is not None else "sesión actual"
    prev_uc, prev_uv = uc, uv

    # ── BODY ──────────────────────────────────────────────────────────────────
    with body_ph.container():
        st.markdown('<div class="content">', unsafe_allow_html=True)

        # Metrics
        st.markdown(f"""
        <div class="metric-strip">
          <div class="metric-cell mc-gold">
            <div class="metric-label">Utilidad Compra</div>
            <div class="metric-value mv-gold">${uc:,.2f}</div>
            <div class="metric-sub">{d_c}</div>
          </div>
          <div class="metric-cell mc-purple">
            <div class="metric-label">Utilidad Venta</div>
            <div class="metric-value mv-purple">${uv:,.2f}</div>
            <div class="metric-sub">{d_v}</div>
          </div>
          <div class="metric-cell mc-green">
            <div class="metric-label">Mejor Rendimiento</div>
            <div class="metric-value mv-green">{rmax*100:.3f}%</div>
            <div class="metric-sub">top oportunidad</div>
          </div>
          <div class="metric-cell mc-teal">
            <div class="metric-label">Capital Requerido</div>
            <div class="metric-value mv-teal">${inv:,.0f}</div>
            <div class="metric-sub">inversión compras</div>
          </div>
          <div class="metric-cell mc-blue">
            <div class="metric-label">Oportunidades</div>
            <div class="metric-value mv-blue">{nc + nv}</div>
            <div class="metric-sub">{nc} compra · {nv} venta</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Tabla Compra
        st.markdown(f"""
        <div class="tbl-header">
          <span class="tbl-tag tag-c">▲ Compra</span>
          <span class="tbl-meta">{nc} oportunidades activas</span>
          <span class="tbl-total tt-green">${uc:,.2f} utilidad total</span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(build_table_html(df_c, "compra"), unsafe_allow_html=True)

        st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)

        # Tabla Venta
        st.markdown(f"""
        <div class="tbl-header">
          <span class="tbl-tag tag-v">▼ Venta</span>
          <span class="tbl-meta">{nv} oportunidades activas</span>
          <span class="tbl-total tt-purple">${uv:,.2f} utilidad total</span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(build_table_html(df_v, "venta"), unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # ── FOOTER ────────────────────────────────────────────────────────────────
    with foot_ph.container():
        st.markdown(f"""
        <div class="footer-bar">
          <div class="footer-item"><span class="fi-label">PLATAFORMA</span><span class="fi-value">Composite Man · Arbitrage Intelligence</span></div>
          <div class="footer-item"><span class="fi-label">APP RECARGADA</span><span class="fi-value">{now_full} CDMX</span></div>
          <div class="footer-item"><span class="fi-label">BLOOMBERG ACTUALIZÓ</span><span class="fi-value">{last_update or '—'} CDMX</span></div>
          <div class="footer-item"><span class="fi-label">DELAY ESTIMADO</span><span class="fi-value">~10 seg Bloomberg → Pantalla</span></div>
          <div class="footer-item"><span class="fi-label">ITER</span><span class="fi-value">#{iteration} · refresco {refresh_sec}s</span></div>
        </div>
        """, unsafe_allow_html=True)

    time.sleep(refresh_sec)
    fetch_csv.clear()
    fetch_meta.clear()
