import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración de página y estética corporativa
st.set_page_config(page_title="Besser Weiss - Dashboard", layout="wide", initial_sidebar_state="expanded")

# CSS personalizado para mejorar el look a modo oscuro premium
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    [data-testid="stSidebar"] { background-color: #0d1117; border-right: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR (CARGA Y FILTROS) ---
with st.sidebar:
    st.title("🛡️ Besser Weiss")
    st.subheader("📁 Carga de Datos")
    archivo_base = st.file_uploader("Base Santander", type=["xlsx"])
    archivo_pagos = st.file_uploader("Pagos", type=["xlsx"])
    archivo_gestiones = st.file_uploader("Gestiones", type=["xlsx"])
    
    st.write("---")
    st.subheader("🎯 Filtros")

# --- LÓGICA DE PROCESAMIENTO ---
if archivo_base and archivo_pagos and archivo_gestiones:
    # Carga de datos
    df_base = pd.read_excel(archivo_base)
    df_pagos = pd.read_excel(archivo_pagos)
    df_gestiones = pd.read_excel(archivo_gestiones)
    
    # Estandarizar columnas a mayúsculas
    for df in [df_base, df_pagos, df_gestiones]:
        df.columns = df.columns.str.upper().str.strip()

    # Procesar fechas de gestiones y pagos
    df_gestiones['FECHA_DT'] = pd.to_datetime(df_gestiones['FECHA'], errors='coerce')
    col_fecha_pago = 'FECHA' if 'FECHA' in df_pagos.columns else df_pagos.columns[0]
    df_pagos['FECHA_PAGO_DT'] = pd.to_datetime(df_pagos[col_fecha_pago], errors='coerce')

    # Unión de datos principal
    df_cruce = pd.merge(df_base, df_pagos, on='DOCUMENTO', how='left')

    # --- CONFIGURACIÓN DE FILTROS EN SIDEBAR ---
    with st.sidebar:
        # Filtro Gestores
        lista_gestores = sorted(df_gestiones['GESTOR'].dropna().unique())
        gestores_sel = st.multiselect("Gestores", options=lista_gestores, default=lista_gestores)
        
        # Filtro Rango de Fechas de Pago
        min_date = df_pagos['FECHA_PAGO_DT'].min().date()
        max_date = df_pagos['FECHA_PAGO_DT'].max().date()
        rango_fecha = st.date_input("Rango de Pagos", [min_date, max_date])
        
        # Filtro Estado (Si existe columna ESTADO en tu base)
        col_estado = 'ESTADO' if 'ESTADO' in df_base.columns else None
        if col_estado:
            lista_estados = sorted(df_base[col_estado].dropna().unique())
            estados_sel = st.multiselect("Estado", options=lista_estados, default=lista_estados)

    # --- APLICAR FILTROS ---
    df_gestiones_f = df_gestiones[df_gestiones['GESTOR'].isin(gestores_sel)]
    
    # Controlamos que el rango de fechas esté bien seleccionado
    if isinstance(rango_fecha, (list, tuple)) and len(rango_fecha) == 2:
        mask_pagos = (df_pagos['FECHA_PAGO_DT'].dt.date >= rango_fecha[0]) & (df_pagos['FECHA_PAGO_DT'].dt.date <= rango_fecha[1])
        df_pagos_f = df_pagos[mask_pagos]
    else:
        df_pagos_f = df_pagos
        
    # --- CUERPO PRINCIPAL ---
    st.title("📊 Dashboard Besser Weiss")
    
    # 1. Kpis (Tarjetas de totales superiores)
    m1, m2, m3, m4 = st.columns(4)
    total_recaudado = df_pagos_f['IMPORTE'].sum() if 'IMPORTE' in df_pagos_f.columns else 0
    m1.metric("Total Recaudado", f"${total_recaudado:,.0f}")
    m2.metric("Gestiones Totales", f"{len(df_gestiones_f):,}")
    m3.metric("Clientes Únicos", f"{df_gestiones_f['DOCUMENTO'].nunique():,}")
    m4.metric("Promedio Gestión", f"{(len(df_gestiones_f)/df_gestiones_f['DOCUMENTO'].nunique() if df_gestiones_f['DOCUMENTO'].nunique() > 0 else 0):.1f}")

    st.write("---")

    # 2. Bloque de Gráficos Interactivos
    g1, g2 = st.columns([6, 4])
    
    with g1:
        st.subheader("📈 Evolución de Pagos (Timeline)")
        if not df_pagos_f.empty and 'IMPORTE' in df_pagos_f.columns:
            pagos_serie = df_pagos_f.groupby('FECHA_PAGO_DT')['IMPORTE'].sum().reset_index()
            fig_line = px.area(pagos_serie, x='FECHA_PAGO_DT', y='IMPORTE', 
                               template="plotly_dark", color_discrete_sequence=['#00f2ff'])
            fig_line.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=300)
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("No hay datos de pagos para este rango.")

    with g2:
        st.subheader("🏆 Rendimiento por Gestor")
        if not df_gestiones_f.empty:
            gestor_perf = df_gestiones_f.groupby('GESTOR').size().reset_index(name='GESTIONES').sort_values('GESTIONES', ascending=False).head(10)
            fig_bar = px.bar(gestor_perf, x='GESTIONES', y='GESTOR', orientation='h',
                             template="plotly_dark", color_discrete_sequence=['#5865f2'])
            fig_bar.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=300)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No hay datos de gestiones.")

    st.write("---")

    # 3. Tablas Dinámicas (Tus cuadros clásicos al final)
    st.header("📋 Detalle de Productividad")
    tab1, tab2 = st.tabs(["💬 Casos Totales", "👤 Casos Únicos"])
    
    with tab1:
        if not df_gestiones_f.empty:
            din_tot = pd.pivot_table(df_gestiones_f, index='GESTOR', columns='FECHA_DT', values='CUENTA', 
                                    aggfunc='count', margins=True, margins_name='Total general').fillna(0).astype(int)
            din_tot.columns = [c.strftime('%d/%m') if isinstance(c, pd.Timestamp) else c for c in din_tot.columns]
            st.dataframe(din_tot, use_container_width=True)
        else:
            st.info("Seleccioná al menos un gestor para armar la tabla.")

    with tab2:
        if not df_gestiones_f.empty:
            din_uni = pd.pivot_table(df_gestiones_f, index='GESTOR', columns='FECHA_DT', values='CUENTA', 
                                    aggfunc='nunique', margins=True, margins_name='Total general').fillna(0).astype(int)
            din_uni.columns = [c.strftime('%d/%m') if isinstance(c, pd.Timestamp) else c for c in din_uni.columns]
            st.dataframe(din_uni, use_container_width=True)
        else:
            st.info("Seleccioná al menos un gestor para armar la tabla.")

else:
    # Portada estética de espera
    st.image("https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&q=80&w=1000", use_container_width=True)
    st.warning("⚠️ Esperando carga de archivos en el panel de la izquierda para generar el reporte Besser Weiss.")
