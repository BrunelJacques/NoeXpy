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

MODULE = os.path.abspath(__file__).split("\\")[-1]
#---------------------- Matrices de paramétres -------------------------------------

DIC_BANDEAU = {'titre': "Gestion des codes analytiques NoeGest",
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
                    'ctrlAction': 'OnAxe',
                    'size':(260,30),
                    'ctrlMaxSize': (200, 20),
                    'txtSize': 130},
]}

def GetBoutons(dlg):
    return  [
        {'name':'btnOK','ID':wx.ID_ANY,'label':"Quitter",'help':"Cliquez ici pour sortir",
            'size':(120,35),'image':"xpy/Images/32x32/Quitter.png",'onBtn':dlg.OnFermer}
    ]

def GetAnalytiques(db, axe="%%",**kwd):
    # appel des items Analytiques de l'axe précisé
    filtreTxt = kwd.pop('filtreTxt','')
    if filtreTxt and len(filtreTxt)>0:
        filtreTxt = """
            AND (IDanalytique LIKE %%%s%%)
            AND (abrege LIKE %%%s%%)
            AND (nom LIKE %%%s%%)
            AND (params LIKE %%%s%%)"""
    req = """   
            SELECT "0",IDanalytique, abrege, nom, params, axe
            FROM cpta_analytiques
            WHERE (( axe Like '%s') %s)
            GROUP BY "0",IDanalytique, abrege, nom, params, axe
            ORDER BY IDanalytique;
            """ %(axe,filtreTxt)
    lstDonnees = []
    retour = db.ExecuterReq(req, mess='DLG_Analytique.GetAnalytiques')
    if retour == "ok":
        recordset = db.ResultatReq()
        lstDonnees = [list(x) for x in recordset]
    return lstDonnees

def GetOne(db,IDanalytique):
    # appel un item Analytique
    req = """   
            SELECT "0",IDanalytique, abrege, nom, params, axe
            FROM cpta_analytiques
            WHERE ( IDanalytique = '%s');
            """ %(IDanalytique)
    lstDonnees = None
    retour = db.ExecuterReq(req, mess='DLG_Analytique.GetAnalytiques')
    if retour == "ok":
        recordset = db.ResultatReq()
        for record in recordset:
            lstDonnees = record
    return lstDonnees

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

def GetOlvCodesSup():
    # codes dans les données olv, mais pas dans les colonnes, attributs des tracks non visibles en tableau
    return ['axe',]

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

