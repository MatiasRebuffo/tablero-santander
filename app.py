import streamlit as st
import pandas as pd

# Configuramos la página para que se vea ancha y linda
st.set_page_config(page_title="Tablero Santander - Besser Weiss", layout="wide")

# --- TRUCO CSS MAXIMO PARA ELIMINAR EL ESPACIO SUPERIOR ---
st.markdown("""
    <style>
    /* Remueve el espacio de arriba de toda la barra lateral */
    [data-testid="stSidebarContent"] > div:first-child {
        padding-top: 0rem !important;
    }
    [data-testid="stSidebarUserContent"] {
        padding-top: 0rem !important;
        margin-top: -40px !important; /* Fuerza a subir el contenido */
    }
    /* Elimina cualquier espacio extra de la imagen */
    [data-testid="stSidebarUserContent"] img {
        margin-top: 0px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- BARRA LATERAL (SIDEBAR) ---
try:
    st.sidebar.image("image_3f4829.png", use_container_width=True)
except:
    st.sidebar.header("🛡️ Besser Weiss")

st.sidebar.header("📁 Carga de Archivos Crudos")
# ... (El resto de tu código con los file_uploader y las tablas sigue igual abajo)
