#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# app.py

import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster
import matplotlib.pyplot as plt
from streamlit_folium import st_folium

# --------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE LA PÁGINA
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Análisis de Acceso a Hospitales en Perú",
    page_icon="🏥",
    layout="wide"
)

st.title("🏥 Acceso a Infraestructura Hospitalaria en Perú")
st.markdown("Análisis geoespacial de la distribución de hospitales públicos operativos y su accesibilidad desde centros poblados.")

# --------------------------------------------------------------------------
# 2. CARGA Y CACHÉ DE DATOS
# --------------------------------------------------------------------------
# Usamos @st.cache_data para que los datos se carguen una sola vez.
@st.cache_data
def load_and_prepare_data():
    # --- Carga de Hospitales (IPRESS) ---
    try:
        ipress_df = pd.read_csv('data/IPRESS.csv', encoding='utf-8')
    except UnicodeDecodeError:
        ipress_df = pd.read_csv('data/IPRESS.csv', encoding='latin1')

    # Filtrado según requisitos:
    # a) Solo hospitales operativos ('EN FUNCIONAMIENTO')
    hp_df = ipress_df[ipress_df['Situación'] == 'EN FUNCIONAMIENTO'].copy()

    # b) Limpieza de coordenadas y eliminación de registros inválidos
    hp_df['LATITUD'] = pd.to_numeric(hp_df['NORTE'], errors='coerce')
    hp_df['LONGITUD'] = pd.to_numeric(hp_df['ESTE'], errors='coerce')
    hp_df.dropna(subset=['LATITUD', 'LONGITUD'], inplace=True)
    hp_df = hp_df[hp_df['LATITUD'].between(-18.5, 0)]
    hp_df = hp_df[hp_df['LONGITUD'].between(-81.5, -68.5)]

    # c) Convertir a GeoDataFrame
    hp_gdf = gpd.GeoDataFrame(
        hp_df,
        geometry=gpd.points_from_xy(hp_df['LONGITUD'], hp_df['LATITUD']),
        crs="EPSG:4326"
    )

    # --- Carga de Límites Distritales ---
    distritos_gdf = gpd.read_file('data/DISTRITOS.shp')

    # --- Carga de Centros Poblados ---
    ccpp_gdf = gpd.read_file('data/CCPP_IGN100K.shp')

    return hp_gdf, distritos_gdf, ccpp_gdf

# Ejecutar la carga de datos
with st.spinner('Cargando y procesando datos geoespaciales...'):
    hp_gdf, distritos_gdf, ccpp_gdf = load_and_prepare_data()

# --------------------------------------------------------------------------
# 3. ANÁLISIS GEOESPACIAL (Cálculos principales)
# --------------------------------------------------------------------------

# --- Tarea 2.1: Conteo de hospitales por distrito ---
@st.cache_data
def analyze_districts(_hp_gdf, _distritos_gdf):
    # Asegurar que ambos GDFs usan el mismo CRS
    _hp_gdf = _hp_gdf.to_crs(_distritos_gdf.crs)

    # Unir espacialmente hospitales y distritos
    join_distritos = gpd.sjoin(_distritos_gdf, _hp_gdf, how="left", op="contains")

    # Contar hospitales por distrito
    conteo_distrital = join_distritos.groupby("IDDIST").size().reset_index(name="N_HOSPITALES")

    # Unir el conteo de vuelta al GeoDataFrame de distritos
    distritos_con_conteo = _distritos_gdf.merge(conteo_distrital, on="IDDIST", how="left")
    distritos_con_conteo["N_HOSPITALES"] = distritos_con_conteo["N_HOSPITALES"].fillna(0).astype(int)

    return distritos_con_conteo

# --- Tarea 2.2: Agregación a nivel departamental ---
@st.cache_data
def analyze_departments(_distritos_con_conteo):
    # Disolver distritos para crear departamentos
    departamentos_gdf = _distritos_con_conteo.dissolve(by="DEPARTAMEN", aggfunc={"N_HOSPITALES": "sum"})
    departamentos_gdf.reset_index(inplace=True)
    departamentos_gdf.rename(columns={'DEPARTAMEN': 'DEPARTAMENTO'}, inplace=True)

    summary_table = departamentos_gdf[['DEPARTAMENTO', 'N_HOSPITALES']].sort_values(by="N_HOSPITALES", ascending=False)
    return departamentos_gdf, summary_table

