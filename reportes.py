"""
Reporte completo del Dashboard Comercial.

Arma, con los mismos números que se ven en pantalla, dos descargas:
  - generar_pdf_completo(datos, secciones): un PDF con todas las vistas (gráficas + tablas)
    y, debajo de cada gráfica, la tabla con los números que la forman (pensado para que
    la IA lea los valores exactos y no tenga que interpretar las barras).
  - generar_excel_completo(datos): un Excel con una hoja por tabla.

`datos` es un diccionario que arma app.py (ver construir_datos_reporte en app.py).
Este archivo no usa Streamlit, así que se puede ejecutar en segundo plano.
"""
import io
import os
import threading

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Patch

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (CondPageBreak, Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

# -----------------------------------
# PALETA (la misma del dashboard)
# -----------------------------------
NAVY_900 = "#052136"
NAVY_800 = "#072C47"
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
PALETA = [NAVY_800, COBRE_500, NAVY_400, ARENA, "#2A8C82", PIZARRA, "#0E3E61", COBRE_400]

SECCIONES = {
    "resumen": "Resumen",
    "sucursales": "Sucursales",
    "departamentos": "Departamentos",
    "articulos": "Artículos",
    "areas": "Áreas",
    "vendedores": "Vendedores",
}

# -----------------------------------
# FORMATOS (iguales a los de la pantalla)
# -----------------------------------
_CAMBIO = str.maketrans({",": ".", ".": ","})


def moneda(v):
    if v is None or pd.isna(v):
        return "$ 0,00"
    return "$ " + f"{float(v):,.2f}".translate(_CAMBIO)


def porcentaje(v):
    if v is None or pd.isna(v):
        return "—"
    return f"{float(v):,.2f}".translate(_CAMBIO) + " %"


def entero(v):
    if v is None or pd.isna(v) or float(v) == 0:
        return "—"
    return f"{float(v):,.0f}".replace(",", ".")


def numero(v, dec=2):
    if v is None or pd.isna(v):
        return "—"
    return f"{float(v):,.{dec}f}".translate(_CAMBIO)


def metros(v):
    if v is None or pd.isna(v) or float(v) == 0:
        return "—"
    return numero(v) + " m²"


def compacto(v):
    if v is None or pd.isna(v):
        return "$ 0"
    a = abs(float(v))
    if a >= 1_000_000:
        return "$ " + f"{v / 1_000_000:,.2f}".translate(_CAMBIO) + " M"
    if a >= 1_000:
        return "$ " + f"{v / 1_000:,.1f}".translate(_CAMBIO) + " K"
    return "$ " + f"{v:,.0f}".translate(_CAMBIO)


def titulo(texto):
    return str(texto).title()


def color_avance(avance, meta):
    if meta is None or pd.isna(meta) or meta <= 0:
        return NAVY_600
    if avance >= 100:
        return EXITO
    if avance >= 90:
        return ALERTA
    return PELIGRO


# -----------------------------------
# FUENTES (DejaVu viene con matplotlib: tiene tildes, ñ, ², —)
# -----------------------------------
_FUENTES_LISTAS = False


def _registrar_fuentes():
    global _FUENTES_LISTAS
    if _FUENTES_LISTAS:
        return
    carpeta = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")
    pdfmetrics.registerFont(TTFont("Texto", os.path.join(carpeta, "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("Texto-Negrita", os.path.join(carpeta, "DejaVuSans-Bold.ttf")))
    pdfmetrics.registerFontFamily("Texto", normal="Texto", bold="Texto-Negrita")
    _FUENTES_LISTAS = True


plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.edgecolor": BORDE,
    "axes.labelcolor": TEXTO_SUAVE,
    "xtick.color": TEXTO_SUAVE,
    "ytick.color": TEXTO_SUAVE,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": False,
})

ANCHO_UTIL = 9.8 * inch  # carta horizontal con márgenes de 0,5" (el marco deja 6 pt por lado)
ALTO_MAX_IMAGEN = 6.6 * inch


# -----------------------------------
# ESTILOS DEL PDF
# -----------------------------------
def _estilos():
    _registrar_fuentes()
    return {
        "portada_titulo": ParagraphStyle("pt", fontName="Texto-Negrita", fontSize=26, leading=30, textColor=colors.white),
        "portada_sub": ParagraphStyle("ps", fontName="Texto", fontSize=11, leading=15, textColor=colors.HexColor(COBRE_200)),
        "seccion": ParagraphStyle("se", fontName="Texto-Negrita", fontSize=15, leading=19, textColor=colors.white),
        "h2": ParagraphStyle("h2", fontName="Texto-Negrita", fontSize=11.5, leading=15, textColor=colors.HexColor(NAVY_800),
                             spaceBefore=8, spaceAfter=2),
        "sub": ParagraphStyle("sb", fontName="Texto", fontSize=8.5, leading=11.5, textColor=colors.HexColor(TEXTO_SUAVE), spaceAfter=4),
        "nota": ParagraphStyle("no", fontName="Texto", fontSize=8, leading=11, textColor=colors.HexColor(TEXTO_SUAVE)),
        "datos": ParagraphStyle("da", fontName="Texto-Negrita", fontSize=7.5, leading=10, textColor=colors.HexColor(COBRE_600),
                                spaceBefore=4, spaceAfter=2),
        "celda": ParagraphStyle("ce", fontName="Texto", fontSize=7.2, leading=9, textColor=colors.HexColor(TEXTO)),
        "celda_der": ParagraphStyle("cd", fontName="Texto", fontSize=7.2, leading=9, textColor=colors.HexColor(TEXTO), alignment=TA_RIGHT),
        "cab": ParagraphStyle("ca", fontName="Texto-Negrita", fontSize=7.2, leading=9, textColor=colors.white),
        "cab_der": ParagraphStyle("cad", fontName="Texto-Negrita", fontSize=7.2, leading=9, textColor=colors.white, alignment=TA_RIGHT),
        "kpi_label": ParagraphStyle("kl", fontName="Texto-Negrita", fontSize=7, leading=9, textColor=colors.HexColor(TEXTO_SUAVE)),
        "kpi_valor": ParagraphStyle("kv", fontName="Texto-Negrita", fontSize=15, leading=19, textColor=colors.HexColor(NAVY_800)),
        "kpi_pie": ParagraphStyle("kp", fontName="Texto", fontSize=7, leading=9.5, textColor=colors.HexColor(TEXTO_SUAVE)),
    }


def _banda_seccion(texto, est):
    t = Table([[Paragraph(texto, est["seccion"])]], colWidths=[ANCHO_UTIL])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(NAVY_800)),
        ("LINEBELOW", (0, 0), (-1, -1), 2.5, colors.HexColor(COBRE_500)),
        ("LEFTPADDING", (0, 0), (-1, -1), 12), ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def _imagen(fig, ancho=ANCHO_UTIL, alto_in=None):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    w, h = fig.get_size_inches()
    alto = alto_in * inch if alto_in else ancho * h / w
    if alto > ALTO_MAX_IMAGEN:  # gráficas muy altas (muchos vendedores): se reducen sin deformarse
        ancho, alto = ancho * ALTO_MAX_IMAGEN / alto, ALTO_MAX_IMAGEN
    return Image(buf, width=ancho, height=alto)


def _tabla(df, est, anchos=None, derecha=None, filas_total=None, filas_subtotal=None, colores_celda=None, repetir=True):
    """
    Tabla con cabecera azul. `derecha`: columnas alineadas a la derecha.
    `filas_total` / `filas_subtotal`: índices (posición) a resaltar.
    `colores_celda`: lista de (fila, col, color_texto) para el semáforo.
    Los estilos se deciden al crear cada celda (reportlab no los cambia después).
    """
    if df is None or df.empty:
        return Paragraph("Sin datos para los filtros seleccionados.", est["nota"])
    derecha = set(derecha or [])
    filas_total, filas_subtotal = set(filas_total or []), set(filas_subtotal or [])
    color_de = {(f, c): col for f, c, col in (colores_celda or [])}
    cache = {}

    def estilo(base, negrita=False, color=None):
        clave = (base.name, negrita, color)
        if clave not in cache:
            cache[clave] = ParagraphStyle(f"{base.name}-{negrita}-{color}", parent=base,
                                          fontName="Texto-Negrita" if negrita else base.fontName,
                                          textColor=colors.HexColor(color) if color else base.textColor)
        return cache[clave]

    cab = [Paragraph(str(c), est["cab_der"] if c in derecha else est["cab"]) for c in df.columns]
    filas = [cab]
    for i, (_, r) in enumerate(df.iterrows()):
        fila = []
        for j, (c, v) in enumerate(zip(df.columns, r)):
            base = est["celda_der"] if c in derecha else est["celda"]
            if i in filas_total:
                st_c = estilo(base, True, "#FFFFFF")
            elif i in filas_subtotal:
                st_c = estilo(base, True, COBRE_700)
            elif (i, j) in color_de:
                st_c = estilo(base, True, color_de[(i, j)])
            else:
                st_c = base
            fila.append(Paragraph(str(v), st_c))
        filas.append(fila)
    if anchos is None:
        anchos = [ANCHO_UTIL / len(df.columns)] * len(df.columns)
    elif sum(anchos) > ANCHO_UTIL:  # se ajusta al ancho de la página
        anchos = [a * ANCHO_UTIL / sum(anchos) for a in anchos]
    t = Table(filas, colWidths=anchos, repeatRows=1 if repetir else 0)
    estilo_t = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(NAVY_800)),
        ("LINEBELOW", (0, 0), (-1, 0), 1.5, colors.HexColor(COBRE_500)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, colors.HexColor(DIVISOR)),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]
    for i in range(1, len(filas)):
        if i % 2 == 0:
            estilo_t.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#FBFAF8")))
    for i in filas_subtotal:
        estilo_t.append(("BACKGROUND", (0, i + 1), (-1, i + 1), colors.HexColor(COBRE_100)))
    for i in filas_total:
        estilo_t.append(("BACKGROUND", (0, i + 1), (-1, i + 1), colors.HexColor(NAVY_800)))
    t.setStyle(TableStyle(estilo_t))
    return t


