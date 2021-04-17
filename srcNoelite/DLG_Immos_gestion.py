#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------------
# Application :    Noelite, Getion des immos
# Usage : Grille d'affichage des lignes d'immobilisation et gestion par boutons
# Auteur:          Jacques BRUNEL
# Licence:         Licence GNU GPL
# -------------------------------------------------------------------------------------

import wx
import xpy.xGestion_TableauEditor       as xgte
import xpy.xGestionConfig               as xgc
import xpy.xUTILS_SaisieParams          as xusp
import srcNoelite.UTILS_Noegest         as nunoegest
import srcNoelite.UTILS_Utilisateurs    as nuutil
from copy                       import deepcopy
from srcNoelite                 import DB_schema
from xpy.outils.ObjectListView  import ColumnDefn, CellEditor
from xpy.outils                 import xformat,xbandeau,ximport,xexport

#************************************** Paramètres PREMIER ECRAN ******************************************

MODULE = 'DLG_Immos_gestion'
TITRE = "Gestion des immobilisations"
INTRO = "Gerez les immobilisations, avant de calculer la dotation et exporter les écritures d'amortissements"

# Info par défaut
INFO_OLV = "Double clic pour modifier, ou gérer les lignes par les boutons à droite"

# Fonctions de transposition entrée à gérer pour chaque item FORMAT_xxxx pour les spécificités
def ComposeFuncImp(dlg,entete,donnees):
    # cf modèle dans DLG_Km_saisie
    lst = None
    return lst

# Description des paramètres à définir en haut d'écran pour PNL_params
MATRICE_PARAMS = {}

# description des boutons en pied d'écran et de leurs actions
def GetBoutons(dlg):
    return  [
                {'name': 'btnDot', 'label': "Calcul\ndotations",
                    'help': "Cliquez ici pour lancer l'importation du fichier de km consommés",
                    'size': (120, 35), 'image': wx.ART_UNDO,'onBtn':dlg.OnCalcul},
                {'name': 'btnExp', 'label': "Exporter\ndotations",
                    'help': "Cliquez ici pour lancer l'exportation des dotations vers la compta",
                    'size': (120, 35), 'image': wx.ART_REDO,'onBtn':dlg.OnExport},
                {'name':'btnOK','ID':wx.ID_ANY,'label':"Quitter",'help':"Cliquez ici pour fermer la fenêtre",
                    'size':(120,35),'image':"xpy/Images/32x32/Quitter.png",'onBtn':dlg.OnFermer}
            ]

# description des boutons à droite de l'écran de leurs actions
def GetOlvActions(pnl):
    # les fonctions appellées devront être présente dans PNL_corps qui implémentera les actions
    return  [
                {'name': 'ajouter',
                    'help': "Ajouter une nouvelle ligne",
                    'size': (25, 25), 
                    'image': wx.Bitmap("xpy/Images/16x16/Ajouter.png", wx.BITMAP_TYPE_ANY),
                    'onBtn': pnl.OnAjouter},
                {'name': 'modifier',
                    'help': "Modifier les propriétés de la ligne selectionnée",
                    'size': (25, 25), 
                    'image': wx.Bitmap("xpy/Images/16x16/Modifier.png", wx.BITMAP_TYPE_ANY),
                    'onBtn': pnl.OnModifier},
                {'name': 'supprimer',
                 'help': "Supprimer la ligne selectionnée",
                 'size': (25, 25),
                 'image': wx.Bitmap("xpy/Images/16x16/Supprimer.png", wx.BITMAP_TYPE_ANY),
                 'onBtn': pnl.OnSupprimer},
            ]

