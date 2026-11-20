"""Tableau de bord TVA — Meridian Distribution.

Lancement :  streamlit run app.py
La page se met à jour toute seule chaque fois que vous enregistrez ce fichier.

Complétez les TODO dans l'ordre des étapes du brief. Chaque TODO porte un nom
(par exemple « CHIFFRES ») que l'étape du brief vous indique.
ATTENTION : ils ne sont pas dans l'ordre du fichier (les étapes 3 et 6 sont en haut).
Cherchez-les avec Ctrl+F (Cmd+F sur Mac).
Ne passez à l'étape suivante que quand la vérification de l'étape en cours est bonne.
"""

import pandas as pd
import numpy as np
import plotly.express as px  # noqa: F401 — servira aux étapes 2 et 4, ne pas supprimer
import streamlit as st

st.set_page_config(page_title="Référentiel TVA", layout="wide")


# Déjà écrit pour vous. @st.cache_data évite de relire le fichier à chaque clic.
@st.cache_data
def charger_donnees():
    df = pd.read_csv(
        "data/resultats_vies.csv", parse_dates=["date_saisie", "date_verification"]
    )
    df["etape_rejet"] = df["etape_rejet"].fillna("envoyé à VIES")
    return df


# Déjà écrit pour vous : sert à l'étape 4.
def taux_invalides(donnees, colonne):
    """Pour chaque valeur de `colonne` (chaque canal, chaque pays...), calcule la part
    de numéros invalides en %. Renvoie un tableau à deux colonnes : `colonne` et "taux d'erreur (%)"."""
    return (
        donnees.groupby(colonne)["statut"]
        .apply(lambda statuts: round((statuts == "invalide").mean() * 100, 1))
        .sort_values()
        .reset_index(name="taux d'erreur (%)")
    )


df = charger_donnees()

# =============================================================================
# ÉTAPE 3 — Les filtres (à faire APRÈS les étapes 1 et 2)
# =============================================================================
st.sidebar.header("Filtres")

# Exemple déjà écrit : le filtre pays. Une liste vide veut dire « tous les pays ».
pays = st.sidebar.multiselect("Pays déclaré", sorted(df["pays_declare"].unique()))

# TODO FILTRE_CANAL (étape 3a) : sur le même modèle, un filtre « Canal de saisie » sur la colonne source_saisie.
canal = st.sidebar.multiselect("Canal de saisie", sorted(df["source_saisie"].unique()))

# TODO FILTRE_PERIODE (étape 3b) : un filtre « Période de saisie » avec st.sidebar.slider (voir le brief).
debut, fin = st.sidebar.slider( 
	"Période de saisie",
	min_value=df["date_saisie"].min().date(),
	max_value=df["date_saisie"].max().date(),
	value=(df["date_saisie"].min().date(), df["date_saisie"].max().date()),
	format="DD/MM/YYYY", 
)

# `selection` contient les lignes qui passent les filtres. Toute la suite utilise
# `selection`, jamais `df` : c'est ce qui fait réagir la page aux filtres.
selection = df
if pays:
    selection = selection[selection["pays_declare"].isin(pays)]
if canal:
    selection = selection[selection["source_saisie"].isin(canal)]
# TODO APPLIQUER_FILTRES (étape 3c) : appliquer le filtre canal et le filtre période à `selection`.
#           Toujours `selection = selection[...]`, jamais `selection = df[...]`.
    selection = selection[selection["date_saisie"].dt.date.between(debut, fin)]
# =============================================================================
# ÉTAPE 6 — Rendre la page lisible par tous (à faire APRÈS l'étape 5)
# =============================================================================
st.title("Qualité du référentiel TVA")
# TODO AIDE (étape 6a) : une phrase d'aide pour la directrice financière (st.write).
st.write("Ce tableau de bord représente le travail de nettoyage des données de numéros TVA. Il met en évidence les numéros non traités et indique automatiquement quelles mesures prendre pour les numéros non traités. Il appose des filtres de manière dynamique.")
# TODO DATE_REGLE (étape 6b) : la date de la dernière vérification VIES et la règle pour les non tranchés (st.info).
derniere = df["date_verification"].max() 
st.info(f"Dernière vérification VIES : {derniere:%d/%m/%Y à %H:%M}. Règle : un numéro non tranché ne doit pas être facturé hors taxe tant qu'il n'a pas été revérifié.")
# =============================================================================
# ÉTAPE 1 — Les quatre chiffres clés
# =============================================================================
total = len(selection)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Numéros", total)
# TODO CHIFFRES (étape 1) : dans col2, col3 et col4, le nombre de valides, d'invalides et de non tranchés,
#          chacun avec son pourcentage du total.

