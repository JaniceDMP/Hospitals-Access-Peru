#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# app.py

import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Análisis de Acceso a Hospitales en Perú",
    page_icon="🏥",
    layout="wide"
)

st.title("🏥 Acceso a Infraestructura Hospitalaria en Perú")

# --- 2. CREACIÓN DE LAS PESTAÑAS (TABS) ---
tab1, tab2, tab3 = st.tabs([
    "🗂️ **Descripción de Datos**",
    "🗺️ **Mapas Estáticos y Análisis Departamental**",
    "🌍 **Mapas Dinámicos e Interactivos**"
])

# --- PESTAÑA 1: DESCRIPCIÓN ---
with tab1:
    st.header("Metodología y Fuentes de Datos")
    st.markdown("""
    Esta aplicación presenta un análisis sobre la accesibilidad a hospitales públicos en Perú,
    utilizando datos abiertos para generar visualizaciones estáticas e interactivas.
    """)
    st.info("""
    - **Unidad de análisis**: Hospitales públicos operativos en Perú.
    - **Fuentes**: MINSA-IPRESS, INEI (Centros Poblados), IGN (Límites Distritales).
    - **Reglas**: Solo hospitales 'EN FUNCIONAMIENTO' con coordenadas válidas.
    """)

# --- PESTAÑA 2: ANÁLISIS DEPARTAMENTAL Y MAPAS ESTÁTICOS ---
with tab2:
    st.header("Análisis a Nivel Departamental")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Tabla Resumen por Departamento")
        
        try:
            df_summary = pd.read_csv("data/tabla_resumen_departamentos.csv")
            st.dataframe(df_summary.set_index('Departamento'), height=600)
        except FileNotFoundError:
            st.error("Asegúrate de tener el archivo 'tabla_resumen_departamentos.csv' en la carpeta 'data/'.")

    with col2:
        st.subheader("Gráfico de Barras")
        # --- ADAPTAR AQUÍ ---
        # Carga tu gráfico de barras pre-generado.
        # Asegúrate de que la imagen esté en la carpeta 'assets/'.
        try:
            st.image("assets/grafico_barras_departamentos.png", caption="Número de Hospitales Operativos por Departamento.")
        except FileNotFoundError:
            st.error("Asegúrate de tener la imagen 'grafico_barras_departamentos.png' en la carpeta 'assets/'.")

    st.divider()
    st.header("Mapas Estáticos a Nivel Distrital")

    col_map1, col_map2, col_map3 = st.columns(3)

    with col_map1:
        st.subheader("Total de hospitales por distrito")
        # --- ADAPTAR AQUÍ ---
        try:
            st.image("assets/mapa_distrital_total.png")
        except FileNotFoundError:
            st.error("Asegúrate de tener la imagen 'mapa_distrital_total.png' en la carpeta 'assets/'.")

    with col_map2:
        st.subheader("Distritos sin hospitales")
        # --- ADAPTAR AQUÍ ---
        try:
            st.image("assets/mapa_distrital_cero.png")
        except FileNotFoundError:
            st.error("Asegúrate de tener la imagen 'mapa_distrital_cero.png' en la carpeta 'assets/'.")

    with col_map3:
        st.subheader("Top 10 distritos")
        # --- ADAPTAR AQUÍ ---
        try:
            st.image("assets/mapa_distrital_top10.png")
        except FileNotFoundError:
            st.error("Asegúrate de tener la imagen 'mapa_distrital_top10.png' en la carpeta 'assets/'.")


# --- PESTAÑA 3: MAPAS DINÁMICOS (FOLIUM) ---
with tab3:
    st.header("Mapa Nacional Interactivo de Hospitales")

    # --- ADAPTAR AQUÍ ---
    # Carga tu mapa nacional de Folium desde un archivo HTML.
    # Asegúrate de que el archivo esté en la carpeta 'html_maps/'.
    try:
        with open("html_maps/mapa_nacional_folium.html", 'r', encoding='utf-8') as f:
            mapa_nacional_html = f.read()
        components.html(mapa_nacional_html, height=600)
    except FileNotFoundError:
        st.error("Asegúrate de tener el archivo 'mapa_nacional_folium.html' en la carpeta 'html_maps/'.")

    st.divider()
    st.header("Análisis de Proximidad en Lima y Loreto")

    col_lima, col_loreto = st.columns(2)

    with col_lima:
        st.subheader("Proximidad en Lima")
        # --- ADAPTAR AQUÍ ---
        try:
            with open("html_maps/proximidad_lima.html", 'r', encoding='utf-8') as f:
                mapa_lima_html = f.read()
            components.html(mapa_lima_html, height=500)
        except FileNotFoundError:
            st.error("Asegúrate de tener el archivo 'proximidad_lima.html' en la carpeta 'html_maps/'.")

    with col_loreto:
        st.subheader("Proximidad en Loreto")
        # --- ADAPTAR AQUÍ ---
        try:
            with open("html_maps/proximidad_loreto.html", 'r', encoding='utf-8') as f:
                mapa_loreto_html = f.read()
            components.html(mapa_loreto_html, height=500)
        except FileNotFoundError:
            st.error("Asegúrate de tener el archivo 'proximidad_loreto.html' en la carpeta 'html_maps/'.")