# paramètre les options de l'OLV
DICOLV = {
    'lstColonnes': [
                ColumnDefn("IDimmo", 'centre', 0, 'IDimmo'),
                ColumnDefn("IDcomposant", 'centre', 0, 'IDcomposant'),
                ColumnDefn("Cpte Immo", 'centre', 80, 'compteimmo'),
                ColumnDefn("Cpte Dot", 'center', 70, 'cptedot', ),
                ColumnDefn("Section", 'left', 60, 'section'),
                ColumnDefn("MiseEnServ", 'center', 80, 'miseenservice',
                           stringConverter=xformat.FmtDate,),
                ColumnDefn("Ensemble", 'center', 120, 'enemble', isSpaceFilling=True),
                ColumnDefn("Etat", 'left', 30, 'etat'),
                ColumnDefn("Composant", 'center', 120, 'composant', isSpaceFilling=True),
                ColumnDefn("Valeur", 'right', 90, 'valeur', valueSetter=0,
                           stringConverter=xformat.FmtDecimal),
                ColumnDefn("Amo", 'center', 40, 'typeamo'),
                ColumnDefn("Taux", 'right', 50, 'taux', valueSetter=0,
                           stringConverter=xformat.FmtPercent),
                ColumnDefn("Amo Antér.", 'right', 90, 'ante', valueSetter=0,
                           stringConverter=xformat.FmtDecimal),
                ColumnDefn("Dotation", 'right', 90, 'dotation',
                           stringConverter=xformat.FmtDecimal),
                ColumnDefn("Cession", 'left', 80, 'cession',
                           stringConverter=xformat.FmtDate,),
                ],
    'dictColFooter': {'composant': {"mode": "nombre", "alignement": wx.ALIGN_CENTER,'pluriel':"lignes"},
                      'valeur': {"mode": "total","alignement": wx.ALIGN_RIGHT},
                      'ante': {"mode": "total","alignement": wx.ALIGN_RIGHT},
                      'dotation': {"mode": "total","alignement": wx.ALIGN_RIGHT},
                      },
    'lstChamps': ['immobilisations.IDimmo', 'immosComposants.IDcomposant', 'immobilisations.compteImmo',
                  'immobilisations.compteDotation','immobilisations.IDanalytique', 'immosComposants.dteMiseEnService',
                  'immobilisations.libelle','immosComposants.etat', 'immosComposants.libComposant',
                  'immosComposants.valeur','immosComposants.type', 'immosComposants.tauxAmort',
                  'immosComposants.amortAnterieur','immosComposants.dotation', 'immosComposants.cessionDate'],
    'getActions': GetOlvActions,
    'minSize': (1300,400),
    'sortColumnIndex':2,
    'sortAscending':True,
    'checkColonne': False,
    'recherche': True,
    'autoAddRow': False,
    'editMode': False,
    'msgIfEmpty':"Aucune immobilisation à afficher !",
    }

#************************************ Paramètres ECRAN GESTION LIGNE **************************************

lTITRE = "Gestion d'un ensemble immobilisé"
lINTRO = "Gerez les composants d'une immobilisation dans le tableau, ou l'ensemble dans l'écran du haut."

# Info par défaut
lINFO_OLV = "Double clic pour modifier une cellule."
# Infos d'aide en pied d'écran
lDIC_INFOS = {'dteAcquisition':"Les dates peuvent se saisir 'jjmmaa' ou 'jj/mm/aa' ou 'aaaa-mm-jj'\n"+
                               "C'est la date d'acquisition du composant",
            'type':    "L pour linéraire, D pour un taux qui sera majoré pour être dégressif\n"+
                                "N pour non amortissable. Seuls L et D pourront provoquer des dotations par calcul",
            'tauxLin':    "ATTENTION c'est 100 divisé par le nombre d'années d'amortissement\n"+
                                "2ans-> 50, 3ans-> 33.33, 5ans-> 20, 7ans-> 14.29, 12ans-> 8.33, 15ans-> 6.67 etc ",
            'dotation':     "Cette zone est modifiée automatiquement par le calcul,\nune correction est ephémère",
            'valeur':      "Montant en €",
            'miseenservice': "On peut saisir jjmmaa\nC'est la date qui détermine le début de l'amortissement",
            'cessionDate': "Les dates peuvent se saisir 'jjmmaa' ou 'jj/mm/aa' ou 'aaaa-mm-jj'",
            }


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

# description des boutons en pied d'écran et de leurs actions
def lGetBoutons(dlg):
    return  [
                {'name':'btnAbandon','ID':wx.ID_CANCEL,'label':"Abandon",'help':"Cliquez ici pour fermer sans modifs",
                    'size':(120,36),'image':"xpy/Images/16x16/Abandon.png",'onBtn':dlg.OnAbandon},
                {'name':'btnOK','ID':wx.ID_ANY,'label':"Valider",'help':"Cliquez ici pour enrgistrer les modifs",
                    'size':(120,35),'image':"xpy/Images/32x32/Valider.png",'onBtn':dlg.OnValider},
            ]

