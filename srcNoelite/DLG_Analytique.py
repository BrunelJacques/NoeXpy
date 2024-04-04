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

DIC_BANDEAU = {'titre': "Gestion des codes analytiques communs à Noethys",
        'texte': "La saisie dans le tableau modifie la table cpta_analytiques\n"+
                 "Choisissez l'axe que vous souhaitez gérer",
        'hauteur': 20,
        'sizeImage': (60, 60),
        'nomImage':"xpy/Images/80x80/Analytic.png",
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
                    'size':(260,15),
                    'ctrlMaxSize': (200, 20),
                    'txtSize': 130},
]}

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
            ColumnDefn("Code", 'left', 50, 'IDanalytique', valueSetter=" ",isSpaceFilling=False,
                       isEditable=True),
            ColumnDefn("Nom Court", 'left', 140, 'abrege', valueSetter=" ",isSpaceFilling=False,
                       isEditable=True),
            ColumnDefn("Nom Long", 'left', 300, 'nom', valueSetter=" ",isSpaceFilling=False,
                       isEditable=True),
            ColumnDefn("Params divers", 'left', 200, 'params', valueSetter=" ",isSpaceFilling=True,
                       isEditable=True)
            ]
    return lstCol

def GetOlvCodesSup():
    # codes dans les données olv, mais pas dans les colonnes, attributs des tracks non visibles en tableau
    return ['axe',]

def GetOlvOptions(dlg):
    # Options paramètres de l'OLV ds PNLcorps
    return {
        'recherche': True,
        'autoAddRow': False,
        'toutCocher':True,
        'toutDecocher':True,
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

def ValideLigne(dlg,track):

    # validation de la ligne de inventaire
    track.valide = True
    track.messageRefus = "Saisie incorrecte\n\n"

    # envoi de l'erreur
    if track.messageRefus != "Saisie incorrecte\n\n":
        track.valide = False
    else: track.messageRefus = ""
    return

def RowFormatter(listItem, track):
    anomalie = None
    if False:
        anomalie = True
    if anomalie:
        # anomalie rouge / fushia
        listItem.SetTextColour(wx.RED)
        listItem.SetBackgroundColour(wx.Colour(255, 180, 200))

class PNL_corps(xGTE.PNL_corps):
    #panel olv avec habillage optionnel pour des boutons actions (à droite) des infos (bas gauche) et boutons sorties
    def __init__(self, parent, dicOlv,*args, **kwds):
        xGTE.PNL_corps.__init__(self,parent,dicOlv,*args,**kwds)
        self.db = parent.db

    def ValideParams(self):
        return

    def OnEditStarted(self,code,track=None,editor=None):
        # affichage de l'aide
        if code in DIC_INFOS.keys():
            self.parent.pnlPied.SetItemsInfos( DIC_INFOS[code],
                                               wx.ArtProvider.GetBitmap(wx.ART_FIND, wx.ART_OTHER, (16, 16)))
        else:
            self.parent.pnlPied.SetItemsInfos( INFO_OLV,wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)))

    def OnEditFinishing(self,code=None,value=None,editor=None):
        self.parent.pnlPied.SetItemsInfos( INFO_OLV,wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)))
        # flagSkipEdit permet d'occulter les évènements redondants. True durant la durée du traitement
        if self.flagSkipEdit : return
        self.flagSkipEdit = True

        (row, col) = self.ctrlOlv.cellBeingEdited
        track = self.ctrlOlv.GetObjectAt(row)

        # Traitement des spécificités selon les zones
        if code == 'qteStock' or code == 'pxUn':
            # force la tentative d'enregistrement même en l'absece de saisie
            track.noSaisie = False

        # enlève l'info de bas d'écran
        self.parent.pnlPied.SetItemsInfos( INFO_OLV,wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)))
        self.flagSkipEdit = False
        return value

    def ValideLigne(self,code,track):
        # Relais de l'appel par cellEditor à chaque colonne
        ValideLigne(self.parent,track)

    def SauveLigne(self,track):
        db = self.db
        track.qteMvts += track.deltaQte

        # génération de l'od corrective dans un mouvement
        if not hasattr(track,'IDmouvement'):
            track.IDmouvement = None
            track.qteMvtsOld = 0.0
        lstDonnees = [
            ('IDarticle', track.IDarticle),
            ('prixUnit', track.pxUn),
            ('ordi', self.parent.ordi),
            ('dateSaisie', self.parent.today),
            ('modifiable', 1),]
        if track.IDmouvement :
            qteMvts = track.deltaQte + track.qteMvtsOld
            lstDonnees += [('qte', qteMvts),]
            ret = db.ReqMAJ("stMouvements", lstDonnees,
                            "IDmouvement", track.IDmouvement,
                            mess="DLG_Inventaires.SauveLigne Modif: %d"%track.IDmouvement)
        else:
            qteMvts = track.deltaQte
            ret = 'abort'
            if qteMvts != 0.0:
                lstDonnees += [('origine', 'od_in'),
                               ('qte', qteMvts),
                               ('date', self.parent.date),
                               ('IDanalytique', '00'),
                               ]
                ret = db.ReqInsert("stMouvements",lstDonnees= lstDonnees, mess="DLG_Inventaires.SauveLigne Insert")
        if ret == 'ok':
            track.IDmouvement = db.newID
            track.qteMvtsOld = qteMvts

        # MAJ de l'article
        lstDonnees = [('qteStock',track.qteMvts),
                      ('prixMoyen',track.pxUn),
                      ]
        mess = "MAJ article '%s'"%track.IDarticle
        db.ReqMAJ('stArticles',lstDonnees,'IDarticle',track.IDarticle,mess=mess,IDestChaine=True)

