import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests

# set_page_config debe ser SIEMPRE el primer comando de Streamlit
# layout="wide" aprovecha todo el ancho de la pantalla
st.set_page_config(
    page_title = "Ibanasca — Defensa Planetaria de Dr. Z Academy",
    page_icon  = "🪨",
    layout     = "wide"
)

# @st.cache_data guarda el resultado en memoria
# sin esto la app descargaría 41,000 asteroides
# cada vez que el usuario toca cualquier control
@st.cache_data
def cargar_datos():
    url    = "https://ssd-api.jpl.nasa.gov/sbdb_query.api"
    campos = "full_name,H,albedo,diameter,moid,e,a,i,class,neo,pha"
    params = {
        "fields"   : campos,
        "sb-kind"  : "a",
        "sb-group" : "neo",
    }
    r  = requests.get(url, params=params, timeout=60)
    df = pd.DataFrame(r.json()["data"], columns=r.json()["fields"])

    for col in ["H", "albedo", "diameter", "moid", "e", "a", "i"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["nombre"] = df["full_name"].str.strip()
    return df

# st.spinner muestra un mensaje mientras espera la descarga
with st.spinner("Descargando catálogo del JPL..."):
    df = cargar_datos()

st.title("Ibanasca — Defensa Planetaria de Dr.Z Academy")
st.caption(f"Catálogo JPL — {len(df):,} asteroides NEA")

st.sidebar.header("Filtros")

clases = ["Todas"] + sorted(df["class"].dropna().unique().tolist())
clase_sel = st.sidebar.selectbox("Clase orbital", clases)

solo_pha = st.sidebar.checkbox("Solo PHAs")

h_min, h_max = st.sidebar.slider(
    "Rango de magnitud H",
    min_value = float(df["H"].min()),
    max_value = float(df["H"].max()),
    value     = (float(df["H"].min()), 25.0)
)

df_filtrado = df.copy()

if clase_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado["class"] == clase_sel]
if solo_pha:
    df_filtrado = df_filtrado[df_filtrado["pha"] == "Y"]
df_filtrado = df_filtrado[
    (df_filtrado["H"] >= h_min) & (df_filtrado["H"] <= h_max)
]

st.sidebar.markdown(f"**{len(df_filtrado):,} asteroides** con estos filtros")

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["Catálogo", "Mapas", "Ficha", "Simulador", "¿Coincidimos?", "Predicción ML", "Clasificador PHA"])

with tab1:
    st.subheader("Catálogo de Asteroides NEA")
    columnas = ["nombre", "H", "albedo", "diameter", "moid", "class", "pha"]
    st.dataframe(
        df_filtrado[columnas].rename(columns={
            "nombre"   : "Nombre",
            "H"        : "Mag. H",
            "albedo"   : "Albedo",
            "diameter" : "Diámetro (km)",
            "moid"     : "MOID (UA)",
            "class"    : "Clase",
            "pha"      : "PHA"
        }),
        use_container_width = True,
        height              = 500
    )