# paramètre les options de l'OLV
lcutend = 2
lDICOLV = {
    'lstColonnes': xformat.GetLstColonnes(table=DB_schema.DB_TABLES['immosComposants'][:-lcutend],wxDates=False),
    'dictColFooter': {'libComposant': {"mode": "nombre", "alignement": wx.ALIGN_CENTER,'pluriel':"lignes"},
                      'valeur': {"mode": "total","alignement": wx.ALIGN_RIGHT},
                      'amortAnterieur': {"mode": "total","alignement": wx.ALIGN_RIGHT},
                      'dotation': {"mode": "total","alignement": wx.ALIGN_RIGHT},
                      },
    'lstChamps': xformat.GetLstChamps(DB_schema.DB_TABLES['immosComposants'][:-lcutend]),
    'lstChmpEns': xformat.GetLstChamps(DB_schema.DB_TABLES['immobilisations']),
    'minSize': (1350,400),
    'checkColonne': False,
    'recherche': True,
    'autoAddRow': True,
    'editMode': True,
    'msgIfEmpty':"Aucune ligne d'immobilisation à afficher !",
    }

def AdaptDicOlv(dicOlv):
    # Si dicOlv est construit directement à partir du schéma des tables, il faut personnaliser
    ix = dicOlv['lstChamps'].index('type')
    (column,) = ColumnDefn("type", 'centre', 50, 'type',
                        valueSetter='L',
                        choices=['L','D','N'],
                        isSpaceFilling=False,
                        cellEditorCreator=CellEditor.ChoiceEditor),
    dicOlv['lstColonnes'][ix] = column

    ix = dicOlv['lstChamps'].index('tauxAmort')
    column = dicOlv['lstColonnes'][ix]
    column.title = "TauxLin"
    column.valueGetter = "tauxLin"
    dicOlv['lstColonnes'][ix] = column

    ix = dicOlv['lstChamps'].index('IDimmo')
    dicOlv['lstColonnes'][ix].width = 0
    dicOlv['lstColonnes'][ix].isEditable = False
    return dicOlv

#*********************** Parties de l'écran de gestion d'un ensemble ******************

class Pnl_params(xgc.PNL_paramsLocaux):
    #panel de paramètres de l'application
    def __init__(self, parent, **kwds):
        self.parent = parent
        #('pos','size','style','name','matrice','donnees','lblBox')
        kwds = {
                'name':"Pnl_params",
                'matrice':lMATRICE_PARAMS,
                'lblBox':None,
                'pathdata':"srcNoelite/Data",
                'nomfichier':"params",
                'nomgroupe': MODULE
                }
        super().__init__(parent, **kwds)
        self.Init()

