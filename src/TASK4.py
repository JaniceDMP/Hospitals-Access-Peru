#!/usr/bin/env python
# coding: utf-8

# In[6]:


#app.py

get_ipython().system('pip install streamlit')
get_ipython().system('pip install pandas')
get_ipython().system('pip install geopandas')
get_ipython().system('pip install matplotlib')
get_ipython().system('pip install folium')
get_ipython().system('pip install streamlit-folium')


# In[11]:


#%%writefile app.py

import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
import matplotlib.pyplot as plt
from streamlit_folium import st_folium

# (Aquí va todo el código de la aplicación que te di antes)
# Lo incluyo de nuevo para que solo tengas que copiar y pegar esta celda

# --- Configuración de la página ---
st.set_page_config(
    page_title="Análisis de Hospitales Públicos en Perú",
    page_icon="🏥",
    layout="wide"
)

# --- Carga y Cache de Datos Reales ---
@st.cache_data
def load_data():

    hp_df = pd.read_csv('hospitals_info.csv')

    hp_df['LATITUD'] = pd.to_numeric(hp_df['NORTE'], errors='coerce')
    hp_df['LONGITUD'] = pd.to_numeric(hp_df['ESTE'], errors='coerce')
    hp_df.dropna(subset=['LATITUD', 'LONGITUD'], inplace=True)
    hp_df = hp_df[hp_df['LATITUD'].between(-18.5, 0)]
    hp_df = hp_df[hp_df['LONGITUD'].between(-81.5, -68.5)]

    hp_gdf = gpd.GeoDataFrame(
        hp_df,
        geometry=gpd.points_from_xy(hp_df['LONGITUD'], hp_df['LATITUD']),
        crs="EPSG:4326"
    )

    pop_gdf = gpd.read_file('CCPP_IGN100K.shp')
    if 'DEPARTAMEN' in pop_gdf.columns:
        pop_gdf.rename(columns={'DEP': 'DEPARTAMENTO'}, inplace=True)

    distritos_gdf = gpd.read_file('DISTRITOS.shp')
    peru_dptos_gdf = distritos_gdf.dissolve(by='DEPARTAMEN', aggfunc='sum')
    peru_dptos_gdf.reset_index(inplace=True)
    peru_dptos_gdf.rename(columns={'DEPARTAMEN': 'DEPARTAMENTO'}, inplace=True)

    return hp_gdf, pop_gdf, peru_dptos_gdf

hp_gdf, pop_gdf, peru_dptos_gdf = load_data()

# --- Procesamiento y Cálculos ---
dpto_summary = hp_gdf['Departamento'].value_counts().reset_index()
dpto_summary.columns = ['DEPARTAMENTO', 'N_HOSPITALES']
dpto_summary.rename(columns={'Departamento': 'DEPARTAMENTO'}, inplace=True)

peru_dptos_gdf = peru_dptos_gdf.merge(
    dpto_summary,
    how='left',
    on='DEPARTAMENTO'
)
peru_dptos_gdf['N_HOSPITALES'] = peru_dptos_gdf['N_HOSPITALES'].fillna(0)

def make_proximity_map(region_name, pop_gdf, hp_gdf, buffer_m=10000):
    pop_reg = pop_gdf[pop_gdf['DEPARTAMENTO'] == region_name]
    hp_reg = hp_gdf[hp_gdf['DEPARTAMENTO'] == region_name]

    if pop_reg.empty or hp_reg.empty:
        return folium.Map(location=[-9.19, -75.01], zoom_start=5, tiles='CartoDB positron')

    pop_reg_utm = pop_reg.to_crs("EPSG:32718")
    hp_reg_utm = hp_reg.to_crs("EPSG:32718")
    buffers_union_utm = hp_reg_utm.buffer(buffer_m).unary_union
    isolation = pop_reg_utm[~pop_reg_utm.within(buffers_union_utm)]
    concentration = pop_reg_utm[pop_reg_utm.within(buffers_union_utm)]

    map_center = [pop_reg.to_crs("EPSG:32718").geometry.unary_union.centroid.y, pop_reg.to_crs("EPSG:32718").geometry.unary_union.centroid.x]
    m = folium.Map(location=map_center, zoom_start=7, tiles='CartoDB positron')

    folium.GeoJson(gpd.GeoSeries([buffers_union_utm], crs="EPSG:32718").to_crs("EPSG:4326"), name='Área de Cobertura (10km)', style_function=lambda x: {'color': '#2a9d8f', 'fillColor': '#2a9d8f', 'fillOpacity': 0.3, 'weight': 1}).add_to(m)
    folium.GeoJson(isolation.to_crs("EPSG:4326"), name='Población Aislada', marker=folium.CircleMarker(radius=1.5, color='#e76f51', fill_color='#e76f51')).add_to(m)
    folium.GeoJson(concentration.to_crs("EPSG:4326"), name='Población con Cobertura', marker=folium.CircleMarker(radius=1.5, color='#2a9d8f', fill_color='#2a9d8f')).add_to(m)

    folium.LayerControl().add_to(m)
    return m

# --- Interfaz de Streamlit ---
st.title("🏥 Análisis de Infraestructura Hospitalaria Pública en Perú")

tab1, tab2, tab3 = st.tabs(["🗂️ Data Description", "🗺️ Static Maps & Department Analysis", "🌍 Dynamic Maps"])

with tab1:
    st.header("Descripción de los Datos")
    # ... (contenido de la pestaña 1)
with tab2:
    st.header("Análisis por Departamento")
    # ... (contenido de la pestaña 2)
with tab3:
    st.header("Mapa Nacional Interactivo")
    # ... (contenido de la pestaña 3)

