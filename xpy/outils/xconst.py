#!/usr/bin/python3
# -*- coding: utf-8 -*-

#  Jacques Brunel x Sébastien Gouast x Ivan Lucas
#  MATTHANIA - Projet XPY - xconst.py (constantes)
#  2019/04/18

from wx import FONTWEIGHT_NORMAL, FONTWEIGHT_LIGHT, FONTWEIGHT_BOLD
from wx import ALIGN_LEFT, ALIGN_CENTER, ALIGN_RIGHT
from wx import PRINT_QUALITY_DRAFT, PRINT_QUALITY_LOW, PRINT_QUALITY_MEDIUM, PRINT_QUALITY_HIGH

# repris dans plusieurs fichiers

SYMBOLE = "€"

PREFIXE_DOSSIER_IMG = "xpy/"


LISTE_JOURS = ["Lundi", "Mardi", "Mercredi","Jeudi","Vendredi", "Samedi", "Dimanche"]

LISTE_MOIS = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet","Août",
              "Septembre", "Octobre", "Novembre", "Décembre"]

LISTE_MOIS_ABREGE =[("Janv."), ("Fév."), ("Mars"), ("Avril"), ("Mai"), ("Juin"), ("Juil."),
                    ("Août"), ("Sept."), ("Oct."), ("Nov."), ("Déc.")]

PREMIER_32X32_IMG = PREFIXE_DOSSIER_IMG + "Images/32x32/Premier.png"
PRECEDENT_32X32_IMG = PREFIXE_DOSSIER_IMG + "Images/32x32/Precedent.png"
SUIVANT_32X32_IMG = PREFIXE_DOSSIER_IMG + "Images/32x32/Suivant.png"
DERNIER_32X32_IMG = PREFIXE_DOSSIER_IMG + "Images/32x32/Dernier.png"
FERMER_32X32_IMG = PREFIXE_DOSSIER_IMG + "Images/32x32/Annuler.png"
IMPRIMANTE_32X32_IMG = PREFIXE_DOSSIER_IMG + "Images/32x32/Imprimante.png"
IMPRIMERx1_32X32_IMG = PREFIXE_DOSSIER_IMG + "Images/32x32/Imprimer-x1.png"
IMPRIMERx2_32X32_IMG = PREFIXE_DOSSIER_IMG + "Images/32x32/Imprimer-x2.png"
ZOOM_MOINS_32X32_IMG = PREFIXE_DOSSIER_IMG + "Images/32x32/Zoom_moins.png"
ZOOM_PLUS_32X32_IMG = PREFIXE_DOSSIER_IMG + "Images/32x32/Zoom_plus.png"
EMAILS_EXP_32X32_IMG = PREFIXE_DOSSIER_IMG + "Images/32x32/Emails_exp.png"
VALIDER_32X32_IMG = PREFIXE_DOSSIER_IMG + "Images/32x32/Valider.png"
ANNULER_32X32_IMG = PREFIXE_DOSSIER_IMG + "Images/32x32/Annuler.png"
DOCUMENT_PARAM_32X32_IMG = PREFIXE_DOSSIER_IMG + "Images/32x32/Document_parametres.png"
ORIENTATION_VER_32X32_IMG = PREFIXE_DOSSIER_IMG + "Images/32x32/Orientation_vertical.png"
ORIENTATION_HOR_32X32_IMG = PREFIXE_DOSSIER_IMG + "Images/32x32/Orientation_horizontal.png"

MECANISME_16X16_IMG = PREFIXE_DOSSIER_IMG + "Images/16x16/Mecanisme.png"
MAGIQUE_16X16_IMG = PREFIXE_DOSSIER_IMG + "Images/16x16/Magique.png"
ACTUALISER_16X16_IMG = PREFIXE_DOSSIER_IMG + "Images/16x16/Actualiser.png"
ABANDON_16X16_IMG = PREFIXE_DOSSIER_IMG + "Images/16x16/Abandon.png"
SAUVEGARDER_16X16_IMG = PREFIXE_DOSSIER_IMG + "Images/16x16/Sauvegarder.png"
APERCU_16X16_IMG = PREFIXE_DOSSIER_IMG + "Images/16x16/Apercu.png"
TEXTE2_16X16_IMG = PREFIXE_DOSSIER_IMG + "Images/16x16/Texte2.png"
EXCEL_16X16_IMG = PREFIXE_DOSSIER_IMG + "Images/16x16/Excel.png"
COPIER_16X16_IMG = PREFIXE_DOSSIER_IMG + "Images/16x16/Copier.png"
COUPER_16X16_IMG = PREFIXE_DOSSIER_IMG + "Images/16x16/Couper.png"
COLLER_16X16_IMG = PREFIXE_DOSSIER_IMG + "Images/16x16/Coller.png"
COCHER_16X16_IMG = PREFIXE_DOSSIER_IMG + "Images/16x16/Cocher.png"
DECOCHER_16X16_IMG = PREFIXE_DOSSIER_IMG + "Images/16x16/Decocher.png"
IMPRIMANTE_16X16_IMG = PREFIXE_DOSSIER_IMG + "Images/16x16/Imprimante.png"
ACTIVITE_16X16_IMG = PREFIXE_DOSSIER_IMG + "Images/16x16/Activite.png"
FILTRE_16X16_IMG = PREFIXE_DOSSIER_IMG + "Images/16x16/Filtre.png"
FILTREOUT_16X16_IMG = PREFIXE_DOSSIER_IMG + "Images/16x16/Filtre_supprimer.png"