class Pnl_corps(xgte.PNL_corps):
    #panel olv avec habillage optionnel pour des boutons actions (à droite) des infos (bas gauche) et boutons sorties
    def __init__(self, parent, dicOlv,*args, **kwds):
        xgte.PNL_corps.__init__(self,parent,dicOlv,*args,**kwds)
        self.ctrlOlv.Choices={}
        self.flagSkipEdit = False
        self.oldRow = None

    def OnEditStarted(self,code,track=None,editor=None):
        # affichage de l'aide
        if code in lDIC_INFOS.keys():
            self.parent.pnlPied.SetItemsInfos( lDIC_INFOS[code],
                                               wx.ArtProvider.GetBitmap(wx.ART_FIND, wx.ART_OTHER, (16, 16)))
        else:
            self.parent.pnlPied.SetItemsInfos( INFO_OLV,wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)))
        row, col = self.ctrlOlv.cellBeingEdited

        if not self.oldRow: self.oldRow = row
        if row != self.oldRow:
            track = self.ctrlOlv.GetObjectAt(self.oldRow)
            test = self.parent.noegest.ValideLigneComposant(track)
            if test:
                track.valide = True
                self.oldRow = row
            else:
                track.valide = False
        track = self.ctrlOlv.GetObjectAt(row)
        if code == 'comptefrn':
            pass
        # conservation de l'ancienne valeur
        track.oldValue = None
        try:
            eval("track.oldValue = track.%s"%code)
        except: pass

    def OnEditFinishing(self,code=None,value=None,parent=None):
        self.parent.pnlPied.SetItemsInfos( INFO_OLV,wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)))
        # flagSkipEdit permet d'occulter les évènements redondants. True durant la durée du traitement
        row, col = self.ctrlOlv.cellBeingEdited
        if self.flagSkipEdit : return
        self.flagSkipEdit = True
        track = self.ctrlOlv.GetObjectAt(row)

        # si pas de saisie on passe
        if (not value) or track.oldValue == value:
            self.flagSkipEdit = False
            return

        # l'enregistrement de la ligne se fait à chaque saisie pour gérer les montées et descentes
        okSauve = False

        # Traitement des spécificités selon les zones
        if code == 'dteAcquisition':
            if track.old_data != value:
                track.miseenservice = value
                ix = self.ctrlOlv.lstCodesColonnes.index('dteMiseEnService')
                track.donnees[ix] = track.miseenservice
                self.ctrlOlv.Refresh()


        # l'enregistrement de la ligne se fait à chaque saisie pour gérer les montées et descentes
        self.parent.noegest.ValideLigneComposant(track)


        # enlève l'info de bas d'écran
        self.parent.pnlPied.SetItemsInfos( INFO_OLV,wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)))
        self.flagSkipEdit = False

    def OnDelete(self,noligne,track,parent=None):
        pass

    def OnEditFunctionKeys(self,event):
        row, col = self.ctrlOlv.cellBeingEdited
        track = self.ctrlOlv.GetObjectAt(row)
        code = self.ctrlOlv.lstCodesColonnes[col]
        if event.GetKeyCode() == wx.WXK_F4 and code == 'vehicule':
            # F4 Choix
            dict = self.parent.noegest.GetVehicule(filtre=track.vehicule,mode='F4')
            if dict:
                self.OnEditFinishing('vehicule',dict['abrege'])
                track.vehicule = dict['abrege']
                track.nomvehicule = dict['nom']
                track.IDvehicule = dict['idanalytique']

class Pnl_pied(xgte.PNL_pied):
    #panel infos (gauche) et boutons sorties(droite)
    def __init__(self, parent, dicPied, **kwds):
        xgte.PNL_pied.__init__(self,parent, dicPied, **kwds)