def _agrupar_datos(historia):
    """
    La etiqueta «Datos de la gráfica» nunca queda sola al final de una página: si la tabla que
    la sigue es corta, van juntas; si es larga, la etiqueta se pega a las primeras filas.
    """
    salida, i = [], 0
    while i < len(historia):
        el = historia[i]
        siguiente = historia[i + 1] if i + 1 < len(historia) else None
        if isinstance(el, Paragraph) and el.style.name == "da" and isinstance(siguiente, Table):
            if getattr(siguiente, "_nrows", 99) <= 30:
                salida.append(KeepTogether([el, siguiente]))
            else:
                salida += [CondPageBreak(1.6 * inch), el, siguiente]
            i += 2
            continue
        if isinstance(el, Paragraph) and el.style.name in ("h2",):
            salida.append(CondPageBreak(1.4 * inch))
        salida.append(el)
        i += 1
    return salida


def _colores_avance(df, col_avance, col_meta, excluir=None):
    """Lista (fila, col, color) para el semáforo de la columna AVANCE."""
    excluir = set(excluir or [])
    idx_col = list(df.columns).index(col_avance)
    salida = []
    for i, (a, m) in enumerate(zip(df["_AV"], df["_MT"])):
        if i in excluir or pd.isna(m) or m <= 0:
            continue
        salida.append((i, idx_col, color_avance(a, m)))
    return salida


# -----------------------------------
# GRÁFICAS (matplotlib, con la misma lógica de colores del dashboard)
# -----------------------------------
def _ejes_moneda(ax, eje="y"):
    f = matplotlib.ticker.FuncFormatter(lambda v, _: compacto(v))
    (ax.yaxis if eje == "y" else ax.xaxis).set_major_formatter(f)


def graf_venta_meta_mes(mes):
    fig, ax = plt.subplots(figsize=(11, 3.6))
    x = np.arange(len(mes))
    ax.bar(x, mes["VENTA"], color=NAVY_800, width=0.62, label="Venta", zorder=2)
    for xi, v in zip(x, mes["VENTA"]):
        if v > 0:
            ax.text(xi, v, compacto(v), ha="center", va="bottom", fontsize=7.5, color=TEXTO_SUAVE)
    if mes["META"].sum() > 0:
        ax.plot(x, mes["META"], color=COBRE_500, lw=2.4, marker="o", mfc="white", mec=COBRE_500, mew=2, label="Meta", zorder=3)
    ax.set_xticks(x, [titulo(m) for m in mes["MES"]])
    _ejes_moneda(ax)
    ax.grid(axis="y", color=DIVISOR, zorder=0)
    ax.legend(frameon=False, loc="upper left", ncol=2)
    return fig


def graf_avance_meta(avance, meta):
    tope = max(120.0, float(avance) + 10.0)
    fig, ax = plt.subplots(figsize=(11, 1.25))
    ax.barh([0], [90], color=PELIGRO_BG, height=0.8)
    ax.barh([0], [10], left=90, color=ALERTA_BG, height=0.8)
    ax.barh([0], [tope - 100], left=100, color=EXITO_BG, height=0.8)
    ax.barh([0], [avance], color=color_avance(avance, meta), height=0.36)
    ax.axvline(100, color=COBRE_600, lw=2.5)
    ax.text(min(avance, tope) + tope * 0.01, 0, porcentaje(avance), va="center", fontsize=12, fontweight="bold", color=NAVY_800)
    ax.set_xlim(0, tope)
    ax.set_yticks([])
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.0f} %"))
    ax.spines["left"].set_visible(False)
    return fig


def graf_mix_sucursal(mix):
    fig, ax = plt.subplots(figsize=(5.4, 3.6))
    wedges, _t, autot = ax.pie(mix["VENTA"], colors=PALETA[:len(mix)], startangle=90, counterclock=False,
                               wedgeprops=dict(width=0.38, edgecolor="white", linewidth=2),
                               autopct=lambda p: f"{p:.1f}".replace(".", ",") + " %" if p >= 4 else "", pctdistance=0.81,
                               textprops=dict(color="white", fontsize=8, fontweight="bold"))
    ax.text(0, 0.05, compacto(mix["VENTA"].sum()), ha="center", fontsize=13, fontweight="bold", color=NAVY_800)
    ax.text(0, -0.17, "venta total", ha="center", fontsize=8, color=TEXTO_SUAVE)
    ax.legend(wedges, [titulo(s) for s in mix["SUCURSAL"]], frameon=False, loc="center left", bbox_to_anchor=(1, 0.5), fontsize=8)
    ax.set_aspect("equal")
    return fig