# --- Tarea 2.3: Análisis de Proximidad ---
@st.cache_data
def analyze_proximity(_ccpp_gdf, _hp_gdf, region_name):
    ccpp_region = _ccpp_gdf[_ccpp_gdf['DEPARTAMEN'] == region_name]
    hp_region = _hp_gdf[_hp_gdf['DEPARTAMENTO'] == region_name]

    # Reproyectar a un CRS métrico para el buffer (UTM 18S para Perú)
    ccpp_utm = ccpp_region.to_crs("EPSG:32718")
    hp_utm = hp_region.to_crs("EPSG:32718")

    # Crear buffer para cada centro poblado y contar hospitales dentro
    hospital_count = []
    for index, ccpp in ccpp_utm.iterrows():
        buffer = ccpp.geometry.buffer(10000)  # Buffer de 10 km
        count = hp_utm.within(buffer).sum()
        hospital_count.append(count)

    ccpp_region = ccpp_region.assign(HOSP_IN_10KM=hospital_count)

    # Identificar centros de mayor aislamiento y concentración
    isolation = ccpp_region.loc[ccpp_region['HOSP_IN_10KM'].idxmin()]
    concentration = ccpp_region.loc[ccpp_region['HOSP_IN_10KM'].idxmax()]

    return isolation, concentration

# Ejecutar los análisis
distritos_analizados_gdf = analyze_districts(hp_gdf, distritos_gdf)
departamentos_analizados_gdf, dept_summary_table = analyze_departments(distritos_analizados_gdf)

# --------------------------------------------------------------------------
# 4. CREACIÓN DE LA APLICACIÓN CON PESTAÑAS (TABS)
# --------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs([
    "🗂️ **Descripción de Datos**",
    "🗺️ **Mapas Estáticos y Análisis Departamental**",
    "🌍 **Mapas Dinámicos e Interactivos**"
])

# --- PESTAÑA 1: DESCRIPCIÓN ---
with tab1:
    st.header("Metodología y Fuentes de Datos")
    st.markdown("""
    Esta aplicación presenta un análisis sobre la accesibilidad a hospitales públicos en Perú, utilizando datos abiertos para generar visualizaciones estáticas e interactivas.
    """)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Unidad de Análisis")
        st.info("**Hospitales públicos operativos** en Perú, geolocalizados a partir de sus coordenadas.")
    with col2:
        st.subheader("Fuentes de Datos")
        st.info("""
        - **MINSA - IPRESS**: Registro Nacional de Instituciones Prestadoras de Servicios de Salud.
        - **INEI**: Centros Poblados (CCPP).
        - **IGN**: Límites administrativos distritales.
        """)
    with col3:
        st.subheader("Reglas de Filtrado")
        st.info("""
        - Se incluyen únicamente hospitales con estado **'EN FUNCIONAMIENTO'**.
        - Se descartan registros sin coordenadas de latitud/longitud válidas.
        """)

# --- PESTAÑA 2: ANÁLISIS DEPARTAMENTAL Y MAPAS ESTÁTICOS ---
with tab2:
    st.header("Análisis a Nivel Departamental")

    # Tarea 2.2: Tabla y Gráfico de Barras
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Tabla Resumen")
        st.dataframe(dept_summary_table.set_index('DEPARTAMENTO'), height=600)
    with col2:
        st.subheader("Gráfico de Barras")
        fig, ax = plt.subplots(figsize=(10, 8))
        dept_summary_table.sort_values('N_HOSPITALES', ascending=True).plot(
            kind='barh', x='DEPARTAMENTO', y='N_HOSPITALES', ax=ax, legend=False, color='#2a9d8f'
        )
        ax.set_title('Número de Hospitales Operativos por Departamento', fontsize=16)
        ax.set_xlabel('Cantidad de Hospitales', fontsize=12)
        ax.set_ylabel('Departamento', fontsize=12)
        st.pyplot(fig)

    st.divider()
    st.header("Mapas Estáticos a Nivel Distrital (GeoPandas)")

    # Tarea 2.1: Mapas estáticos
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Mapa 1: Total de hospitales")
        fig1, ax1 = plt.subplots(1, 1, figsize=(10, 10))
        distritos_analizados_gdf.plot(column='N_HOSPITALES', cmap='viridis', linewidth=0.5, ax=ax1, edgecolor='0.8', legend=True)
        ax1.set_axis_off()
        ax1.set_title("Hospitales por Distrito")
        st.pyplot(fig1)

    with col2:
        st.subheader("Mapa 2: Distritos sin hospitales")
        fig2, ax2 = plt.subplots(1, 1, figsize=(10, 10))
        distritos_analizados_gdf['SIN_HOSPITAL'] = distritos_analizados_gdf['N_HOSPITALES'] == 0
        distritos_analizados_gdf.plot(column='SIN_HOSPITAL', cmap='autumn', linewidth=0.5, ax=ax2, edgecolor='0.8', legend=True)
        ax2.set_axis_off()
        ax2.set_title("Distritos con Cero Hospitales")
        st.pyplot(fig2)

    with col3:
        st.subheader("Mapa 3: Top 10 distritos")
        top_10_districts = distritos_analizados_gdf.nlargest(10, 'N_HOSPITALES')
        fig3, ax3 = plt.subplots(1, 1, figsize=(10, 10))
        distritos_analizados_gdf.plot(color='lightgrey', linewidth=0.5, ax=ax3, edgecolor='0.8')
        top_10_districts.plot(column='N_HOSPITALES', cmap='plasma', linewidth=0.5, ax=ax3, edgecolor='0.8', legend=True)
        ax3.set_axis_off()
        ax3.set_title("Top 10 Distritos con Más Hospitales")
        st.pyplot(fig3)

