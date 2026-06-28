import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Configuramos la página para que se vea ancha y linda
st.set_page_config(page_title="Tablero Santander - Besser Weiss", layout="wide")

# --- TRUCO CSS PARA PEGAR LA IMAGEN BIEN ARRIBA ---
st.markdown("""
    <style>
    /* Quita el espacio vacío del contenedor de la barra lateral */
    [data-testid="stSidebarContent"] > div:first-child {
        padding-top: 0rem !important;
    }
    [data-testid="stSidebarUserContent"] {
        padding-top: 0rem !important;
        margin-top: -35px !important; /* Fuerza a la imagen a subir */
    }
    </style>
    """, unsafe_allow_html=True)

# --- BARRA LATERAL (SIDEBAR) ---
try:
    st.sidebar.image("image_3f4829.png", use_container_width=True)
except:
    st.sidebar.header("🛡️ Besser Weiss")

st.sidebar.header("📁 Carga de Archivos Crudos")
archivo_base = st.sidebar.file_uploader("1. Subir BASE SANTANDER (Excel)", type=["xlsx"])
archivo_pagos = st.sidebar.file_uploader("2. Subir PAGOS (Excel)", type=["xlsx"])
archivo_gestiones = st.sidebar.file_uploader("3. Subir GESTIONES (Excel)", type=["xlsx"])


# --- CUERPO PRINCIPAL ---
st.title("📊 Tablero de Control de Cobranzas - Santander")
st.markdown("Subí los tres archivos crudos del CRM para actualizar las métricas y dinámicas al instante.")

# Forzamos formato plata para los datos que muestre Pandas
pd.options.display.float_format = '${:,.2f}'.format