def graf_barras_h(etiquetas, valores, color=NAVY_800, colores=None, formato=compacto, ancho=5.4, linea=None, sufijo_eje=None):
    n = len(etiquetas)
    fig, ax = plt.subplots(figsize=(ancho, max(2.2, 0.27 * n + 0.8)))
    y = np.arange(n)[::-1]
    ax.barh(y, valores, color=colores if colores is not None else color, height=0.66, zorder=2)
    maximo = max([abs(float(v)) for v in valores] + [1.0])
    for yi, v in zip(y, valores):
        ax.text(v + maximo * 0.01, yi, formato(v), va="center", fontsize=7.3, color=TEXTO_SUAVE)
    ax.set_yticks(y, etiquetas, fontsize=7.6)
    ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(5))
    ax.set_xlim(0, maximo * 1.2 if linea is None else max(maximo, linea) * 1.18)
    if linea is not None:
        ax.axvline(linea, color=COBRE_600, lw=1.6, ls="--", zorder=3)
    if sufijo_eje:
        ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.0f}{sufijo_eje}"))
    else:
        _ejes_moneda(ax, "x")
    ax.grid(axis="x", color=DIVISOR, zorder=0)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    return fig


def graf_sucursales(suc):
    fig, ax = plt.subplots(figsize=(11, 3.4))
    x = np.arange(len(suc))
    ax.bar(x, suc["VENTA"], color=NAVY_800, width=0.6, label="Venta", zorder=2)
    if suc["META"].sum() > 0:
        ax.scatter(x, suc["META"], marker="_", s=2400, linewidths=3.5, color=COBRE_500, label="Meta", zorder=3)
        for xi, v, m, a in zip(x, suc["VENTA"], suc["META"], suc["AVANCE"]):
            if m > 0:
                ax.text(xi, max(v, m) * 1.03, porcentaje(a), ha="center", va="bottom", fontsize=8.5, fontweight="bold",
                        color=color_avance(a, m))
    ax.set_xticks(x, [titulo(s) for s in suc["SUCURSAL"]])
    _ejes_moneda(ax)
    ax.set_ylim(0, max(suc["VENTA"].max(), suc["META"].max()) * 1.18)
    ax.grid(axis="y", color=DIVISOR, zorder=0)
    ax.legend(frameon=False, loc="upper right", ncol=2, markerscale=0.25)
    return fig


def graf_calor(matriz):
    """matriz: DataFrame índice=sucursal, columnas=mes, valores=avance % (NaN sin meta)."""
    filas, cols = matriz.shape
    fig, ax = plt.subplots(figsize=(11, max(1.8, 0.48 * filas + 0.8)))
    cmap = LinearSegmentedColormap.from_list("av", [(0, "#E0574A"), (0.35, "#F2B8B0"), (0.5, "#FBF3D9"),
                                                    (0.65, "#BFE5CF"), (1, "#2E9B67")])
    cmap.set_bad("#F3EFE9")
    datos = np.ma.masked_invalid(matriz.values.astype(float))
    im = ax.imshow(datos, cmap=cmap, vmin=60, vmax=140, aspect="auto")
    for i in range(filas):
        for j in range(cols):
            v = matriz.values[i, j]
            ax.text(j, i, "—" if pd.isna(v) else f"{v:.0f} %", ha="center", va="center", fontsize=7.5, color=TEXTO)
    ax.set_xticks(range(cols), [titulo(m)[:3] for m in matriz.columns])
    ax.set_yticks(range(filas), [titulo(s) for s in matriz.index])
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    cb = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.01)
    cb.outline.set_visible(False)
    cb.ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.0f} %"))
    cb.ax.tick_params(labelsize=7)
    return fig


def graf_participacion_dep(dep):
    """Reemplaza el mapa de árbol: participación de cada departamento en la venta, coloreada por avance."""
    total = dep["VENTA"].sum()
    d = dep.sort_values("VENTA", ascending=False)
    colores_d = [color_avance(a, m) for a, m in zip(d["AVANCE"], d["META"])]
    fig = graf_barras_h([titulo(x) for x in d["DEPARTAMENTO"]], list(d["VENTA"]), colores=colores_d, ancho=5.4,
                        formato=lambda v: f"{compacto(v)} · {numero(v / total * 100 if total else 0, 1)} %")
    fig.axes[0].legend(handles=[Patch(color=EXITO, label="Meta cumplida"), Patch(color=ALERTA, label="90 – 99 %"),
                                Patch(color=PELIGRO, label="Menos de 90 %")], frameon=False, fontsize=7, loc="lower right")
    return fig


# -----------------------------------
# SECCIONES DEL PDF
# -----------------------------------
def _kpis(datos, est):
    k = datos["kpis"]
    tarjetas = [
        ("VENTAS TOTALES", moneda(k["ventas"]), k.get("pie_ventas", "")),
        ("META FIJADA", moneda(k["meta"]), k.get("pie_meta", "")),
        ("PORCENTAJE DE AVANCE", porcentaje(k["avance"]), k.get("pie_avance", "")),
        ("EFICIENCIA EXHIBICIÓN (VENTA/M²)", moneda(k["eficiencia"]), k.get("pie_eficiencia", "")),
        ("COBERTURA DE INVENTARIO", k.get("cobertura_txt", "—"), k.get("pie_cobertura", "")),
        ("TICKET PROMEDIO", moneda(k["ticket"]), k.get("pie_ticket", "")),
    ]
    celdas = [[Paragraph(e, est["kpi_label"]), Paragraph(v, est["kpi_valor"]), Paragraph(p, est["kpi_pie"])] for e, v, p in tarjetas]
    ancho = ANCHO_UTIL / 3
    filas = [[celdas[0], celdas[1], celdas[2]], [celdas[3], celdas[4], celdas[5]]]
    # Cada tarjeta es una mini-tabla
    def tarjeta(c, destacada=False):
        t = Table([[c[0]], [c[1]], [c[2]]], colWidths=[ancho - 10])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(COBRE_100 if destacada else "#FFFFFF")),
            ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor(COBRE_200 if destacada else BORDE)),
            ("LEFTPADDING", (0, 0), (-1, -1), 9), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        return t
    grid = Table([[tarjeta(filas[0][0], True), tarjeta(filas[0][1]), tarjeta(filas[0][2])],
                  [tarjeta(filas[1][0]), tarjeta(filas[1][1]), tarjeta(filas[1][2])]], colWidths=[ancho] * 3)
    grid.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                              ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    return grid