def ValideLigne(dlg,track):
    # validation de la ligne, messageRefus sera affiché par CellEditor.GetValideLigne
    track.valide = True
    track.messageRefus = "Saisie incorrecte\n\n"

    # IDmanquant manquant
    valNulles =  (None,0," ","")
    if track.IDanalytique in valNulles :
        track.messageRefus += "L'IDanalytique n'est pas été déterminé\n"
    # IDnom ou abrégé absent
    if track.nom in valNulles:
        track.messageRefus += "Un nom est obligatoires\n"
    if track.abrege in valNulles:
        track.messageRefus += "Un abrégé est obligatoires\n"
    # envoi de l'erreur
    if track.messageRefus != "Saisie incorrecte\n\n":
        track.valide = False
        dlg.pnlPied.SetItemsInfos("Ligne non valide, non enregistrée",
                                          wx.ArtProvider.GetBitmap(wx.ART_ERROR,
                                                                   wx.ART_OTHER,
                                                                   (16, 16)))
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

    def OnEditFinishing(self,code=None,value=None,event=None):
        self.parent.pnlPied.SetItemsInfos( INFO_OLV,wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)))
        # flagSkipEdit permet d'occulter les évènements redondants. True durant la durée du traitement
        if self.flagSkipEdit : return
        self.flagSkipEdit = True

        (row, col) = self.ctrlOlv.cellBeingEdited
        track = self.ctrlOlv.GetObjectAt(row)

        # Traitement des spécificités selon les zones
        if code == 'IDanalytique':
            if track.vierge or value != track.oldDonnees[1]:
                oldRecord = GetOne(self.db,value)
                if oldRecord:
                    mess = "Code déjà présent\n\n"
                    mess += "pour l'axe '%s'\n"%oldRecord[-1]
                    mess += "%s"%str(oldRecord)
                    wx.MessageBox(mess,"Saisie Invalide")
                    value = track.oldDonnees[1]
                    if event: event.Veto(True)

        # enlève l'info de bas d'écran
        self.parent.pnlPied.SetItemsInfos( INFO_OLV,wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)))
        self.flagSkipEdit = False
        return value

    def ValideLigne(self,code,track):
        # Relais de l'appel par cellEditor à chaque colonne
        ValideLigne(self.parent,track)

    def SauveLigne(self,track):
        if not track.valide or len(track.IDanalytique) < 2:
            wx.MessageBox("Track non valide, pas enregistrée")
            return
        db = self.db
        # génération de l'od corrective dans un mouvement
        if not hasattr(track,'IDanalytique') or len(track.IDanalytique) == 0:
            mess = "Un code analytique est obligatoire"
            wx.MessageBox(mess,"Saisie incomplète")
            return
        lstDonnees = [
            ('IDanalytique', track.IDanalytique[:8]),
            ('abrege', track.abrege[:16]),
            ('nom', track.nom[:200]),
            ('params', track.params[:400]),
            ('axe', self.parent.axe[:24])]

        mess = "DLG_Analytique.SauveLigne"
        IDold = track.oldDonnees[1]
        IDanalytique = track.IDanalytique[:8]
        if IDold != IDanalytique:
            ret = 'ok'
            if not IDold in (None, ''):
                # supprime l'antérieur
                ret = db.ReqDEL('cpta_analytiques','IDanalytique',IDold,mess=mess)
            # Ajout de l'enregistrement
            if ret == 'ok':
                ret = db.ReqInsert("cpta_analytiques", lstDonnees=lstDonnees, mess=mess)
        else:
            # update du record
            ret = db.ReqMAJ("cpta_analytiques",lstDonnees,"IDanalytique",track.IDanalytique,
                      affichError=False)
            if ret != 'ok':
                print(ret, track.IDanalytique)

    def OnDelete(self,track):
        mess = "DLG_Analytique.OnDelete"
        IDanalytique = track.IDanalytique[:8]
        self.db.ReqDEL('cpta_analytiques', 'IDanalytique', IDanalytique, mess=mess)
        req = """FLUSH  TABLES cpta_analytiques;"""
        retour = self.db.ExecuterReq(req, mess=req)

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

        # boutons de bas d'écran - infos: texte ou objet window.  Les infos sont  placées en bas à gauche
        txtInfo =  "Info à suivre, aide à la saisie"
        lstInfos = [ wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)),txtInfo]
        dicPied = {'lstBtns': GetBoutons(self), "lstInfos": lstInfos}
        # Propriétés de l'écran global type Dialog
        kwds['autoSizer'] = False
        kwds['dicParams'] = GetDicPnlParams(self)
        kwds['dicOlv'] = {}
        kwds['dicPied'] = dicPied
        self.db = xdb.DB()
        kwds['db'] = self.db
        kwds['name'] = MODULE

        super().__init__(None, **kwds)

        self.ordi = xuid.GetNomOrdi()
        self.today = datetime.date.today()
        self.date = date

        ret = self.Init()
        if ret == wx.ID_ABORT: self.Destroy()
        self.Sizer()
        # appel des données
        self.oldParams = None
        self.OnAxe(None)
        self.GetDonnees()

    def Init(self):
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
        self.ctrlOlv = self.pnlOlv.ctrlOlv
        self.Bind(wx.EVT_CLOSE, self.OnFermer)
        self.InitOlv()

    # ------------------- Gestion des actions -----------------------

    def InitOlv(self):
        self.ctrlOlv.lstColonnes = GetOlvColonnes(self)
        self.ctrlOlv.lstCodesColonnes = self.ctrlOlv.GetLstCodesColonnes()
        self.ctrlOlv.rowFormatter = RowFormatter
        self.ctrlOlv.InitObjectListView()

    def OnAxe(self,event):
        self.axe= self.pnlParams.GetOneValue('axe', codeBox='filtres')
        self.GetDonnees()
        if event: event.Skip()

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

        lstDonnees = GetAnalytiques(self.db,dParams['axe'])

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
