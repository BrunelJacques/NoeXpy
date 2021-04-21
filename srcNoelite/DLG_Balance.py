#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------------
# Application :    Noelite, Affichage d'une balance comptable
# Usage : Grille d'affichage des lignes d'une balance
# Auteur:          Jacques BRUNEL
# Licence:         Licence GNU GPL
# -------------------------------------------------------------------------------------

import wx
import xpy.xGestion_TableauRecherche       as xgtr
import srcNoelite.UTILS_Utilisateurs    as nuutil
import srcNoelite.UTILS_Compta          as nucompta
from xpy.outils.ObjectListView  import ColumnDefn
from xpy.outils                 import xformat,xbandeau

#************************************** Paramètres PREMIER ECRAN ******************************************

MODULE = 'DLG_Balance'
TITRE = "BALANCE COMPTABLE"
INTRO = "Cette balance provient de la base de donnée comptablilité"

# Info par défaut
INFO_OLV = "Le Double clic sur une ligne permet de sortir"

# Description des paramètres à définir en haut d'écran pour PNL_params
MATRICE_PARAMS = {}

# paramètre les options de l'OLV
def GetDicOlv():
    return {
    'lstColonnes': [
                ColumnDefn("Compte", 'centre', 90, 'IDcompte'),
                ColumnDefn("Section", 'left', 60, 'section',valueSetter=''),
                ColumnDefn("Libellé du compte", 'left', 150, 'label', isSpaceFilling=True),
                ColumnDefn("Débits", 'right', 90, 'debit', valueSetter=0,stringConverter=xformat.FmtDecimal),
                ColumnDefn("Crédits", 'right', 90, 'credit', valueSetter=0,stringConverter=xformat.FmtDecimal),
                ColumnDefn("Solde", 'right', 90, 'solde', valueSetter=0,stringConverter=xformat.FmtDecimal),
                ],
    'dictColFooter': {'label': {"mode": "nombre", "alignement": wx.ALIGN_CENTER,'pluriel':"lignes"},
                      'debit': {"mode": "total","alignement": wx.ALIGN_RIGHT},
                      'credit': {"mode": "total","alignement": wx.ALIGN_RIGHT},
                      'solde': {"mode": "total","alignement": wx.ALIGN_RIGHT},
                      },
    'getDonnees': SqlBalance,
    'lstChamps': ['Numero','Intitule','Debit','Credit'],
    'minSize': (600,300),
    'sortColumnIndex':0,
    'sortAscending':True,
    'checkColonne': False,
    'recherche': True,
    'editMode': False,
    'msgIfEmpty':"Aucune écriture trouvée !",
    }

#************************************ Paramètres ECRAN GESTION LIGNE **************************************

# Description des paramètres à définir en haut d'écran pour PNL_params
lMATRICE_PARAMS = {
    ("comptes","Comptes d'amortissements"): [
            {'name': 'compteimmo', 'label': "Immobilisation", 'genre': 'texte', 'size':(200,30),
             'help': "Compte du plan comptable pour cet ensemble dans la classe 2"},
            {'name': 'comptedotation', 'label': "Dotation", 'genre': 'texte', 'size': (200, 30),
             'help': "Compte du plan comptable pour cet ensemble dans la classe 68"},
            {'name': 'idanalytique', 'label': "Section analytique", 'genre': 'texte', 'size': (400, 30),
             'help': "Section analytique s'insérant dans les deux comptes ci dessus",
             'btnLabel': "...", 'btnHelp': "Cliquez pour choisir une section analytique",
             'btnAction': 'OnBtnSection'},
            ],
    ("ensemble", "Propriétés de l'ensemble"): [
            {'name': 'libelle', 'label': "Libellé", 'genre': 'texte', 'size':(500,30),
             'help': "Libellé désignant cet ensemble"},
            {'name': 'nbreplaces', 'label': "Nombre places", 'genre': 'int', 'size':(200,30),
             'help': "Capacité ou nombre de places en service (dernière connue"},
            {'name': 'noserie', 'label': "No de série", 'genre': 'str', 'size':(200,30),
             'help': "Immatriculation des véhicules ou identification facultative"},
            ],
    ("infos", "Informations"): [
            {'name': 'mode', 'label': "", 'genre': 'texte', 'size': (100, 30),
             'enable':False},
            ],
    }

def SqlBalance(olv,**kwd):
    compta = nucompta.Compta(olv)
    return compta.GetBalance()

#*********************** Parties de l'écran d'affichage de la liste *******************

class DLG_balance(xgtr.DLG_tableau):
    # ------------------- Composition de l'écran de gestion----------
    def __init__(self,parent):
        self.dicOlv = GetDicOlv
        self.IDutilisateur = nuutil.GetIDutilisateur()
        if (not self.IDutilisateur) or not nuutil.VerificationDroitsUtilisateurActuel('facturation_factures','creer'):
            self.Destroy()
        super().__init__(parent,dicOlv=GetDicOlv())


#------------------------ Lanceur de test  -------------------------------------------

if __name__ == '__main__':
    import os
    app = wx.App()
    os.chdir("..")
    frame_1 = wx.Frame()
    app.SetTopWindow(frame_1)
    frame_1.dlg = DLG_balance(frame_1)
    frame_1.dlg.ShowModal()
    app.MainLoop()