class DLG(xGTE.DLG_tableau):
    # ------------------- Composition de l'écran de gestion----------
    def __init__(self,date=None,**kwd):
        kwds = GetDlgOptions(self)
        self.dicParams = GetDicPnlParams(self)
        self.dicOlv = {'lstColonnes': GetOlvColonnes(self)}
        self.dicOlv.update({'lstCodesSup': GetOlvCodesSup()})
        self.dicOlv.update(GetOlvOptions(self))
        self.checkColonne = self.dicOlv.get('checkColonne',False)
        self.dicOlv['lstCodes'] = xformat.GetCodesColonnes(GetOlvColonnes(self))
        self.dicOlv['db'] = xdb.DB()

        # Propriétés de l'écran global type Dialog
        kwds = GetDlgOptions(self)
        kwds['autoSizer'] = False
        kwds['dicParams'] = GetDicPnlParams(self)
        kwds['dicOlv'] = {}
        kwds['dicPied'] = {}
        kwds['db'] = xdb.DB()

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
        self.db = xdb.DB()
        self.pnlParams.SetOneValue('date',self.date, codeBox='param1')
        # définition de l'OLV
        self.ctrlOlv = None
        # récup des modesReglements nécessaires pour passer du texte à un ID d'un mode ayant un mot en commun
        for colonne in self.dicOlv['lstColonnes']:
            if 'mode' in colonne.valueGetter:
                choicesMode = colonne.choices
            if 'libelle' in colonne.valueGetter:
                self.libelleDefaut = colonne.valueSetter

        self.pnlOlv = PNL_corps(self, self.dicOlv)
        #self.pnlPied = PNL_pied(self, dicPied)
        self.ctrlOlv = self.pnlOlv.ctrlOlv
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        self.InitOlv()

    # ------------------- Gestion des actions -----------------------

    def InitOlv(self):
        self.ctrlOlv.lstColonnes = GetOlvColonnes(self)
        self.ctrlOlv.lstCodesColonnes = self.ctrlOlv.GetLstCodesColonnes()
        self.ctrlOlv.rowFormatter = RowFormatter
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
                if not key in self.oldParams.keys(): idem = False
                elif not key in dParams.keys(): idem = False
                elif self.oldParams[key] != dParams[key]: idem = False
        if idem : return

        attente = wx.BusyInfo("Recherche des données...", None)
        # appel des données de l'Olv principal à éditer

        lstDonnees = []

        # alimente la grille, puis création de modelObejects pr init
        self.ctrlOlv.lstDonnees = lstDonnees
        self.ctrlOlv.MAJ()
        # les écritures reprises sont censées être valides
        for track in self.ctrlOlv.modelObjects[:-1]:
            track.IDmouvement = None
        self.oldParams = None
        del attente

    def OnImprimer(self,event):
        self.ctrlOlv.Apercu(None)

    def OnClose(self,event):
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
