import streamlit as st
import pandas as pd

# Configuramos la página para que se vea ancha y linda
st.set_page_config(page_title="Tablero Santander", layout="wide")

st.title("📊 Tablero de Control de Cobranzas - Santander")
st.markdown("Subí los tres archivos crudos del CRM para actualizar las métricas y dinámicas al instante.")

# Forzamos formato plata para los datos que muestre Pandas
pd.options.display.float_format = '${:,.2f}'.format

# 1. Creamos la barra lateral para subir los archivos
st.sidebar.header("📁 Carga de Archivos Crudos")
archivo_base = st.sidebar.file_uploader("1. Subir BASE SANTANDER (Excel)", type=["xlsx"])
archivo_pagos = st.sidebar.file_uploader("2. Subir PAGOS (Excel)", type=["xlsx"])
archivo_gestiones = st.sidebar.file_uploader("3. Subir GESTIONES (Excel)", type=["xlsx"])

# 2. Si el usuario subió los 3 archivos, arranca el proceso automático
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

        # --- SECCIÓN 2: FILTRO DE GESTORES ---
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

        # Validamos que al menos haya un gestor seleccionado para no romper las tablas
        if not gestores_seleccionados:
            st.warning("⚠️ Por favor, seleccioná al menos un gestor en el cuadro de arriba para mostrar los resultados.")
        else:
            # Filtramos el DataFrame original según lo que eligió el usuario
            df_gestiones_filtrado = df_gestiones[df_gestiones['GESTOR'].isin(gestores_seleccionados)]

            # Dinámica 1: Casos Totales (con la base filtrada)
            dinamica_totales = pd.pivot_table(
                df_gestiones_filtrado, index='GESTOR', columns='FECHA_DT', values='CUENTA', aggfunc='count',
                margins=True, margins_name='Total general'
            ).fillna(0).astype(int)
            dinamica_totales.columns = [col.strftime('%d/%m/%Y') if isinstance(col, pd.Timestamp) else col for col in dinamica_totales.columns]

            # Dinámica 2: Casos Únicos (con la base filtrada)
            dinamica_unicos = pd.pivot_table(
                df_gestiones_filtrado, index='GESTOR', columns='FECHA_DT', values='CUENTA', aggfunc='nunique',
                margins=True, margins_name='Total general'
            ).fillna(0).astype(int)
            dinamica_unicos.columns = [col.strftime('%d/%m/%Y') if isinstance(col, pd.Timestamp) else col for col in dinamica_unicos.columns]

            st.write("---")
            st.header("📈 Reporte de Productividad de Gestores")
            
            # Creamos solapas para cambiar entre Totales y Únicos limpiamente
            tab1, tab2 = st.tabs(["💬 Casos Totales (Llamadas)", "👤 Casos Únicos (Cuentas Tocadas)"])
            
            with tab1:
                st.subheader("Evolución Diaria - Gestiones Hechas")
                st.dataframe(dinamica_totales, use_container_width=True)
                
            with tab2:
                st.subheader("Evolución Diaria - Clientes Únicos Contactados")
                st.dataframe(dinamica_unicos, use_container_width=True)

else:
    # Mensaje de bienvenida si todavía falta subir algún archivo
    st.info("👋 ¡Todo listo! Por favor, arrastrá los 3 archivos de Excel en el menú de la izquierda para ver la magia.")
