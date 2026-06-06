import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from fpdf import FPDF
from shapely.geometry import Polygon
import os

class SAGEEngine:
    def __init__(self):
        """
        Initialise le moteur S.A.G.E.
        """
        self.df_attr = None
        self.gdf_spatial = None
        self.merged_gdf = None

    def _clean_toponymy(self, text):
        """
        Règles strictes de toponymie (critique B2B).
        Corrige les fautes d'orthographe avant toute jointure spatiale.
        """
        if pd.isna(text):
            return text
        
        # Conversion en string pour garantir les opérations
        text = str(text).strip()
        
        # Application des règles strictes
        if "بوتحاف دير" in text:
            return "Boulhaf Dir"
        if "الكؤؤؤف" in text:
            return "El Kouif"
            
        return text

    def load_data(self, shp_file, xlsx_file):
        """
        Charge et harmonise les fichiers Shapefile et Excel.
        - Harmonisation du système de coordonnées vers EPSG:4326.
        - Nettoyage toponymique immédiat.
        """
        try:
            # 1. Chargement du Shapefile
            self.gdf_spatial = gpd.read_file(shp_file)
            
            # Harmonisation CRS (Coordinate Reference System)
            if self.gdf_spatial.crs is None:
                # Si aucun CRS n'est défini, on assume WGS84 par défaut (EPSG:4326)
                self.gdf_spatial.set_crs(epsg=4326, inplace=True)
            elif self.gdf_spatial.crs.to_epsg() != 4326:
                self.gdf_spatial = self.gdf_spatial.to_crs(epsg=4326)

            # 2. Chargement des données attributaires (Excel/CSV)
            self.df_attr = pd.read_excel(xlsx_file) if xlsx_file.name.endswith('.xlsx') else pd.read_csv(xlsx_file)

            # 3. Application stricte de la toponymie sur la colonne de jointure 'Commune'
            if 'Commune' in self.df_attr.columns:
                self.df_attr['Commune'] = self.df_attr['Commune'].apply(self._clean_toponymy)
            
            if 'Commune' in self.gdf_spatial.columns:
                self.gdf_spatial['Commune'] = self.gdf_spatial['Commune'].apply(self._clean_toponymy)

            return True
        except Exception as e:
            raise Exception(f"Erreur lors du chargement des données : {str(e)}")

    def process_and_merge(self):
        """
        Fusionne les données spatiales et attributaires sur la colonne 'Commune'.
        Calcule les KPIs environnementaux.
        """
        if self.df_attr is None or self.gdf_spatial is None:
            raise Exception("Les données doivent être chargées avant la fusion.")

        # Jointure gauche (Left Join) pour conserver toutes les entités spatiales
        self.merged_gdf = self.gdf_spatial.merge(self.df_attr, on='Commune', how='left')

        # --- Calcul des KPIs (Logique métier) ---
        
        # Exemple 1: Volume de lixiviats (basé sur la tonnage)
        # Supposons une densité moyenne et un taux de génération (exemple)
        if 'Tonnage' in self.merged_gdf.columns:
            # Facteur de génération arbitraire pour l'exemple (à ajuster selon les normes locales)
            # 0.15 m3/tonne est une estimation courante
            self.merged_gdf['Volume_Lixiviat_m3'] = self.merged_gdf['Tonnage'] * 0.15
        
        # Exemple 2: Saturation %
        if 'Volume_Occupe' in self.merged_gdf.columns and 'Capacite_Totale' in self.merged_gdf.columns:
            self.merged_gdf['Saturation_Pct'] = (
                (self.merged_gdf['Volume_Occupe'] / self.merged_gdf['Capacite_Totale']) * 100
            ).round(2)

        return self.merged_gdf

    def export_dashboard_excel(self, output_path):
        """
        Génère un tableau de bord Excel propre (White-label).
        """
        if self.merged_gdf is None:
            raise Exception("Aucune donnée traitée pour l'export.")
        
        # On retire la géométrie pour l'export Excel (non supportée directement)
        df_export = self.merged_gdf.drop(columns=['geometry'])
        
        # Sauvegarde
        df_export.to_excel(output_path, index=False)
        return output_path

    def generate_white_label_map(self, output_path):
        """
        Génère une carte haute résolution avec contraintes visuelles strictes (White-label).
        Règles appliquées :
        - Pas de bordures d'axes (set_axis_off)
        - Pas de titre principal
        - Pas de boîte de légende
        - Pas de boîtes de statistiques
        - Pas de noms d'auteurs
        """
        if self.merged_gdf is None:
            raise Exception("Aucune donnée géospatiale pour la carte.")

        fig, ax = plt.subplots(1, 1, figsize=(12, 10), dpi=300)

        # Cartographie des données (ex: saturation par couleur)
        # Utilisation d'une colormap discrète pour un rendu professionnel
        if 'Saturation_Pct' in self.merged_gdf.columns:
            self.merged_gdf.plot(
                column='Saturation_Pct',
                cmap='Greens',
                linewidth=0.5,
                ax=ax,
                legend=False,  # Désactive la légende par défaut
                edgecolor='black'
            )
        else:
            # Fallback si KPI absent
            self.merged_gdf.plot(ax=ax, color='lightblue', edgecolor='black', linewidth=0.5)

        # --- RÈGLES VISUELLES STRICTES (CRITICAL) ---
        
        # 1. Supprimer les axes (coordonnées et bordures)
        ax.set_axis_off()
        
        # 2. Supprimer le titre principal
        ax.set_title('')
        
        # 3. Ajuster les marges pour un look propre
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
        
        # 4. Sauvegarde haute résolution sans padding blanc excessif
        plt.savefig(output_path, bbox_inches='tight', pad_inches=0, dpi=300)
        plt.close(fig)
        
        return output_path

    def generate_pdf_report(self, output_path, map_path, excel_path):
        """
        Génère un rapport PDF professionnel (White-label).
        """
        if self.merged_gdf is None:
            raise Exception("Aucune donnée pour le rapport.")

        pdf = FPDF(unit='mm', format='A4')
        pdf.add_page()
        
        # Police standard (Helvetica pour un look propre)
        pdf.set_font("Helvetica", size=12)
        
        # En-tête minimaliste
        pdf.cell(0, 10, "Rapport d'Analyse Geospatiale - S.A.G.E.", ln=True, align='C')
        pdf.ln(10)
        
        # Section 1: Résumé des données
        pdf.set_font("Helvetica", size=10)
        pdf.cell(0, 10, f"Nombre de sites analytiques: {len(self.merged_gdf)}", ln=True)
        
        # Calcul de some des KPIs pour le résumé
        if 'Tonnage' in self.merged_gdf.columns:
            total_tonnage = self.merged_gdf['Tonnage'].sum()
            pdf.cell(0, 10, f"Tonnage Total: {total_tonnage:,.2f} tonnes", ln=True)
        
        if 'Saturation_Pct' in self.merged_gdf.columns:
            avg_sat = self.merged_gdf['Saturation_Pct'].mean()
            pdf.cell(0, 10, f"Saturation Moyenne: {avg_sat:.2f}%", ln=True)
            
        pdf.ln(10)
        
        # Section 2: Insertion de la carte
        pdf.set_font("Helvetica", size=10)
        pdf.cell(0, 10, "Carte de Synthese:", ln=True)
        pdf.ln(5)
        
        # Redimensionnement de l'image pour A4 (largeur max ~190mm)
        pdf.image(map_path, x=10, y=pdf.get_y(), w=190)
        pdf.ln(110) # Espace réservé pour l'image
        
        # Section 3: Médonnées et export
        pdf.add_page()
        pdf.set_font("Helvetica", size=10)
        pdf.cell(0, 10, "Donnees Extraites (Tableau de Bord):", ln=True)
        pdf.ln(5)
        
        # Ajout d'un lien ou référence vers le fichier Excel
        pdf.set_text_color(0, 0, 255) # Bleu pour lien
        pdf.cell(0, 10, f"Fichier Excel genere: {os.path.basename(excel_path)}", ln=True)
        pdf.set_text_color(0, 0, 0) # Retour au noir
        
        pdf.output(output_path)
        return output_path
