import streamlit as st
import pandas as pd
import numpy as np
import os
import io
import gdown
import re
import unicodedata
import plotly.graph_objects as go
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# -----------------------------------
# CONFIGURACION DE LA PAGINA Y ESTILOS CSS
# -----------------------------------
st.set_page_config(page_title="Dashboard Comercial", page_icon=":material/insights:", layout="wide")

# Paleta CuentaClara: azul marino = estructura, cobre = acción y énfasis,
# verde / ámbar / rojo solo para bueno / cerca / malo.
NAVY_950 = "#031523"
NAVY_900 = "#052136"
NAVY_800 = "#072C47"
NAVY_700 = "#0E3E61"
NAVY_600 = "#1A5480"
NAVY_400 = "#5B87AB"
NAVY_100 = "#E3ECF3"
NAVY_50 = "#F2F6F9"
COBRE_700 = "#7A4B15"
COBRE_600 = "#965E1E"
COBRE_500 = "#B5782F"
COBRE_400 = "#D19549"
COBRE_200 = "#EED6B6"
COBRE_100 = "#F8EDDF"
ARENA = "#E0B882"
PIZARRA = "#8C9AA6"
FONDO = "#FAF8F5"
SUPERFICIE_2 = "#F3EFE9"
BORDE = "#E6E0D7"
DIVISOR = "#EEE9E1"
TEXTO = "#0F1C28"
TEXTO_SUAVE = "#5A6774"
EXITO = "#1A7A4F"
EXITO_BG = "#E5F4EC"
ALERTA = "#8A6900"
ALERTA_BG = "#FBF3D9"
PELIGRO = "#C0392B"
PELIGRO_BG = "#FBE9E7"

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Playfair+Display:wght@600;700&display=swap');

    :root {
        --navy-900: #052136; --navy-800: #072C47; --navy-700: #0E3E61; --navy-600: #1A5480;
        --navy-400: #5B87AB; --navy-100: #E3ECF3; --navy-50: #F2F6F9;
        --copper-700: #7A4B15; --copper-600: #965E1E; --copper-500: #B5782F;
        --copper-400: #D19549; --copper-200: #EED6B6; --copper-100: #F8EDDF;
        --surface: #FFFFFF; --surface-2: #F3EFE9; --border: #E6E0D7; --divider: #EEE9E1;
        --text: #0F1C28; --text-muted: #5A6774;
        --success: #1A7A4F; --success-bg: #E5F4EC;
        --warning: #8A6900; --warning-bg: #FBF3D9;
        --danger: #C0392B; --danger-bg: #FBE9E7;
        --shadow-1: 0 1px 2px rgba(7,44,71,0.06), 0 1px 3px rgba(7,44,71,0.06);
        --shadow-2: 0 6px 18px rgba(7,44,71,0.10);
        --ease: cubic-bezier(0.2, 0.8, 0.2, 1);
    }

    .block-container { padding-top: 2.2rem !important; padding-bottom: 3rem !important; max-width: 1500px; }
    div[data-testid="stAppDeployButton"] { display: none; }

    /* ---------- Encabezado ---------- */
    .cc-hero {
        position: relative; overflow: hidden;
        background:
            radial-gradient(circle at 92% 10%, rgba(209,149,73,0.22), transparent 42%),
            linear-gradient(135deg, var(--navy-900) 0%, var(--navy-800) 55%, var(--navy-700) 100%);
        border-radius: 14px; padding: 26px 30px; margin-bottom: 18px;
        color: #F2F6F9; box-shadow: var(--shadow-2);
        animation: cc-rise .5s var(--ease) both;
    }
    .cc-hero::after {
        content: ""; position: absolute; right: -40px; bottom: -60px; width: 220px; height: 220px;
        border: 1px solid rgba(209,149,73,0.25); border-radius: 50%;
    }
    .cc-hero-top { display: flex; flex-wrap: wrap; align-items: flex-end; justify-content: space-between; gap: 16px; position: relative; z-index: 1; }
    .cc-eyebrow {
        display: inline-flex; align-items: center; gap: 8px;
        font-family: 'Manrope', sans-serif; font-size: 12px; font-weight: 700;
        letter-spacing: .14em; text-transform: uppercase; color: var(--copper-400);
    }
    .cc-tri { width: 0; height: 0; border-left: 6px solid transparent; border-right: 6px solid transparent; border-bottom: 10px solid var(--copper-400); display: inline-block; }
    .cc-hero h1 {
        font-family: 'Playfair Display', Georgia, serif !important; font-weight: 700 !important;
        font-size: 38px !important; line-height: 1.1 !important; color: #FFFFFF !important;
        margin: 6px 0 4px 0 !important; padding: 0 !important; letter-spacing: -0.01em;
    }
    .cc-hero p { margin: 0; color: #C9D6E2; font-size: 15px; }
    .cc-chips { display: flex; flex-wrap: wrap; gap: 8px; }
    .cc-chip {
        display: inline-flex; align-items: center; gap: 6px;
        background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.14);
        color: #F2F6F9; border-radius: 999px; padding: 6px 12px; font-size: 13px; font-weight: 600;
        white-space: nowrap;
    }
    .cc-chip b { color: var(--copper-400); font-weight: 800; }

    /* ---------- Tarjetas KPI ---------- */
    .cc-kpis { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 14px; margin: 4px 0 18px 0; }
    @media (max-width: 1200px) { .cc-kpis { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
    @media (max-width: 760px)  { .cc-kpis { grid-template-columns: repeat(1, minmax(0, 1fr)); } }
    .cc-kpi {
        position: relative; background: var(--surface); border: 1px solid var(--border);
        border-radius: 12px; padding: 16px 18px 14px 18px; box-shadow: var(--shadow-1);
        transition: transform .2s var(--ease), box-shadow .2s var(--ease);
        animation: cc-rise .5s var(--ease) both; animation-delay: calc(var(--i, 0) * 70ms);
        min-height: 128px; display: flex; flex-direction: column; gap: 6px;
    }
    .cc-kpi:hover { transform: translateY(-3px); box-shadow: var(--shadow-2); }
    .cc-kpi.destacado { background: linear-gradient(180deg, var(--copper-100), #FFFFFF 70%); border-color: var(--copper-200); }
    .cc-kpi-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
    .cc-kpi-label { font-size: 11.5px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; color: var(--text-muted); line-height: 1.3; }
    .cc-kpi-icon {
        flex: 0 0 auto; width: 32px; height: 32px; border-radius: 9px; display: grid; place-items: center;
        background: var(--navy-50); color: var(--navy-800);
    }
    .cc-kpi.destacado .cc-kpi-icon { background: #FFFFFF; color: var(--copper-600); }
    .cc-kpi-value {
        font-size: clamp(18px, 1.45vw, 25px); font-weight: 800; color: var(--navy-800); letter-spacing: -0.02em;
        font-variant-numeric: tabular-nums; line-height: 1.15; white-space: nowrap;
    }
    .cc-kpi-value.pequeno { font-size: 17px; font-weight: 700; color: var(--text-muted); white-space: normal; }
    @media (max-width: 760px) { .cc-kpi-value { font-size: 26px; } }
    .cc-kpi-foot { font-size: 12.5px; color: var(--text-muted); display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-top: auto; }
    .cc-pill { display: inline-flex; align-items: center; gap: 4px; border-radius: 999px; padding: 2px 8px; font-weight: 700; font-size: 12px; }
    .cc-pill.ok { background: var(--success-bg); color: var(--success); }
    .cc-pill.medio { background: var(--warning-bg); color: var(--warning); }
    .cc-pill.bajo { background: var(--danger-bg); color: var(--danger); }
    .cc-pill.neutro { background: var(--navy-50); color: var(--navy-600); }
    .cc-bar { height: 8px; border-radius: 999px; background: var(--surface-2); overflow: hidden; position: relative; }
    .cc-bar > span { display: block; height: 100%; border-radius: 999px; animation: cc-fill 1s var(--ease) both; animation-delay: .25s; }

    @keyframes cc-rise { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
    @keyframes cc-fill { from { width: 0; } }

    /* ---------- Tarjetas de gráficos ---------- */
    div[class*="st-key-cc-card"] {
        background: var(--surface); border: 1px solid var(--border) !important; border-radius: 12px;
        box-shadow: var(--shadow-1); padding: 16px 18px 8px 18px;
        animation: cc-rise .5s var(--ease) both;
    }
    .cc-card-title { font-size: 16px; font-weight: 800; color: var(--navy-800); margin: 0; line-height: 1.3; }
    .cc-card-sub { font-size: 13.5px; color: var(--text-muted); margin: 2px 0 0 0; }
    .cc-card-sub b { color: var(--copper-700); }

    .cc-section { display: flex; align-items: center; gap: 10px; margin: 6px 0 10px 0; }
    .cc-section h3 { font-family: 'Playfair Display', Georgia, serif !important; font-size: 22px !important; color: var(--navy-800) !important; margin: 0 !important; padding: 0 !important; }
    .cc-note {
        background: var(--navy-50); border: 1px solid var(--navy-100); border-radius: 10px;
        padding: 10px 14px; font-size: 13.5px; color: var(--navy-700); margin: 4px 0 12px 0;
    }
    .cc-legend { display: flex; flex-wrap: wrap; gap: 14px; font-size: 12.5px; color: var(--text-muted); margin: 2px 0 8px 0; }
    .cc-legend span { display: inline-flex; align-items: center; gap: 6px; }
    .cc-legend i { width: 12px; height: 12px; border-radius: 3px; display: inline-block; }

    /* ---------- Pestañas (navegación principal) ---------- */
    div[class*="st-key-cc-nav"] { margin: 2px 0 14px 0; border-bottom: 2px solid var(--border); padding-bottom: 10px; }
    div[class*="st-key-cc-nav"] div[data-testid="stElementToolbar"] { display: none; }
    div[class*="st-key-cc-nav"] [role="radiogroup"],
    div[class*="st-key-cc-nav"] [data-baseweb="button-group"] { gap: 8px !important; flex-wrap: wrap; }
    div[class*="st-key-cc-nav"] button {
        height: 46px !important; padding: 0 20px !important; border-radius: 10px !important;
        font-weight: 700 !important; font-size: 14.5px !important;
        color: var(--text-muted) !important; background: transparent !important;
        border: 1px solid transparent !important;
        transition: background .15s var(--ease), color .15s var(--ease), box-shadow .15s var(--ease);
    }
    div[class*="st-key-cc-nav"] button:hover {
        background: var(--copper-100) !important; color: var(--copper-700) !important;
    }
    /* La pestaña activa: fondo azul marino, texto blanco y barra de cobre debajo */
    div[class*="st-key-cc-nav"] button[aria-checked="true"],
    div[class*="st-key-cc-nav"] button[aria-pressed="true"],
    div[class*="st-key-cc-nav"] button[kind="segmented_controlActive"] {
        background: var(--navy-800) !important; color: #FFFFFF !important;
        border-color: var(--navy-800) !important;
        box-shadow: 0 4px 10px rgba(7, 44, 71, .22), inset 0 -3px 0 0 var(--copper-500) !important;
    }
    div[class*="st-key-cc-nav"] button[aria-checked="true"]:hover,
    div[class*="st-key-cc-nav"] button[aria-pressed="true"]:hover,
    div[class*="st-key-cc-nav"] button[kind="segmented_controlActive"]:hover {
        background: var(--navy-700) !important; color: #FFFFFF !important;
    }

    /* ---------- Botones ---------- */
    div[data-testid="stDownloadButton"] button, div[data-testid="stButton"] button {
        min-height: 46px; font-weight: 700; transition: transform .15s var(--ease), box-shadow .15s var(--ease);
    }
    div[data-testid="stDownloadButton"] button:hover, div[data-testid="stButton"] button:hover {
        transform: translateY(-2px); box-shadow: var(--shadow-2);
    }

    /* ---------- Barra lateral (marino) ---------- */
    section[data-testid="stSidebar"] { border-right: none; }
    section[data-testid="stSidebar"] > div { background:
        radial-gradient(circle at 0% 0%, rgba(209,149,73,0.14), transparent 40%), #072C47; }
    .cc-side-title { display: flex; align-items: center; gap: 10px; margin: 4px 0 2px 0; }
    .cc-side-title span { font-family: 'Playfair Display', Georgia, serif; font-size: 22px; font-weight: 700; color: #FFFFFF; }
    .cc-side-sub { font-size: 12.5px; color: #9FB2C3; margin: 0 0 14px 0; }
    section[data-testid="stSidebar"] label {
        font-size: 12px !important;
        font-weight: 700 !important;
        letter-spacing: .08em; text-transform: uppercase;
        color: var(--copper-400) !important;
    }
    section[data-testid="stSidebar"] div[data-baseweb="select"] {
        font-size: 14px !important;
    }
    section[data-testid="stSidebar"] span[data-baseweb="tag"] {
        font-size: 12px !important;
        padding: 4px 8px !important;
        margin: 2px !important;
        background-color: #965E1E !important;
        color: #FFFFFF !important;
        border-radius: 999px !important;
    }
    section[data-testid="stSidebar"] span[data-baseweb="tag"] span, section[data-testid="stSidebar"] span[data-baseweb="tag"] svg { color: #FFFFFF !important; }
    ul[role="listbox"] {
        max-height: 60vh !important;
    }
    div[data-baseweb="popover"] div:has(> div:contains("No results")) {
        display: none !important;
    }
    ul[role="listbox"] > div {
        display: none !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stMultiSelect"]:nth-of-type(3) div[data-baseweb="select"] > div:first-child {
        min-height: 300px !important;
        align-items: flex-start !important;
        align-content: flex-start !important;
        background-color: #0E3E61 !important;
        border-radius: 8px !important;
    }

    @media (max-width: 640px) {
        .cc-hero { padding: 20px 18px; }
        .cc-hero h1 { font-size: 28px !important; }
    }
    @media (prefers-reduced-motion: reduce) {
        .cc-hero, .cc-kpi, .cc-bar > span, div[class*="st-key-cc-card"] { animation: none !important; }
        .cc-kpi, div[data-testid="stDownloadButton"] button { transition: none !important; }
    }
    </style>
""", unsafe_allow_html=True)


def html_limpio(contenido):
    """Quita la sangría de cada línea para que st.markdown no lo tome como bloque de código."""
    return "".join(linea.strip() for linea in contenido.splitlines())


def render_hero(subtitulo="Ventas, metas, exhibición e inventario en un solo lugar.", chips=None):
    chips_html = "".join(f'<span class="cc-chip">{c}</span>' for c in (chips or []))
    return html_limpio(f"""
        <div class="cc-hero">
            <div class="cc-hero-top">
                <div>
                    <div class="cc-eyebrow"><span class="cc-tri"></span>Reporte ejecutivo</div>
                    <h1>Dashboard Comercial</h1>
                    <p>{subtitulo}</p>
                </div>
                <div class="cc-chips">{chips_html}</div>
            </div>
        </div>
    """)


hero_slot = st.empty()
hero_slot.markdown(render_hero(), unsafe_allow_html=True)

# -----------------------------------
# FUNCIONES DE FORMATEO Y LIMPIEZA
# -----------------------------------
def normalizar_texto(texto):
    if pd.isna(texto):
        return ""
    texto_sin_tildes = ''.join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn')
    return " ".join(texto_sin_tildes.upper().split())

def limpiar_numero(valor):
    """
    Función súper robusta para leer números de Excel/CSV sin importar si están 
    en formato europeo (189.723,02), gringo (189,723.02), o puro decimal (189723.02).
    """
    if pd.isna(valor):
        return 0.0
    v = str(valor).strip()
    v = v.replace('%', '').replace('$', '').replace(' ', '')
    if v == '-' or v == '': 
        return 0.0
    
    if '.' in v and ',' in v:
        if v.rfind(',') > v.rfind('.'):
            v = v.replace('.', '').replace(',', '.')
        else:
            v = v.replace(',', '')
    elif ',' in v and '.' not in v:
        partes = v.split(',')
        if len(partes) > 2:
            v = "".join(partes[:-1]) + "." + partes[-1]
        else:
            v = v.replace(',', '.')
            
    try:
        return float(v)
    except:
        return 0.0

def limpiar_numero_nulo(valor):
    """Como limpiar_numero, pero deja vacío lo que no trae dato (en vez de convertirlo en 0)."""
    if pd.isna(valor) or str(valor).strip() in ('', '-'):
        return np.nan
    return limpiar_numero(valor)

def formatear_moneda(valor):
    if pd.isna(valor):
        return "$ 0,00"
    base = f"{valor:,.2f}"
    tabla_cambio = str.maketrans({',': '.', '.': ','})
    return f"$ {base.translate(tabla_cambio)}"

def formatear_porcentaje(valor):
    if pd.isna(valor):
        return "0,00 %"
    base = f"{valor:,.2f}"
    tabla_cambio = str.maketrans({',': '.', '.': ','})
    return f"{base.translate(tabla_cambio)} %"

def formatear_cobertura(valor):
    if pd.isna(valor) or valor == "" or valor is None:
        return "Sin data de inventario"
    try:
        base = f"{float(valor):,.2f}"
        tabla_cambio = str.maketrans({',': '.', '.': ','})
        return base.translate(tabla_cambio)
    except:
        return "Sin data de inventario"

def formatear_compacto(valor):
    """$ 1,25 M / $ 845,3 K para etiquetas de gráficos."""
    if pd.isna(valor):
        return "$ 0"
    tabla_cambio = str.maketrans({',': '.', '.': ','})
    absoluto = abs(valor)
    if absoluto >= 1_000_000:
        return f"$ {f'{valor / 1_000_000:,.2f}'.translate(tabla_cambio)} M"
    if absoluto >= 1_000:
        return f"$ {f'{valor / 1_000:,.1f}'.translate(tabla_cambio)} K"
    return f"$ {f'{valor:,.0f}'.translate(tabla_cambio)}"

# -----------------------------------
# COMPONENTES VISUALES (KPIs, TARJETAS Y GRÁFICOS)
# -----------------------------------
ICONOS = {
    "ventas": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 3v18h18"/><path d="m7 15 4-4 3 3 6-6"/><path d="M20 8V4h-4"/></svg>',
    "meta": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/></svg>',
    "avance": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3a9 9 0 1 0 9 9"/><path d="M12 7v5l3 2"/><path d="M16 3h5v5"/></svg>',
    "m2": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/></svg>',
    "inventario": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m21 8-9-5-9 5 9 5 9-5Z"/><path d="M3 8v8l9 5 9-5V8"/><path d="M12 13v8"/></svg>',
}

def nivel_avance(avance, meta):
    """Semáforo del avance: (clase css, color, texto)."""
    if meta <= 0:
        return "neutro", NAVY_600, "Sin meta asignada"
    if avance >= 100:
        return "ok", EXITO, "Meta cumplida"
    if avance >= 90:
        return "medio", ALERTA, "Cerca de la meta"
    return "bajo", PELIGRO, "Por debajo de la meta"

def kpi_card(indice, etiqueta, valor, icono, pie_html="", barra=None, destacado=False, valor_pequeno=False):
    clase = "cc-kpi destacado" if destacado else "cc-kpi"
    clase_valor = "cc-kpi-value pequeno" if valor_pequeno else "cc-kpi-value"
    barra_html = ""
    if barra is not None:
        ancho, color = barra
        barra_html = f'<div class="cc-bar"><span style="width:{max(0.0, min(ancho, 100.0)):.1f}%; background:{color};"></span></div>'
    return f"""
        <div class="{clase}" style="--i:{indice}">
            <div class="cc-kpi-head">
                <div class="cc-kpi-label">{etiqueta}</div>
                <div class="cc-kpi-icon">{ICONOS[icono]}</div>
            </div>
            <div class="{clase_valor}">{valor}</div>
            {barra_html}
            <div class="cc-kpi-foot">{pie_html}</div>
        </div>
    """

def render_kpis(tarjetas):
    st.markdown(html_limpio('<div class="cc-kpis">' + "".join(tarjetas) + '</div>'), unsafe_allow_html=True)

def titulo_tarjeta(titulo, subtitulo=""):
    sub = f'<p class="cc-card-sub">{subtitulo}</p>' if subtitulo else ""
    st.markdown(html_limpio(f'<div><p class="cc-card-title">{titulo}</p>{sub}</div>'), unsafe_allow_html=True)

CONFIG_GRAFICO = {
    "displaylogo": False,
    "locale": "es",
    "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d", "toggleSpikelines"],
    "toImageButtonOptions": {"format": "png", "scale": 2},
}

def estilo_figura(fig, alto=360, leyenda=True):
    fig.update_layout(
        height=alto,
        margin=dict(l=8, r=8, t=12, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Manrope, sans-serif", size=12.5, color=TEXTO),
        separators=",.",
        hoverlabel=dict(bgcolor=NAVY_800, bordercolor=NAVY_800, font=dict(family="Manrope, sans-serif", size=13, color="#FFFFFF")),
        showlegend=leyenda,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, bgcolor="rgba(0,0,0,0)"),
        bargap=0.28,
        transition=dict(duration=500, easing="cubic-in-out"),
    )
    fig.update_xaxes(showgrid=False, linecolor=BORDE, tickfont=dict(color=TEXTO_SUAVE), title=None, automargin=True)
    fig.update_yaxes(gridcolor=DIVISOR, zeroline=False, tickfont=dict(color=TEXTO_SUAVE), title=None, automargin=True)
    return fig

def mostrar_grafico(fig, clave):
    st.plotly_chart(fig, theme=None, config=CONFIG_GRAFICO, key=clave)

def estado_vacio(mensaje):
    st.markdown(html_limpio(f'<div class="cc-note">{mensaje}</div>'), unsafe_allow_html=True)


# -----------------------------------
# DETALLE POR ARTÍCULO (NOMBRE UNIFICADO Y UNIDADES VENDIDAS)
# -----------------------------------
ARCHIVO_REFERENCIA_ARTICULOS = "ARTICULOS_REFERENCIA.csv"

def _ordenar_medidas(texto):
    """Deja las medidas en un orden fijo: '214 330' y '330 214' son la misma lámina."""
    def cambia(m):
        a, b = int(m.group(1)), int(m.group(2))
        return f"{min(a, b)} {max(a, b)}"
    return re.sub(r'\b(\d{2,4}) (\d{2,4})\b', cambia, texto)

def normalizar_nombre_articulo(serie):
    """Deja el nombre del artículo limpio y comparable entre el sistema anterior y el actual."""
    s = serie.astype(str).fillna('').str.upper()
    s = s.str.replace(r'[\r\n]+', ' ', regex=True)
    s = s.str.replace(r'(MEDIDA|ANCHO|ACABADO)\s*:.*$', '', regex=True)
    s = s.str.replace(r'[^A-Z0-9ÑÁÉÍÓÚ"\'/\.\(\)\- ]', ' ', regex=True)
    s = s.str.split().str.join(' ')
    s = s.fillna('').astype('object').where(s.notna(), '')
    return s.map(lambda t: _ordenar_medidas(t) if isinstance(t, str) else '')

@st.cache_data(ttl=300)
def cargar_referencia_articulos():
    """
    Tabla de apoyo para contar unidades vendidas:
      - por CODIGO: unidad de medida y metros por unidad (un perfil de 6,10 m es 1 unidad).
      - por NOMBRE: precio unitario de referencia, para deducir la cantidad cuando el
        sistema no la trae (pasa sobre todo con las cotizaciones).
    Si el archivo no está, el dashboard sigue funcionando sin conversión.
    """
    vacio = pd.DataFrame(columns=['UNIDAD', 'METROS_POR_UNIDAD', 'PRECIO_REF'])
    if not os.path.exists(ARCHIVO_REFERENCIA_ARTICULOS):
        return vacio.copy(), vacio.copy()
    try:
        ref = leer_csv_auto_sep(ARCHIVO_REFERENCIA_ARTICULOS)
    except Exception:
        return vacio.copy(), vacio.copy()

    ref.columns = ref.columns.str.strip().str.upper()
    if 'CLAVE' not in ref.columns or 'TIPO' not in ref.columns:
        return vacio.copy(), vacio.copy()

    ref['CLAVE'] = ref['CLAVE'].astype(str).str.strip()
    ref['TIPO'] = ref['TIPO'].astype(str).str.strip().str.upper()
    if 'UNIDAD' in ref.columns:
        ref['UNIDAD'] = ref['UNIDAD'].astype(str).str.strip().str.upper()
    else:
        ref['UNIDAD'] = 'UND'
    for col in ('METROS_POR_UNIDAD', 'PRECIO_REF'):
        if col in ref.columns:
            ref[col] = ref[col].apply(limpiar_numero).replace(0.0, np.nan)
        else:
            ref[col] = np.nan

    ref = ref[ref['CLAVE'].ne('') & ref['CLAVE'].ne('NAN')]
    por_codigo = ref[ref['TIPO'] == 'CODIGO'].drop_duplicates('CLAVE').set_index('CLAVE')
    por_nombre = ref[ref['TIPO'] == 'NOMBRE'].drop_duplicates('CLAVE').set_index('CLAVE')
    return por_codigo, por_nombre

def preparar_detalle_articulos(df):
    """
    Agrega ARTICULO, SISTEMA, UNIDADES, UNIDAD_MEDIDA y CANT_ESTIMADA.

    El sistema anterior (pedidos PV) medía los perfiles por metro lineal: 6,10 m es una
    unidad y 18,30 m son tres. El sistema actual (COT/VTA) ya trae la unidad vendida.
    El vidrio y las láminas se siguen contando en m², que es como se venden.
    """
    for col in ('ARTICULO', 'SISTEMA', 'UNIDADES', 'UNIDAD_MEDIDA', 'CANT_ESTIMADA'):
        if col not in df.columns:
            df[col] = np.nan
    if 'NumeroPedido' not in df.columns:
        return df

    prefijo = df['NumeroPedido'].astype(str).str.extract(r'^([A-Za-z]+)', expand=False).str.upper()
    es_anterior = prefijo.eq('PV')
    df['SISTEMA'] = np.where(es_anterior, 'Sistema anterior', 'Sistema actual')

    # El nombre no siempre está en la misma columna: en el sistema actual, cuando
    # 'Articulo' viene lleno es ahí donde está el nombre y 'DescrArticulo' trae el acabado.
    desc = df['DescrArticulo'] if 'DescrArticulo' in df.columns else pd.Series('', index=df.index)
    art = df['Articulo'] if 'Articulo' in df.columns else pd.Series(np.nan, index=df.index)
    df['ARTICULO'] = normalizar_nombre_articulo(art.where((~es_anterior) & art.notna(), desc))

    # El sistema anterior le pega el acabado al final del nombre (... BLANCO, ... NEGRO) y el
    # actual no, así que el mismo artículo quedaba partido en varias filas. Aquí se le quita
    # para que un ángulo sea un solo artículo, venga del sistema que venga.
    if 'DescrAcabado' in df.columns:
        acabados = normalizar_nombre_articulo(df['DescrAcabado'].fillna('')).tolist()
        df['ARTICULO'] = [
            str(nombre)[: -len(acab)].strip()
            if (acab and isinstance(nombre, str) and nombre.endswith(' ' + acab) and len(nombre) > len(acab) + 1)
            else ('' if nombre is None or (isinstance(nombre, float) and pd.isna(nombre)) else str(nombre))
            for nombre, acab in zip(df['ARTICULO'].tolist(), acabados)
        ]

    df['ARTICULO'] = df['ARTICULO'].astype('object').fillna('')
    df.loc[df['ARTICULO'].isin(['', 'NAN', 'NAN NAN', 'NONE']), 'ARTICULO'] = 'SIN DESCRIPCION'

    codigo = art.astype(str).str.strip().where(es_anterior, '')
    if 'TMetraje' in df.columns:
        metraje = df['TMetraje'].apply(limpiar_numero_nulo)
    else:
        metraje = pd.Series(np.nan, index=df.index)
    venta = pd.to_numeric(df.get('ImporteDivisaPrincipal'), errors='coerce')

    por_codigo, por_nombre = cargar_referencia_articulos()
    if not por_codigo.empty:
        unidad = codigo.map(por_codigo['UNIDAD'])
        factor = pd.to_numeric(codigo.map(por_codigo['METROS_POR_UNIDAD']), errors='coerce')
    else:
        unidad = pd.Series(np.nan, index=df.index)
        factor = pd.Series(np.nan, index=df.index)

    unidad = unidad.where(es_anterior).fillna('UND')
    factor = factor.where(es_anterior).fillna(1.0)
    factor = factor.mask(~(factor > 0), 1.0)

    es_m2 = unidad.eq('M2')
    cantidad = pd.Series(np.where(es_m2, metraje, metraje / factor), index=df.index)

    # Vidrio cortado a la medida ("VIDRIO POR M2 (TIENDA)"): TMetraje trae las PIEZAS y la
    # medida viene en la descripción, así que los m² son ancho x alto (cm) x piezas.
    desc_txt = desc.astype(str).str.upper()
    medidas = desc_txt.str.extract(r'ANCHO:\s*([\d\.,]+)\s*X\s*ALTO:\s*([\d\.,]+)')
    ancho = medidas[0].apply(limpiar_numero_nulo)
    alto = medidas[1].apply(limpiar_numero_nulo)
    es_corte = (desc_txt.str.contains('POR M2', regex=False)
                & ancho.gt(0) & alto.gt(0) & metraje.gt(0))
    if es_corte.any():
        cantidad.loc[es_corte] = (ancho * alto / 10000 * metraje)[es_corte]
        es_m2 = es_m2 | es_corte

    # Los servicios (corte, canto pulido, flete...) no son piezas: se dejan sin unidades
    # para que no inflen "Unidades vendidas". Su venta sí se sigue sumando.
    if 'DescrLineaNegocio' in df.columns:
        es_servicio = df['DescrLineaNegocio'].apply(normalizar_texto).str.startswith('SERVICIO')
    else:
        es_servicio = pd.Series(False, index=df.index)
    es_servicio = es_servicio & ~es_m2
    cantidad.loc[es_servicio] = np.nan

    # Lo que no trae cantidad (sobre todo cotizaciones) se deduce del precio unitario.
    estimada = pd.Series(False, index=df.index)
    falta = cantidad.isna() & venta.gt(0) & ~es_servicio
    if falta.any() and not por_nombre.empty:
        precio = pd.to_numeric(df.loc[falta, 'ARTICULO'].map(por_nombre['PRECIO_REF']), errors='coerce')
        deducida = (venta[falta] / precio).round()
        deducida = deducida.where(deducida >= 1)
        cantidad.loc[falta] = deducida
        estimada.loc[falta] = deducida.notna()

    # Si aun así no hay con qué deducirla, se cuenta el renglón como una unidad:
    # toda venta movió al menos una pieza, y una unidad es el valor más frecuente
    # (el 55 % de los renglones con cantidad conocida son exactamente uno).
    resto = cantidad.isna() & venta.ne(0) & (~es_m2) & (~es_servicio)
    if resto.any():
        cantidad.loc[resto] = 1.0
        estimada.loc[resto] = True

    # Sistema actual: el vidrio y el espejo se venden por lámina completa, media (1/2) o
    # tercio (1/3), así que la cantidad viene en piezas. Se pasa a m² con la medida de la
    # lámina que trae el nombre (330×214, 366×214, 183×244...); si no la trae, se usa la
    # lámina estándar de 3,30 x 2,14 m.
    nombre = df['ARTICULO'].astype(str)
    es_lamina = ((~es_anterior) & (~es_m2) & (~es_servicio) & cantidad.notna()
                 & nombre.str.contains(r'^(?:VIDRIO|ESPEJO)\b.*\b\d+\s*MM\b', regex=True))
    if es_lamina.any():
        lados = nombre.str.extract(r'\b(\d{2,4}) (\d{2,4})\b').apply(pd.to_numeric, errors='coerce')
        area = (lados[0] * lados[1] / 10000).fillna(3.30 * 2.14)
        fraccion = pd.Series(np.select(
            [nombre.str.contains(r'\bTERCIO\b|\b1/3\b', regex=True),
             nombre.str.contains(r'\bMEDIA\b|\b1/2\b', regex=True)],
            [1 / 3, 1 / 2], default=1.0), index=df.index)
        cantidad.loc[es_lamina] = (cantidad * area * fraccion)[es_lamina]
        es_m2 = es_m2 | es_lamina
        # Ya en m², la lámina, la media y el tercio son el mismo vidrio, venga la lámina
        # del tamaño que venga: se quita la fracción y la medida del nombre para que queden
        # en una sola fila (y coincidan con el nombre del sistema anterior).
        df.loc[es_lamina, 'ARTICULO'] = (
            nombre[es_lamina]
            .str.replace(r'\s*\b(?:TERCIO|MEDIA)\b', '', regex=True)
            .str.replace(r'\s*\b1/[23]\b', '', regex=True)
            .str.replace(r'\s*\b\d{2,4} \d{2,4}\b', '', regex=True)
            .str.split().str.join(' ')
        )

    # Las devoluciones (venta negativa) traen la cantidad en positivo: se le pone el mismo
    # signo que la venta para que resten unidades, igual que restan dinero.
    cantidad = cantidad.abs().where(~venta.lt(0), -cantidad.abs())

    df['UNIDADES'] = cantidad.where(es_m2, cantidad.round())
    df['UNIDAD_MEDIDA'] = np.select([es_servicio, es_m2], ['servicio', 'm²'], default='unid')
    df['CANT_ESTIMADA'] = estimada
    return df

# -----------------------------------
# CARGA Y LIMPIEZA DE DATA
# -----------------------------------
ID_DRIVE_VENTAS = "16XYtA31ebAE1Ad2Ldj7OV-CBbxO0IVSf"

def _es_html(contenido):
    """Detecta si Google Drive devolvió una página web (aviso/bloqueo) en lugar del CSV."""
    inicio = contenido[:1000].lstrip().lower()
    return inicio.startswith(b"<!doctype html") or inicio.startswith(b"<html") or b"<html" in inicio

def leer_csv_flexible(origen, sep=";"):
    """
    Lee un CSV sin importar si fue guardado en UTF-8 (Excel 'CSV UTF-8', GitHub)
    o en ANSI/latin-1 (Excel 'CSV delimitado por comas'). Así la Ñ y las tildes
    (ej. PUERTAS DE BAÑO) siempre se leen bien.
    """
    ultimo_error = None
    for enc in ("utf-8-sig", "latin-1"):
        try:
            if hasattr(origen, "seek"):
                origen.seek(0)
            return pd.read_csv(origen, encoding=enc, sep=sep, low_memory=False)
        except UnicodeDecodeError as e:
            ultimo_error = e
    raise ultimo_error

def leer_csv_auto_sep(ruta):
    """Lee con ';' y, si sale una sola columna, reintenta con ','."""
    df_tmp = leer_csv_flexible(ruta, sep=";")
    if len(df_tmp.columns) < 2:
        df_tmp = leer_csv_flexible(ruta, sep=",")
    return df_tmp

def _leer_csv_ventas(origen):
    return leer_csv_flexible(origen, sep=";")

def descargar_ventas_drive(file_id):
    """
    Descarga el CSV de Ventas desde Google Drive.
    1) Enlace directo de drive.usercontent (salta el aviso de 'no se pudo analizar en busca de virus').
    2) Respaldo con gdown.
    Devuelve (DataFrame, lista_de_errores).
    """
    errores = []

    # Intento 1: descarga directa con requests
    try:
        import requests
        resp = requests.get(
            "https://drive.usercontent.google.com/download",
            params={"id": file_id, "export": "download", "confirm": "t"},
            timeout=180,
        )
        resp.raise_for_status()
        contenido = resp.content
        if _es_html(contenido):
            raise ValueError("Drive devolvió una página HTML en lugar del CSV (permisos o límite de descargas).")
        df = _leer_csv_ventas(io.BytesIO(contenido))
        if not df.empty:
            return df, errores
        errores.append("Descarga directa: el archivo llegó vacío.")
    except Exception as e:
        errores.append(f"Descarga directa: {e}")

    # Intento 2: gdown
    archivo_temp = "ventas_drive_temp.csv"
    try:
        gdown.download(id=file_id, output=archivo_temp, quiet=True)
        if os.path.exists(archivo_temp):
            with open(archivo_temp, "rb") as f:
                if _es_html(f.read(1000)):
                    raise ValueError("gdown descargó una página HTML en lugar del CSV.")
            df = _leer_csv_ventas(archivo_temp)
            if not df.empty:
                return df, errores
            errores.append("gdown: el archivo llegó vacío.")
        else:
            errores.append("gdown: no se generó el archivo.")
    except Exception as e:
        errores.append(f"gdown: {e}")
    finally:
        if os.path.exists(archivo_temp):
            try:
                os.remove(archivo_temp)
            except Exception:
                pass

    return pd.DataFrame(), errores

@st.cache_data(ttl=300, show_spinner="Cargando base de datos de Ventas...")
def cargar_datos():
    df, errores = descargar_ventas_drive(ID_DRIVE_VENTAS)

    # Respaldo local en el repositorio (ventas.csv.gz pesa ~4 MB y sí cabe en GitHub)
    if df.empty:
        for archivo_local in ["ventas.csv.gz", "ventas.zip", "ventas.csv"]:
            if os.path.exists(archivo_local):
                try:
                    df = _leer_csv_ventas(archivo_local)
                    if not df.empty:
                        break
                except Exception as e:
                    errores.append(f"{archivo_local}: {e}")
        else:
            if df.empty:
                errores.append("No hay respaldo local (ventas.csv.gz / ventas.zip / ventas.csv) en el repositorio.")

    if df.empty:
        return pd.DataFrame(), pd.DataFrame(), errores

    col_año = [c for c in df.columns if 'AÑO' in c.upper() or 'AÃ' in c.upper()]
    if col_año:
        df = df.rename(columns={col_año[0]: 'AÑO'})
        
    if 'AÑO' in df.columns:
        df['AÑO'] = pd.to_numeric(df['AÑO'], errors='coerce').fillna(0).astype(int)
        
    df.columns = df.columns.str.strip()
    
    if 'ImporteDivisaPrincipal' in df.columns:
        df['ImporteDivisaPrincipal'] = df['ImporteDivisaPrincipal'].apply(limpiar_numero)

    df = preparar_detalle_articulos(df)
    
    if 'Nombre' in df.columns:
        df['Nombre'] = df['Nombre'].str.replace('SUCURSAL ', '', regex=False).str.upper().str.strip()
        df['Nombre'] = df['Nombre'].replace({
            'ALUMINIOLOGO WEB': 'ALUMUNIOLOGO WED',
            'SHOWROOM - 000': 'SHOWROOM'
        })
    
    if 'DEPARTAMENTO' in df.columns:
        df['DEPARTAMENTO'] = df['DEPARTAMENTO'].apply(normalizar_texto)
    
    archivo_m2 = "METROS CUADRADOS POR CATEGORIA.csv"
    if not os.path.exists(archivo_m2):
        return df, pd.DataFrame(), errores
        
    df_m2 = leer_csv_flexible(archivo_m2, sep=";")
    df_m2.columns = df_m2.columns.str.strip()
    
    if 'DEPARTAMENTO' in df_m2.columns:
        df_m2['DEPARTAMENTO'] = df_m2['DEPARTAMENTO'].ffill().apply(normalizar_texto)
        
    if 'CATEGORIA' in df_m2.columns:
        df_m2['CATEGORIA'] = df_m2['CATEGORIA'].apply(normalizar_texto)
        df_m2 = df_m2[(df_m2['CATEGORIA'] != 'NAN') & (df_m2['CATEGORIA'] != '')]
    
    if 'METROS' in df_m2.columns:
        df_m2['METROS'] = df_m2['METROS'].apply(limpiar_numero)
        
    return df, df_m2, errores

ARCHIVO_AREAS = "AREAS_RETAIL_2026.xlsx"
SIN_AREA = "SIN ÁREA"

@st.cache_data(ttl=300)
def cargar_areas():
    """
    Lee AREAS_RETAIL_2026.xlsx (ÁREA | DEPARTAMENTO | CATEGORIA) y devuelve un diccionario
    CATEGORIA -> ÁREA. La categoría basta, porque cada una pertenece a una sola área.
    Si el archivo no está, el dashboard sigue funcionando y todo queda en "SIN ÁREA".
    """
    if not os.path.exists(ARCHIVO_AREAS):
        return {}
    try:
        areas = pd.read_excel(ARCHIVO_AREAS, dtype=str)
    except Exception:
        return {}
    areas.columns = [normalizar_texto(c) for c in areas.columns]
    if 'AREA' not in areas.columns or 'CATEGORIA' not in areas.columns:
        return {}
    areas = areas.dropna(subset=['AREA', 'CATEGORIA'])
    areas['CATEGORIA'] = areas['CATEGORIA'].apply(normalizar_texto)
    areas['AREA'] = areas['AREA'].astype(str).str.strip().str.upper()
    areas = areas[areas['CATEGORIA'].ne('')].drop_duplicates('CATEGORIA')
    return dict(zip(areas['CATEGORIA'], areas['AREA']))

@st.cache_data(ttl=60)
def cargar_inventario():
    archivo_inv = "INVENTARIO.csv"
    if not os.path.exists(archivo_inv):
        return pd.DataFrame()
    try:
        df_inv = leer_csv_flexible(archivo_inv, sep=";")
        df_inv.columns = df_inv.columns.str.strip()
        
        col_año = [c for c in df_inv.columns if 'AÑO' in c.upper() or 'AÃ' in c.upper()]
        if col_año:
            df_inv = df_inv.rename(columns={col_año[0]: 'AÑO'})
            
        if 'AÑO' in df_inv.columns:
            df_inv['AÑO'] = pd.to_numeric(df_inv['AÑO'], errors='coerce').fillna(0).astype(int)
            
        if 'DEPARTAMENTO' in df_inv.columns:
            df_inv['DEPARTAMENTO'] = df_inv['DEPARTAMENTO'].apply(normalizar_texto)
            
        if 'DescrLineaNegocio' in df_inv.columns:
            df_inv['CATEGORIA'] = df_inv['DescrLineaNegocio'].apply(normalizar_texto)
            
        if 'MES' in df_inv.columns:
            df_inv['MES'] = df_inv['MES'].astype(str).str.strip().str.upper()
            
        if 'NOMBRE DE ALMACEN' in df_inv.columns:
            df_inv['SUCURSAL'] = df_inv['NOMBRE DE ALMACEN'].astype(str).str.upper().str.strip()
            df_inv['SUCURSAL'] = df_inv['SUCURSAL'].str.replace('TIENDA ', '', regex=False)
            df_inv['SUCURSAL'] = df_inv['SUCURSAL'].str.replace('SUCURSAL ', '', regex=False)
            
        if 'Valor' in df_inv.columns:
            df_inv['Valor'] = df_inv['Valor'].apply(limpiar_numero)
        return df_inv
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def cargar_metas_y_porcentajes_estructurados():
    df_meta = pd.DataFrame()
    if os.path.exists("META_2026.csv"):
        try:
            df_meta = leer_csv_auto_sep("META_2026.csv")
            df_meta.columns = df_meta.columns.str.strip()
        except Exception:
            pass

    df_pct = pd.DataFrame()
    if os.path.exists("METAS_POR_SUCURSAL_Y_CATEGORIA_PORCENTAJES.csv"):
        try:
            df_pct = leer_csv_auto_sep("METAS_POR_SUCURSAL_Y_CATEGORIA_PORCENTAJES.csv")
            df_pct.columns = df_pct.columns.str.strip()
        except Exception:
            pass

    return df_meta, df_pct

df, df_m2, errores_carga = cargar_datos()

if df.empty:
    st.error("No se pudo cargar la base de datos de Ventas. Revisa la conexión o el archivo.")
    with st.expander("Ver detalle técnico del error"):
        for err in errores_carga:
            st.write(f"- {err}")
    if st.button("Reintentar carga", icon=":material/refresh:", type="primary"):
        st.cache_data.clear()
        st.rerun()
    st.stop()

if errores_carga:
    st.warning("No se pudo descargar Ventas desde Google Drive; se está usando el respaldo del repositorio (puede no estar actualizado).", icon=":material/cloud_off:")

df_inv = cargar_inventario()
df_meta_csv, df_pct_csv = cargar_metas_y_porcentajes_estructurados()

df = df.rename(columns={
    'ImporteDivisaPrincipal': 'VENTA',
    'DescrLineaNegocio': 'CATEGORIA',
    'Nombre': 'SUCURSAL'
})

if 'CATEGORIA' in df.columns:
    df['CATEGORIA'] = df['CATEGORIA'].apply(normalizar_texto)
    # Área comercial de cada categoría (AREAS_RETAIL_2026.xlsx).
    df['AREA'] = df['CATEGORIA'].map(cargar_areas()).fillna(SIN_AREA)
if 'DEPARTAMENTO' in df.columns:
    df['DEPARTAMENTO'] = df['DEPARTAMENTO'].apply(normalizar_texto)

# -----------------------------------
# ESTRUCTURA DE ORDENAMIENTO ESTRICTO
# -----------------------------------
orden_meses = ['ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO', 
               'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']

orden_sucursales = ['CATIA', 'LA GUAIRA', 'MARICHE', 'GUATIRE', 'ALUMUNIOLOGO WED', 
                    'DISTRIBUIDORES', 'REPRESENTANTES COMERCIALES', 'SHOWROOM']

orden_departamentos_base = [
    'VENTANAS Y PUERTAS CORREDIZAS', 'VENTANAS ABATIBLES', 'DIVISIONES DE AMBIENTE',
    'PERFILES ESTANDAR', 'PRODUCTOS ESTANDAR', 'PUERTAS EXTERIORES', 'PUERTAS INTERIORES',
    'BARANDAS', 'PUERTAS DE BAÑO', 'VIDRIOS', 'SIL Y SELL', 'HERRAMIENTAS',
    'IMPULSO', 'CERRADURAS Y CANDADOS', 'PERSIANAS Y MOSQUITEROS', 'LAMINAS'
]

if 'DEPARTAMENTO' in df.columns:
    otros_deps = [d for d in df['DEPARTAMENTO'].dropna().unique() if d not in orden_departamentos_base]
    orden_departamentos = orden_departamentos_base + otros_deps
else:
    orden_departamentos = orden_departamentos_base

if 'MES' in df.columns:
    df['MES'] = pd.Categorical(df['MES'].astype(str).str.upper().str.strip(), categories=orden_meses, ordered=True)
if 'SUCURSAL' in df.columns:
    df['SUCURSAL'] = df['SUCURSAL'].where(df['SUCURSAL'].isin(orden_sucursales))
    df['SUCURSAL'] = pd.Categorical(df['SUCURSAL'], categories=[s.upper() for s in orden_sucursales], ordered=True)
if 'DEPARTAMENTO' in df.columns:
    df['DEPARTAMENTO'] = pd.Categorical(df['DEPARTAMENTO'], categories=orden_departamentos, ordered=True)


# -----------------------------------
# FILTROS LATERALES SIMPLES Y ROBUSTOS
# -----------------------------------
st.sidebar.markdown(html_limpio("""
    <div class="cc-side-title"><span class="cc-tri"></span><span>Filtros de análisis</span></div>
    <p class="cc-side-sub">Todo el reporte se recalcula al cambiar un filtro.</p>
"""), unsafe_allow_html=True)

if 'AÑO' not in df.columns:
    st.stop()

anios_disponibles = sorted(df['AÑO'].dropna().unique(), reverse=True)
año_sel = st.sidebar.selectbox("Año Seleccionado", anios_disponibles)

if año_sel is None:
    st.stop()

todas_sucursales = [s for s in orden_sucursales if s in df['SUCURSAL'].astype(str).unique()]
todos_departamentos = [d for d in orden_departamentos if d in df['DEPARTAMENTO'].astype(str).unique()]

meses_sel = st.sidebar.multiselect(
    "Meses", 
    options=orden_meses, 
    default=orden_meses, 
    placeholder="Seleccione Meses..."
)

sucursal_sel = st.sidebar.multiselect(
    "Sucursales", 
    options=todas_sucursales, 
    default=todas_sucursales, 
    placeholder="Seleccione Sucursales..."
)

departamentos_sel = st.sidebar.multiselect(
    "Departamentos", 
    options=todos_departamentos, 
    default=todos_departamentos, 
    placeholder="Seleccione Departamentos..."
)

if not meses_sel or not sucursal_sel or not departamentos_sel:
    render_kpis([
        kpi_card(0, "Ventas totales", "$ 0,00", "ventas", "Sin datos para mostrar", destacado=True),
        kpi_card(1, "Meta fijada", "$ 0,00", "meta", "Sin datos para mostrar"),
        kpi_card(2, "Porcentaje de avance", "0,00 %", "avance", "Sin datos para mostrar", barra=(0, COBRE_500)),
        kpi_card(3, "Eficiencia exhibición frontal (venta/m²)", "$ 0,00", "m2", "Sin datos para mostrar"),
        kpi_card(4, "Cobertura de inventario", "Sin data de inventario", "inventario", "Sin datos para mostrar", valor_pequeno=True),
    ])
    st.warning("Debes seleccionar al menos un Mes, una Sucursal y un Departamento en la barra lateral para poder generar el reporte.", icon=":material/filter_alt:")
    st.stop()

mask_mes = df['MES'].astype(str).isin(meses_sel)
mask_sucursal = df['SUCURSAL'].astype(str).isin(sucursal_sel)
mask_depto = df['DEPARTAMENTO'].astype(str).isin(departamentos_sel)

mask_comun = mask_mes & mask_sucursal & mask_depto
df_filtrado = df[(df['AÑO'] == int(año_sel)) & mask_comun]

# -------------------------------------------------------------------------
# CALCULO DINAMICO DE METAS (CON LIMPIEZA ROBUSTA Y NORMALIZACIÓN EXACTA)
# -------------------------------------------------------------------------
tabla_ant = pd.DataFrame(columns=['DEPARTAMENTO', 'CATEGORIA', 'META'])
# Misma meta, repartida por sucursal y mes (solo para los gráficos)
metas_suc_mes = pd.DataFrame(columns=['SUCURSAL', 'MES', 'META'])

if not df_meta_csv.empty and not df_pct_csv.empty:
    try:
        df_m_calc = df_meta_csv.copy()
        df_m_calc.columns = df_m_calc.columns.str.strip()
        df_m_calc['SUCURSAL'] = df_m_calc['SUCURSAL'].astype(str).str.upper().str.strip()
        df_m_calc['SUCURSAL'] = df_m_calc['SUCURSAL'].replace({'ECOMMERCE': 'ALUMUNIOLOGO WED', 'ALUMINIOLOGO WEB': 'ALUMUNIOLOGO WED'})
        
        sucursales_up = [str(s).upper().strip() for s in sucursal_sel]
        
        mask_m = (
            (df_m_calc['AÑO'].astype(str) == str(año_sel)) &
            (df_m_calc['MESES'].astype(str).str.upper().str.strip().isin(meses_sel)) &
            (df_m_calc['SUCURSAL'].isin(sucursales_up))
        )
        df_m_fil = df_m_calc[mask_m].copy()
        
        # Uso de la nueva limpieza robusta
        df_m_fil['META_NUM'] = df_m_fil['META'].apply(limpiar_numero)
        totales_meta_suc = df_m_fil.groupby('SUCURSAL')['META_NUM'].sum().to_dict()
        
        df_p_calc = df_pct_csv.copy()
        df_p_calc.columns = df_p_calc.columns.str.strip()
        df_p_calc['SUCURSAL'] = df_p_calc['SUCURSAL'].astype(str).str.upper().str.strip()
        df_p_calc['SUCURSAL'] = df_p_calc['SUCURSAL'].replace({'ECOMMERCE': 'ALUMUNIOLOGO WED', 'ALUMINIOLOGO WEB': 'ALUMUNIOLOGO WED'})
        
        df_p_calc['DEPARTAMENTO'] = df_p_calc['DEPARTAMENTO'].apply(normalizar_texto)
        df_p_calc['CATEGORIA'] = df_p_calc['CATEGORIA'].apply(normalizar_texto)
        
        # Limpieza robusta de los porcentajes
        df_p_calc['PCT_VAL'] = df_p_calc['PORCENTAJE'].apply(limpiar_numero)
        
        # Normalizar los porcentajes por sucursal para que sumen exactamente el 100% (o 1.0)
        # Esto previene diferencias de centavos y garantiza la fidelidad exacta de META_2026.csv
        suma_pcts_por_suc = df_p_calc.groupby('SUCURSAL')['PCT_VAL'].transform('sum')
        df_p_calc['PCT_VAL_NORM'] = np.where(suma_pcts_por_suc > 0, df_p_calc['PCT_VAL'] / suma_pcts_por_suc, 0.0)
        
        df_p_fil = df_p_calc[
            (df_p_calc['SUCURSAL'].isin(sucursales_up)) &
            (df_p_calc['DEPARTAMENTO'].isin(departamentos_sel))
        ].copy()
        
        lista_metas = []
        lista_metas_mes = []
        for suc in sucursales_up:
            monto_suc = totales_meta_suc.get(suc, 0.0)
            if monto_suc > 0:
                df_s = df_p_fil[df_p_fil['SUCURSAL'] == suc].copy()
                df_s['META'] = df_s['PCT_VAL_NORM'] * monto_suc
                lista_metas.append(df_s[['DEPARTAMENTO', 'CATEGORIA', 'META']])

                factor_deptos = df_s['PCT_VAL_NORM'].sum()
                df_mes_s = df_m_fil[df_m_fil['SUCURSAL'] == suc].copy()
                df_mes_s['MES'] = df_mes_s['MESES'].astype(str).str.upper().str.strip()
                df_mes_s = df_mes_s.groupby('MES')['META_NUM'].sum().reset_index()
                df_mes_s['META'] = df_mes_s['META_NUM'] * factor_deptos
                df_mes_s['SUCURSAL'] = suc
                lista_metas_mes.append(df_mes_s[['SUCURSAL', 'MES', 'META']])

        if lista_metas_mes:
            metas_suc_mes = pd.concat(lista_metas_mes, ignore_index=True)
                
        if lista_metas:
            df_concat_m = pd.concat(lista_metas, ignore_index=True)
            tabla_ant = df_concat_m.groupby(['DEPARTAMENTO', 'CATEGORIA'], observed=True)['META'].sum().reset_index()
            
    except Exception as e:
        st.error(f"Error procesando metas estructuradas: {e}")

# --- FILTROS COBERTURA MULTI-MES (GLOBAL - SIN FILTRO DE SUCURSAL) ---
df_inv_filtrado = pd.DataFrame()
df_venta_mes_ant = pd.DataFrame()
mes_inventario = None

if not df_inv.empty and 'AÑO' in df_inv.columns and 'DEPARTAMENTO' in df_inv.columns and 'MES' in df_inv.columns:
    mask_inv_comun = (df_inv['AÑO'] == int(año_sel)) & (df_inv['DEPARTAMENTO'].isin(departamentos_sel))
    df_inv_base = df_inv[mask_inv_comun]
    meses_validos_inv = [m for m in orden_meses if m in meses_sel and m in df_inv_base['MES'].unique()]
    
    if meses_validos_inv:
        ultimo_mes_existente = meses_validos_inv[-1]
        mes_inventario = ultimo_mes_existente
        df_inv_filtrado = df_inv_base[df_inv_base['MES'] == ultimo_mes_existente]
        
        idx_ultimo = orden_meses.index(ultimo_mes_existente)
        meses_anteriores_en_seleccion = [m for m in meses_sel if orden_meses.index(m) < idx_ultimo]
        
        if len(meses_anteriores_en_seleccion) == 0:
            if idx_ultimo > 0:
                meses_para_ventas = [(int(año_sel), orden_meses[idx_ultimo - 1])]
            else:
                meses_para_ventas = [(int(año_sel) - 1, 'DICIEMBRE')]
        else:
            meses_para_ventas = [(int(año_sel), m) for m in meses_anteriores_en_seleccion]
            
        frames_ant = []
        for a_ant, m_ant in meses_para_ventas:
            frame_ventas = df[(df['AÑO'] == a_ant) & (df['MES'] == m_ant) & (df['DEPARTAMENTO'].isin(departamentos_sel))]
            frames_ant.append(frame_ventas)
        
        if frames_ant:
            df_venta_mes_ant = pd.concat(frames_ant, ignore_index=True)

if not df_venta_mes_ant.empty:
    ventas_ant_agrupadas = df_venta_mes_ant.groupby(['DEPARTAMENTO', 'CATEGORIA'], observed=True)['VENTA'].sum().reset_index()
    ventas_ant_agrupadas = ventas_ant_agrupadas.rename(columns={'VENTA': 'VENTA_MES_ANT'})
else:
    ventas_ant_agrupadas = pd.DataFrame(columns=['DEPARTAMENTO', 'CATEGORIA', 'VENTA_MES_ANT'])

# -----------------------------------
# PROCESAMIENTO MATRICIAL DE LOS DATOS
# -----------------------------------
df_m2_sel = pd.DataFrame()
if not df_m2.empty and 'DEPARTAMENTO' in df_m2.columns:
    df_m2_sel = df_m2[df_m2['DEPARTAMENTO'].isin(departamentos_sel)].copy()

if not df_filtrado.empty and 'DEPARTAMENTO' in df_filtrado.columns and 'CATEGORIA' in df_filtrado.columns:
    tabla_actual = df_filtrado.groupby(['DEPARTAMENTO', 'CATEGORIA'], observed=True)['VENTA'].sum().reset_index()
else:
    tabla_actual = pd.DataFrame(columns=['DEPARTAMENTO', 'CATEGORIA', 'VENTA'])

if not tabla_actual.empty or not tabla_ant.empty:
    tabla_ventas = pd.merge(tabla_actual, tabla_ant, on=['DEPARTAMENTO', 'CATEGORIA'], how='outer')
else:
    tabla_ventas = pd.DataFrame(columns=['DEPARTAMENTO', 'CATEGORIA', 'VENTA', 'META'])

if not df_m2_sel.empty and 'METROS' in df_m2_sel.columns:
    tabla_base = pd.merge(df_m2_sel[['DEPARTAMENTO', 'CATEGORIA', 'METROS']], tabla_ventas, on=['DEPARTAMENTO', 'CATEGORIA'], how='outer')
else:
    tabla_base = tabla_ventas.copy()
    tabla_base['METROS'] = 0.0

tabla_base['VENTA'] = pd.to_numeric(tabla_base.get('VENTA', pd.Series(dtype=float)), errors='coerce').fillna(0.0)
tabla_base['META'] = pd.to_numeric(tabla_base.get('META', pd.Series(dtype=float)), errors='coerce').fillna(0.0)
tabla_base['METROS'] = pd.to_numeric(tabla_base.get('METROS', pd.Series(dtype=float)), errors='coerce').fillna(0.0)
tabla_base = tabla_base.rename(columns={'METROS': 'M2'})

tabla_base = tabla_base[(tabla_base['VENTA'] > 0) | (tabla_base['META'] > 0) | (tabla_base['M2'] > 0)]

tabla_base['AVANCE'] = np.where(tabla_base['META'] > 0, (tabla_base['VENTA'] / tabla_base['META']) * 100, 0.0)
tabla_base['EFICIENCIA EXHIBICION FRONTAL (VENTA/M2)'] = np.where(tabla_base['M2'] > 0, tabla_base['VENTA'] / tabla_base['M2'], 0.0)

# --- CRUCE Y CÁLCULO DE COBERTURA ---
if not df_inv_filtrado.empty and 'Valor' in df_inv_filtrado.columns:
    inv_agrupado = df_inv_filtrado.groupby(['DEPARTAMENTO', 'CATEGORIA'], observed=True)['Valor'].sum().reset_index()
    tabla_base = pd.merge(tabla_base, inv_agrupado, on=['DEPARTAMENTO', 'CATEGORIA'], how='left')
    tabla_base = pd.merge(tabla_base, ventas_ant_agrupadas, on=['DEPARTAMENTO', 'CATEGORIA'], how='left')
    
    tabla_base['Valor'] = pd.to_numeric(tabla_base.get('Valor', pd.Series(dtype=float)), errors='coerce').fillna(0.0)
    tabla_base['VENTA_MES_ANT'] = pd.to_numeric(tabla_base.get('VENTA_MES_ANT', pd.Series(dtype=float)), errors='coerce').fillna(0.0)
    
    tabla_base['COBERTURA'] = np.where(tabla_base['VENTA_MES_ANT'] > 0, tabla_base['Valor'] / tabla_base['VENTA_MES_ANT'], 0.0)
else:
    tabla_base['Valor'] = 0.0
    tabla_base['VENTA_MES_ANT'] = 0.0
    tabla_base['COBERTURA'] = np.nan

tabla_base['ORDEN_REGISTRO'] = 0

if not tabla_base.empty:
    agg_dict = {'VENTA': 'sum', 'META': 'sum', 'M2': 'sum', 'Valor': 'sum'}
    if 'VENTA_MES_ANT' in tabla_base.columns:
        agg_dict['VENTA_MES_ANT'] = 'sum'
        
    subtotales = tabla_base.groupby('DEPARTAMENTO', observed=True).agg(agg_dict).reset_index()
    subtotales['CATEGORIA'] = 'TOTAL DEPARTAMENTO'
    subtotales['AVANCE'] = np.where(subtotales['META'] > 0, (subtotales['VENTA'] / subtotales['META']) * 100, 0.0)
    subtotales['EFICIENCIA EXHIBICION FRONTAL (VENTA/M2)'] = np.where(subtotales['M2'] > 0, subtotales['VENTA'] / subtotales['M2'], 0.0)
    
    if not df_inv_filtrado.empty and 'VENTA_MES_ANT' in subtotales.columns:
        subtotales['COBERTURA'] = np.where(subtotales['VENTA_MES_ANT'] > 0, subtotales['Valor'] / subtotales['VENTA_MES_ANT'], 0.0)
    else:
        subtotales['COBERTURA'] = np.nan
    subtotales['ORDEN_REGISTRO'] = 1
else:
    subtotales = pd.DataFrame()

total_g_venta = tabla_base["VENTA"].sum() if not tabla_base.empty else 0.0
total_g_meta = subtotales["META"].sum() if not subtotales.empty else 0.0
total_g_m2 = subtotales["M2"].sum() if not subtotales.empty else 0.0
total_g_avance = (total_g_venta / total_g_meta) * 100 if total_g_meta > 0 else 0.0
total_g_eficiencia = total_g_venta / total_g_m2 if total_g_m2 > 0 else 0.0

total_g_valor = tabla_base["Valor"].sum() if not tabla_base.empty else 0.0
total_g_venta_ant = tabla_base["VENTA_MES_ANT"].sum() if not tabla_base.empty and 'VENTA_MES_ANT' in tabla_base.columns else 0.0

if not df_inv_filtrado.empty:
    total_g_cobertura = total_g_valor / total_g_venta_ant if total_g_venta_ant > 0 else 0.0
else:
    total_g_cobertura = np.nan

fila_total_general = pd.DataFrame([{
    'DEPARTAMENTO': 'TOTAL GENERAL',
    'CATEGORIA': 'REPORTE CONSOLIDADO',
    'M2': total_g_m2,
    'VENTA': total_g_venta,
    'META': total_g_meta,
    'AVANCE': total_g_avance,
    'EFICIENCIA EXHIBICION FRONTAL (VENTA/M2)': total_g_eficiencia,
    'Valor': total_g_valor,
    'COBERTURA': total_g_cobertura,
    'ORDEN_REGISTRO': 2
}])

if not tabla_base.empty:
    tabla_final = pd.concat([tabla_base, subtotales, fila_total_general], ignore_index=True)
    tabla_final['DEPARTAMENTO'] = pd.Categorical(
        tabla_final['DEPARTAMENTO'], 
        categories=orden_departamentos + ['TOTAL GENERAL'], 
        ordered=True
    )
    tabla_final = tabla_final.sort_values(by=["DEPARTAMENTO", "ORDEN_REGISTRO", "VENTA"], ascending=[True, True, False])
    tabla_final = tabla_final.drop(columns=['M2', 'ORDEN_REGISTRO', 'Valor'], errors='ignore')
    if 'VENTA_MES_ANT' in tabla_final.columns:
        tabla_final = tabla_final.drop(columns=['VENTA_MES_ANT'])
else:
    columnas_drop = ['M2', 'ORDEN_REGISTRO', 'Valor', 'VENTA_MES_ANT']
    tabla_final = fila_total_general.drop(columns=[c for c in columnas_drop if c in fila_total_general.columns], errors='ignore')

df_para_excel = tabla_final.copy()
df_render_app = tabla_final.copy()
df_render_app['VENTA'] = df_render_app['VENTA'].apply(formatear_moneda)
df_render_app['META'] = df_render_app['META'].apply(formatear_moneda)
df_render_app['AVANCE'] = df_render_app['AVANCE'].apply(formatear_porcentaje)
df_render_app['EFICIENCIA EXHIBICION FRONTAL (VENTA/M2)'] = df_render_app['EFICIENCIA EXHIBICION FRONTAL (VENTA/M2)'].apply(formatear_moneda)
df_render_app['COBERTURA'] = df_render_app['COBERTURA'].apply(formatear_cobertura)

df_render_app = df_render_app.rename(columns={
    'DEPARTAMENTO': 'DEPARTAMENTO',
    'CATEGORIA': 'CATEGORÍA',
    'COBERTURA': 'COBERTURA DE INVENTARIO'
})

def aplicar_colores_matriz(row):
    if row['DEPARTAMENTO'] == 'TOTAL GENERAL':
        return [f'font-weight: bold; background-color: {NAVY_800}; color: #FFFFFF;'] * len(row)
    elif row['CATEGORÍA'] == 'TOTAL DEPARTAMENTO':
        estilos = [f'font-weight: bold; background-color: {COBRE_100}; color: {COBRE_700};'] * len(row)
    else:
        estilos = [f'background-color: #FFFFFF; color: {TEXTO};'] * len(row)
    # Semáforo en la columna AVANCE (verde cumplida, ámbar cerca, rojo por debajo)
    meta_fila = tabla_final.loc[row.name, 'META'] if 'META' in tabla_final.columns else 0
    avance_fila = tabla_final.loc[row.name, 'AVANCE'] if 'AVANCE' in tabla_final.columns else 0
    if pd.notna(meta_fila) and meta_fila > 0 and 'AVANCE' in row.index:
        _, color_av, _ = nivel_avance(avance_fila, meta_fila)
        pos = list(row.index).index('AVANCE')
        estilos[pos] = estilos[pos] + f' color: {color_av}; font-weight: bold;'
    return estilos

tabla_estilizada = (
    df_render_app.style
    .apply(aplicar_colores_matriz, axis=1)
    .set_properties(**{'text-align': 'right', 'font-family': 'Manrope, sans-serif'})
)

total_ventas = total_g_venta
meta_dinamica_total = total_g_meta
avance_general = total_g_avance
eficiencia_total = total_g_eficiencia

def generar_excel_descarga_sumable(dataframe):
    output = io.BytesIO()
    if not dataframe.empty and 'CATEGORIA' in dataframe.columns:
        df_excel = dataframe[dataframe['CATEGORIA'] != 'TOTAL DEPARTAMENTO'].copy()
    else:
        df_excel = dataframe.copy()
        
    if 'AVANCE' in df_excel.columns:
        df_excel['AVANCE'] = df_excel['AVANCE'] / 100.0
    
    if 'COBERTURA' in df_excel.columns:
        df_excel = df_excel.rename(columns={'COBERTURA': 'COBERTURA DE INVENTARIO'})
        
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_excel.to_excel(writer, index=False, sheet_name='Reporte Comercial')
        worksheet = writer.sheets['Reporte Comercial']
        formato_numero_excel = '#,##0.00'
        formato_porcentaje_excel = '0.00%'
        
        for row in range(2, len(df_excel) + 2):
            worksheet[f'C{row}'].number_format = formato_numero_excel
            worksheet[f'D{row}'].number_format = formato_numero_excel
            worksheet[f'E{row}'].number_format = formato_porcentaje_excel
            worksheet[f'F{row}'].number_format = formato_numero_excel
            if 'COBERTURA DE INVENTARIO' in df_excel.columns:
                worksheet[f'G{row}'].number_format = formato_numero_excel
    return output.getvalue()

def generar_pdf_descarga(dataframe, año, ventas, meta, avance, eficiencia):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor(NAVY_800), spaceAfter=8)
    subtitle_style = ParagraphStyle('SubStyle', parent=styles['Normal'], fontSize=9, leading=13, textColor=colors.HexColor(TEXTO_SUAVE), spaceAfter=12)
    header_table_style = ParagraphStyle('HeaderTable', parent=styles['Normal'], fontSize=8, leading=11, fontName='Helvetica-Bold', textColor=colors.white, alignment=1)
    cell_table_style = ParagraphStyle('CellTable', parent=styles['Normal'], fontSize=8, leading=10, alignment=2)
    cell_total_style = ParagraphStyle('CellTotal', parent=styles['Normal'], fontSize=8, leading=10, fontName='Helvetica-Bold', alignment=2, textColor=colors.HexColor(COBRE_700))
    cell_total_general_style = ParagraphStyle('CellTotalGeneral', parent=cell_total_style, textColor=colors.white)
    
    story.append(Paragraph(f"<b>REPORTE EJECUTIVO COMERCIAL - AÑO {año}</b>", title_style))
    story.append(Paragraph(f"Filtros aplicados - Ventas Totales: {ventas} | Meta Dinámica: {meta} | Avance: {avance} | EFICIENCIA EXHIBICION FRONTAL (VENTA/M2): {eficiencia}", subtitle_style))
    story.append(Spacer(1, 8))
    
    data_tabla = [[Paragraph("<b>DEPARTAMENTO</b>", header_table_style), 
                    Paragraph("<b>CATEGORÍA</b>", header_table_style), 
                    Paragraph("<b>VENTA</b>", header_table_style), 
                    Paragraph("<b>META</b>", header_table_style), 
                    Paragraph("<b>AVANCE</b>", header_table_style), 
                    Paragraph("<b>EFICIENCIA EXHIBICION FRONTAL (VENTA/M2)</b>", header_table_style),
                    Paragraph("<b>COBERTURA DE INVENTARIO</b>", header_table_style)]]
    
    estilos_celdas = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(NAVY_800)),
        ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor(COBRE_500)),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor(BORDE)),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]
    
    for i, row in enumerate(dataframe.values):
        idx_fila = i + 1
        es_total_general = (row[0] == 'TOTAL GENERAL')
        es_subtotal = (row[1] == 'TOTAL DEPARTAMENTO')
        
        if es_total_general:
            style_actual = cell_total_general_style
        elif es_subtotal:
            style_actual = cell_total_style
        else:
            style_actual = cell_table_style
        
        data_tabla.append([
            Paragraph(str(row[0]), style_actual),
            Paragraph(str(row[1]), style_actual),
            Paragraph(formatear_moneda(row[2]), style_actual),
            Paragraph(formatear_moneda(row[3]), style_actual),
            Paragraph(formatear_porcentaje(row[4]), style_actual),
            Paragraph(formatear_moneda(row[5]), style_actual),
            Paragraph(formatear_cobertura(row[6]), style_actual)
        ])
        
        if es_total_general:
            estilos_celdas.append(('BACKGROUND', (0, idx_fila), (-1, idx_fila), colors.HexColor(NAVY_800)))
            estilos_celdas.append(('TEXTCOLOR', (0, idx_fila), (-1, idx_fila), colors.white))
        elif es_subtotal:
            estilos_celdas.append(('BACKGROUND', (0, idx_fila), (-1, idx_fila), colors.HexColor(COBRE_100)))
            estilos_celdas.append(('TEXTCOLOR', (0, idx_fila), (-1, idx_fila), colors.HexColor(COBRE_700)))
            
    pdf_table = Table(data_tabla, colWidths=[110, 110, 85, 85, 65, 115, 115])
    pdf_table.setStyle(TableStyle(estilos_celdas))
    story.append(pdf_table)
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# -----------------------------------
# DATOS PARA LA VISTA (ENCABEZADO, KPIs Y GRÁFICOS)
# -----------------------------------
def formatear_numero(valor):
    base = f"{valor:,.2f}"
    return base.translate(str.maketrans({',': '.', '.': ','}))

def rango_meses(seleccion):
    meses_orden = [m for m in orden_meses if m in seleccion]
    if len(meses_orden) == 12:
        return "Enero – Diciembre"
    if len(meses_orden) == 1:
        return meses_orden[0].title()
    indices = [orden_meses.index(m) for m in meses_orden]
    if indices == list(range(indices[0], indices[-1] + 1)):
        return f"{meses_orden[0].title()} – {meses_orden[-1].title()}"
    return f"{len(meses_orden)} meses"

meses_en_orden = [m for m in orden_meses if m in meses_sel]
sucursales_en_orden = [s for s in orden_sucursales if s in sucursal_sel]

if not df_filtrado.empty:
    ventas_mes = df_filtrado.groupby(df_filtrado['MES'].astype(str))['VENTA'].sum()
    ventas_suc = df_filtrado.groupby(df_filtrado['SUCURSAL'].astype(str))['VENTA'].sum()
    ventas_suc_mes = df_filtrado.groupby([df_filtrado['SUCURSAL'].astype(str), df_filtrado['MES'].astype(str)])['VENTA'].sum()
else:
    ventas_mes = pd.Series(dtype=float)
    ventas_suc = pd.Series(dtype=float)
    ventas_suc_mes = pd.Series(dtype=float)
ventas_mes = ventas_mes.reindex(meses_en_orden, fill_value=0.0)

if not metas_suc_mes.empty:
    metas_mes = metas_suc_mes.groupby('MES')['META'].sum()
    metas_suc = metas_suc_mes.groupby('SUCURSAL')['META'].sum()
    metas_suc_mes_idx = metas_suc_mes.groupby(['SUCURSAL', 'MES'])['META'].sum()
else:
    metas_mes = pd.Series(dtype=float)
    metas_suc = pd.Series(dtype=float)
    metas_suc_mes_idx = pd.Series(dtype=float)
metas_mes = metas_mes.reindex(meses_en_orden, fill_value=0.0)

# Comparación justa: solo los meses que ya tienen ventas en el año seleccionado
meses_con_venta = [m for m in meses_en_orden if ventas_mes[m] > 0]
venta_año_anterior = df[(df['AÑO'] == int(año_sel) - 1) & mask_comun & df['MES'].astype(str).isin(meses_con_venta)]['VENTA'].sum()

# --- Encabezado con la conclusión del periodo ---
if meta_dinamica_total > 0:
    diferencia_meta = total_ventas - meta_dinamica_total
    if diferencia_meta >= 0:
        conclusion = f"Llevas el <b style='color:{COBRE_400}'>{formatear_porcentaje(avance_general)}</b> de la meta: superada por {formatear_moneda(diferencia_meta)}."
    else:
        conclusion = f"Llevas el <b style='color:{COBRE_400}'>{formatear_porcentaje(avance_general)}</b> de la meta: faltan {formatear_moneda(-diferencia_meta)} para cumplirla."
else:
    conclusion = "No hay meta cargada para esta selección; se muestran solo las ventas."

hero_slot.markdown(render_hero(conclusion, [
    f"Año <b>{año_sel}</b>",
    f"<b>{rango_meses(meses_sel)}</b>",
]), unsafe_allow_html=True)

# --- KPIs ---
clase_av, color_av, texto_av = nivel_avance(avance_general, meta_dinamica_total)

if venta_año_anterior > 0:
    variacion = (total_ventas / venta_año_anterior - 1) * 100
    clase_var = "ok" if variacion >= 0 else "bajo"
    flecha = "▲" if variacion >= 0 else "▼"
    pie_ventas = f'<span class="cc-pill {clase_var}">{flecha} {formatear_porcentaje(abs(variacion))}</span> vs. mismo periodo {int(año_sel) - 1}'
else:
    pie_ventas = "Periodo y filtros seleccionados"

if meta_dinamica_total > 0:
    if total_ventas >= meta_dinamica_total:
        pie_meta = f'<span class="cc-pill ok">▲ Superada</span> por {formatear_moneda(total_ventas - meta_dinamica_total)}'
    else:
        pie_meta = f'Faltan <b style="color:{NAVY_800}">{formatear_moneda(meta_dinamica_total - total_ventas)}</b>'
else:
    pie_meta = "Sin meta para esta selección"

pie_m2 = f"{formatear_numero(total_g_m2)} m² de exhibición" if total_g_m2 > 0 else "Sin metros cargados"

if mes_inventario:
    pie_cobertura = f"Inventario de {mes_inventario.title()} vs. venta anterior"
else:
    pie_cobertura = "Sin inventario para los meses elegidos"

render_kpis([
    kpi_card(0, "Ventas totales", formatear_moneda(total_ventas), "ventas", pie_ventas, destacado=True),
    kpi_card(1, "Meta fijada", formatear_moneda(meta_dinamica_total), "meta", pie_meta),
    kpi_card(2, "Porcentaje de avance", formatear_porcentaje(avance_general), "avance",
             f'<span class="cc-pill {clase_av}">{texto_av}</span>', barra=(avance_general, color_av)),
    kpi_card(3, "Eficiencia exhibición frontal (venta/m²)", formatear_moneda(eficiencia_total), "m2", pie_m2),
    kpi_card(4, "Cobertura de inventario", formatear_cobertura(total_g_cobertura), "inventario", pie_cobertura,
             valor_pequeno=pd.isna(total_g_cobertura)),
])

# -----------------------------------
# PESTAÑAS DEL REPORTE
# -----------------------------------
# La vista se guarda en la sesión, así que cambiar un filtro de la barra lateral
# devuelve a la misma pestaña en la que estabas.
VISTAS = {
    "Resumen": ":material/insights: Resumen",
    "Sucursales": ":material/storefront: Sucursales",
    "Departamentos": ":material/category: Departamentos",
    "Detalle": ":material/table_chart: Detalle y descargas",
    "Articulos": ":material/inventory_2: Artículos",
}

with st.container(key="cc-nav"):
    vista = st.segmented_control(
        "Vista", options=list(VISTAS.keys()), format_func=lambda v: VISTAS[v],
        default="Resumen", key="cc_vista", label_visibility="collapsed",
    )
if vista is None:
    vista = st.session_state.get("cc_vista_previa", "Resumen")
st.session_state["cc_vista_previa"] = vista

PALETA = [NAVY_800, COBRE_500, NAVY_400, ARENA, "#2A8C82", PIZARRA, NAVY_700, COBRE_400]

# ===== RESUMEN =====
if vista == "Resumen":
    col_a, col_b = st.columns([2, 1], gap="medium")

    with col_a:
        with st.container(key="cc-card-mes"):
            meses_con_meta = [m for m in meses_en_orden if metas_mes[m] > 0]
            meses_cumplidos = [m for m in meses_con_meta if ventas_mes[m] >= metas_mes[m]]
            if meses_con_meta:
                sub = f"<b>{len(meses_cumplidos)} de {len(meses_con_meta)}</b> meses alcanzaron la meta"
            else:
                sub = "Ventas del periodo seleccionado"
            titulo_tarjeta("Venta vs. meta por mes", sub)

            if ventas_mes.sum() > 0 or metas_mes.sum() > 0:
                avance_mes = np.where(metas_mes.values > 0, ventas_mes.values / np.where(metas_mes.values > 0, metas_mes.values, 1) * 100, np.nan)
                etiquetas_mes = [m.title() for m in meses_en_orden]
                fig = go.Figure()
                fig.add_bar(
                    x=etiquetas_mes, y=ventas_mes.values, name="Venta",
                    marker=dict(color=NAVY_800, cornerradius=6),
                    text=[formatear_compacto(v) if v > 0 else "" for v in ventas_mes.values], textposition="inside",
                    insidetextanchor="end", textangle=0, textfont=dict(color="#FFFFFF", size=11),
                    customdata=np.stack([metas_mes.values, avance_mes], axis=-1),
                    hovertemplate="<b>%{x}</b><br>Venta: $ %{y:,.2f}<br>Meta: $ %{customdata[0]:,.2f}<br>Avance: %{customdata[1]:.1f} %<extra></extra>",
                )
                if metas_mes.sum() > 0:
                    fig.add_scatter(
                        x=etiquetas_mes, y=metas_mes.values, name="Meta", mode="lines+markers",
                        line=dict(color=COBRE_500, width=3, shape="spline"),
                        marker=dict(size=9, color="#FFFFFF", line=dict(color=COBRE_500, width=2.5)),
                        hovertemplate="<b>%{x}</b><br>Meta: $ %{y:,.2f}<extra></extra>",
                    )
                fig.update_yaxes(tickprefix="$ ", tickformat="~s")
                mostrar_grafico(estilo_figura(fig, 380), "graf_mes")
            else:
                estado_vacio("No hay ventas ni metas para los filtros seleccionados.")

    with col_b:
        with st.container(key="cc-card-gauge"):
            titulo_tarjeta("Avance de la meta", texto_av)
            tope = max(120.0, float(avance_general) + 10.0)
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=float(avance_general),
                number=dict(suffix=" %", valueformat=",.1f", font=dict(size=40, color=NAVY_800, family="Manrope, sans-serif")),
                gauge=dict(
                    axis=dict(range=[0, tope], ticksuffix=" %", tickcolor=BORDE, tickfont=dict(color=TEXTO_SUAVE, size=11)),
                    bar=dict(color=color_av, thickness=0.32),
                    bgcolor=SUPERFICIE_2, borderwidth=0,
                    steps=[
                        dict(range=[0, 90], color=PELIGRO_BG),
                        dict(range=[90, 100], color=ALERTA_BG),
                        dict(range=[100, tope], color=EXITO_BG),
                    ],
                    threshold=dict(line=dict(color=COBRE_600, width=4), thickness=0.85, value=100),
                ),
            ))
            fig = estilo_figura(fig, 290, leyenda=False)
            fig.update_layout(margin=dict(l=28, r=28, t=36, b=8))
            mostrar_grafico(fig, "graf_gauge")
            st.markdown(html_limpio(f"""
                <div class="cc-legend">
                    <span><i style="background:{PELIGRO_BG}; border:1px solid {PELIGRO}"></i>Menos de 90 %</span>
                    <span><i style="background:{ALERTA_BG}; border:1px solid {ALERTA}"></i>90 – 99 %</span>
                    <span><i style="background:{EXITO_BG}; border:1px solid {EXITO}"></i>100 % o más</span>
                </div>
            """), unsafe_allow_html=True)

    col_c, col_d = st.columns(2, gap="medium")

    with col_c:
        with st.container(key="cc-card-mix"):
            ventas_suc_orden = ventas_suc.reindex(sucursales_en_orden, fill_value=0.0)
            ventas_suc_orden = ventas_suc_orden[ventas_suc_orden > 0]
            if not ventas_suc_orden.empty:
                lider = ventas_suc_orden.idxmax()
                peso_lider = ventas_suc_orden.max() / ventas_suc_orden.sum() * 100
                titulo_tarjeta("Mix de ventas por sucursal", f"<b>{lider.title()}</b> aporta el {formatear_porcentaje(peso_lider)} de la venta")
                fig = go.Figure(go.Pie(
                    labels=[s.title() for s in ventas_suc_orden.index], values=ventas_suc_orden.values,
                    hole=0.62, sort=False, direction="clockwise",
                    marker=dict(colors=PALETA, line=dict(color="#FFFFFF", width=2)),
                    textinfo="percent", textfont=dict(color="#FFFFFF", size=12),
                    hovertemplate="<b>%{label}</b><br>$ %{value:,.2f}<br>%{percent}<extra></extra>",
                ))
                fig.add_annotation(text=f"<b>{formatear_compacto(ventas_suc_orden.sum())}</b><br><span style='font-size:12px;color:{TEXTO_SUAVE}'>venta total</span>",
                                   showarrow=False, font=dict(size=20, color=NAVY_800, family="Manrope, sans-serif"))
                fig = estilo_figura(fig, 340)
                fig.update_layout(legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02))
                mostrar_grafico(fig, "graf_mix")
            else:
                titulo_tarjeta("Mix de ventas por sucursal")
                estado_vacio("No hay ventas registradas para los filtros seleccionados.")

    with col_d:
        with st.container(key="cc-card-top"):
            top_cat = tabla_base[tabla_base['VENTA'] > 0].sort_values('VENTA', ascending=False).head(10) if not tabla_base.empty else pd.DataFrame()
            if not top_cat.empty:
                primera = top_cat.iloc[0]
                titulo_tarjeta("Top 10 categorías por venta", f"<b>{str(primera['CATEGORIA']).title()}</b> lidera con {formatear_compacto(primera['VENTA'])}")
                top_cat = top_cat.iloc[::-1]
                fig = go.Figure(go.Bar(
                    x=top_cat['VENTA'], y=[str(c).title() for c in top_cat['CATEGORIA']], orientation="h",
                    marker=dict(color=[COBRE_500 if i == len(top_cat) - 1 else NAVY_800 for i in range(len(top_cat))], cornerradius=5),
                    text=[formatear_compacto(v) for v in top_cat['VENTA']], textposition="outside",
                    textfont=dict(color=TEXTO_SUAVE, size=11), cliponaxis=False,
                    customdata=np.stack([top_cat['DEPARTAMENTO'].astype(str).str.title(), top_cat['AVANCE']], axis=-1),
                    hovertemplate="<b>%{y}</b><br>%{customdata[0]}<br>Venta: $ %{x:,.2f}<br>Avance: %{customdata[1]:.1f} %<extra></extra>",
                ))
                fig.update_xaxes(tickprefix="$ ", tickformat="~s", showgrid=True, gridcolor=DIVISOR,
                                 range=[0, float(top_cat['VENTA'].max()) * 1.22])
                fig.update_yaxes(showgrid=False)
                mostrar_grafico(estilo_figura(fig, 340, leyenda=False), "graf_top")
            else:
                titulo_tarjeta("Top 10 categorías por venta")
                estado_vacio("No hay ventas registradas para los filtros seleccionados.")

# ===== SUCURSALES =====
if vista == "Sucursales":
    # Solo las sucursales que vendieron en el periodo; las demás aparecen cuando tengan ventas
    sucursales_con_venta = [s for s in sucursales_en_orden if ventas_suc.get(s, 0.0) > 0]

    with st.container(key="cc-card-suc"):
        venta_s = ventas_suc.reindex(sucursales_con_venta, fill_value=0.0)
        meta_s = metas_suc.reindex(sucursales_con_venta, fill_value=0.0)
        avance_s = pd.Series(np.where(meta_s > 0, venta_s / meta_s.where(meta_s > 0, 1) * 100, np.nan), index=sucursales_con_venta)

        if avance_s.notna().any():
            mejor = avance_s.idxmax()
            sub = f"<b>{mejor.title()}</b> tiene el mejor avance: {formatear_porcentaje(avance_s[mejor])}"
        else:
            sub = "Venta de cada sucursal en el periodo"
        titulo_tarjeta("Venta y meta por sucursal", sub)

        if sucursales_con_venta:
            etiquetas_s = [s.title() for s in sucursales_con_venta]
            colores_s = [nivel_avance(a if pd.notna(a) else 0, m)[1] if m > 0 else NAVY_800 for a, m in zip(avance_s, meta_s)]
            fig = go.Figure()
            fig.add_bar(
                x=etiquetas_s, y=venta_s.values, name="Venta",
                marker=dict(color=NAVY_800, cornerradius=6),
                customdata=np.stack([meta_s.values, avance_s.fillna(0).values], axis=-1),
                hovertemplate="<b>%{x}</b><br>Venta: $ %{y:,.2f}<br>Meta: $ %{customdata[0]:,.2f}<br>Avance: %{customdata[1]:.1f} %<extra></extra>",
            )
            if meta_s.sum() > 0:
                fig.add_scatter(
                    x=etiquetas_s, y=meta_s.values, name="Meta", mode="markers",
                    marker=dict(symbol="line-ew", size=46, line=dict(color=COBRE_500, width=4)),
                    hovertemplate="<b>%{x}</b><br>Meta: $ %{y:,.2f}<extra></extra>",
                )
                for etiqueta, v, m, a, c in zip(etiquetas_s, venta_s.values, meta_s.values, avance_s.values, colores_s):
                    if m > 0:
                        fig.add_annotation(x=etiqueta, y=max(v, m), text=f"<b>{formatear_porcentaje(a)}</b>", showarrow=False,
                                           yshift=16, font=dict(color=c, size=12))
            fig.update_yaxes(tickprefix="$ ", tickformat="~s")
            mostrar_grafico(estilo_figura(fig, 400), "graf_suc")
        else:
            estado_vacio("Ninguna de las sucursales seleccionadas tiene ventas en este periodo.")

    with st.container(key="cc-card-calor"):
        titulo_tarjeta("Mapa de calor: avance por sucursal y mes", "Rojo: por debajo de la meta · Verde: meta superada. Pasa el cursor para ver venta y meta.")
        if not sucursales_con_venta:
            estado_vacio("Ninguna de las sucursales seleccionadas tiene ventas en este periodo.")
        elif not metas_suc_mes_idx.empty and metas_suc_mes_idx.sum() > 0:
            z, texto, datos = [], [], []
            for s in sucursales_con_venta:
                fila_z, fila_t, fila_d = [], [], []
                for m in meses_en_orden:
                    v = float(ventas_suc_mes.get((s, m), 0.0))
                    mt = float(metas_suc_mes_idx.get((s, m), 0.0))
                    if mt > 1 and m in meses_con_venta:
                        a = v / mt * 100
                        fila_z.append(a)
                        fila_t.append(f"{a:.0f}%")
                    else:
                        a = np.nan
                        fila_z.append(None)
                        fila_t.append("—")
                    fila_d.append([v, mt])
                z.append(fila_z)
                texto.append(fila_t)
                datos.append(fila_d)
            fig = go.Figure(go.Heatmap(
                z=z, x=[m.title()[:3] for m in meses_en_orden], y=[s.title() for s in sucursales_con_venta],
                text=texto, texttemplate="%{text}", textfont=dict(size=12, color=TEXTO),
                customdata=datos, xgap=3, ygap=3,
                colorscale=[[0, "#E0574A"], [0.35, "#F2B8B0"], [0.5, "#FBF3D9"], [0.65, "#BFE5CF"], [1, "#2E9B67"]],
                zmin=60, zmax=140,
                colorbar=dict(title=dict(text="Avance", side="top"), ticksuffix=" %", thickness=12, outlinewidth=0, len=0.9),
                hovertemplate="<b>%{y} · %{x}</b><br>Venta: $ %{customdata[0]:,.2f}<br>Meta: $ %{customdata[1]:,.2f}<br>Avance: %{z:.1f} %<extra></extra>",
            ))
            fig.update_yaxes(autorange="reversed", showgrid=False)
            mostrar_grafico(estilo_figura(fig, max(260, 46 * len(sucursales_con_venta) + 80), leyenda=False), "graf_calor")
        else:
            estado_vacio("No hay metas mensuales cargadas para las sucursales seleccionadas.")

# ===== DEPARTAMENTOS =====
if vista == "Departamentos":
    col_e, col_f = st.columns([1, 1], gap="medium")

    with col_e:
        with st.container(key="cc-card-dep"):
            dep = subtotales[subtotales['META'] > 0].copy() if not subtotales.empty else pd.DataFrame()
            if not dep.empty:
                dep = dep.sort_values('AVANCE')
                cumplen = int((dep['AVANCE'] >= 100).sum())
                titulo_tarjeta("Avance por departamento", f"<b>{cumplen} de {len(dep)}</b> departamentos cumplen la meta")
                colores_d = [nivel_avance(a, m)[1] for a, m in zip(dep['AVANCE'], dep['META'])]
                fig = go.Figure(go.Bar(
                    x=dep['AVANCE'], y=dep['DEPARTAMENTO'].astype(str).str.title(), orientation="h",
                    marker=dict(color=colores_d, cornerradius=5),
                    text=[formatear_porcentaje(a) for a in dep['AVANCE']], textposition="outside",
                    textfont=dict(color=TEXTO_SUAVE, size=11), cliponaxis=False,
                    customdata=np.stack([dep['VENTA'], dep['META']], axis=-1),
                    hovertemplate="<b>%{y}</b><br>Venta: $ %{customdata[0]:,.2f}<br>Meta: $ %{customdata[1]:,.2f}<br>Avance: %{x:.1f} %<extra></extra>",
                ))
                fig.add_vline(x=100, line=dict(color=COBRE_600, width=2, dash="dash"),
                              annotation_text="Meta 100 %", annotation_position="top", annotation_font=dict(color=COBRE_700, size=11))
                fig.update_xaxes(ticksuffix=" %", showgrid=True, gridcolor=DIVISOR)
                fig.update_yaxes(showgrid=False)
                mostrar_grafico(estilo_figura(fig, max(320, 30 * len(dep) + 90), leyenda=False), "graf_dep")
            else:
                titulo_tarjeta("Avance por departamento")
                estado_vacio("No hay metas cargadas para los departamentos seleccionados.")

    with col_f:
        with st.container(key="cc-card-tree"):
            titulo_tarjeta("Dónde se concentra la venta", "Haz clic en un departamento para ver sus categorías. El color indica el avance.")
            arbol = tabla_base[tabla_base['VENTA'] > 0].copy() if not tabla_base.empty else pd.DataFrame()
            if not arbol.empty:
                colores_nivel = {"ok": "#BFE5CF", "medio": "#F4E4AE", "bajo": "#F2B8B0", "neutro": NAVY_100}
                ids, etiquetas, padres, valores, colores_t, datos_t, texto_t = [], [], [], [], [], [], []
                for depto, grupo in arbol.groupby(arbol['DEPARTAMENTO'].astype(str), sort=False):
                    v_dep = grupo['VENTA'].sum()
                    m_dep = grupo['META'].sum()
                    a_dep = v_dep / m_dep * 100 if m_dep > 0 else 0.0
                    ids.append(depto); etiquetas.append(depto.title()); padres.append("")
                    valores.append(v_dep); colores_t.append(NAVY_800); datos_t.append([m_dep, a_dep]); texto_t.append("#FFFFFF")
                    for _, fila in grupo.iterrows():
                        clase_n, _, _ = nivel_avance(fila['AVANCE'], fila['META'])
                        ids.append(f"{depto}/{fila['CATEGORIA']}"); etiquetas.append(str(fila['CATEGORIA']).title()); padres.append(depto)
                        valores.append(fila['VENTA']); colores_t.append(colores_nivel[clase_n]); datos_t.append([fila['META'], fila['AVANCE']]); texto_t.append(TEXTO)
                fig = go.Figure(go.Treemap(
                    ids=ids, labels=etiquetas, parents=padres, values=valores, branchvalues="total",
                    marker=dict(colors=colores_t, line=dict(color="#FFFFFF", width=2), cornerradius=4),
                    customdata=datos_t, maxdepth=2,
                    texttemplate="<b>%{label}</b><br>$ %{value:,.0f}",
                    textfont=dict(family="Manrope, sans-serif", size=12, color=texto_t),
                    pathbar=dict(visible=True, thickness=24, textfont=dict(color="#FFFFFF")),
                    hovertemplate="<b>%{label}</b><br>Venta: $ %{value:,.2f}<br>Meta: $ %{customdata[0]:,.2f}<br>Avance: %{customdata[1]:.1f} %<br>%{percentRoot:.1%} del total<extra></extra>",
                ))
                mostrar_grafico(estilo_figura(fig, 470, leyenda=False), "graf_tree")
            else:
                estado_vacio("No hay ventas registradas para los departamentos seleccionados.")

# ===== DETALLE Y DESCARGAS =====
if vista == "Detalle":
    st.markdown(html_limpio(f"""
        <div class="cc-legend">
            <span><i style="background:{COBRE_100}; border:1px solid {COBRE_200}"></i>Total por departamento</span>
            <span><i style="background:{NAVY_800}"></i>Total general</span>
            <span><b style="color:{EXITO}">Avance</b>&nbsp;meta cumplida</span>
            <span><b style="color:{ALERTA}">Avance</b>&nbsp;90 – 99 %</span>
            <span><b style="color:{PELIGRO}">Avance</b>&nbsp;menos de 90 %</span>
        </div>
    """), unsafe_allow_html=True)

    st.dataframe(tabla_estilizada, width="stretch", height=530, hide_index=True)

    st.markdown(html_limpio("""
        <div class="cc-section"><span class="cc-tri"></span><h3>Descarga de reportes</h3></div>
        <div class="cc-note">El informe de Excel se descarga libre de filas de subtotales y con codificación contable nativa de miles/decimales, permitiéndote realizar operaciones matemáticas al instante.</div>
    """), unsafe_allow_html=True)

    bot1, bot2 = st.columns(2)

    data_excel = generar_excel_descarga_sumable(df_para_excel)
    bot1.download_button(
        label="Descargar Reporte en Excel (Sumable)",
        data=data_excel,
        file_name=f"Reporte_Comercial_{año_sel}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        icon=":material/table_view:",
        type="primary",
        width="stretch"
    )

    data_pdf = generar_pdf_descarga(
        tabla_final,
        año_sel,
        formatear_moneda(total_ventas),
        formatear_moneda(meta_dinamica_total),
        formatear_porcentaje(avance_general),
        formatear_moneda(eficiencia_total)
    )
    bot2.download_button(
        label="Descargar Reporte Completo en PDF",
        data=data_pdf,
        file_name=f"Reporte_Comercial_{año_sel}.pdf",
        mime="application/pdf",
        icon=":material/picture_as_pdf:",
        width="stretch"
    )


# ===== ARTÍCULOS =====
if vista == "Articulos":
    COLS_ART = {'ARTICULO', 'UNIDADES', 'UNIDAD_MEDIDA', 'CATEGORIA'}

    def abreviar(texto, largo=46):
        texto = str(texto).title()
        return texto if len(texto) <= largo else texto[:largo - 1].rstrip() + "…"

    def formatear_entero(valor):
        if pd.isna(valor):
            return "—"
        return f"{valor:,.0f}".replace(",", ".")

    def formatear_metros(valor):
        if pd.isna(valor) or valor == 0:
            return "—"
        return formatear_numero(valor) + " m²"

    def resumen_articulos(datos, llaves=('ARTICULO',)):
        """Agrupa ventas y unidades, separando lo que se vende por m² de lo que se vende por pieza."""
        if datos.empty:
            return pd.DataFrame(columns=list(llaves) + ['VENTA', 'UNIDADES', 'M2', 'PEDIDOS', 'SIN_UNIDAD', 'ESTIMADAS', 'RENGLONES'])
        aux = datos.assign(
            _UND=np.where(datos['UNIDAD_MEDIDA'].eq('unid'), datos['UNIDADES'], np.nan),
            _M2=np.where(datos['UNIDAD_MEDIDA'].eq('m²'), datos['UNIDADES'], np.nan),
            _SIN=datos['UNIDADES'].isna().astype(int),
            _EST=datos['CANT_ESTIMADA'].fillna(False).astype(int),
        )
        agregados = {
            'VENTA': ('VENTA', 'sum'),
            'UNIDADES': ('_UND', 'sum'),
            'M2': ('_M2', 'sum'),
            'SIN_UNIDAD': ('_SIN', 'sum'),
            'ESTIMADAS': ('_EST', 'sum'),
            'RENGLONES': ('VENTA', 'size'),
        }
        if 'NumeroPedido' in aux.columns:
            agregados['PEDIDOS'] = ('NumeroPedido', 'nunique')
        tabla = aux.groupby(list(llaves), observed=True).agg(**agregados).reset_index()
        if 'PEDIDOS' not in tabla.columns:
            tabla['PEDIDOS'] = 0
        return tabla.sort_values('VENTA', ascending=False)

    def tabla_presentable(tabla, mostrar_categoria=False):
        """Arma la tabla visible, con la columna de m² solo si hace falta."""
        total = tabla['VENTA'].sum()
        salida = pd.DataFrame()
        salida['ARTÍCULO'] = tabla['ARTICULO'].astype(str).str.title()
        if 'AREA' in tabla.columns:
            salida['ÁREA'] = tabla['AREA'].astype(str).str.title()
        if mostrar_categoria and 'CATEGORIA' in tabla.columns:
            salida['CATEGORÍA'] = tabla['CATEGORIA'].astype(str).str.title()
        unidades = tabla['UNIDADES'].where(tabla['UNIDADES'] > 0)
        salida['UNIDADES'] = [formatear_entero(u) for u in unidades]
        if (tabla['M2'].fillna(0) > 0).any():
            salida['M² VENDIDOS'] = tabla['M2'].apply(formatear_metros)
        salida['VENTA'] = tabla['VENTA'].apply(formatear_moneda)
        salida['% DEL TOTAL'] = [
            formatear_porcentaje(v / total * 100 if total > 0 else 0.0) for v in tabla['VENTA']
        ]
        salida['PEDIDOS'] = tabla['PEDIDOS'].apply(formatear_entero)
        return salida

    def excel_articulos(tabla, mostrar_categoria=False):
        """Mismas columnas que la pantalla, pero con los números como números."""
        salida = io.BytesIO()
        total = tabla['VENTA'].sum()
        export = pd.DataFrame()
        export['ARTÍCULO'] = tabla['ARTICULO'].astype(str).str.title()
        if 'AREA' in tabla.columns:
            export['ÁREA'] = tabla['AREA'].astype(str).str.title()
        if mostrar_categoria and 'CATEGORIA' in tabla.columns:
            export['CATEGORÍA'] = tabla['CATEGORIA'].astype(str).str.title()
        # Lo que se vende por m² deja la celda de unidades vacía en vez de poner 0.
        export['UNIDADES'] = tabla['UNIDADES'].where(tabla['UNIDADES'].fillna(0) != 0).round(0).astype('Int64')
        if (tabla['M2'].fillna(0) > 0).any():
            export['M² VENDIDOS'] = tabla['M2'].fillna(0).round(2)
        export['VENTA'] = tabla['VENTA'].round(2)
        export['% DEL TOTAL'] = (tabla['VENTA'] / total if total else 0.0).round(6)
        export['PEDIDOS'] = tabla['PEDIDOS'].fillna(0).astype(int)

        with pd.ExcelWriter(salida, engine='openpyxl') as writer:
            export.to_excel(writer, index=False, sheet_name='Articulos')
            hoja = writer.sheets['Articulos']
            letras = {c: chr(ord('A') + i) for i, c in enumerate(export.columns)}
            anchos = {'ARTÍCULO': 52, 'ÁREA': 30, 'CATEGORÍA': 30, 'UNIDADES': 12,
                      'M² VENDIDOS': 14, 'VENTA': 16, '% DEL TOTAL': 13, 'PEDIDOS': 11}
            for col, letra in letras.items():
                hoja.column_dimensions[letra].width = anchos.get(col, 14)
                formato = {'UNIDADES': '#,##0', 'PEDIDOS': '#,##0', '% DEL TOTAL': '0.00%'}.get(col, '#,##0.00')
                if col in ('ARTÍCULO', 'ÁREA', 'CATEGORÍA'):
                    continue
                for fila in range(2, len(export) + 2):
                    hoja[f'{letra}{fila}'].number_format = formato
        return salida.getvalue()

    if not COLS_ART.issubset(df_filtrado.columns) or df_filtrado.empty:
        estado_vacio("No hay detalle de artículos para los filtros seleccionados.")
    else:
        # Se incluyen las notas de crédito (montos negativos) para que el total de esta
        # sección cuadre exactamente con el KPI de Ventas Totales.
        base_art = df_filtrado[df_filtrado['VENTA'].notna()].copy()

        if base_art.empty:
            estado_vacio("No hay artículos con venta en el periodo seleccionado.")
        else:
            resumen_total = resumen_articulos(base_art)
            resumen_total = resumen_total[resumen_total['VENTA'] != 0]
            venta_art = resumen_total['VENTA'].sum()
            total_unidades = resumen_total['UNIDADES'].sum()
            total_m2 = resumen_total['M2'].sum()
            lider = resumen_total.iloc[0]

            # ---------- KPIs ----------
            tarjetas = [
                kpi_card(0, "ARTÍCULOS DISTINTOS", formatear_entero(len(resumen_total)), "inventario",
                         f"En {rango_meses(meses_sel)} de {año_sel}"),
                kpi_card(1, "UNIDADES VENDIDAS", formatear_entero(total_unidades), "ventas",
                         "Piezas, perfiles y kits (sin servicios)"),
                kpi_card(2, "M² VENDIDOS", formatear_metros(total_m2), "m2",
                         "Vidrio, espejos y láminas"),
                kpi_card(3, "ARTÍCULO LÍDER", abreviar(lider['ARTICULO'], 30), "avance",
                         f"<b>{formatear_moneda(lider['VENTA'])}</b> en ventas", valor_pequeno=True),
            ]
            render_kpis(tarjetas)

            # ---------- Vista 1: top del periodo ----------
            col_g, col_t = st.columns([1, 1], gap="medium")

            with col_g:
                with st.container(key="cc-card-art-top"):
                    cuantos = st.selectbox("Cuántos mostrar", [10, 15, 20, 30], index=1,
                                           key="art_top_n", label_visibility="collapsed")
                    top = resumen_total.head(int(cuantos)).iloc[::-1]
                    peso = top['VENTA'].sum() / venta_art * 100 if venta_art > 0 else 0.0
                    titulo_tarjeta(
                        f"Top {int(cuantos)} artículos del periodo",
                        f"Concentran <b>{formatear_porcentaje(peso)}</b> de la venta filtrada",
                    )
                    etiquetas = [
                        (formatear_entero(u) + " unid") if u and u > 0 else
                        (formatear_metros(m) if m and m > 0 else "—")
                        for u, m in zip(top['UNIDADES'], top['M2'])
                    ]
                    fig = go.Figure(go.Bar(
                        x=top['VENTA'], y=[abreviar(a, 40) for a in top['ARTICULO']], orientation="h",
                        marker=dict(color=NAVY_800, cornerradius=5),
                        text=[formatear_moneda(v) for v in top['VENTA']], textposition="outside",
                        textfont=dict(color=TEXTO_SUAVE, size=11), cliponaxis=False,
                        customdata=np.stack([etiquetas, top['PEDIDOS']], axis=-1),
                        hovertemplate="<b>%{y}</b><br>Venta: $ %{x:,.2f}<br>Cantidad: %{customdata[0]}<br>Pedidos: %{customdata[1]}<extra></extra>",
                    ))
                    fig.update_xaxes(showgrid=True, gridcolor=DIVISOR, tickprefix="$ ")
                    fig.update_yaxes(showgrid=False)
                    mostrar_grafico(estilo_figura(fig, max(320, 26 * len(top) + 110), leyenda=False), "graf_art_top")

            with col_t:
                with st.container(key="cc-card-art-cat"):
                    agrupar_por = st.segmented_control(
                        "Agrupar por", options=["Área", "Categoría"], default="Área",
                        key="art_agrupar", label_visibility="collapsed",
                    ) or "Área"
                    llave_graf = 'AREA' if agrupar_por == "Área" else 'CATEGORIA'
                    nombre_graf = "áreas" if agrupar_por == "Área" else "categorías"
                    todos_graf = resumen_articulos(base_art, llaves=(llave_graf,))
                    todos_graf = todos_graf[todos_graf['VENTA'] != 0]
                    por_cat = todos_graf.head(12)
                    titulo_tarjeta(
                        f"Venta por {agrupar_por.lower()}",
                        f"<b>{len(todos_graf)}</b> {nombre_graf} con venta en el periodo",
                    )
                    if por_cat.empty:
                        estado_vacio(f"No hay {nombre_graf} con venta en el periodo.")
                    else:
                        orden_cat = por_cat.iloc[::-1]
                        cantidades = [
                            " · ".join(p for p in (
                                (formatear_entero(u) + " unid") if u and u > 0 else "",
                                formatear_metros(m) if m and m > 0 else "",
                            ) if p) or "—"
                            for u, m in zip(orden_cat['UNIDADES'], orden_cat['M2'])
                        ]
                        fig = go.Figure(go.Bar(
                            x=orden_cat['VENTA'], y=[abreviar(c, 34) for c in orden_cat[llave_graf]],
                            orientation="h", marker=dict(color=COBRE_500, cornerradius=5),
                            text=[formatear_moneda(v) for v in orden_cat['VENTA']], textposition="outside",
                            textfont=dict(color=TEXTO_SUAVE, size=11), cliponaxis=False,
                            customdata=cantidades,
                            hovertemplate="<b>%{y}</b><br>Venta: $ %{x:,.2f}<br>Cantidad: %{customdata}<extra></extra>",
                        ))
                        fig.update_xaxes(showgrid=True, gridcolor=DIVISOR, tickprefix="$ ")
                        fig.update_yaxes(showgrid=False)
                        mostrar_grafico(estilo_figura(fig, max(320, 26 * len(orden_cat) + 110), leyenda=False), "graf_art_cat")

            # ---------- Vista 2: artículos dentro de un área y una categoría ----------
            with st.container(key="cc-card-art-detalle"):
                titulo_tarjeta(
                    "Artículos vendidos por área y categoría",
                    "Elige un área y, si quieres, una categoría dentro de ella",
                )
                if 'AREA' not in base_art.columns:
                    base_art['AREA'] = SIN_AREA
                TODAS_AREAS, TODAS_CATS = "TODAS LAS ÁREAS", "TODAS LAS CATEGORÍAS"
                areas_venta = resumen_articulos(base_art, llaves=('AREA',))
                opciones_area = [TODAS_AREAS] + [str(a) for a in areas_venta['AREA']]
                col_area, col_sel, col_bus = st.columns([1, 1, 1], gap="medium")
                with col_area:
                    area_sel = st.selectbox("Área", opciones_area, key="art_area")
                base_area = base_art if area_sel == TODAS_AREAS else \
                    base_art[base_art['AREA'].astype(str) == area_sel]

                cats = resumen_articulos(base_area, llaves=('CATEGORIA',))
                opciones = [TODAS_CATS] + [str(c) for c in cats['CATEGORIA']]
                # Si la categoría elegida antes no existe en el área nueva, vuelve a "todas".
                if st.session_state.get("art_categoria") not in opciones:
                    st.session_state["art_categoria"] = TODAS_CATS
                with col_sel:
                    cat_sel = st.selectbox("Categoría", opciones, key="art_categoria")
                with col_bus:
                    busqueda = st.text_input("Buscar artículo", key="art_busqueda",
                                             placeholder="Ej: angulo, vidrio, cerradura...")

                detalle_base = base_area if cat_sel == TODAS_CATS else \
                    base_area[base_area['CATEGORIA'].astype(str) == cat_sel]

                llaves = ('ARTICULO', 'AREA', 'CATEGORIA') if cat_sel == TODAS_CATS else ('ARTICULO', 'AREA')
                detalle = resumen_articulos(detalle_base, llaves=llaves)
                detalle = detalle[detalle['VENTA'] != 0]

                if busqueda.strip():
                    patron = normalizar_texto(busqueda)
                    detalle = detalle[detalle['ARTICULO'].astype(str).str.contains(patron, case=False, na=False, regex=False)]

                if detalle.empty:
                    estado_vacio("Ningún artículo coincide con la búsqueda en esta área o categoría.")
                else:
                    resumen_linea = (
                        f"<b>{formatear_entero(len(detalle))}</b> artículos · "
                        f"<b>{formatear_moneda(detalle['VENTA'].sum())}</b> en ventas"
                    )
                    st.markdown(html_limpio(f'<p class="cc-card-sub">{resumen_linea}</p>'), unsafe_allow_html=True)
                    st.dataframe(
                        tabla_presentable(detalle, mostrar_categoria=(cat_sel == "TODAS LAS CATEGORÍAS")),
                        width="stretch", height=460, hide_index=True,
                    )

                    st.download_button(
                        label="Descargar artículos en Excel",
                        data=excel_articulos(detalle, mostrar_categoria=(cat_sel == "TODAS LAS CATEGORÍAS")),
                        file_name=f"Articulos_{año_sel}_{(cat_sel if cat_sel != TODAS_CATS else area_sel).replace(' ', '_')[:30]}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        width="stretch",
                        icon=":material/download:",
                        key="descarga_articulos",
                    )