def _portada(datos, est, secciones):
    f = datos["filtros"]
    elementos = []
    cab = Table([[Paragraph("▲ REPORTE EJECUTIVO", ParagraphStyle("ov", fontName="Texto-Negrita", fontSize=8,
                                                                 textColor=colors.HexColor(COBRE_400)))],
                 [Paragraph("Dashboard Comercial · Reporte completo", est["portada_titulo"])],
                 [Paragraph(datos["kpis"].get("conclusion", ""), est["portada_sub"])]],
                colWidths=[ANCHO_UTIL])
    cab.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(NAVY_800)),
                             ("LEFTPADDING", (0, 0), (-1, -1), 18), ("TOPPADDING", (0, 0), (0, 0), 16),
                             ("BOTTOMPADDING", (0, -1), (-1, -1), 16), ("LINEBELOW", (0, -1), (-1, -1), 3, colors.HexColor(COBRE_500))]))
    elementos += [cab, Spacer(1, 10)]

    filtros = [
        ["Año", str(f["año"]), "Meses", f["meses"]],
        ["Sucursales", f["sucursales"], "Áreas", f["areas"]],
        ["Departamentos", f["departamentos"], "Generado", f["generado"]],
        ["Fuente de ventas", f.get("fuente", ""), "Secciones", ", ".join(SECCIONES[s] for s in secciones)],
    ]
    t = Table([[Paragraph(f"<b>{a}</b>", est["nota"]), Paragraph(b, est["celda"]), Paragraph(f"<b>{c}</b>", est["nota"]),
                Paragraph(d, est["celda"])] for a, b, c, d in filtros],
              colWidths=[1.2 * inch, 3.7 * inch, 1.0 * inch, 3.9 * inch])
    t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor(BORDE)),
                           ("LINEBELOW", (0, 0), (-1, -2), 0.4, colors.HexColor(DIVISOR)),
                           ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(NAVY_50)),
                           ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 4),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    elementos += [Paragraph("Filtros aplicados", est["h2"]), t, Spacer(1, 6)]
    elementos += [Paragraph("Indicadores del periodo", est["h2"]), _kpis(datos, est), Spacer(1, 6)]

    notas = [
        "<b>Venta</b>: ImporteDivisaPrincipal en divisa (USD), incluye notas de crédito; pedidos PV (sistema anterior) y COT/VTA (sistema actual).",
        "<b>Meta</b>: META_2026 por sucursal y mes, repartida por categoría con METAS_POR_SUCURSAL_Y_CATEGORIA. <b>Avance</b> = venta / meta.",
        "<b>Eficiencia de exhibición</b> = venta / m² de exhibición frontal. <b>Cobertura</b> = inventario del último mes / venta del periodo anterior.",
        "<b>Ticket promedio</b> = venta total / pedidos únicos con venta (una transacción por número de pedido).",
        "<b>Meta por vendedor</b>: la meta de cada sucursal en cada mes se reparte en partes iguales entre sus vendedores de ese mes (≥ 5 % de la venta de la sucursal).",
        "<b>Unidades</b>: perfiles del sistema anterior convertidos de metro lineal a pieza; vidrio y espejo en m² (lámina, media y tercio). Los servicios no suman unidades.",
        "Debajo de cada gráfica está la tabla <b>«Datos de la gráfica»</b> con los valores exactos que la forman.",
    ]
    elementos += [Paragraph("Cómo leer este reporte", est["h2"])] + [Paragraph("• " + n, est["nota"]) for n in notas]
    return elementos


def _datos_de(texto, est):
    return Paragraph("DATOS DE LA GRÁFICA · " + texto, est["datos"])


def _seccion_resumen(datos, est):
    r = datos["resumen"]
    el = [PageBreak(), _banda_seccion("Resumen", est)]

    mes = r["mes"]
    if not mes.empty and (mes["VENTA"].sum() > 0 or mes["META"].sum() > 0):
        con_meta = mes[mes["META"] > 0]
        cumplidos = int((con_meta["VENTA"] >= con_meta["META"]).sum())
        el += [Paragraph("Venta vs. meta por mes", est["h2"]),
               Paragraph(f"{cumplidos} de {len(con_meta)} meses alcanzaron la meta" if len(con_meta) else "Ventas del periodo", est["sub"]),
               _imagen(graf_venta_meta_mes(mes))]
        t = pd.DataFrame({
            "MES": [titulo(m) for m in mes["MES"]], "VENTA": mes["VENTA"].map(moneda), "META": mes["META"].map(moneda),
            "AVANCE": [porcentaje(a) if m > 0 else "—" for a, m in zip(mes["AVANCE"], mes["META"])],
            "DIFERENCIA": [moneda(v - m) for v, m in zip(mes["VENTA"], mes["META"])],
        })
        t["_AV"], t["_MT"] = mes["AVANCE"].values, mes["META"].values
        el += [_datos_de("venta, meta y avance por mes", est),
               _tabla(t.drop(columns=["_AV", "_MT"]), est, anchos=[1.6 * inch, 2.1 * inch, 2.1 * inch, 1.6 * inch, 2.6 * inch],
                      derecha={"VENTA", "META", "AVANCE", "DIFERENCIA"}, colores_celda=_colores_avance(t, "AVANCE", "_MT"))]

    k = datos["kpis"]
    el += [KeepTogether([Paragraph("Avance de la meta", est["h2"]),
                         Paragraph(f"{porcentaje(k['avance'])} de {moneda(k['meta'])} · venta {moneda(k['ventas'])}", est["sub"]),
                         _imagen(graf_avance_meta(k["avance"], k["meta"]))])]

    mix = r["mix"]
    if not mix.empty:
        lider = mix.iloc[mix["VENTA"].values.argmax()]
        bloque = [Paragraph("Mix de ventas por sucursal", est["h2"]),
                  Paragraph(f"{titulo(lider['SUCURSAL'])} aporta el {porcentaje(lider['PESO'])} de la venta", est["sub"])]
        img = _imagen(graf_mix_sucursal(mix), ancho=5.1 * inch)
        tm = pd.DataFrame({"SUCURSAL": [titulo(s) for s in mix["SUCURSAL"]], "VENTA": mix["VENTA"].map(moneda),
                           "% DE LA VENTA": mix["PESO"].map(porcentaje)})
        lado = Table([[img, [_datos_de("venta por sucursal", est),
                             _tabla(tm, est, anchos=[1.7 * inch, 1.55 * inch, 1.1 * inch], derecha={"VENTA", "% DE LA VENTA"})]]],
                     colWidths=[5.3 * inch, 4.5 * inch])
        lado.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
        el += [KeepTogether(bloque + [lado])]

    top = r["top_cat"]
    if not top.empty:
        el += [PageBreak(), Paragraph("Top 10 categorías por venta", est["h2"]),
               Paragraph(f"{titulo(top.iloc[0]['CATEGORIA'])} lidera con {compacto(top.iloc[0]['VENTA'])}", est["sub"])]
        cols = [COBRE_500] + [NAVY_800] * (len(top) - 1)
        el += [_imagen(graf_barras_h([titulo(c) for c in top["CATEGORIA"]], list(top["VENTA"]), colores=cols, ancho=10.5),
                       ancho=ANCHO_UTIL)]
        t = pd.DataFrame({"CATEGORÍA": [titulo(c) for c in top["CATEGORIA"]], "DEPARTAMENTO": [titulo(d) for d in top["DEPARTAMENTO"]],
                          "VENTA": top["VENTA"].map(moneda), "META": top["META"].map(moneda),
                          "AVANCE": [porcentaje(a) if m > 0 else "—" for a, m in zip(top["AVANCE"], top["META"])]})
        t["_AV"], t["_MT"] = top["AVANCE"].values, top["META"].values
        el += [_datos_de("top 10 categorías", est),
               _tabla(t.drop(columns=["_AV", "_MT"]), est, anchos=[2.9 * inch, 2.6 * inch, 1.6 * inch, 1.6 * inch, 1.3 * inch],
                      derecha={"VENTA", "META", "AVANCE"}, colores_celda=_colores_avance(t, "AVANCE", "_MT"))]
    return el


