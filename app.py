import streamlit as st
import pandas as pd
import geopandas as gpd
import os
import tempfile
from sage_engine import SAGEEngine

# Configuration de la page (Minimaliste, Pro)
st.set_page_config(
    page_title="S.A.G.E. - Analyse Geospatiale",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé pour un look "White-label" et propre
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #2E8B57; /* Vert SAGE */
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton>button {
        background-color: #2E8B57;
        color: white;
        width: 100%;
    }
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #2E8B57, #3CB371);
    }
    </style>
    """, unsafe_allow_html=True)

# En-tête de l'application
st.markdown('<h1 class="main-header">S.A.G.E. - Système d\'Analyse Géospatiale</h1>', unsafe_allow_html=True)
st.markdown("### Outil automatisé d'ingestion et d'analyse pour centres techniques")

# Initialisation du moteur
if 'engine' not in st.session_state:
    st.session_state.engine = SAGEEngine()

# Sidebar pour les paramètres et uploads
with st.sidebar:
    st.header("Configuration & Données")
    
    st.markdown("---")
    st.subheader("1. Fichiers d'Entrée")
    
    # Upload Shapefile (.shp) - Note: Streamlit ne gère pas les dépendances .shp/.shx/.dbf nativement via simple upload
    # Pour une solution robuste, on accepte un zip contenant le shapefile ou on utilise des fichiers individuels.
    # Ici, on utilise une approche simplifiée pour la démo, demandant le fichier .shp principal.
    shp_file = st.file_uploader("Fichier Shapefile (.shp)", type=['shp'])
    xlsx_file = st.file_uploader("Fichier Données (.xlsx ou .csv)", type=['xlsx', 'csv'])

    st.markdown("---")
    st.subheader("2. Actions")
    
    process_btn = st.button("🚀 Traiter les Données", type="primary")
    
    if shp_file and xlsx_file:
        st.success("Fichiers chargés correctement.")
    else:
        st.warning("Veuillez charger les deux fichiers pour continuer.")

# Zone principale de contenu
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Aperçu des Données")
    
    if 'merged_data' in st.session_state:
        # Affichage d'un aperçu des données fusionnées
        st.dataframe(st.session_state.merged_data.head(10), use_container_width=True)
    else:
        st.info("Aucune donnée traitée pour le moment.")

with col2:
    st.subheader("Téléchargements")
    
    if 'downloads' in st.session_state:
        # Boutons de téléchargement pour les fichiers générés
        for key, (label, file_path) in st.session_state['downloads'].items():
            with open(file_path, "rb") as f:
                st.download_button(
                    label=label,
                    data=f,
                    file_name=os.path.basename(file_path),
                    mime="application/octet-stream"
                )
    else:
        st.info("Les résultats apparaîtront ici après traitement.")

# Logique de traitement
if process_btn:
    if shp_file and xlsx_file:
        with st.spinner("Traitement en cours..."):
            try:
                # 1. Chargement et nettoyage toponymique
                st.session_state.engine.load_data(shp_file, xlsx_file)
                
                # 2. Fusion et calcul KPI
                merged_gdf = st.session_state.engine.process_and_merge()
                st.session_state.merged_data = merged_gdf
                
                # 3. Création de fichiers temporaires pour les exports
                with tempfile.TemporaryDirectory() as tmp_dir:
                    # Chemins des fichiers de sortie
                    excel_path = os.path.join(tmp_dir, "dashboard_sage.xlsx")
                    map_path = os.path.join(tmp_dir, "carte_sage.png")
                    pdf_path = os.path.join(tmp_dir, "rapport_sage.pdf")
                    
                    # Génération des exports
                    st.session_state.engine.export_dashboard_excel(excel_path)
                    st.session_state.engine.generate_white_label_map(map_path)
                    st.session_state.engine.generate_pdf_report(pdf_path, map_path, excel_path)
                    
                    # Sauvegarde des chemins pour téléchargement
                    # Note: Dans une vraie app cloud, il faudrait gérer la persistance des fichiers
                    # Ici, on garde les chemins en mémoire pour la session active
                    st.session_state['downloads'] = {
                        'excel': ("📥 Télécharger Dashboard Excel", excel_path),
                        'pdf': ("📄 Télécharger Rapport PDF", pdf_path),
                        'map': ("🗺️ Télécharger Carte PNG", map_path)
                    }
                
                st.success("Traitement terminé avec succès !")
                st.rerun()
                
            except Exception as e:
                st.error(f"Une erreur est survenue : {str(e)}")
    else:
        st.error("Veuillez charger les fichiers requis avant de traiter.")