# Si el usuario subió los 3 archivos, arranca el proceso automático
if archivo_base and archivo_pagos and archivo_gestiones:
    with st.spinner("Procesando datos y armando tablas..."):
        
        # Leemos los Excels directamente de la memoria de la web
        df_base = pd.read_excel(archivo_base)
        df_pagos = pd.read_excel(archivo_pagos)
        df_gestiones = pd.read_excel(archivo_gestiones)

        # Estandarizamos columnas a mayúsculas
        df_base.columns = df_base.columns.str.upper().str.strip()
        df_pagos.columns = df_pagos.columns.str.upper().str.strip()
        df_gestiones.columns = df_gestiones.columns.str.upper().str.strip()

        # Hacemos el cruce principal
        df_cruce = pd.merge(df_base, df_pagos, on='DOCUMENTO', how='left')

        # --- SECCIÓN 1: METRICAS CLAVE ---
        total_recaudado = df_cruce['IMPORTE'].sum()
        total_clientes_base = df_cruce['DOCUMENTO'].nunique()
        clientes_que_pagaron = df_cruce[df_cruce['IMPORTE'].notna()]['DOCUMENTO'].nunique()

        st.header("📌 Resumen Ejecutivo del Mes")
        
        # Creamos 4 tarjetitas visuales con métricas
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Clientes Totales", f"{total_clientes_base:,}")
        m2.metric("Clientes con Pago", f"{clientes_que_pagaron:,}")
        m3.metric("% Efectividad", f"{(clientes_que_pagaron / total_clientes_base * 100):.2f}%")
        m4.metric("Total Recaudado", f"${total_recaudado:,.2f}")

        # --- NUEVA SECCIÓN: EVOLUCIÓN DIARIA DE PAGOS INTERACTIVA (ESTILO LINE/AREA) ---
        st.write("---")
        st.header("📉 Evolución Diaria de Ingresos (Recaudación)")
        
        col_fecha_pagos = [col for col in df_pagos.columns if 'FECHA' in col]
        
        if col_fecha_pagos:
            nombre_col_fecha = col_fecha_pagos[0]
            # Convertimos a tipo Fecha de forma segura
            df_pagos['FECHA_LIMPIA'] = pd.to_datetime(df_pagos[nombre_col_fecha], errors='coerce')
            
            # Agrupamos los pagos por día sumando los importes y ordenamos cronológicamente
            df_linea_tiempo = df_pagos.groupby('FECHA_LIMPIA')['IMPORTE'].sum().reset_index()
            df_linea_tiempo = df_linea_tiempo.dropna().sort_values('FECHA_LIMPIA')
            
            # Forzamos las fechas a formato texto en español (DD/MM/YYYY) para anular el formato inglés automático
            fechas_espanol = df_linea_tiempo['FECHA_LIMPIA'].dt.strftime('%d/%m/%Y').tolist()
            valores_recaudados = df_linea_tiempo['IMPORTE'].tolist()
            
            # Construimos el gráfico interactivo usando Plotly para igualar el estilo solicitado
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=fechas_espanol,
                y=valores_recaudados,
                mode='lines+markers',                # Líneas continuas con puntos marcadores
                line=dict(shape='spline', width=3, color='#1f77b4'), # 'spline' suaviza la curva como la imagen
                marker=dict(size=8, color='#ffffff', line=dict(color='#1f77b4', width=2)), # Círculos rellenos
                fill='tozeroy',                      # Pinta el área de fondo hasta el eje cero
                fillcolor='rgba(31, 119, 180, 0.15)', # Azul translúcido y sutil para el sombreado
                name='Recaudación Diaria'
            ))
            
            # Ajustamos la estética general del gráfico para que se asimile al entorno oscuro/limpio
            fig.update_layout(
                margin=dict(l=40, r=40, t=20, b=40),
                hovermode="x unified",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(
                    showgrid=False,
                    tickmode='linear',
                    tickangle=-45,
                    type='category' # Forzado a categoría para respetar estrictamente las cadenas de texto del eje X
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(255,255,255,0.05)', # Grilla horizontal muy sutil
                    tickformat="$,"                     # Formato de dinero en el eje Y
                ),
                showlegend=False,
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("ℹ️ No se detectó una columna con la palabra 'FECHA' en el archivo de pagos para armar la línea de tiempo.")


        # --- SECCIÓN 3: FILTRO DE GESTORES ---
        df_gestiones['FECHA_DT'] = pd.to_datetime(df_gestiones['FECHA'], errors='coerce')

        st.write("---")
        st.header("🔍 Filtros de Visualización")
        
        # Extraemos la lista única de gestores ordenados alfabéticamente
        lista_gestores = sorted(df_gestiones['GESTOR'].dropna().unique())
        
        # Creamos el componente de selección múltiple
        gestores_seleccionados = st.multiselect(
            "Seleccioná los gestores que querés ver en las tablas (borrá o agregá nombres):",
            options=lista_gestores,
            default=lista_gestores  # Por defecto arranca con todos marcados
        )

        if not gestores_seleccionados:
            st.warning("⚠️ Por favor, seleccioná al menos un gestor en el cuadro de arriba para mostrar los resultados.")
        else:
            df_gestiones_filtrado = df_gestiones[df_gestiones['GESTOR'].isin(gestores_seleccionados)]

            # Dinámica 1: Casos Totales
            dinamica_totales = pd.pivot_table(
                df_gestiones_filtrado, index='GESTOR', columns='FECHA_DT', values='CUENTA', aggfunc='count',
                margins=True, margins_name='Total general'
            ).fillna(0).astype(int)
            dinamica_totales.columns = [col.strftime('%d/%m/%Y') if isinstance(col, pd.Timestamp) else col for col in dinamica_totales.columns]

            # Dinámica 2: Casos Únicos
            dinamica_unicos = pd.pivot_table(
                df_gestiones_filtrado, index='GESTOR', columns='FECHA_DT', values='CUENTA', aggfunc='nunique',
                margins=True, margins_name='Total general'
            ).fillna(0).astype(int)
            dinamica_unicos.columns = [col.strftime('%d/%m/%Y') if isinstance(col, pd.Timestamp) else col for col in dinamica_unicos.columns]

            st.write("---")
            st.header("📈 Reporte de Productividad de Gestores")
            
            tab1, tab2 = st.tabs(["💬 Casos Totales (Llamadas)", "👤 Casos Únicos (Cuentas Tocadas)"])
            
            with tab1:
                st.subheader("Evolución Diaria - Gestiones Hechas")
                st.dataframe(dinamica_totales, use_container_width=True)
                
            with tab2:
                st.subheader("Evolución Diaria - Clientes Únicos Contactados")
                st.dataframe(dinamica_unicos, use_container_width=True)

else:
    st.info("👋 ¡Todo listo! Por favor, arrastrá los 3 archivos de Excel en el menú de la izquierda para ver la magia.")
