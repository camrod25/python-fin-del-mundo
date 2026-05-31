
tab1, tab2, tab3 = st.tabs(["📋 Catálogo", "🗺️ Mapas", "🔍 Ficha"])

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