def _seccion_sucursales(datos, est):
    s = datos["sucursales"]
    el = [PageBreak(), _banda_seccion("Sucursales", est)]
    suc = s["tabla"]
    if suc.empty:
        return el + [Paragraph("Ninguna sucursal seleccionada tiene ventas en el periodo.", est["nota"])]
    con_meta = suc[suc["META"] > 0]
    sub = (f"{titulo(con_meta.loc[con_meta['AVANCE'].idxmax(), 'SUCURSAL'])} tiene el mejor avance: "
           f"{porcentaje(con_meta['AVANCE'].max())}") if not con_meta.empty else "Venta de cada sucursal en el periodo"
    el += [Paragraph("Venta y meta por sucursal", est["h2"]), Paragraph(sub, est["sub"]), _imagen(graf_sucursales(suc))]
    t = pd.DataFrame({"SUCURSAL": [titulo(x) for x in suc["SUCURSAL"]], "VENTA": suc["VENTA"].map(moneda),
                      "META": suc["META"].map(moneda),
                      "AVANCE": [porcentaje(a) if m > 0 else "—" for a, m in zip(suc["AVANCE"], suc["META"])],
                      "% DE LA VENTA": suc["PESO"].map(porcentaje)})
    t["_AV"], t["_MT"] = suc["AVANCE"].values, suc["META"].values
    el += [_datos_de("venta, meta y avance por sucursal", est),
           _tabla(t.drop(columns=["_AV", "_MT"]), est, anchos=[2.4 * inch, 2.1 * inch, 2.1 * inch, 1.6 * inch, 1.8 * inch],
                  derecha={"VENTA", "META", "AVANCE", "% DE LA VENTA"}, colores_celda=_colores_avance(t, "AVANCE", "_MT"))]

    av, ve = s["matriz_avance"], s["matriz_venta"]
    if not av.empty and av.notna().any().any():
        el += [PageBreak(), Paragraph("Mapa de calor: avance por sucursal y mes", est["h2"]),
               Paragraph("Rojo: por debajo de la meta · Verde: meta superada · «—»: sin meta o sin venta ese mes", est["sub"]),
               _imagen(graf_calor(av))]
        n = len(av.columns)
        ancho_c = (ANCHO_UTIL - 1.4 * inch) / max(n, 1)
        ta = av.copy()
        ta = ta.apply(lambda c: c.map(lambda v: "—" if pd.isna(v) else numero(v, 0) + " %"))
        ta.insert(0, "SUCURSAL", [titulo(x) for x in av.index])
        ta.columns = ["SUCURSAL"] + [titulo(m)[:3] for m in av.columns]
        colores_av = []
        for i, sname in enumerate(av.index):
            for j, m in enumerate(av.columns):
                v = av.loc[sname, m]
                if pd.notna(v):
                    colores_av.append((i, j + 1, color_avance(v, 1)))
        el += [_datos_de("avance % por sucursal y mes", est),
               _tabla(ta, est, anchos=[1.4 * inch] + [ancho_c] * n, derecha=set(ta.columns[1:]), colores_celda=colores_av)]
        tv = ve.apply(lambda c: c.map(compacto))
        tv.insert(0, "SUCURSAL", [titulo(x) for x in ve.index])
        tv.columns = ["SUCURSAL"] + [titulo(m)[:3] for m in ve.columns]
        el += [_datos_de("venta por sucursal y mes", est),
               _tabla(tv, est, anchos=[1.4 * inch] + [ancho_c] * n, derecha=set(tv.columns[1:]))]
    return el


def _tabla_detalle_departamentos(det, est):
    """La misma tabla de 'Detalle por departamento y categoría' (con totales)."""
    filas_sub = [i for i, c in enumerate(det["CATEGORIA"]) if c == "TOTAL DEPARTAMENTO"]
    filas_tot = [i for i, d in enumerate(det["DEPARTAMENTO"]) if d == "TOTAL GENERAL"]
    t = pd.DataFrame({
        "DEPARTAMENTO": [titulo(x) for x in det["DEPARTAMENTO"]], "CATEGORÍA": [titulo(x) for x in det["CATEGORIA"]],
        "VENTA": det["VENTA"].map(moneda), "META": det["META"].map(moneda),
        "AVANCE": [porcentaje(a) if m > 0 else "0,00 %" for a, m in zip(det["AVANCE"], det["META"])],
        "EFICIENCIA (VENTA/M²)": det["EFICIENCIA"].map(moneda),
        "COBERTURA INV.": det["COBERTURA"].map(lambda v: "—" if pd.isna(v) else numero(v)),
    })
    t["_AV"], t["_MT"] = det["AVANCE"].values, det["META"].values
    return _tabla(t.drop(columns=["_AV", "_MT"]), est,
                  anchos=[2.05 * inch, 2.45 * inch, 1.2 * inch, 1.2 * inch, 0.9 * inch, 1.25 * inch, 0.95 * inch],
                  derecha={"VENTA", "META", "AVANCE", "EFICIENCIA (VENTA/M²)", "COBERTURA INV."},
                  filas_subtotal=filas_sub, filas_total=filas_tot,
                  colores_celda=_colores_avance(t, "AVANCE", "_MT", excluir=filas_sub + filas_tot))


def _seccion_departamentos(datos, est):
    d = datos["departamentos"]
    el = [PageBreak(), _banda_seccion("Departamentos", est)]
    dep = d["tabla"]
    if dep.empty:
        return el + [Paragraph("No hay datos de departamentos para los filtros seleccionados.", est["nota"])]
    con_meta = dep[dep["META"] > 0].sort_values("AVANCE", ascending=False)
    if not con_meta.empty:
        cumplen = int((con_meta["AVANCE"] >= 100).sum())
        img_av = _imagen(graf_barras_h([titulo(x) for x in con_meta["DEPARTAMENTO"]], list(con_meta["AVANCE"]),
                                       colores=[color_avance(a, m) for a, m in zip(con_meta["AVANCE"], con_meta["META"])],
                                       formato=porcentaje, linea=100, sufijo_eje=" %", ancho=5.4), ancho=4.8 * inch)
        bloque_av = [Paragraph("Avance por departamento", est["h2"]),
                     Paragraph(f"{cumplen} de {len(con_meta)} departamentos cumplen la meta", est["sub"]), img_av]
    else:
        bloque_av = [Paragraph("Avance por departamento", est["h2"]), Paragraph("Sin metas cargadas.", est["nota"])]
    con_venta = dep[dep["VENTA"] > 0]
    img_part = _imagen(graf_participacion_dep(con_venta), ancho=4.8 * inch) if not con_venta.empty else Spacer(1, 1)
    bloque_part = [Paragraph("Dónde se concentra la venta", est["h2"]),
                   Paragraph("Participación de cada departamento en la venta; el color indica el avance", est["sub"]), img_part]
    lado = Table([[bloque_av, bloque_part]], colWidths=[4.9 * inch, 4.9 * inch])
    lado.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    el.append(lado)

    total = dep["VENTA"].sum()
    dd = dep.sort_values("VENTA", ascending=False)
    t = pd.DataFrame({"DEPARTAMENTO": [titulo(x) for x in dd["DEPARTAMENTO"]], "VENTA": dd["VENTA"].map(moneda),
                      "% DE LA VENTA": [porcentaje(v / total * 100 if total else 0) for v in dd["VENTA"]],
                      "META": dd["META"].map(moneda),
                      "AVANCE": [porcentaje(a) if m > 0 else "—" for a, m in zip(dd["AVANCE"], dd["META"])],
                      "EFICIENCIA (VENTA/M²)": dd["EFICIENCIA"].map(moneda),
                      "COBERTURA INV.": dd["COBERTURA"].map(lambda v: "—" if pd.isna(v) else numero(v))})
    t["_AV"], t["_MT"] = dd["AVANCE"].values, dd["META"].values
    el += [_datos_de("venta, meta, avance, eficiencia y cobertura por departamento", est),
           _tabla(t.drop(columns=["_AV", "_MT"]), est,
                  anchos=[2.6 * inch, 1.35 * inch, 1.1 * inch, 1.35 * inch, 1.0 * inch, 1.45 * inch, 1.15 * inch],
                  derecha={"VENTA", "% DE LA VENTA", "META", "AVANCE", "EFICIENCIA (VENTA/M²)", "COBERTURA INV."},
                  colores_celda=_colores_avance(t, "AVANCE", "_MT"))]

    det = d["detalle"]
    if not det.empty:
        el += [PageBreak(), Paragraph("Detalle por departamento y categoría", est["h2"]),
               Paragraph("Fila cobre: total del departamento · Fila azul: total general", est["sub"]),
               _tabla_detalle_departamentos(det, est)]
    return el