class Dlg_immo(xusp.DLG_vide):
    # ------------------- Composition de l'écran de gestion des composants d'une immo ---
    def __init__(self,IDimmo=None):
        super().__init__(self,name = MODULE)
        self.IDimmo = IDimmo
        self.ctrlOlv = None
        self.dicOlv = AdaptDicOlv(lDICOLV)
        self.noegest = nunoegest.Noegest(self)
        self.IDutilisateur = nuutil.GetIDutilisateur()
        if (not self.IDutilisateur) or not nuutil.VerificationDroitsUtilisateurActuel('facturation_factures','creer'):
            self.Destroy()
        self.Init()
        self.Sizer()

    # Initialisation des panels
    def Init(self):
        # boutons de bas d'écran - infos: texte ou objet window.  Les infos sont  placées en bas à gauche
        lstInfos = [ wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)),lINFO_OLV]
        dicPied = {'lstBtns': lGetBoutons(self), "lstInfos": lstInfos}

        # lancement de l'écran en blocs principaux
        self.pnlBandeau = xbandeau.Bandeau(self,lTITRE,lINTRO,nomImage="xpy/Images/32x32/Matth.png")
        self.pnlParams = Pnl_params(self)
        self.pnlOlv = Pnl_corps(self, self.dicOlv)
        self.pnlPied = Pnl_pied(self, dicPied)
        self.ctrlOlv = self.pnlOlv.ctrlOlv
        self.Bind(wx.EVT_CLOSE,self.OnFermer)
        # placement des données
        if self.IDimmo:
            self.noegest.GetEnsemble(self.IDimmo,self.dicOlv['lstChmpEns'],self.pnlParams)
            self.noegest.GetComposants(self.IDimmo,self.dicOlv['lstChamps'])
        for object in self.ctrlOlv.modelObjects:
            self.noegest.ValideLigneComposant(object)
        self.ctrlOlv._FormatAllRows()
        self.ctrlOlv.Refresh()
        # conservation des originaux
        self.modelOriginal = [deepcopy(x) for x in self.ctrlOlv.modelObjects if not hasattr(x,'vierge')]
        self.ddParamsOriginal = self.pnlParams.GetValues()
        if self.IDimmo:
            self.pnlParams.SetOneValue('mode','Modification',codeBox='infos')
        else: self.pnlParams.SetOneValue('mode','Création',codeBox='infos')
        self.pnlParams.Refresh()

    def Sizer(self):
        sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=0, hgap=0)
        sizer_base.Add(self.pnlBandeau, 1, wx.TOP | wx.EXPAND, 3)
        sizer_base.Add(self.pnlParams, 1, wx.TOP , 3)
        sizer_base.Add(self.pnlOlv, 1, wx.TOP | wx.EXPAND, 3)
        sizer_base.Add(self.pnlPied, 0, wx.ALL | wx.EXPAND, 3)
        sizer_base.AddGrowableCol(0)
        sizer_base.AddGrowableRow(1)
        self.CenterOnScreen()
        self.SetSizerAndFit(sizer_base)
        self.CenterOnScreen()

    def OnBtnSection(self,event):
        wx.MessageBox("La recherche est prévue mais pas encore fait!")

    def OnAbandon(self,event):
        self.OnFermer(event)

    def OnValider(self,event):
        ddParams = self.pnlParams.GetValues()
        flag = False
        for boxname, dict in ddParams.items():
            for ctrl, value in dict.items():
                if self.ddParamsOriginal[boxname][ctrl] !=  value:
                    flag = True
                    break
        if len(self.ctrlOlv.modelObjects) == 0 or (len(self.ctrlOlv.modelObjects)==1
                                                   and self.ctrlOlv.modelObjects[0].vierge):
            # supprime un ensemble sans composants
            self.noegest.DelEnsemble(self.IDimmo)
        elif flag:
            # le cartouche ensemble a été modifié
            self.IDimmo = self.noegest.SetEnsemble(self.IDimmo,self.pnlParams)
        lstNews, lstCancels, lstModifs = xformat.CompareModels(self.modelOriginal,self.ctrlOlv.modelObjects)
        if (lstNews,lstCancels,lstModifs) != ([],[],[]):
            self.noegest.SetComposants(self.IDimmo,lstNews,lstCancels,lstModifs,self.dicOlv['lstChamps'])
        self.OnFermer(event)

#*********************** Parties de l'écran d'affichage de la liste *******************

class PNL_params(xgc.PNL_paramsLocaux):
    #panel de paramètres de l'application
    def __init__(self, parent, **kwds):
        self.parent = parent
        #('pos','size','style','name','matrice','donnees','lblBox')
        kwds = {
                'name':"PNL_params",
                'matrice':MATRICE_PARAMS,
                'lblBox':None,
                'pathdata':"srcNoelite/Data",
                'nomfichier':"params",
                'nomgroupe': MODULE
                }
        super().__init__(parent, **kwds)
        self.Init()

class PNL_corps(xgte.PNL_corps):
    #panel olv avec habillage optionnel pour des boutons actions (à droite) des infos (bas gauche) et boutons sorties
    def __init__(self, parent, dicOlv,*args, **kwds):
        xgte.PNL_corps.__init__(self,parent,dicOlv,*args,**kwds)
        self.ctrlOlv.Bind(wx.EVT_LEFT_DCLICK,self.OnModifier)

    def OnAjouter(self,evt):
        row = 0
        if self.ctrlOlv.GetSelectedObject():
            row =  self.ctrlOlv.modelObjects.index(self.ctrlOlv.GetSelectedObject())
        dlg = Dlg_immo()
        dlg.ShowModal()
        self.parent.noegest.GetImmosComposants(self.parent.dicOlv['lstChamps'])
        self.ctrlOlv.Select(row)
        return

    def OnModifier(self,evt):
        row = 0
        if self.ctrlOlv.GetSelectedObject():
            row =  self.ctrlOlv.modelObjects.index(self.ctrlOlv.GetSelectedObject())
        if not self.ctrlOlv.GetSelectedObject():
            wx.MessageBox("Il vous faut sélectionner une ligne pour pouvoir la modifier!!")
            return
        track = self.ctrlOlv.GetSelectedObject()
        IDimmo = track.IDimmo
        dlg = Dlg_immo(IDimmo=IDimmo)
        dlg.ShowModal()
        self.parent.noegest.GetImmosComposants(self.parent.dicOlv['lstChamps'])
        self.ctrlOlv.Select(row)
        return

    def OnSupprimer(self,evt):
        wx.MessageBox("Pour supprimer, passez en modification puis supprimez les lignes superflues de l'ensemble")
        return