with tab4:
    st.subheader("Simulador de Impacto")
    st.caption("Calcula la energía y el cráter estimado para un impacto asteroidal")

    col_izq, col_der = st.columns(2)

    with col_izq:
        diametro_km = st.slider(
            "Diámetro del asteroide (km)",
            min_value = 0.01,
            max_value = 20.0,
            value     = 0.14,
            step      = 0.01,
            format    = "%.2f km"
        )

        tipo = st.selectbox(
            "Tipo de asteroide",
            ["Tipo C — carbonáceo (1,400 kg/m³)",
             "Tipo S — silíceo (2,700 kg/m³)",
             "Tipo M — metálico (5,000 kg/m³)"]
        )

    with col_der:
        velocidad_kms = st.slider(
            "Velocidad de impacto (km/s)",
            min_value = 11.0,
            max_value = 70.0,
            value     = 20.0,
            step      = 0.5,
            format    = "%.1f km/s"
        )

        angulo = st.slider(
            "Ángulo de impacto (°)",
            min_value = 10,
            max_value = 90,
            value     = 45,
            help      = "90° = impacto vertical directo. Los impactos oblicuos son más frecuentes."
        )

    # --- Cálculos físicos ---
    densidades = {
        "Tipo C — carbonáceo (1,400 kg/m³)" : 1400,
        "Tipo S — silíceo (2,700 kg/m³)"    : 2700,
        "Tipo M — metálico (5,000 kg/m³)"   : 5000
    }
    rho      = densidades[tipo]
    r_m      = (diametro_km * 1000) / 2
    volumen  = (4/3) * np.pi * r_m**3
    masa_kg  = rho * volumen
    v_ms     = velocidad_kms * 1000
    E_J      = 0.5 * masa_kg * v_ms**2
    E_MT     = E_J / 4.184e15
    crater_km = diametro_km * 20

    st.divider()

    # --- Resultados ---
    st.subheader("Resultados")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Masa",              f"{masa_kg:.2e} kg")
    c2.metric("Energía cinética",  f"{E_J:.2e} J")
    c3.metric("Energía en Mt TNT", f"{E_MT:.2e} Mt")
    c4.metric("Cráter estimado",   f"{crater_km:.2f} km")

    st.divider()

    # --- Comparación histórica ---
    st.subheader("¿Qué tan grande es esa energía?")

    referencias = {
        "Bomba de Hiroshima"        : 0.015,
        "Chelyabinsk 2013"          : 0.5,
        "Bomba Castle Bravo (EEUU)" : 15.0,
        "Krakatoa 1883"             : 200.0,
        "Chicxulub (~KT)"           : 100_000_000.0
    }

    filas = []
    for evento, e_ref in referencias.items():
        if E_MT >= e_ref:
            ratio = E_MT / e_ref
            comparacion = f"{ratio:.1f}× más grande"
        else:
            ratio = e_ref / E_MT
            comparacion = f"{ratio:.1f}× más pequeño"
        filas.append({"Evento de referencia": evento,
                      "Energía (Mt TNT)": e_ref,
                      "Comparación": comparacion})

    st.dataframe(
        pd.DataFrame(filas),
        use_container_width = True,
        hide_index          = True
    )

    if E_MT < 0.015:
        st.success("Energía menor a Hiroshima — evento local menor")
    elif E_MT < 15:
        st.warning("Energía entre Hiroshima y Castle Bravo — evento regional severo")
    elif E_MT < 10_000:
        st.error("Energía entre Castle Bravo y Krakatoa — evento continental catastrófico")
    else:
        st.error("Energía comparable o superior a Chicxulub — evento de extinción masiva")

with tab5:
    st.subheader("¿Coincidimos con NASA?")
    st.write("""
    El CNEOS — Centro de Estudios de Objetos Cercanos a la Tierra del JPL —
    tiene una herramienta oficial para estimar el tamaño de asteroides a partir
    de su magnitud absoluta H y su albedo. Vamos a comparar sus resultados con los nuestros.
    """)

    st.info("Herramienta oficial CNEOS: https://cneos.jpl.nasa.gov/tools/ast_size_est.html")

    st.divider()
    st.subheader("Calcula y compara")

    col1, col2 = st.columns(2)
    with col1:
        H_cneos = st.number_input(
            "Magnitud absoluta H",
            min_value = 0.0,
            max_value = 40.0,
            value     = 19.2,
            step      = 0.1,
            help      = "Apophis: H=19.2 | Bennu: H=20.8 | Chelyabinsk: H=26.0"
        )
    with col2:
        albedo_cneos = st.number_input(
            "Albedo visual",
            min_value = 0.01,
            max_value = 0.90,
            value     = 0.30,
            step      = 0.01,
            help      = "Tipo S (silíceo): ~0.20-0.30 | Tipo C (carbonáceo): ~0.05-0.10"
        )

    # Nuestra fórmula de Harris
    d_nuestro = (1329 / np.sqrt(albedo_cneos)) * 10**(-0.2 * H_cneos)

    # Fórmula del CNEOS — publicada explícitamente en su página web
    # Referencia: Harris y Harris (1997), Icarus 126:450-454
    d_cneos = 10 ** (3.1236 - 0.5 * np.log10(albedo_cneos) - 0.2 * H_cneos)

    st.divider()
    st.subheader("Resultado")

    c1, c2, c3 = st.columns(3)
    c1.metric("Nuestra fórmula (Harris)",  f"{d_nuestro:.2f} km")
    c2.metric("Fórmula CNEOS oficial",     f"{d_cneos:.2f} km")
    diferencia = abs(d_nuestro - d_cneos)
    c3.metric("Diferencia",                f"{diferencia:.2e} km")

    if diferencia < 1e-10:
        st.success("Los resultados son idénticos — nuestra implementación es correcta.")
    else:
        st.warning(f"Diferencia numérica mínima por redondeo de punto flotante: {diferencia:.2e} km")