def _seccion_articulos(datos, est):
    a = datos["articulos"]
    el = [PageBreak(), _banda_seccion("Artículos", est)]
    top = a["top"]
    if top.empty:
        return el + [Paragraph("No hay artículos con venta en el periodo.", est["nota"])]
    k = a["kpis"]
    resumen = Table([[Paragraph(f"<b>{entero(k['distintos'])}</b> artículos distintos", est["celda"]),
                      Paragraph(f"<b>{entero(k['unidades'])}</b> unidades vendidas (sin servicios)", est["celda"]),
                      Paragraph(f"<b>{metros(k['m2'])}</b> de vidrio, espejos y láminas", est["celda"]),
                      Paragraph(f"Líder: <b>{titulo(k['lider'])}</b> ({moneda(k['lider_venta'])})", est["celda"])]],
                    colWidths=[1.9 * inch, 2.5 * inch, 2.6 * inch, 2.8 * inch])
    resumen.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(NAVY_50)),
                                 ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor(BORDE)),
                                 ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    el += [Spacer(1, 6), resumen]

    top15 = top.head(15)
    img_top = _imagen(graf_barras_h([titulo(x)[:42] for x in top15["ARTICULO"]], list(top15["VENTA"]), color=NAVY_800, ancho=5.4),
                      ancho=4.8 * inch)
    cat = a["categorias"].head(12)
    img_cat = _imagen(graf_barras_h([titulo(x)[:36] for x in cat["CATEGORIA"]], list(cat["VENTA"]), color=COBRE_500, ancho=5.4),
                      ancho=4.8 * inch) if not cat.empty else Spacer(1, 1)
    peso15 = top15["VENTA"].sum() / k["venta"] * 100 if k["venta"] else 0
    lado = Table([[[Paragraph("Top 15 artículos del periodo", est["h2"]),
                    Paragraph(f"Concentran {porcentaje(peso15)} de la venta filtrada", est["sub"]), img_top],
                   [Paragraph("Venta por categoría (top 12)", est["h2"]),
                    Paragraph(f"{k['categorias']} categorías con venta en el periodo", est["sub"]), img_cat]]],
                 colWidths=[4.9 * inch, 4.9 * inch])
    lado.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    el.append(lado)

    if not cat.empty:
        tc = pd.DataFrame({"CATEGORÍA": [titulo(x) for x in cat["CATEGORIA"]], "VENTA": cat["VENTA"].map(moneda),
                           "% DEL TOTAL": [porcentaje(v / k["venta"] * 100 if k["venta"] else 0) for v in cat["VENTA"]],
                           "UNIDADES": cat["UNIDADES"].map(entero), "M² VENDIDOS": cat["M2"].map(metros),
                           "PEDIDOS": cat["PEDIDOS"].map(entero)})
        el += [_datos_de("venta, unidades y m² de las 12 categorías con más venta", est),
               _tabla(tc, est, anchos=[3.4 * inch, 1.5 * inch, 1.1 * inch, 1.2 * inch, 1.6 * inch, 1.2 * inch],
                      derecha={"VENTA", "% DEL TOTAL", "UNIDADES", "M² VENDIDOS", "PEDIDOS"})]

    n = len(top)
    tt = pd.DataFrame({
        "#": range(1, n + 1), "ARTÍCULO": [titulo(x) for x in top["ARTICULO"]],
        "CATEGORÍA": [titulo(x) for x in top["CATEGORIA"]], "ÁREA": [titulo(x) for x in top["AREA"]],
        "UNIDADES": top["UNIDADES"].map(entero), "M²": top["M2"].map(metros),
        "VENTA": top["VENTA"].map(moneda),
        "% DEL TOTAL": [porcentaje(v / k["venta"] * 100 if k["venta"] else 0) for v in top["VENTA"]],
        "PEDIDOS": top["PEDIDOS"].map(entero),
    })
    el += [PageBreak(), Paragraph(f"Top {n} artículos por venta", est["h2"]),
           Paragraph(f"Concentran {porcentaje(top['VENTA'].sum() / k['venta'] * 100 if k['venta'] else 0)} de la venta. "
                     "La lista completa está en el Excel de todas las tablas.", est["sub"]),
           _tabla(tt, est, anchos=[0.3 * inch, 2.7 * inch, 1.6 * inch, 1.35 * inch, 0.8 * inch, 0.9 * inch, 1.0 * inch,
                                   0.7 * inch, 0.7 * inch],
                  derecha={"#", "UNIDADES", "M²", "VENTA", "% DEL TOTAL", "PEDIDOS"})]
    return el


def _seccion_areas(datos, est):
    a = datos["areas"]
    el = [PageBreak(), _banda_seccion("Áreas", est)]
    res = a["resumen"]
    if res.empty:
        return el + [Paragraph("No hay ventas por área para los filtros seleccionados.", est["nota"])]
    total = res["VENTA"].sum()
    lider = res.iloc[0]
    el += [Paragraph("Venta por área", est["h2"]),
           Paragraph(f"{titulo(lider['AREA'])} lidera con {porcentaje(lider['VENTA'] / total * 100 if total else 0)} de la venta", est["sub"]),
           _imagen(graf_barras_h([titulo(x) for x in res["AREA"]], list(res["VENTA"]), color=COBRE_500, ancho=10.5,
                                 formato=lambda v: f"{compacto(v)} · {numero(v / total * 100 if total else 0, 1)} %"),
                   ancho=ANCHO_UTIL)]
    tr = pd.DataFrame({"ÁREA": [titulo(x) for x in res["AREA"]], "VENTA": res["VENTA"].map(moneda),
                       "% DEL TOTAL": [porcentaje(v / total * 100 if total else 0) for v in res["VENTA"]],
                       "UNIDADES": res["UNIDADES"].map(entero), "M² VENDIDOS": res["M2"].map(metros),
                       "ARTÍCULOS": res["ARTICULOS"].map(entero)})
    el += [_datos_de("resumen por área", est),
           _tabla(tr, est, anchos=[3.0 * inch, 1.7 * inch, 1.2 * inch, 1.3 * inch, 1.6 * inch, 1.2 * inch],
                  derecha={"VENTA", "% DEL TOTAL", "UNIDADES", "M² VENDIDOS", "ARTÍCULOS"})]

    kpi = a["reporte"]
    if not kpi.empty:
        filas_sub = [i for i, d in enumerate(kpi["DEPARTAMENTO"]) if d == "TOTAL ÁREA"]
        filas_tot = [i for i, d in enumerate(kpi["DEPARTAMENTO"]) if d == "TOTAL GENERAL"]
        t = pd.DataFrame({
            "ÁREA": [titulo(x) for x in kpi["ÁREA"]], "DEPARTAMENTO": [titulo(x) for x in kpi["DEPARTAMENTO"]],
            "CATEGORÍA": [titulo(x) for x in kpi["CATEGORIA"]], "VENTA": kpi["VENTA"].map(moneda), "META": kpi["META"].map(moneda),
            "AVANCE": [porcentaje(x) if m > 0 else "0,00 %" for x, m in zip(kpi["AVANCE"], kpi["META"])],
            "EFICIENCIA (VENTA/M²)": kpi["EFICIENCIA EXHIBICION FRONTAL (VENTA/M2)"].map(moneda),
            "COBERTURA INV.": kpi["COBERTURA"].map(lambda v: "—" if pd.isna(v) else numero(v)),
        })
        t["_AV"], t["_MT"] = kpi["AVANCE"].values, kpi["META"].values
        el += [PageBreak(), Paragraph("Reporte comercial por área", est["h2"]),
               Paragraph("Fila cobre: total del área · Fila azul: total general", est["sub"]),
               _tabla(t.drop(columns=["_AV", "_MT"]), est,
                      anchos=[1.55 * inch, 1.75 * inch, 2.0 * inch, 1.05 * inch, 1.05 * inch, 0.8 * inch, 1.05 * inch, 0.75 * inch],
                      derecha={"VENTA", "META", "AVANCE", "EFICIENCIA (VENTA/M²)", "COBERTURA INV."},
                      filas_subtotal=filas_sub, filas_total=filas_tot,
                      colores_celda=_colores_avance(t, "AVANCE", "_MT", excluir=filas_sub + filas_tot))]
    return el