# --- PESTAÑA 3: MAPAS DINÁMICOS (FOLIUM) ---
with tab3:
    st.header("Mapa Nacional Interactivo de Hospitales")

    # Tarea 3.1: Coropletas nacional con clusters
    m_nacional = folium.Map(location=[-9.19, -75.01], zoom_start=5, tiles="CartoDB positron")

    folium.Choropleth(
        geo_data=distritos_analizados_gdf.to_json(),
        name='Coropletas Distrital',
        data=distritos_analizados_gdf,
        columns=['IDDIST', 'N_HOSPITALES'],
        key_on='feature.properties.IDDIST',
        fill_color='YlGnBu',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Número de Hospitales por Distrito'
    ).add_to(m_nacional)

    # Cluster de marcadores
    marker_cluster = MarkerCluster().add_to(m_nacional)
    for idx, row in hp_gdf.iterrows():
        popup_text = f"<b>{row['Nombre del establecimiento']}</b><br>Categoría: {row['Categoria']}<br>Institución: {row['Institución']}"
        folium.Marker(
            [row['LATITUD'], row['LONGITUD']],
            popup=popup_text,
            icon=folium.Icon(color='red', icon='hospital', prefix='fa')
        ).add_to(marker_cluster)

    st_folium(m_nacional, width=1200, height=600)

    st.divider()
    st.header("Análisis de Proximidad en Lima y Loreto")
    st.markdown("""
    Visualización de los centros poblados con mayor y menor número de hospitales en un radio de 10 km.
    - <span style='color:green;'>**Círculo Verde**</span>: Centro poblado con **mayor concentración** de hospitales cercanos.
    - <span style='color:red;'>**Círculo Rojo**</span>: Centro poblado con **mayor aislamiento** (menos hospitales cercanos).
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    # Tarea 3.2: Proximidad en Lima y Loreto
    for region, column in [("LIMA", col1), ("LORETO", col2)]:
        with column:
            st.subheader(f"Región: {region}")
            with st.spinner(f"Calculando proximidad para {region}..."):
                iso, con = analyze_proximity(ccpp_gdf, hp_gdf, region)

                m_prox = folium.Map(
                    location=[iso.geometry.centroid.y, iso.geometry.centroid.x],
                    zoom_start=8,
                    tiles="CartoDB positron"
                )

                # Círculo de aislamiento (rojo)
                folium.Circle(
                    location=[iso.geometry.y, iso.geometry.x],
                    radius=10000,
                    color='red',
                    fill=True,
                    fill_color='red',
                    fill_opacity=0.2,
                    popup=f"Aislamiento: {iso['NOMCCPP']}<br>Hospitales en 10km: {iso['HOSP_IN_10KM']}"
                ).add_to(m_prox)

                # Círculo de concentración (verde)
                folium.Circle(
                    location=[con.geometry.y, con.geometry.x],
                    radius=10000,
                    color='green',
                    fill=True,
                    fill_color='green',
                    fill_opacity=0.2,
                    popup=f"Concentración: {con['NOMCCPP']}<br>Hospitales en 10km: {con['HOSP_IN_10KM']}"
                ).add_to(m_prox)

                st_folium(m_prox, height=500)