class PNL_pied(xgte.PNL_pied):
    #panel infos (gauche) et boutons sorties(droite)
    def __init__(self, parent, dicPied, **kwds):
        xgte.PNL_pied.__init__(self,parent, dicPied, **kwds)

class DLG_immos(xusp.DLG_vide):
    # ------------------- Composition de l'écran de gestion----------
    def __init__(self,parent):
        super().__init__(parent,name = MODULE)
        self.ctrlOlv = None
        self.dicOlv = DICOLV
        self.noegest = nunoegest.Noegest(self)
        self.IDutilisateur = nuutil.GetIDutilisateur()
        if (not self.IDutilisateur) or not nuutil.VerificationDroitsUtilisateurActuel('facturation_factures','creer'):
            self.Destroy()
        self.Init()
        self.Sizer()

    # Initialisation des panels
    def Init(self):
        # boutons de bas d'écran - infos: texte ou objet window.  Les infos sont  placées en bas à gauche
        lstInfos = [ wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)),INFO_OLV]
        dicPied = {'lstBtns': GetBoutons(self), "lstInfos": lstInfos}

        # lancement de l'écran en blocs principaux
        self.pnlBandeau = xbandeau.Bandeau(self,TITRE,INTRO,nomImage="xpy/Images/32x32/Matth.png")
        self.pnlParams = PNL_params(self)
        self.pnlOlv = PNL_corps(self, self.dicOlv)
        self.pnlPied = PNL_pied(self, dicPied)
        self.ctrlOlv = self.pnlOlv.ctrlOlv
        self.Bind(wx.EVT_CLOSE,self.OnFermer)
        self.noegest.GetImmosComposants(self.dicOlv['lstChamps'])

    def Sizer(self):
        sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=0, hgap=0)
        sizer_base.Add(self.pnlBandeau, 1, wx.TOP | wx.EXPAND, 3)
        sizer_base.Add(self.pnlParams, 1, wx.TOP | wx.EXPAND, 3)
        sizer_base.Add(self.pnlOlv, 1, wx.TOP | wx.EXPAND, 3)
        sizer_base.Add(self.pnlPied, 0, wx.ALL | wx.EXPAND, 3)
        sizer_base.AddGrowableCol(0)
        sizer_base.AddGrowableRow(1)
        self.CenterOnScreen()
        self.SetSizerAndFit(sizer_base)
        self.CenterOnScreen()

    def GetDonneesIn(self,nomFichier):
        # importation des donnéees du fichier entrée
        entrees = None
        if nomFichier[-4:].lower() == 'xlsx':
            entrees = ximport.GetFichierXlsx(nomFichier,maxcol=7)
        elif nomFichier[-3:].lower() == 'xls':
            entrees = ximport.GetFichierXls(nomFichier,maxcol=7)
        else: wx.MessageBox("Il faut choisir un fichier .xls ou .xlsx",'NomFichier non reconnu')
        # filtrage des premières lignes incomplètes
        entete = None
        if entrees:
            for ix in range(len(entrees)):
                sansNull= [x for x in entrees[ix] if x]
                if len(sansNull)>5:
                    entete = entrees[ix]
                    entrees = entrees[ix + 1:]
                    break
        return entete,entrees

    def OnExport(self,event):
        wx.MessageBox("Non développé! ")

    def OnCalcul(self,event):
        exercice = self.noegest.ChoixExercice()
        if exercice:
            ixdot = self.ctrlOlv.lstCodesColonnes.index('dotation')
            ixetat = self.ctrlOlv.lstCodesColonnes.index('etat')
            lstChamps = ['IDcomposant','etat','dotation']
            lstModifs = []
            debex = exercice[0]
            finex = exercice[1]
            for track in self.ctrlOlv.modelObjects:
                # si l'état a été forcé la cession n'est pas après l'exercice, on ne dote pas l'exercice
                if track.etat.upper() in ('R','C') and track.cession <= finex: continue
                # l'absence de taux le fait non amortissable
                if not track.taux : continue
                if not track.typeamo in ('D','L'): continue
                if not track.ante: track.ante = 0.0
                vnc = track.valeur - track.ante
                tauxlin = track.taux
                if track.typeamo == 'D':
                    #même en dégressif le taux saisi était celui du linéaire, soit: 1/nbre années
                    tauxdot = tauxlin
                    if tauxlin < 50.0 :
                        tauxdot = tauxlin * 1.25
                    if tauxlin <= 25.0:
                        tauxdot = tauxlin * 1.75
                    if tauxlin <= 16.6:
                        tauxdot = tauxlin * 2.25
                    basedot = vnc
                    entree = xformat.DebutDeMois(track.miseenservice)
                elif track.typeamo == "L":
                    tauxdeg = 0.0
                    tauxdot = tauxlin
                    basedot = track.valeur
                    entree = track.miseenservice
                proratacumul = xformat.ProrataCommercial(track.miseenservice,track.cession,track.miseenservice,finex)
                # calcul correctif pour le mini dégressif
                cumulamolin = track.valeur * tauxlin * proratacumul / 100
                prorataex = xformat.ProrataCommercial(entree,track.cession,debex,finex)
                dotcalculex = round(basedot * tauxdot * prorataex / 100,2)

                cumulamosdot = track.ante + dotcalculex
                if dotcalculex > 0.0 and cumulamolin > cumulamosdot:
                    correctif = cumulamolin - track.ante - dotcalculex
                    if correctif > 5:
                        dotcalculex += correctif
                dotation = round(min(dotcalculex,vnc),2)
                # seules les modifs seront enregistrées
                if track.dotation != dotation:
                    track.dotation = dotation
                    track.donnees[ixdot] = dotation
                    if vnc - dotation <= 0.01:
                        track.etat = 'A'
                        track.donnees[ixetat] = 'A'
                    lstModifs.append([track.IDcomposant,track.etat,track.dotation])
            if len(lstModifs) > 0:
                self.noegest.SetComposants(None, [], [], lstModifs, lstChamps)
            self.ctrlOlv.MAJ()

    def OnImporter(self,event):
        """ Open a file"""
        self.dirname = ''
        dlg = wx.FileDialog(self, "Choisissez un fichier à importer", self.dirname)
        nomFichier = None
        if dlg.ShowModal() == wx.ID_OK:
            nomFichier = dlg.GetPath()
        dlg.Destroy()
        if not nomFichier: return
        entete,donnees = self.GetDonneesIn(nomFichier)
        if donnees:
            donExist = [x.donnees for x in self.ctrlOlv.modelObjects]
            if len(donExist)>0:
                ix = self.ctrlOlv.lstCodesColonnes.index('conso')
                if xformat.Nz(donExist[-1][ix]) == 0:
                    del donExist[-1]
                    del self.ctrlOlv.modelObjects[-1]
            donNew = ComposeFuncImp(self,entete,donnees)
            self.ctrlOlv.lstDonnees = donExist + donNew
            # ajout de la ligne dans olv
            self.ctrlOlv.AddTracks(donNew)
            # test de validité pour changer la couleur de la ligne
            for object in self.ctrlOlv.modelObjects:
                self.noegest.ValideLigne(object)
                self.noegest.SauveLigne(object)
            self.ctrlOlv._FormatAllRows()
            self.ctrlOlv.Refresh()

#------------------------ Lanceur de test  -------------------------------------------

if __name__ == '__main__':
    import os
    app = wx.App()
    os.chdir("..")
    frame_1 = wx.Frame()
    app.SetTopWindow(frame_1)

    #frame_1.dlg = DLG_implantation(frame_1)
    frame_1.dlg = DLG_immos(frame_1)
    frame_1.dlg.ShowModal()
    app.MainLoop()

    #dlg = Dlg_immo(IDimmo=3)