def _seccion_vendedores(datos, est):
    v = datos["vendedores"]
    el = [PageBreak(), _banda_seccion("Vendedores", est)]
    tabla = v["tabla"]
    if tabla.empty:
        return el + [Paragraph("No hay ventas por vendedor para los filtros seleccionados.", est["nota"])]
    tot = tabla[tabla["ÁREA"] == "TOTAL VENDEDOR"].sort_values("VENTA", ascending=False)
    general = tabla[tabla["USUARIO"] == "TOTAL GENERAL"]
    el += [Paragraph("Avance por vendedor", est["h2"]),
           Paragraph("La meta de cada sucursal en cada mes se reparte en partes iguales entre sus vendedores de ese mes "
                     "(los que hicieron al menos el 5 % de la venta de la sucursal). Usuarios de ambos sistemas unificados.", est["sub"])]
    con_meta = tot[tot["META"] > 0].sort_values("AVANCE", ascending=False)
    if not con_meta.empty:
        el.append(_imagen(graf_barras_h([titulo(x) for x in con_meta["USUARIO"]], list(con_meta["AVANCE"]),
                                        colores=[color_avance(a, m) for a, m in zip(con_meta["AVANCE"], con_meta["META"])],
                                        formato=porcentaje, linea=100, sufijo_eje=" %", ancho=10.5), ancho=ANCHO_UTIL))
    t = pd.DataFrame({"VENDEDOR": [titulo(x) for x in tot["USUARIO"]], "VENTA": tot["VENTA"].map(moneda),
                      "META": tot["META"].map(moneda),
                      "AVANCE": [porcentaje(a) if m > 0 else "—" for a, m in zip(tot["AVANCE"], tot["META"])]})
    t["_AV"], t["_MT"] = tot["AVANCE"].values, tot["META"].values
    if not general.empty:
        g = general.iloc[0]
        t = pd.concat([t, pd.DataFrame([{"VENDEDOR": "Total general", "VENTA": moneda(g["VENTA"]), "META": moneda(g["META"]),
                                         "AVANCE": porcentaje(g["AVANCE"]), "_AV": g["AVANCE"], "_MT": 0}])], ignore_index=True)
    el += [_datos_de("venta, meta y avance por vendedor", est),
           _tabla(t.drop(columns=["_AV", "_MT"]), est, anchos=[3.4 * inch, 2.3 * inch, 2.3 * inch, 2.0 * inch],
                  derecha={"VENTA", "META", "AVANCE"}, filas_total=[len(t) - 1] if not general.empty else None,
                  colores_celda=_colores_avance(t, "AVANCE", "_MT"))]

    det = tabla.copy()
    filas_sub = [i for i, x in enumerate(det["ÁREA"]) if x == "TOTAL VENDEDOR"]
    filas_tot = [i for i, x in enumerate(det["USUARIO"]) if x == "TOTAL GENERAL"]
    td = pd.DataFrame({"VENDEDOR": [titulo(x) for x in det["USUARIO"]], "ÁREA": [titulo(x) for x in det["ÁREA"]],
                       "VENTA": det["VENTA"].map(moneda), "META": det["META"].map(moneda),
                       "AVANCE": [porcentaje(a) if m > 0 else "0,00 %" for a, m in zip(det["AVANCE"], det["META"])]})
    td["_AV"], td["_MT"] = det["AVANCE"].values, det["META"].values
    el += [PageBreak(), Paragraph("Reporte de vendedores por área", est["h2"]),
           Paragraph("Fila cobre: total del vendedor · Fila azul: total general", est["sub"]),
           _tabla(td.drop(columns=["_AV", "_MT"]), est, anchos=[2.6 * inch, 3.0 * inch, 1.6 * inch, 1.6 * inch, 1.2 * inch],
                  derecha={"VENTA", "META", "AVANCE"}, filas_subtotal=filas_sub, filas_total=filas_tot,
                  colores_celda=_colores_avance(td, "AVANCE", "_MT", excluir=filas_sub + filas_tot))]
    return el


def _pie_pagina(generado):
    def dibujar(canvas, doc):
        canvas.saveState()
        canvas.setFont("Texto", 7)
        canvas.setFillColor(colors.HexColor(TEXTO_SUAVE))
        canvas.drawString(0.5 * inch, 0.32 * inch, f"Dashboard Comercial · Reporte completo · {generado}")
        canvas.drawRightString(10.5 * inch, 0.32 * inch, f"Página {doc.page}")
        canvas.setStrokeColor(colors.HexColor(COBRE_500))
        canvas.setLineWidth(1.2)
        canvas.line(0.5 * inch, 0.45 * inch, 10.5 * inch, 0.45 * inch)
        canvas.restoreState()
    return dibujar


_CANDADO = threading.Lock()  # matplotlib no es seguro si dos personas descargan a la vez


def generar_pdf_completo(datos, secciones=None):
    """Devuelve los bytes del PDF con las secciones pedidas (por defecto, todas)."""
    with _CANDADO:
        return _generar_pdf(datos, secciones)


def _generar_pdf(datos, secciones=None):
    secciones = [s for s in (secciones or list(SECCIONES)) if s in SECCIONES]
    est = _estilos()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(letter), leftMargin=0.5 * inch, rightMargin=0.5 * inch,
                            topMargin=0.45 * inch, bottomMargin=0.6 * inch,
                            title=f"Reporte comercial {datos['filtros']['año']}", author="Dashboard Comercial")
    historia = _portada(datos, est, secciones)
    constructores = {"resumen": _seccion_resumen, "sucursales": _seccion_sucursales, "departamentos": _seccion_departamentos,
                     "articulos": _seccion_articulos, "areas": _seccion_areas, "vendedores": _seccion_vendedores}
    for s in secciones:
        historia += constructores[s](datos, est)
    historia = _agrupar_datos(historia)
    pie = _pie_pagina(datos["filtros"]["generado"])
    doc.build(historia, onFirstPage=pie, onLaterPages=pie)
    return buf.getvalue()