# -----------------------------------------------------------

#  outils/xtableau.py
COPIER_LIGNE = "Copier la sélection <Ctrl C>"
COUPER_LIGNE = "Couper la sélection <Ctrl X>"
COLLER_LIGNE = "Coller la sélection <Ctrl V>"
SUPPRIMER_LIGNE = "Supprimer la sélection <Suppr>"
INSERER_LIGNE = "Insérer une ligne <Inser>"
TOUT_COCHER_TXT = "Tout cocher"
TOUT_DECOCHER_TXT = "Tout décocher"
INVERSER_COCHES_TXT = "Inverser les coches"
APERCU_IMP_TXT = "Aperçu avant impression"
UN_FILTRE = "Poser un filtre"
SUPPRIMER_FILTRES = "Supprimer les filtres"
IMPRIMER_TXT = "Imprimer"
EXPORT_TEXTE_TXT = "Exporter au format texte"
EXPORT_EXCEL_TXT = "Exporter au format Excel"
COPIER_TOUT_TXT = "Copier tout le tableau"
COPIER_SELECTION_TXT = "Copier la sélection"
COPIER_COCHES_TXT = "Copier les cases cochées"
INVERSER_SELECTION_TXT = "Inverser jusqu'à la sélection"

# -----------------------------------------------------------

#  outils/xexport.py

AUCUNE_DONNEE_TXT = "Il n'y a aucune donnée dans la liste !"
SELECTIONNER_REP_TXT = "Veuillez sélectionner le répertoire de destination et le nom du fichier"
FICHIER_EXISTE_DEJA_TXT = "Un fichier portant ce nom existe déjà. \n\nVoulez-vous le remplacer ?"
FICHIER_TEXTE_CREE_TXT = "Le fichier Texte a été créé avec succès. Souhaitez-vous l'ouvrir dès maintenant ?"
ERREUR_ENREGISTR_EXCEL_TXT = "Il est impossible d'enregistrer le fichier Excel. Veuillez vérifier que ce fichier " \
                             "n'est pas déjà ouvert en arrière-plan. "
FICHIER_EXCEL_CREE_TXT = "Le fichier Excel a été créé avec succès. Souhaitez-vous l'ouvrir dès maintenant ?"

# -----------------------------------------------------------


PARAM_IMP_TXT = "Cliquez ici pour accéder à la gestion des paramètres"

REINITIALISER_PARAM_QUEST_TXT = "Souhaitez-vous vraiment réinitialiser tous les paramètres ?"
REINITIALISER_PARAM_BTN_TXT = "Cliquez ici pour réinitialiser tous les paramètres"

MEMORISER_PARAM_BTN_TXT = "Cliquez ici pour mémoriser tous les paramètres"

INCLURE_IMG_LABEL = "Inclure les images"
INCLURE_IMG_HELP = "Cochez cette case pour inclure les images"

AFFICHER_ENTETE_LABEL = "Afficher les entêtes sur chaque page"
AFFICHER_ENTETE_HELP = "Cochez cette case pour afficher les entêtes de colonne sur chaque page"

CHOIX_QUALITE_LABEL = "Qualité d'impression"
CHOIX_QUALITE_HELP = "Sélectionnez la qualité d'impression (Moyenne par défaut)"
CHOIX_QUALITE_LABELS = ["Brouillon", "Basse", "Moyenne", "Haute"]
CHOIX_QUALITE_VALEURS = [PRINT_QUALITY_DRAFT, PRINT_QUALITY_LOW, PRINT_QUALITY_MEDIUM, PRINT_QUALITY_HIGH]

MARGE_GAUCHE_LABEL = "Gauche"
MARGE_DROITE_LABEL = "Droite"
MARGE_HAUT_LABEL = "Haut"
MARGE_BAS_LABEL = "Bas"
TAILLE_MARGE_HELP = "Saisissez une taille de marge"

EPAISSEUR_TRAIT_LABEL = "Epaisseur de trait"
EPAISSEUR_TRAIT_HELP = "Saisissez une épaisseur de trait (Par défaut '0.25')"

