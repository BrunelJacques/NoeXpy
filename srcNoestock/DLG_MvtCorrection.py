#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------
# Application:     Noelite et autre pouvant lancer ce module partagé
# Module:          Gestion des codes analytiques
# Auteur:          Jacques BRUNEL 2024-04
# Licence:         Licence GNU GPL
# ------------------------------------------------------------------

import wx
import os
import datetime
import xpy.ObjectListView.xGTE as xGTE
import xpy.xUTILS_Identification       as xuid
import xpy.xUTILS_DB                   as xdb
from xpy.ObjectListView.ObjectListView import ColumnDefn
from xpy.outils                 import xformat

#---------------------- Matrices de paramétres -------------------------------------

DIC_BANDEAU = {'titre': "Correction d'écritures en lot",
        'texte': "Les valeurs saisies s'appliqueront aux écritures en sortie d'écran"+
                    "\n sur les seules écritures cochées ou sur toutes si aucune cochée",
        'hauteur': 20,
        'sizeImage': (32, 32),
        'nomImage':"xpy/Images/32x32/Depannage.png",
        'bgColor': (220, 250, 220), }

DIC_INFOS = {
        'IDanalytique': "Ce code est attribué par Matthania, clé d'accès 8car",
        'abrege': "nom court de 16 caractères maxi",
        'nom': "nom détaillé 200 caractères possibles",
        'params': "Infos complémentaires sous forme balise xml, dictionnaire à respecter",
        'axe': "16 caractères, non modifiable",
         }

INFO_OLV = "<Inser>"

# Description des paramètres de la gestion des inventaires
AXES = ['ACTIVITES','VEHICULES','CONVOIS','DEBOURS']

MATRICE_PARAMS = {
("filtres", "Filtres"): [
    {'name': 'axe', 'genre': 'Choice', 'label': "Axe analytique",
                    'help': "Le choix de cet axe appelle l'ensemble des lignes concernées",
                    'value':0, 'values': AXES,
                    'ctrlAction': '',
                    'size':(260,15),
                    'ctrlMaxSize': (200, 20),
                    'txtSize': 130},
]}

def GetBoutons(dlg):
    return  [
        {'name':'btnOK','ID':wx.ID_ANY,'label':"Quitter",'help':"Cliquez ici pour sortir",
            'size':(120,35),'image':"xpy/Images/32x32/Quitter.png",'onBtn':dlg.OnFermer}
    ]

def GetDicPnlParams(dlg):
    return {
                'name':"PNL_params",
                'matrice':MATRICE_PARAMS,
                'dicBandeau':DIC_BANDEAU,
                'lblBox':True,
                'boxesSizes': [(300, 60),None],
            }

def GetOlvColonnes(dlg):
    # retourne la liste des colonnes de l'écran principal, valueGetter correspond aux champ des tables ou calculs
    lstCol = [
            ColumnDefn("pseudoID", 'centre', 0, 'IDpseudo',
                   isEditable=False), # La première colonne n'est jamais éditable, le code doit être éditable
            ColumnDefn("Code", 'left', 50, 'IDanalytique', valueSetter="",isSpaceFilling=False,
                       isEditable=True),
            ColumnDefn("Nom Court", 'left', 140, 'abrege', valueSetter="",isSpaceFilling=False,
                       isEditable=True),
            ColumnDefn("Nom Long", 'left', 300, 'nom', valueSetter="",isSpaceFilling=False,
                       isEditable=True),
            ColumnDefn("Params divers", 'left', 200, 'params', valueSetter="",isSpaceFilling=True,
                       isEditable=True)
            ]
    return lstCol

def GetOlvOptions(dlg):
    # Options paramètres de l'OLV ds PNLcorps
    return {
        'recherche': True,
        'autoAddRow': True,
        'checkColonne': False,
        'toutCocher':False,
        'toutDecocher':False,
        'msgIfEmpty': "Aucune ligne présente pour cet axe",
        'dictColFooter': {"nom": {"mode": "nombre", "alignement": wx.ALIGN_CENTER}},
    }

def GetDlgOptions(dlg):
    # Options du Dlg de lancement
    return {
        'minSize': (700, 450),
        'size': (1150, 800),
        'autoSizer': False
        }

    #----------------------- Parties de l'écrans -----------------------------------------


class DLG(xGTE.DLG_tableau):
    # ------------------- Composition de l'écran de gestion----------
    def __init__(self,date=None,**kwd):
        kwds = GetDlgOptions(self)
        self.dicOlv = {'lstColonnes': GetOlvColonnes(self)}
        self.dicOlv.update(GetOlvOptions(self))
        self.checkColonne = self.dicOlv.get('checkColonne',False)
        self.dicOlv['lstCodes'] = xformat.GetCodesColonnes(GetOlvColonnes(self))
        self.db = xdb.DB()
        self.dicOlv['db'] = self.db

        # boutons de bas d'écran - infos: texte ou objet window.  Les infos sont  placées en bas à gauche
        lstInfos = [ wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)),INFO_OLV]
        dicPied = {'lstBtns': GetBoutons(self), "lstInfos": lstInfos}

        # Propriétés de l'écran global type Dialog
        kwds['autoSizer'] = False
        kwds['dicParams'] = GetDicPnlParams(self)
        kwds['dicOlv'] = self.dicOlv
        kwds['dicPied'] = dicPied
        self.db = xdb.DB()
        kwds['db'] = self.db

        super().__init__(None, **kwds)

        self.ordi = xuid.GetNomOrdi()
        self.today = datetime.date.today()
        self.date = date

        ret = self.Init()
        if ret == wx.ID_ABORT: self.Destroy()
        self.Sizer()
        # appel des données
        self.oldParams = None
        self.GetDonnees()

    def Init(self):
        self.Bind(wx.EVT_CLOSE, self.OnFermer)
        self.InitOlv()

    # ------------------- Gestion des actions -----------------------

    def InitOlv(self):
        self.ctrlOlv.lstColonnes = GetOlvColonnes(self)
        self.ctrlOlv.lstCodesColonnes = self.ctrlOlv.GetLstCodesColonnes()
        self.ctrlOlv.InitObjectListView()

    def GetDonnees(self,dParams=None):
        # test si les paramètres ont changé
        if not dParams:
            dParams = self.pnlParams.GetValues(fmtDD=False)
        idem = True
        if self.oldParams == None :
            idem = False
        else:
            for key in ('axe',):
                if not key in self.oldParams: idem = False
                elif not key in dParams: idem = False
                elif self.oldParams[key] != dParams[key]: idem = False
        if idem : return

        attente = wx.BusyInfo("Recherche des données...", None)
        # appel des données de l'Olv principal à éditer
        lstDonnees = []

        # alimente la grille, puis création de modelObejects pr init
        self.ctrlOlv.lstDonnees = lstDonnees
        self.ctrlOlv.MAJ()
        self.oldParams = None
        del attente

    def OnImprimer(self,event):
        self.ctrlOlv.Apercu(None)

    def OnFermer(self, event):
        #wx.MessageBox("Traitement de sortie")
        if event:
            event.Skip()
        self.db.Close()
        if self.IsModal():
            self.EndModal(wx.ID_CANCEL)
        else:
            self.Close()

#------------------------ Lanceur de test  -------------------------------------------

if __name__ == '__main__':
    app = wx.App(0)
    os.chdir("..")
    dlg = DLG()
    dlg.ShowModal()
    app.MainLoop()