valides = (selection["statut"] == "valide").sum() 
col2.metric("Valides", valides, f"{valides / total:.1%} du total", delta_color="off")

invalides = (selection["statut"] == "invalide").sum() 
col3.metric("Invalides", invalides, f"{invalides / total:.1%} du total", delta_color="off")

non_tranches = (selection["statut"] == "non_tranche").sum() 
col4.metric("Non tranchés", non_tranches, f"{non_tranches / total:.1%} du total", delta_color="off")

tab1, tab2, tab3, tab4 = st.tabs(["☑️ Numéros viables", "❌ Provenance des erreurs", "⏱️ Temps de réponse", "💼 à traiter"])
# =============================================================================
# ÉTAPE 2 — L'entonnoir
# =============================================================================

with tab1:
	st.subheader("Combien de numéros ont pu être envoyés à VIES ?")
	# TODO ENTONNOIR (étape 2) : compter, étape par étape, les numéros qui restent après le retrait des absents,
	#          des doublons, puis des numéros mal formés, et les afficher avec px.funnel.
	absents = (selection["etape_rejet"] == "absent").sum() 
	doublons = (selection["etape_rejet"] == "doublon").sum() 
	structure = (selection["etape_rejet"] == "structure").sum() 
	entonnoir = pd.DataFrame({ 
		"étape": ["Référentiel", "Sans les absents", "Sans les doublons", "Envoyés à VIES"], 
		"numéros": [total, 
			total - absents, 
			total - absents - doublons, 
			total - absents - doublons - structure],
	})
	fig = px.funnel(entonnoir, x="numéros", y="étape", 
		title="Du référentiel aux numéros envoyés à VIES")
	st.plotly_chart(fig)

# =============================================================================
# ÉTAPE 4 — D'où viennent les erreurs ?
# =============================================================================
with tab2:
	st.subheader("D'où viennent les erreurs ?")
	# TODO GRAPHIQUES (étape 4) : avec taux_invalides(selection, "source_saisie"), puis "pays_declare",
	#          deux graphiques en barres horizontales avec la valeur écrite sur chaque barre,
	#          puis une phrase (st.caption) qui explique quel canal sort du lot.
	taux = taux_invalides(selection, "source_saisie") 
	fig = px.bar(taux, x="taux d'erreur (%)", y="source_saisie", orientation="h",
		text="taux d'erreur (%)", title="Part de numéros invalides par canal de saisie") 
	st.plotly_chart(fig)
	st.caption("La source saisie correspond au canal d'origine du client. La plus grande marge d'erreur correspond à le reprise ERP.")

	taux = taux_invalides(selection, "pays_declare") 
	fig = px.bar(taux, x="taux d'erreur (%)", y="pays_declare", orientation="h",
		text="taux d'erreur (%)", title="Part de numéros invalides par pays déclaré") 
	st.plotly_chart(fig)

