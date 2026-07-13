import streamlit as st
import pandas as pd
import numpy as np
import os
import io
import gdown
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# -----------------------------------
# CONFIGURACION DE LA PAGINA Y ESTILOS CSS
# -----------------------------------
st.set_page_config(page_title="Dashboard Comercial", layout="wide")

st.markdown("""
    <style>
    .main-title {
        color: #1E3A8A; 
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-weight: bold;
        padding-bottom: 10px;
    }
    div[data-testid="stMetric"] {
        background-color: #F8FAFC;
        border-left: 5px solid #10B981; 
        padding: 12px;
        border-radius: 4px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    div[data-testid="stMetric"] label {
        color: #1E40AF !important;
        font-weight: 600 !important;
    }
    section[data-testid="stSidebar"] label {
        font-size: 14px !important; 
        font-weight: 600 !important;
        color: #1E3A8A !important;
    }
    section[data-testid="stSidebar"] div[data-baseweb="select"] {
        font-size: 14px !important;
    }
    section[data-testid="stSidebar"] span[data-baseweb="tag"] {
        font-size: 12px !important;
        padding: 4px 8px !important; 
        margin: 2px !important; 
    }
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
        background-color: #FFFFFF !important; 
        border-radius: 4px !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">📊 DASHBOARD COMERCIAL</h1>', unsafe_allow_html=True)

# -----------------------------------
# FUNCIONES DE FORMATEO REGIONAL
# -----------------------------------
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

# -----------------------------------
# CARGA Y LIMPIEZA DE DATA 
# -----------------------------------
@st.cache_data(ttl=60)
def cargar_datos():
    ID_DRIVE_VENTAS = "16XYtA31ebAE1Ad2Ldj7OV-CBbxO0IVSf"
    ARCHIVO_TEMP_DRIVE = "ventas_drive_temp.csv"

    df = pd.DataFrame()
    try:
        gdown.download(id=ID_DRIVE_VENTAS, output=ARCHIVO_TEMP_DRIVE, quiet=True)
        if os.path.exists(ARCHIVO_TEMP_DRIVE):
            df = pd.read_csv(ARCHIVO_TEMP_DRIVE, encoding="latin-1", sep=";")
    except Exception:
        df = pd.DataFrame()
    finally:
        if os.path.exists(ARCHIVO_TEMP_DRIVE):
            try:
                os.remove(ARCHIVO_TEMP_DRIVE)
            except Exception:
                pass

    if df.empty:
        try:
            df = pd.read_csv("ventas.csv", encoding="latin-1", sep=";")
        except Exception:
            return pd.DataFrame(), pd.DataFrame()
        
    col_año = [c for c in df.columns if 'AÑO' in c.upper() or 'AÃ' in c.upper()]
    if col_año:
        df = df.rename(columns={col_año[0]: 'AÑO'})
        
    if 'AÑO' in df.columns:
        df['AÑO'] = pd.to_numeric(df['AÑO'], errors='coerce').fillna(0).astype(int)
        
    df.columns = df.columns.str.strip()
    
    if 'ImporteDivisaPrincipal' in df.columns:
        df['ImporteDivisaPrincipal'] = (
            df['ImporteDivisaPrincipal']
            .astype(str)
            .str.replace(r'\s+', '', regex=True)
            .str.replace('.', '', regex=False)
            .str.replace(',', '.', regex=False)
        )
        df['ImporteDivisaPrincipal'] = pd.to_numeric(df['ImporteDivisaPrincipal'], errors='coerce').fillna(0.0)
    
    if 'Nombre' in df.columns:
        df['Nombre'] = df['Nombre'].str.replace('SUCURSAL ', '', regex=False).str.upper().str.strip()
        df['Nombre'] = df['Nombre'].replace({
            'ALUMINIOLOGO WEB': 'ALUMUNIOLOGO WED',
            'SHOWROOM - 000': 'SHOWROOM'
        })
    
    if 'DEPARTAMENTO' in df.columns:
        df['DEPARTAMENTO'] = df['DEPARTAMENTO'].astype(str).str.strip().str.upper()
        df['DEPARTAMENTO'] = df['DEPARTAMENTO'].str.replace('BAÃ\x91O', 'BAÑO', regex=False)
    
    archivo_m2 = "METROS CUADRADOS POR CATEGORIA.csv"
    if not os.path.exists(archivo_m2):
        return df, pd.DataFrame()
        
    df_m2 = pd.read_csv(archivo_m2, encoding="latin-1", sep=";")
    df_m2.columns = df_m2.columns.str.strip()
    
    if 'DEPARTAMENTO' in df_m2.columns:
        df_m2['DEPARTAMENTO'] = df_m2['DEPARTAMENTO'].ffill().astype(str).str.strip().str.upper()
        df_m2['DEPARTAMENTO'] = df_m2['DEPARTAMENTO'].str.replace('BAÃ\x91O', 'BAÑO', regex=False)
        
    if 'CATEGORIA' in df_m2.columns:
        df_m2['CATEGORIA'] = df_m2['CATEGORIA'].astype(str).str.strip().str.upper()
        df_m2 = df_m2[(df_m2['CATEGORIA'] != 'NAN') & (df_m2['CATEGORIA'] != '')]
    
    if 'METROS' in df_m2.columns:
        df_m2['METROS'] = (
            df_m2['METROS']
            .astype(str)
            .str.replace(r'\s+', '', regex=True)
            .str.replace(',', '.', regex=False)
        )
        df_m2['METROS'] = pd.to_numeric(df_m2['METROS'], errors='coerce').fillna(0.0)
        
    return df, df_m2

@st.cache_data(ttl=60)
def cargar_inventario():
    archivo_inv = "INVENTARIO.csv"
    if not os.path.exists(archivo_inv):
        return pd.DataFrame()
    try:
        df_inv = pd.read_csv(archivo_inv, encoding="latin-1", sep=";")
        df_inv.columns = df_inv.columns.str.strip()
        
        col_año = [c for c in df_inv.columns if 'AÑO' in c.upper() or 'AÃ' in c.upper()]
        if col_año:
            df_inv = df_inv.rename(columns={col_año[0]: 'AÑO'})
            
        if 'AÑO' in df_inv.columns:
            df_inv['AÑO'] = pd.to_numeric(df_inv['AÑO'], errors='coerce').fillna(0).astype(int)
            
        if 'DEPARTAMENTO' in df_inv.columns:
            df_inv['DEPARTAMENTO'] = df_inv['DEPARTAMENTO'].astype(str).str.strip().str.upper()
            df_inv['DEPARTAMENTO'] = df_inv['DEPARTAMENTO'].str.replace('BAÃ\x91O', 'BAÑO', regex=False)
            
        if 'DescrLineaNegocio' in df_inv.columns:
            df_inv['CATEGORIA'] = df_inv['DescrLineaNegocio'].astype(str).str.strip().str.upper()
            
        if 'MES' in df_inv.columns:
            df_inv['MES'] = df_inv['MES'].astype(str).str.strip().str.upper()
            
        if 'NOMBRE DE ALMACEN' in df_inv.columns:
            df_inv['SUCURSAL'] = df_inv['NOMBRE DE ALMACEN'].astype(str).str.upper().str.strip()
            df_inv['SUCURSAL'] = df_inv['SUCURSAL'].str.replace('TIENDA ', '', regex=False)
            df_inv['SUCURSAL'] = df_inv['SUCURSAL'].str.replace('SUCURSAL ', '', regex=False)
            
        if 'Valor' in df_inv.columns:
            df_inv['Valor'] = (
                df_inv['Valor']
                .astype(str)
                .str.replace(r'\s+', '', regex=True)
                .str.replace('.', '', regex=False)
                .str.replace(',', '.', regex=False)
            )
            df_inv['Valor'] = pd.to_numeric(df_inv['Valor'], errors='coerce').fillna(0.0)
        return df_inv
    except Exception:
        return pd.DataFrame()

df, df_m2 = cargar_datos()

if df.empty:
    st.error("No se pudo cargar la base de datos de Ventas. Revisa la conexión o el archivo.")
    st.stop()

df_inv = cargar_inventario()

df = df.rename(columns={
    'ImporteDivisaPrincipal': 'VENTA',
    'DescrLineaNegocio': 'CATEGORIA',
    'Nombre': 'SUCURSAL'
})

if 'CATEGORIA' in df.columns:
    df['CATEGORIA'] = df['CATEGORIA'].astype(str).str.strip().str.upper()

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
    df['SUCURSAL'] = pd.Categorical(df['SUCURSAL'], categories=[s.upper() for s in orden_sucursales], ordered=True)
if 'DEPARTAMENTO' in df.columns:
    df['DEPARTAMENTO'] = pd.Categorical(df['DEPARTAMENTO'], categories=orden_departamentos, ordered=True)


# -----------------------------------
# FILTROS LATERALES SIMPLES Y ROBUSTOS
# -----------------------------------
st.sidebar.header("Filtros de Análisis")

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
    with st.expander("📊 ANÁLISIS - KPIs DE VENTAS", expanded=True):
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("VENTAS TOTALES", "$ 0,00")
        col2.metric("META FIJADA (X2)", "$ 0,00")
        col3.metric("PORCENTAJE DE AVANCE", "0,00 %")
        col4.metric("EFICIENCIA EXHIBICION FRONTAL (VENTA/M2)", "$ 0,00")
        col5.metric("COBERTURA DE INVENTARIO", "Sin data de inventario")
        
    st.markdown("---")
    st.warning("⚠️ Debes seleccionar al menos un Mes, una Sucursal y un Departamento en la barra lateral para poder generar el reporte.")
    st.stop()

mask_mes = df['MES'].astype(str).isin(meses_sel)
mask_sucursal = df['SUCURSAL'].astype(str).isin(sucursal_sel)
mask_depto = df['DEPARTAMENTO'].astype(str).isin(departamentos_sel)

mask_comun = mask_mes & mask_sucursal & mask_depto
df_filtrado = df[(df['AÑO'] == int(año_sel)) & mask_comun]

try:
    df_año_anterior = df[(df['AÑO'] == (int(año_sel) - 1)) & mask_comun]
except ValueError:
    df_año_anterior = pd.DataFrame()


# --- FILTROS COBERTURA MULTI-MES (LÓGICA ACTUALIZADA) ---
df_inv_filtrado = pd.DataFrame()
df_venta_mes_ant = pd.DataFrame()

if not df_inv.empty and 'AÑO' in df_inv.columns and 'DEPARTAMENTO' in df_inv.columns and 'MES' in df_inv.columns:
    # 1. Aplicar filtros al inventario base
    mask_inv_comun = (df_inv['AÑO'] == int(año_sel)) & (df_inv['DEPARTAMENTO'].isin(departamentos_sel))
    if 'SUCURSAL' in df_inv.columns:
        mask_inv_comun &= df_inv['SUCURSAL'].isin(sucursal_sel)
        
    df_inv_base = df_inv[mask_inv_comun]
    meses_validos_inv = [m for m in orden_meses if m in meses_sel and m in df_inv_base['MES'].unique()]
    
    if meses_validos_inv:
        # El inventario será del ÚLTIMO mes seleccionado disponible
        ultimo_mes_existente = meses_validos_inv[-1]
        df_inv_filtrado = df_inv_base[df_inv_base['MES'] == ultimo_mes_existente]
        
        # 2. Consolidar ventas de TODOS los meses anteriores a los seleccionados
        frames_ant = []
        for m_sel in meses_sel:
            idx = orden_meses.index(m_sel)
            if idx > 0:
                m_ant = orden_meses[idx - 1]
                a_ant = int(año_sel)
            else:
                m_ant = 'DICIEMBRE'
                a_ant = int(año_sel) - 1
                
            frame_ventas = df[(df['AÑO'] == a_ant) & (df['MES'] == m_ant) & mask_sucursal & mask_depto]
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

if not df_año_anterior.empty and 'DEPARTAMENTO' in df_año_anterior.columns and 'CATEGORIA' in df_año_anterior.columns:
    tabla_ant = df_año_anterior.groupby(['DEPARTAMENTO', 'CATEGORIA'], observed=True)['VENTA'].sum().reset_index()
    tabla_ant = tabla_ant.rename(columns={'VENTA': 'META'})
    tabla_ant['META'] = tabla_ant['META'] * 2
else:
    tabla_ant = pd.DataFrame(columns=['DEPARTAMENTO', 'CATEGORIA', 'META'])

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
    
    # Formula real: Inventario del último mes cargado / Suma total de las ventas anteriores
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
        return ['font-weight: bold; background-color: #A7F3D0; color: #047857; border-top: 2px double #047857; border-bottom: 2px double #047857;'] * len(row)
    elif row['CATEGORÍA'] == 'TOTAL DEPARTAMENTO':
        return ['font-weight: bold; background-color: #D1FAE5; color: #065F46; border-bottom: 2px solid #10B981;'] * len(row)
    return ['background-color: #FFFFFF; color: #1F2937; border-bottom: 1px solid #E5E7EB;'] * len(row)

tabla_estilizada = (
    df_render_app.style
    .apply(aplicar_colores_matriz, axis=1)
    .set_properties(**{'text-align': 'right', 'font-family': 'Arial'})
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
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor('#1E3A8A'), spaceAfter=8)
    subtitle_style = ParagraphStyle('SubStyle', parent=styles['Normal'], fontSize=9, leading=13, textColor=colors.HexColor('#4B5563'), spaceAfter=12)
    header_table_style = ParagraphStyle('HeaderTable', parent=styles['Normal'], fontSize=8, leading=11, fontName='Helvetica-Bold', textColor=colors.white, alignment=1)
    cell_table_style = ParagraphStyle('CellTable', parent=styles['Normal'], fontSize=8, leading=10, alignment=2)
    cell_total_style = ParagraphStyle('CellTotal', parent=styles['Normal'], fontSize=8, leading=10, fontName='Helvetica-Bold', alignment=2)
    
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
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]
    
    for i, row in enumerate(dataframe.values):
        idx_fila = i + 1
        es_total_general = (row[0] == 'TOTAL GENERAL')
        es_subtotal = (row[1] == 'TOTAL DEPARTAMENTO')
        
        style_actual = cell_total_style if (es_subtotal or es_total_general) else cell_table_style
        
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
            estilos_celdas.append(('BACKGROUND', (0, idx_fila), (-1, idx_fila), colors.HexColor('#A7F3D0')))
            estilos_celdas.append(('TEXTCOLOR', (0, idx_fila), (-1, idx_fila), colors.HexColor('#047857')))
        elif es_subtotal:
            estilos_celdas.append(('BACKGROUND', (0, idx_fila), (-1, idx_fila), colors.HexColor('#D1FAE5')))
            estilos_celdas.append(('TEXTCOLOR', (0, idx_fila), (-1, idx_fila), colors.HexColor('#065F46')))
            
    pdf_table = Table(data_tabla, colWidths=[110, 110, 85, 85, 65, 115, 115])
    pdf_table.setStyle(TableStyle(estilos_celdas))
    story.append(pdf_table)
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

with st.expander("📊 ANÁLISIS - KPIs DE VENTAS", expanded=True):
    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("VENTAS TOTALES", formatear_moneda(total_ventas))
    col2.metric("META FIJADA (X2)", formatear_moneda(meta_dinamica_total))
    col3.metric("PORCENTAJE DE AVANCE", formatear_porcentaje(avance_general))
    col4.metric("EFICIENCIA EXHIBICION FRONTAL (VENTA/M2)", formatear_moneda(eficiencia_total))
    col5.metric("COBERTURA DE INVENTARIO", formatear_cobertura(total_g_cobertura))

    st.markdown("---")
    
    st.dataframe(tabla_estilizada, use_container_width=True, height=530, hide_index=True)

    st.markdown("### 📥 MENÚ DE DESCARGA DE REPORTES")
    st.info("El informe de Excel se descarga libre de filas de subtotales y con codificación contable nativa de miles/decimales, permitiéndote realizar operaciones matemáticas al instante.")
    
    bot1, bot2 = st.columns(2)
    
    data_excel = generar_excel_descarga_sumable(df_para_excel)
    bot1.download_button(
        label="🟩 Descargar Reporte en Excel (Sumable)",
        data=data_excel,
        file_name=f"Reporte_Comercial_{año_sel}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
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
        label="🟦 Descargar Reporte Completo en PDF",
        data=data_pdf,
        file_name=f"Reporte_Comercial_{año_sel}.pdf",
        mime="application/pdf",
        use_container_width=True
    )