COULEUR_TRAIT_LABEL = "Couleur de trait"
COULEUR_TRAIT_HELP = "Sélectionnez une couleur de trait"

TAILLE_TEXTE_LABEL = "Taille de texte"
TAILLE_TEXTE_HELP = "Saisissez une taille de texte (16 par défaut)"
TAILLE_TEXTE_INTRO_HELP = "Saisissez une taille de texte (7 par défaut)"
TAILLE_TEXTE_CONCL_HELP = "Saisissez une taille de texte (7 par défaut)"
TAILLE_TEXTE_TITRE_COL_HELP = "Saisissez une taille de texte (8 par défaut)"
TAILLE_TEXTE_LIGNE_HELP = "Saisissez une taille de texte (8 par défaut)"
TAILLE_TEXTE_PIED_HELP = "Saisissez une taille de texte (8 par défaut)"

STYLE_TEXTE_LABEL = "Style de texte"
STYLE_TEXTE_HELP = "Sélectionnez un style de texte"
STYLE_TEXTE_LABELS = ["Normal", "Light", "Gras"]
STYLE_TEXTE_VALEURS = [FONTWEIGHT_NORMAL, FONTWEIGHT_LIGHT, FONTWEIGHT_BOLD]

COULEUR_TEXTE_LABEL = "Couleur de texte"
COULEUR_TEXTE_HELP = "Sélectionnez une couleur"

ALIGNEMENT_TEXTE_LABEL = "Alignement du texte"
ALIGNEMENT_TEXTE_LABELS = ["Gauche", "Centre", "Droite"]
ALIGNEMENT_TEXTE_VALUES = [ALIGN_LEFT, ALIGN_CENTER, ALIGN_RIGHT]
ALIGNEMENT_TEXTE_HELP = "Sélectionnez le type d'alignement"

COULEUR_FOND_LABEL = "Couleur de fond"
COULEUR_FOND_HELP = "Sélectionnez une couleur de fond"

AUTORISER_SAUT_LIGNE_LABEL = "Autoriser saut à la ligne"
AUTORISER_SAUT_LIGNE_HELP = "Cochez cette case pour autoriser le saut à la ligne en cas de colonne trop étroite"

PIED_TEXTE_GAUCHE_LABEL = "Texte de gauche"
PIED_TEXTE_MILIEU_LABEL = "Texte du milieu"
PIED_TEXTE_DROITE_LABEL = "Texte de droite"

ORIENTATION_LABEL = "Orientation"
ORIENTATION_PORTRAIT_HELP = "Cliquez ici pour sélectionner une orientation portrait"
ORIENTATION_PAYSAGE_HELP = "Cliquez ici pour sélectionner une orientation paysage"
MODIFIER_TITRE_DOC_HELP = "Vous pouvez modifier ici le titre du document"
MODIFIER_INTRO_DOC_HELP = "Vous pouvez modifier ici l'introduction du document"
MODIFIER_CONCL_DOC_HELP = "Vous pouvez modifier ici la conclusion du document"

PARAM_IMP_TITRE = "Paramètres d'impression"
PARAM_IMP_INTRO = "Vous pouvez ici modifier les paramètres d'impression par défaut des listes. Cliquez sur le bouton " \
                  "'Mémoriser les paramètres' pour réutiliser les même paramètres pour toutes les autres impressions " \
                  "de listes. "

VALIDER_BTN_HELP = "Cliquez ici pour valider"
ANNULER_BTN_HELP = "Cliquez ici pour annuler"

# -----------------------------------------------------------

#  outils Printer.py

AFFICHER_IMPRESSION_HELP = "Cliquez ici pour afficher l'impression"
IMPRESSION_RAP_1_EX_HELP = "Cliquez ici pour lancer une impression rapide en 1 exemplaire"
IMPRESSION_RAP_2_EX_HELP = "Cliquez ici pour lancer une impression rapide en 2 exemplaires"
ALLER_PAGE_1_HELP = "Cliquez ici pour accéder à la première page"
ALLER_PAGE_PREC_HELP = "Cliquez ici pour accéder à la page précédente"
ALLER_PAGE_SUIV_HELP = "Cliquez ici pour accéder à la page suivante"
ALLER_PAGE_DERN_HELP = "Cliquez ici pour accéder à la dernière page"
ZOOM_ARR_HELP = "Cliquez ici pour faire un zoom arrière"
ZOOM_REGLETTE_HELP = "Déplacez la règlette pour zoomer"
ZOOM_AVANT_HELP = "Cliquez ici pour faire un zoom avant"
FERMER_APERCU_HELP = "Cliquez ici pour fermer l'aperçu"
PREVIEW_FRAME_TITLE = "Aperçu avant impression"
DEFAULT_FONT_NAME = "Arial"

# -----------------------------------------------------------