with tab3:
	toutes_donnees = selection["temps_reponse_ms"].dropna()
	donnees_filtrees = selection[selection["temps_reponse_ms"] < 30000].dropna(subset=["temps_reponse_ms"])
	median_val = np.median(donnees_filtrees["temps_reponse_ms"])
	p95_val = np.percentile(toutes_donnees, 95)
	nb_timeouts = len(toutes_donnees) - len(donnees_filtrees)
	fig = px.histogram(
		donnees_filtrees,
		x="temps_reponse_ms",
		nbins=60,
		labels={"temps_reponse_ms": "Temps de réponse (ms)"},
		title="Distribution des temps de réponse",
		color_discrete_sequence=["#378043"],
		opacity=0.8,
	)

	fig.add_vline(
		x=median_val,
		line_width=2.5,
		line_dash="dash",
		line_color="#d62728",
		annotation_text=f"Médiane : {median_val:.1f} ms",
		annotation_position="top right",
		annotation_font_color="#d62728",
	)

	if p95_val < 30000:
		fig.add_vline(
			x=p95_val,
			line_width=2.5,
			line_dash="dot",
			line_color="#ff7f0e",
			annotation_text=f"P95 : {p95_val:.0f} ms",
			annotation_position="top right",
			annotation_font_color="#ff7f0e",
		)

	fig.update_layout(
		bargap=0.05,
		yaxis_title="Nombre de requêtes",
		template="plotly_white",
		height=450,
	)

	st.plotly_chart(fig, use_container_width=True)

	if nb_timeouts > 0:
		st.caption(
			f"Note : {nb_timeouts} requêtes en timeout (≥ 30 s) ont été masquées pour la lisibilité, mais sont incluses dans le calcul de la médiane et du P95 ({p95_val:.0f} ms)."
		)

	total_requetes = len(selection)
	nb_manquantes = selection["temps_reponse_ms"].isna().sum()
	pct_manquantes = (
		(nb_manquantes / total_requetes * 100) if total_requetes > 0 else 0
	)

	nb_timeouts = (selection["temps_reponse_ms"] >= 30000).sum()
	pct_timeouts = (nb_timeouts / total_requetes * 100) if total_requetes > 0 else 0

	nb_valides = total_requetes - nb_manquantes - nb_timeouts
	pct_valides = (nb_valides / total_requetes * 100) if total_requetes > 0 else 0

	col1, col2, col3 = st.columns(3)
	col1.metric("Requêtes valides (< 30 s)", f"{nb_valides:,}", f"{pct_valides:.1f} %")
	col2.metric(
		"Données manquantes (NaN)",
		f"{nb_manquantes:,}",
		f"{pct_manquantes:.1f} %",
		delta_color="inverse",
	)
	col3.metric(
		"Timeouts (≥ 30 s)",
		f"{nb_timeouts:,}",
		f"{pct_timeouts:.1f} %",
		delta_color="inverse",
	)
with tab4:
	non_tranches = selection[selection["statut"] == "non_tranche"]

	df_pays = (
		non_tranches["pays"]
		.fillna("Non renseigné")
		.value_counts()
		.reset_index()
	)
	df_pays.columns = ["Pays", "Nombre"]

	fig_pays = px.bar(
		df_pays,
		x="Nombre",
		y="Pays",
		orientation="h",
		text_auto=True,  
		title="Nombre de cas non tranchés par pays",
		color_discrete_sequence=["#450094"],  
	)

	fig_pays.update_layout(
		yaxis=dict(
			categoryorder="total ascending", title=""
		),  
		xaxis_title="Nombre de non tranchés",
		template="plotly_white",
		height=max(
			350, len(df_pays) * 30
		), 
		margin=dict(l=20, r=20, t=40, b=40),
	)

	fig_pays.update_traces(textposition="outside")  

	st.plotly_chart(fig_pays, use_container_width=True)
	st.caption("L'italie manifeste de loin le plus grand nombre de numéros non tranchés, pour lesquels il faut prendre une décision") 
           
# =============================================================================
# ÉTAPE 5 — Les numéros à traiter
# =============================================================================
st.subheader("Numéros à traiter")
# TODO A_TRAITER (étape 5) : la liste des invalides et des non tranchés, avec une colonne « action »,
#          et un bouton pour la télécharger.
# 1. Garder les lignes dont le statut n'est pas "valide" (!= veut dire « différent de ») 
a_traiter = selection[selection["statut"] != "valide"].copy() 

# 2. Ajouter une colonne "action" : .map remplace chaque statut par le texte associé 
a_traiter["action"] = a_traiter["statut"].map({ 
	"invalide": "Demander un nouveau numéro au client",
	"non_tranche": "Revérifier sur VIES avant la prochaine facture", 
}) 

# 3. Afficher le nombre et le tableau, avec les colonnes utiles pour la comptabilité 
colonnes = ["raison_sociale", "numero_saisi", "pays_declare", "statut", "motif", "action"] 
st.write(f"{len(a_traiter)} numéros demandent une action.")
st.dataframe(a_traiter[colonnes], hide_index=True) 
 
# 4. Le bouton de téléchargement 
st.download_button( 
	"Télécharger la liste", 
	a_traiter[colonnes].to_csv(index=False, sep=";").encode("utf-8-sig"), 
	file_name="numeros_a_traiter.csv", 
)
# Déjà écrit : les données brutes, cachées par défaut.
with st.expander("Voir toutes les données"):
    st.dataframe(selection, hide_index=True)
