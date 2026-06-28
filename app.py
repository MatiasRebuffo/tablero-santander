import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración de página y estética
st.set_page_config(page_title="Besser Weiss - Dashboard", layout="wide", initial_sidebar_state="expanded")

# CSS personalizado para mejorar el look
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
    # Los filtros se poblarán una vez cargados los datos

# --- LÓGICA DE PROCESAMIENTO ---
if archivo_base and archivo_pagos and archivo_gestiones:
    # Carga de datos
    df_base = pd.read_excel(archivo_base)
    df_pagos = pd.read_excel(archivo_pagos)
    df_gestiones = pd.read_excel(archivo_gestiones)
    
    # Estandarizar columnas
    for df in [df_base, df_pagos, df_gestiones]:
        df.columns = df.columns.str.upper().str.strip()

    # Procesar fechas
    df_gestiones['FECHA_DT'] = pd.to_datetime(df_gestiones['FECHA'], errors='coerce')
    # Supongamos que Pagos tiene una columna FECHA_PAGO o similar. Si no, usa FECHA.
    col_fecha_pago = 'FECHA' if 'FECHA' in df_pagos.columns else df_pagos.columns[0]
    df_pagos['FECHA_PAGO_DT'] = pd.to_datetime(df_pagos[col_fecha_pago], errors='coerce')

    # Unión de datos
    df_cruce = pd.merge(df_base, df_pagos, on='DOCUMENTO', how='left')

    # --- CONFIGURACIÓN DE FILTROS EN SIDEBAR ---
    with st.sidebar:
        # Filtro Gestores
        lista_gestores = sorted(df_gestiones['GESTOR'].dropna().unique())
        gestores_sel = st.multiselect("Gestores", options=lista_gestores, default=lista_gestores)
        
        # Filtro Fechas de Pago
        min_date = df_pagos['FECHA_PAGO_DT'].min().date()
        max_date = df_pagos['FECHA_PAGO_DT'].max().date()
        rango_fecha = st.date_input("Rango de Pagos", [min_date, max_date])
        
        # Filtro Estado (Si existe columna ESTADO en base)
        col_estado = 'ESTADO' if 'ESTADO' in df_base.columns else None
        if col_estado:
            lista_estados = sorted(df_base[col_estado].dropna().unique())
            estados_sel = st.multiselect("Estado", options=lista_estados, default=lista_estados)

    # --- APLICAR FILTROS ---
    df_gestiones_f = df_gestiones[df_gestiones['GESTOR'].isin(gestores_sel)]
    
    mask_pagos = (df_pagos['FECHA_PAGO_DT'].dt.date >= rango_fecha[0]) & (df_pagos['FECHA_PAGO_DT'].dt.date <= rango_fecha[1])
    df_pagos_f = df_pagos[mask_pagos]
    
    df_final_f = df_cruce[df_cruce['DOCUMENTO'].isin(df_base['DOCUMENTO'])] # Simplificado para el ejemplo
    if col_estado:
        df_final_f = df_final_f[df_final_f[col_estado].isin(estados_sel)]

    # --- CUERPO PRINCIPAL ---
    st.title("📊 Dashboard Besser Weiss")
    
    # 1. Kpis (Tarjetas)
    m1, m2, m3, m4 = st.columns(4)
    total_recaudado = df_pag_f := df_pagos_f['IMPORTE'].sum() if 'IMPORTE' in df_pagos_f.columns else 0
    m1.metric("Total Recaudado", f"${total_recaudado:,.0f}")
    m2.metric("Gestiones Totales", f"{len(df_gestiones_f):,}")
    m3.metric("Clientes Únicos", f"{df_gestiones_f['DOCUMENTO'].nunique():,}")
    m4.metric("Promedio Gestión", f"{(len(df_gestiones_f)/df_gestiones_f['DOCUMENTO'].nunique() if len(df_gestiones_f)>0 else 0):.1f}")

    st.write("---")

    # 2. Gráficos
    g1, g2 = st.columns([6, 4])
    
    with g1:
        st.subheader("📈 Evolución de Pagos (Timeline)")
        pagos_serie = df_pagos_f.groupby('FECHA_PAGO_DT')['IMPORTE'].sum().reset_index()
        fig_line = px.area(pagos_serie, x='FECHA_PAGO_DT', y='IMPORTE', 
                           template="plotly_dark", color_discrete_sequence=['#00f2ff'])
        fig_line.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=300)
        st.plotly_chart(fig_line, use_container_width=True)

    with g2:
        st.subheader("🏆 Rendimiento por Gestor")
        gestor_perf = df_gestiones_f.groupby('GESTOR').size().reset_index(name='GESTIONES').sort_values('GESTIONES', ascending=False).head(10)
        fig_bar = px.bar(gestor_perf, x='GESTIONES', y='GESTOR', orientation='h',
                         template="plotly_dark", color_discrete_sequence=['#5865f2'])
        fig_bar.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=300)
        st.plotly_chart(fig_bar, use_container_width=True)

    st.write("---")

    # 3. Tablas Dinámicas (Tus tablas de siempre)
    st.header("📋 Detalle de Productividad")
    tab1, tab2 = st.tabs(["💬 Casos Totales", "👤 Casos Únicos"])
    
    with tab1:
        din_tot = pd.pivot_table(df_gestiones_f, index='GESTOR', columns='FECHA_DT', values='CUENTA', 
                                aggfunc='count', margins=True, margins_name='Total general').fillna(0).astype(int)
        din_tot.columns = [c.strftime('%d/%m') if isinstance(c, pd.Timestamp) else c for c in din_tot.columns]
        st.dataframe(din_tot, use_container_width=True)

    with tab2:
        din_uni = pd.pivot_table(df_gestiones_f, index='GESTOR', columns='FECHA_DT', values='CUENTA', 
                                aggfunc='nunique', margins=True, margins_name='Total general').fillna(0).astype(int)
        din_uni.columns = [c.strftime('%d/%m') if isinstance(c, pd.Timestamp) else c for c in din_uni.columns]
        st.dataframe(din_uni, use_container_width=True)

else:
    st.image("https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&q=80&w=1000", use_container_width=True)
    st.warning("⚠️ Esperando carga de archivos en el panel de la izquierda para generar el reporte Besser Weiss.")