with tab5:
    st.subheader("¿Coincidimos con NASA?")
    st.write("""
    El CNEOS — Centro de Estudios de Objetos Cercanos a la Tierra del JPL —
    tiene una herramienta oficial para estimar el tamaño de asteroides a partir
    de su magnitud absoluta H y su albedo. Vamos a comparar sus resultados con los nuestros.
    """)

    st.info("Herramienta oficial CNEOS: https://cneos.jpl.nasa.gov/tools/ast_size_est.html")

    st.divider()
    st.subheader("Calcula y compara")

    col1, col2 = st.columns(2)
    with col1:
        H_cneos = st.number_input(
            "Magnitud absoluta H",
            min_value = 0.0,
            max_value = 40.0,
            value     = 19.2,
            step      = 0.1,
            help      = "Apophis: H=19.2 | Bennu: H=20.8 | Chelyabinsk: H=26.0"
        )
    with col2:
        albedo_cneos = st.number_input(
            "Albedo visual",
            min_value = 0.01,
            max_value = 0.90,
            value     = 0.30,
            step      = 0.01,
            help      = "Tipo S (silíceo): ~0.20-0.30 | Tipo C (carbonáceo): ~0.05-0.10"
        )

    # Nuestra fórmula de Harris
    d_nuestro = (1329 / np.sqrt(albedo_cneos)) * 10**(-0.2 * H_cneos)

    # Fórmula del CNEOS — publicada explícitamente en su página web
    # Referencia: Harris y Harris (1997), Icarus 126:450-454
    d_cneos = 10 ** (3.1236 - 0.5 * np.log10(albedo_cneos) - 0.2 * H_cneos)

    st.divider()
    st.subheader("Resultado")

    c1, c2, c3 = st.columns(3)
    c1.metric("Nuestra fórmula (Harris)",  f"{d_nuestro:.2f} km")
    c2.metric("Fórmula CNEOS oficial",     f"{d_cneos:.2f} km")
    diferencia = abs(d_nuestro - d_cneos)
    c3.metric("Diferencia",                f"{diferencia:.2e} km")

    if diferencia < 1e-10:
        st.success("Los resultados son idénticos — nuestra implementación es correcta.")
    else:
        st.warning(f"Diferencia numérica mínima por redondeo de punto flotante: {diferencia:.2e} km")

import joblib

modelo_reg = joblib.load("modelo_regresion.joblib")
modelo_clf = joblib.load("modelo_clasificacion.joblib")

with tab6:
    st.subheader("Predicción de Diámetro con Modelo de Regresión")
    st.write("""
    Este modelo fue entrenado con datos reales del JPL.
    Usa regresión lineal sobre variables logarítmicas para predecir
    el diámetro de un asteroide a partir de su magnitud absoluta H y su albedo.
    Con R² igual a 0.9905 explica el 99% de la varianza del diámetro.
    """)

    st.info("Este modelo fue entrenado con datos reales del JPL.")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        H_reg = st.slider(
            "Magnitud absoluta H",
            min_value = 10.0,
            max_value = 30.0,
            value     = 19.2,
            step      = 0.1,
            help      = "Apophis: 19.2 | Bennu: 20.8 | Chelyabinsk: 26.0",
            key       = "H_reg"
        )
    with col2:
        albedo_reg = st.slider(
            "Albedo visual",
            min_value = 0.01,
            max_value = 0.90,
            value     = 0.30,
            step      = 0.01,
            help      = "Tipo S: ~0.20-0.30 | Tipo C: ~0.05-0.10",
            key       = "albedo_reg"
        )

    # Paso 1 — transformamos el albedo igual que en el entrenamiento
    log_albedo = np.log10(albedo_reg)

    # Paso 2 — el modelo predice el logaritmo del diámetro
    log_d_predicho = modelo_reg.predict([[H_reg, log_albedo]])[0]

    # Paso 3 — revertimos el logaritmo para obtener el diámetro en km
    d_predicho = 10 ** log_d_predicho

    # Paso 4 — calculamos el diámetro con Harris para comparar
    d_harris = (1329 / np.sqrt(albedo_reg)) * 10**(-0.2 * H_reg)

    st.divider()
    st.subheader("Resultado")

    c1, c2, c3 = st.columns(3)
    c1.metric("Predicción del modelo ML", f"{d_predicho:.3f} km")
    c2.metric("Fórmula de Harris",        f"{d_harris:.3f} km")
    diferencia_reg = abs(d_predicho - d_harris)
    c3.metric("Diferencia",               f"{diferencia_reg:.3f} km")