# -----------------------------------
# EXCEL CON TODAS LAS TABLAS
# -----------------------------------
def generar_excel_completo(datos):
    """Un libro con una hoja por tabla. Sin filas de subtotales para que todo se pueda sumar."""
    hojas = []
    f, k = datos["filtros"], datos["kpis"]
    hojas.append(("Filtros y KPIs", pd.DataFrame([
        ["Año", str(f["año"])], ["Meses", f["meses"]], ["Sucursales", f["sucursales"]], ["Departamentos", f["departamentos"]],
        ["Áreas", f["areas"]], ["Generado", f["generado"]], ["Ventas totales", k["ventas"]], ["Meta fijada", k["meta"]],
        ["Porcentaje de avance", k["avance"] / 100], ["Eficiencia exhibición (venta/m²)", k["eficiencia"]],
        ["Cobertura de inventario", k.get("cobertura")], ["Ticket promedio", k["ticket"]], ["Pedidos (transacciones)", k["transacciones"]],
    ], columns=["INDICADOR", "VALOR"])))

    r = datos["resumen"]
    if not r["mes"].empty:
        m = r["mes"].copy()
        hojas.append(("Venta y meta por mes", pd.DataFrame({"MES": m["MES"].map(titulo), "VENTA": m["VENTA"], "META": m["META"],
                                                             "AVANCE": m["AVANCE"] / 100, "DIFERENCIA": m["VENTA"] - m["META"]})))
    if not r["mix"].empty:
        hojas.append(("Mix por sucursal", pd.DataFrame({"SUCURSAL": r["mix"]["SUCURSAL"].map(titulo), "VENTA": r["mix"]["VENTA"],
                                                         "% DE LA VENTA": r["mix"]["PESO"] / 100})))

    s = datos["sucursales"]
    if not s["tabla"].empty:
        t = s["tabla"]
        hojas.append(("Sucursales", pd.DataFrame({"SUCURSAL": t["SUCURSAL"].map(titulo), "VENTA": t["VENTA"], "META": t["META"],
                                                   "AVANCE": t["AVANCE"] / 100, "% DE LA VENTA": t["PESO"] / 100})))
    if not s["largo"].empty:
        l = s["largo"]
        hojas.append(("Sucursal por mes", pd.DataFrame({"SUCURSAL": l["SUCURSAL"].map(titulo), "MES": l["MES"].map(titulo),
                                                         "VENTA": l["VENTA"], "META": l["META"], "AVANCE": l["AVANCE"] / 100})))

    d = datos["departamentos"]
    if not d["tabla"].empty:
        t = d["tabla"].sort_values("VENTA", ascending=False)
        hojas.append(("Departamentos", pd.DataFrame({"DEPARTAMENTO": t["DEPARTAMENTO"].map(titulo), "VENTA": t["VENTA"], "META": t["META"],
                                                      "AVANCE": t["AVANCE"] / 100, "EFICIENCIA (VENTA/M²)": t["EFICIENCIA"],
                                                      "COBERTURA INVENTARIO": t["COBERTURA"]})))
    if not d["detalle"].empty:
        t = d["detalle"]
        t = t[(t["CATEGORIA"] != "TOTAL DEPARTAMENTO") & (t["DEPARTAMENTO"] != "TOTAL GENERAL")]
        hojas.append(("Departamento y categoria", pd.DataFrame({
            "DEPARTAMENTO": t["DEPARTAMENTO"].map(titulo), "CATEGORÍA": t["CATEGORIA"].map(titulo), "VENTA": t["VENTA"],
            "META": t["META"], "AVANCE": t["AVANCE"] / 100, "EFICIENCIA (VENTA/M²)": t["EFICIENCIA"],
            "COBERTURA INVENTARIO": t["COBERTURA"]})))

    a = datos["articulos"]
    if not a["todos"].empty:
        t = a["todos"]
        tot = t["VENTA"].sum()
        hojas.append(("Articulos", pd.DataFrame({
            "ARTÍCULO": t["ARTICULO"].map(titulo), "CATEGORÍA": t["CATEGORIA"].map(titulo), "ÁREA": t["AREA"].map(titulo),
            "UNIDADES": t["UNIDADES"].where(t["UNIDADES"].fillna(0) != 0), "M² VENDIDOS": t["M2"].where(t["M2"].fillna(0) != 0),
            "VENTA": t["VENTA"], "% DEL TOTAL": t["VENTA"] / tot if tot else 0.0, "PEDIDOS": t["PEDIDOS"]})))
    if not a["categorias"].empty:
        t = a["categorias"]
        hojas.append(("Categorias (articulos)", pd.DataFrame({
            "CATEGORÍA": t["CATEGORIA"].map(titulo), "VENTA": t["VENTA"], "UNIDADES": t["UNIDADES"].where(t["UNIDADES"].fillna(0) != 0),
            "M² VENDIDOS": t["M2"].where(t["M2"].fillna(0) != 0), "PEDIDOS": t["PEDIDOS"]})))

    ar = datos["areas"]
    if not ar["resumen"].empty:
        t = ar["resumen"]
        tot = t["VENTA"].sum()
        hojas.append(("Areas", pd.DataFrame({"ÁREA": t["AREA"].map(titulo), "VENTA": t["VENTA"], "% DEL TOTAL": t["VENTA"] / tot if tot else 0.0,
                                              "UNIDADES": t["UNIDADES"].where(t["UNIDADES"].fillna(0) != 0),
                                              "M² VENDIDOS": t["M2"].where(t["M2"].fillna(0) != 0), "ARTÍCULOS": t["ARTICULOS"]})))
    if not ar["reporte"].empty:
        t = ar["reporte"]
        t = t[~t["DEPARTAMENTO"].isin(["TOTAL ÁREA", "TOTAL GENERAL"])]
        hojas.append(("Reporte por area", pd.DataFrame({
            "ÁREA": t["ÁREA"].map(titulo), "DEPARTAMENTO": t["DEPARTAMENTO"].map(titulo), "CATEGORÍA": t["CATEGORIA"].map(titulo),
            "VENTA": t["VENTA"], "META": t["META"], "AVANCE": t["AVANCE"] / 100,
            "EFICIENCIA (VENTA/M²)": t["EFICIENCIA EXHIBICION FRONTAL (VENTA/M2)"], "COBERTURA INVENTARIO": t["COBERTURA"]})))

    v = datos["vendedores"]["tabla"]
    if not v.empty:
        t = v[~v["ÁREA"].isin(["TOTAL VENDEDOR", "REPORTE CONSOLIDADO"])]
        hojas.append(("Vendedores por area", pd.DataFrame({"VENDEDOR": t["USUARIO"].map(titulo), "ÁREA": t["ÁREA"].map(titulo),
                                                            "VENTA": t["VENTA"], "META": t["META"], "AVANCE": t["AVANCE"] / 100})))
        tt = v[v["ÁREA"] == "TOTAL VENDEDOR"].sort_values("VENTA", ascending=False)
        hojas.append(("Vendedores", pd.DataFrame({"VENDEDOR": tt["USUARIO"].map(titulo), "VENTA": tt["VENTA"], "META": tt["META"],
                                                   "AVANCE": tt["AVANCE"] / 100})))

    salida = io.BytesIO()
    pct = {"AVANCE", "% DE LA VENTA", "% DEL TOTAL"}
    enteros = {"UNIDADES", "PEDIDOS", "ARTÍCULOS"}
    with pd.ExcelWriter(salida, engine="openpyxl") as writer:
        for nombre, df in hojas:
            nombre = nombre[:31]
            df.to_excel(writer, index=False, sheet_name=nombre)
            hoja = writer.sheets[nombre]
            hoja.freeze_panes = "A2"
            for i, col in enumerate(df.columns, start=1):
                letra = hoja.cell(row=1, column=i).column_letter
                largo = max([len(str(col))] + [len(str(x)) for x in df[col].head(200)])
                hoja.column_dimensions[letra].width = min(max(12, largo + 2), 55)
                if not pd.api.types.is_numeric_dtype(df[col]) and nombre != "Filtros y KPIs":
                    continue
                formato = "0.00%" if col in pct else ("#,##0" if col in enteros else "#,##0.00")
                for fila in range(2, len(df) + 2):
                    celda = hoja.cell(row=fila, column=i)
                    if isinstance(celda.value, (int, float)):
                        celda.number_format = formato
            if nombre == "Filtros y KPIs":
                hoja["B10"].number_format = "0.00%"
    return salida.getvalue()
