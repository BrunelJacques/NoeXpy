#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------
# Application:     NoeStock, gestion des stocks et prix de journée
# Module:          Saisie des effectifs présents
# Auteur:          Jacques BRUNEL 2021-04
# Licence:         Licence GNU GPL
# ------------------------------------------------------------------

import wx
import os
import datetime
import srcNoestock.UTILS_Stocks        as nust
import xpy.xGestion_TableauEditor      as xgte
import xpy.xUTILS_Identification       as xuid
import xpy.xUTILS_SaisieParams         as xusp
import xpy.xUTILS_DB                   as xdb
from xpy.outils.ObjectListView  import ColumnDefn
from xpy.outils                 import xformat,xbandeau,xboutons

#---------------------- Matrices de paramétres -------------------------------------

TITRE = "Suivi des effectifs quotidiens"
INTRO = "La saisie des effectifs quotidiens réels permet de déterminer le prix de journée, il est rapprocché " \
        + "du nombre d'inscrits payants et non payants"

DICORIGINES = {'codes':['achat','retour','od_in'],
                          'labels':['achat livraison', 'retour camp', 'od entrée']},

DIC_INFOS = {
            'IDarticle': "<F4> Choix d'un article, ou saisie directe de son code",
            'qte': "L'unité est précisée dans le nom de l'article",
            'pxUn': "HT ou TTC selon le choix en haut d'écran\nEn sortie il sert au calcul du prix de journée, en entrée pour la valeur en stock",
             }

INFO_OLV = "<Suppr> <Inser> <Ctrl C> <Ctrl V>"

# Description des paramètres à choisir en haut d'écran

class CtrlAnterieur(wx.Panel):
    # controle inséré dans la matrice_params qui suit. De genre AnyCtrl pour n'utiliser que le bind bouton
    def __init__(self,parent):
        super().__init__(parent,wx.ID_ANY)
        kwd = {'label':"Rappeler\nl'antérieur",
               'name':'rappel',
               'image':wx.ArtProvider.GetBitmap(wx.ART_FIND,size=(24,24)),
               'help':"Pour reprendre une saisie antérieurement validée",
               'size' : (130,40)}
        self.btn = xboutons.BTN_action(self,**kwd)
        self.Sizer()

    def Sizer(self):
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.btn,1,wx.EXPAND, 0)
        self.SetSizer(box)

    def SetValue(self,value):
        return

    def GetValue(self):
        return None

    def Set(self,values):
        # valeurs multiples
        return

MATRICE_PARAMS = {
("param1", "Paramètres"): [
    {'name': 'origine', 'genre': 'Choice', 'label': "Nature d'entrée",
                    'help': "Le choix de la nature modifie certains contrôles",
                    'value':0, 'values':[],
                    'ctrlAction': 'OnOrigine',
                    'size':(205,30),
                    'txtSize': 90},
    {'name': 'date', 'genre': 'Texte', 'label': "Date d'entrée",
                    'help': "%s\n%s\n%s"%("Saisie JJMMAA ou JJMMAAAA possible.",
                                          "Les séparateurs ne sont pas obligatoires en saisie.",
                                          "Saisissez la date de l'entrée en stock sans séparateurs, "),
                    'value':xformat.DatetimeToStr(datetime.date.today()),
                    'ctrlAction': 'OnDate',
                    'size':(200,30),
                    'txtSize': 90},
    ],
("param2", "Comptes"): [
    {'name': 'fournisseur', 'genre': 'Combo', 'label': 'Fournisseur',
                    'help': "Il s'agit de la provenance de la marchandise qui déterminera le compte crédité, ce peut être un camp",
                    'value':0,'values':[''],
                    'ctrlAction':'OnFournisseur',
                     'btnLabel': "...", 'btnHelp': "Cliquez pour choisir un compte pour l'origine",
                     'btnAction': 'OnBtnFournisseur',
                    'size':(250,30),
                    'txtSize': 70,
     },
    {'name': 'analytique', 'genre': 'Choice', 'label': 'Activité',
                    'ctrlAction':'OnAnalytique',
                    'help': "Il s'agit de l'activité qui a endossé la charge de la sortie",
                    'value':'','values':[''],
                    'btnLabel': "...", 'btnHelp': "Cliquez pour choisir l'activité de destination des mouvements",
                    'btnAction': 'OnBtnAnalytique',
                    'size':(250,30),
                    'txtSize': 70,}
],
("param3", "saisie"): [
    {'name': 'ht_ttc', 'genre': 'Choice', 'label': 'Saisie',
                    'help': "Choix du mode de saisie HT ou TTC selon le plus facile pour vous",
                    'value': 0, 'values': ['TTC', 'HT'],
                    'ctrlAction': 'OnHt_ttc',
                    'txtSize': 40,
                    'ctrlMaxSize': (130,30),
                     },
    {'name': 'vide','genre':None,}
    ],
("param4", "Compléments"): [
    {'name': 'rappel', 'genre': 'anyctrl','label': ' ',
                     'txtSize': 20,
                        'ctrlMaxSize':(150,50),
                     'ctrl': CtrlAnterieur,
                     'ctrlAction': 'OnBtnAnterieur',
                     },
    ],
}

def GetParamsOptions(dlg):
    matrice = MATRICE_PARAMS
    lstChoices = xformat.GetValueInMatrice(matrice,'origine','values')
    lstChoices += DICORIGINES[dlg.sens]['labels']
    return {
                'name':"PNL_params",
                'matrice':matrice,
                'lblBox':None,
                'boxesSizes': [(300, 90), (400, 90), (100, 90), (100, 90)],
                'pathdata':"srcNoelite/Data",
                'nomfichier':"stparams",
                'nomgroupe':"entrees",
            }

def GetBoutons(dlg):
    return  [
                {'name': 'btnImp', 'label': "Imprimer\npour contrôle",
                    'help': "Cliquez ici pour imprimer et enregistrer la saisie de l'entrée en stock",
                    'size': (120, 35), 'image': wx.ART_PRINT,'onBtn':dlg.OnImprimer},
                {'name':'btnOK','ID':wx.ID_ANY,'label':"Validez",'help':"Cliquez ici pour enregistrer et sortir",
                    'size':(120,35),'image':"xpy/Images/32x32/Valider.png",'onBtn':dlg.OnClose}
            ]

def GetOlvColonnes(dlg):
    # retourne la liste des colonnes de l'écran principal, valueGetter correspond aux champ des tables ou calculs
    if dlg.sens == 'entrees':
        titlePrix = "Prix Unit."
    else: titlePrix = "Prix Stock"
    return [
            ColumnDefn("ID", 'centre', 0, 'IDmouvement',
                       isEditable=False),
            ColumnDefn("Article", 'left', 200, 'IDarticle', valueSetter="",isSpaceFilling=True),
            ColumnDefn("Quantité", 'right', 110, 'qte', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal),
            ColumnDefn(titlePrix, 'right', 110, 'pxUn', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal),
            ColumnDefn("Mtt HT", 'right', 110, 'mttHT', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal, isEditable=False),
            ColumnDefn("Mtt TTC", 'right', 110, 'mttTTC', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal, isEditable=False),
            ColumnDefn("Qté stock", 'right', 110, 'qteStock', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal, isEditable=False),
            ColumnDefn("Nbre Rations", 'right', 110, 'nbRations', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal, isEditable=False),
            ]

def GetOlvCodesSup():
    # codes dans les données olv, mais pas dans les colonnes, attributs des tracks non visibles en tableau
    return ['prixTTC','IDmouvement','dicArticle']

def GetOlvOptions(dlg):
    # Options paramètres de l'OLV ds PNLcorps
    origines = DICORIGINES[dlg.sens]['codes']
    return {
            'codesOrigines': origines,
            'checkColonne': False,
            'recherche': True,
            'minSize': (600, 100),
            'dictColFooter': {"IDarticle": {"mode": "nombre", "alignement": wx.ALIGN_CENTER},
                                  "mttHT": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                                  "mttTTC": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                                  },
    }

def GetDlgOptions(dlg):
    # Options du Dlg de lancement
    return {
        'style': wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        'minSize': (700, 450),
        'size': (850, 550),
        }

    #----------------------- Parties de l'écrans -----------------------------------------

class PNL_params(xgte.PNL_params):
    #panel de paramètres de l'application
    def __init__(self, parent, **kwds):
        self.parent = parent
        #('pos','size','style','name','matrice','donnees','lblBox')
        kwds = GetParamsOptions(parent)
        super().__init__(parent, **kwds)
        if hasattr(parent,'lanceur'):
            self.lanceur = parent.lanceur
        else: self.lanceur = parent

class PNL_corps(xgte.PNL_corps):
    #panel olv avec habillage optionnel pour des boutons actions (à droite) des infos (bas gauche) et boutons sorties
    def __init__(self, parent, dicOlv,*args, **kwds):
        xgte.PNL_corps.__init__(self,parent,dicOlv,*args,**kwds)
        self.db = parent.db
        self.lstNewReglements = []
        self.flagSkipEdit = False
        self.oldRow = None
        self.dicArticle = None

    def InitTrackVierge(self,track,modelObject):
        track.creer = True

    def ValideParams(self):
        pnl = self.parent.pnlParams
        dicParams = {'origine': self.parent.GetOrigine(),
                     'date': self.parent.GetDate(),
                     'fournisseur': pnl.GetOneValue('fournisseur',codeBox='param2'),
                     'analytique': pnl.GetOneValue('analytique',codeBox='param2'),
                     'ht_ttc': pnl.GetOneValue('ht_ttc',codeBox='param3')}
        ret = nust.ValideParams(pnl,dicParams)

    def OnCtrlV(self,track):
        # avant de coller une track, raz de certains champs et recalcul
        track.IDmouvement = None
        self.ValideLigne(None,track)
        self.SauveLigne(track)

    def OnDelete(self,track):
        nust.DeleteLigne(self.parent.db,self.ctrlOlv,track)

    def OnNewRow(self,row,track):
        pass

    def OnEditStarted(self,code,track=None,editor=None):
        # affichage de l'aide
        if code in DIC_INFOS.keys():
            self.parent.pnlPied.SetItemsInfos( DIC_INFOS[code],
                                               wx.ArtProvider.GetBitmap(wx.ART_FIND, wx.ART_OTHER, (16, 16)))
        else:
            self.parent.pnlPied.SetItemsInfos( INFO_OLV,wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)))

        # travaux avant saisie
        if code == 'qte':
            if not hasattr(track,'oldQte'):
                track.oldQte = track.qte
        if code == 'pxUn':
            if not hasattr(track, 'oldPu'):
                nust.CalculeLigne(self.parent,track)
                track.oldPu = track.prixTTC

    def OnEditFinishing(self,code=None,value=None,editor=None):
        self.parent.pnlPied.SetItemsInfos( INFO_OLV,wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)))
        # flagSkipEdit permet d'occulter les évènements redondants. True durant la durée du traitement
        if self.flagSkipEdit : return
        self.flagSkipEdit = True

        (row, col) = self.ctrlOlv.cellBeingEdited
        track = self.ctrlOlv.GetObjectAt(row)

        # Traitement des spécificités selon les zones
        if code == 'IDarticle':
            value = nust.SqlOneArticle(self.db,value)
            track.IDarticle = value
            if value:
                track.dicArticle = nust.SqlDicArticle(self.db,self.ctrlOlv,value)
                track.nbRations = track.dicArticle['rations']
                track.qteStock = track.dicArticle['qteStock']
                if self.parent.sens == 'sorties':
                    track.pxUn = track.dicArticle['prixMoyen']
        if code == 'qte' or code == 'pxUn':
            # force la tentative d'enregistrement même en l'absece de saisie
            track.noSaisie = False

        # enlève l'info de bas d'écran
        self.parent.pnlPied.SetItemsInfos( INFO_OLV,wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)))
        self.flagSkipEdit = False
        return value

    def ValideLigne(self,code,track):
        # Appelé par cellEditor en sortie
        nust.ValideLigne(self.db,track)
        nust.CalculeLigne(self.Parent,track)

    def SauveLigne(self,track):
        nust.SauveLigne(self.db,self.Parent,track)

    def OnEditFunctionKeys(self,event):
        row, col = self.ctrlOlv.cellBeingEdited
        code = self.ctrlOlv.lstCodesColonnes[col]
        if event.GetKeyCode() == wx.WXK_F4 and code == 'IDarticle':
            # Choix article
            IDarticle = nust.SqlOneArticle(self.db,self.ctrlOlv.GetObjectAt(row).IDarticle)
            #self.ctrlOlv.GetObjectAt(row).IDarticle = IDarticle
            ret = self.OnEditFinishing('IDarticle',IDarticle)

class PNL_pied(xgte.PNL_pied):
    #panel infos (gauche) et boutons sorties(droite)
    def __init__(self, parent, dicPied, **kwds):
        xgte.PNL_pied.__init__(self,parent, dicPied, **kwds)

class DLG(xusp.DLG_vide):
    # ------------------- Composition de l'écran de gestion----------
    def __init__(self,sens='sorties'):
        self.sens = sens
        kwds = GetDlgOptions(self)
        super().__init__(None,**kwds)
        self.lanceur = self
        self.dicOlv = {'lstColonnes': GetOlvColonnes(self)}
        self.dicOlv.update({'lstCodesSup': GetOlvCodesSup()})
        self.dicOlv.update(GetOlvOptions(self))
        self.origines = self.dicOlv.pop("codesOrigines",[])
        self.ordi = xuid.GetNomOrdi()
        self.today = datetime.date.today()
        self.date = self.today
        self.analytique = ''
        self.fournisseur = ''
        self.ht_ttc = 'TTC'
        ret = self.Init()
        if ret == wx.ID_ABORT: self.Destroy()

    def Init(self):
        self.db = xdb.DB()
        # définition de l'OLV
        self.ctrlOlv = None
        # récup des modesReglements nécessaires pour passer du texte à un ID d'un mode ayant un mot en commun
        for colonne in self.dicOlv['lstColonnes']:
            if 'mode' in colonne.valueGetter:
                choicesMode = colonne.choices
            if 'libelle' in colonne.valueGetter:
                self.libelleDefaut = colonne.valueSetter

        # boutons de bas d'écran - infos: texte ou objet window.  Les infos sont  placées en bas à gauche
        self.txtInfo =  "Ici de l'info apparaîtra selon le contexte de la grille de saisie"
        lstInfos = [ wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)),self.txtInfo]
        dicPied = {'lstBtns': GetBoutons(self), "lstInfos": lstInfos}

        # lancement de l'écran en blocs principaux
        if self.sens == 'entrees':
            self.pnlBandeau = xbandeau.Bandeau(self,TITRE[self.sens],INTRO[self.sens], hauteur=20,
                                               nomImage="xpy/Images/80x80/Entree.png",
                                               sizeImage=(60,40))
            self.pnlBandeau.SetBackgroundColour(wx.Colour(220, 250, 220))
        else:
            self.pnlBandeau = xbandeau.Bandeau(self,TITRE[self.sens],INTRO[self.sens], hauteur=20,
                                                nomImage="xpy/Images/80x80/Sortie.png",
                                                sizeImage=(60,40))
            self.pnlBandeau.SetBackgroundColour(wx.Colour(250, 220, 220))
        self.pnlParams = PNL_params(self)
        self.pnlOlv = PNL_corps(self, self.dicOlv)
        self.pnlPied = PNL_pied(self, dicPied)
        self.ctrlOlv = self.pnlOlv.ctrlOlv

        # charger les valeurs de pnl_params
        self.pnlParams.SetOneSet('fournisseur',values=nust.SqlFournisseurs(self.db),codeBox='param2')
        self.lstAnalytiques = nust.SqlAnalytiques(self.db,'ACTIVITES')
        self.valuesAnalytique = ["%s %s"%(x[0],x[1]) for x in self.lstAnalytiques]
        self.pnlParams.SetOneSet('analytique',values=self.valuesAnalytique,codeBox='param2')
        self.pnlParams.SetOneValue('origine',valeur=DICORIGINES[self.sens]['labels'][0],codeBox='param1')
        self.OnOrigine(None)
        self.OnHt_ttc(None)

        self.Bind(wx.EVT_CLOSE,self.OnClose)
        self.Sizer()

    def Sizer(self):
        sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=0, hgap=0)
        sizer_base.Add(self.pnlBandeau, 0, wx.TOP | wx.EXPAND, 3)
        sizer_base.Add(self.pnlParams, 0, wx.TOP | wx.EXPAND, 3)
        sizer_base.Add(self.pnlOlv, 1, wx.TOP | wx.EXPAND, 3)
        sizer_base.Add(self.pnlPied, 0, wx.ALL | wx.EXPAND, 3)
        sizer_base.AddGrowableCol(0)
        sizer_base.AddGrowableRow(2)
        self.CenterOnScreen()
        self.SetSizer(sizer_base)
        self.CenterOnScreen()

    # ------------------- Gestion des actions -----------------------

    def InitOlv(self):
        self.ctrlOlv.lstColonnes = GetOlvColonnes(self)
        self.ctrlOlv.lstCodesColonnes = self.ctrlOlv.GetLstCodesColonnes()
        self.ctrlOlv.InitObjectListView()
        self.Refresh()

    def GetOrigine(self):
        pnlOrigine = self.pnlParams.GetPnlCtrl('origine',codebox='param1')
        lblOrigine = pnlOrigine.GetValue()
        ixo = DICORIGINES[self.sens]['labels'].index(lblOrigine)
        return DICORIGINES[self.sens]['codes'][ixo]

    def OnOrigine(self,event):
        self.origine = self.GetOrigine()

        # grise les ctrl inutiles
        def setEnable(namePnlCtrl,flag):
            pnlCtrl =  self.pnlParams.GetPnlCtrl(namePnlCtrl,codebox='param2')
            pnlCtrl.txt.Enable(flag)
            pnlCtrl.ctrl.Enable(flag)
            pnlCtrl.btn.Enable(flag)
        #'achat livraison', 'retour camp', 'od_in'
        if 'achat' in self.origine:
            setEnable('fournisseur',True)
            setEnable('analytique',False)
        elif ('retour' in self.origine) or ('camp' in self.origine)  :
            setEnable('fournisseur',False)
            setEnable('analytique',True)
        elif ('od' in self.origine) or ('repas' in self.origine) :
            setEnable('fournisseur',False)
            setEnable('analytique',False)
        else:
            setEnable('fournisseur',True)
            setEnable('analytique',True)

        self.pnlParams.Refresh()
        if event: event.Skip()

    def GetDate(self,fr=False):
        saisie = self.pnlParams.GetOneValue('date',codeBox='param1')
        saisie = xformat.FmtDate(saisie)
        self.date = xformat.DateFrToSql(saisie)
        if fr: return saisie
        else: return self.date

    def OnDate(self,event):
        saisie = self.GetDate(fr=True)
        self.pnlParams.SetOneValue('date',valeur=saisie,codeBox='param1')
        self.GetDonnees()
        if event: event.Skip()

    def OnHt_ttc(self,event):
        self.ht_ttc = self.pnlParams.GetOneValue('ht_ttc',codeBox='param3')
        self.GetDonnees()
        if event: event.Skip()

    def OnFournisseur(self,event):
        self.fournisseur = self.pnlParams.GetOneValue('fournisseur',codeBox='param2')
        self.GetDonnees()
        if event: event.Skip()

    def OnBtnFournisseur(self,event):
        # Simple message explication
        mess = "Choix FOURNISSEURS\n\n"
        mess += "Les fournisseurs proposés sont cherchés dans les utilisations précédentes,\n"
        mess += "Il vous suffit de saisir un nouveau nom pour qu'il vous soit proposé la prochaine fois"
        wx.MessageBox(mess,"Information",style=wx.ICON_INFORMATION|wx.OK)
        if event: event.Skip()

    def OnAnalytique(self,event):
        choixAnalytique = self.pnlParams.GetOneValue('analytique',codeBox='param2')
        if len(choixAnalytique) > 0:
            ix = self.valuesAnalytique.index(choixAnalytique)
            self.analytique = self.lstAnalytiques[ix][0]
        self.GetDonnees()
        if event: event.Skip()

    def OnBtnAnterieur(self,event):
        # lancement de la recherche d'un lot antérieur, on enlève le cellEdit pour éviter l'écho des clics
        self.ctrlOlv.cellEditMode = self.ctrlOlv.CELLEDIT_NONE
        # choix d'un lot de lignes définies par des params
        dicParams = nust.GetAnterieur(self)
        self.ctrlOlv.cellEditMode = self.ctrlOlv.CELLEDIT_DOUBLECLICK        # gestion du retour du choix dépot
        if not 'date' in dicParams.keys(): return
        self.GetDonnees(dicParams)
        if event: event.Skip()

    def GetDonnees(self,dicParams=None):
        if not dicParams:
            dicParams = {'origine':self.origine,
                         'date':self.date,
                         'fournisseur':self.fournisseur,
                         'analytique':self.analytique,
                         'ht_ttx':self.ht_ttc}
        valide = nust.ValideParams(self.pnlParams,dicParams, mute=True)
        if not valide: return

        # appel des données de l'Olv principal à éditer
        lstDonnees = nust.GetDonneesEntrees(self,dicParams)
        lstNoModif = [1 for rec in  lstDonnees if not (rec[-1])]
        # présence de lignes déjà transférées compta
        if len(lstNoModif) >0:
            self.ctrlOlv.cellEditMode = self.ctrlOlv.CELLEDIT_NONE
            self.pnlPied.SetItemsInfos("NON MODIFIABLE: enregistrements transféré ",
                                       wx.ArtProvider.GetBitmap(wx.ART_ERROR, wx.ART_OTHER, (16, 16)))
        # l'appel des données peut avoir retourné d'autres paramètres, il faut mettre à jour l'écran
        if len(lstDonnees) > 0:
            # set date du lot importé
            self.pnlParams.SetOneValue('date',xformat.FmtDate(dicParams['date']),'param1')
            self.date = dicParams['date']

            # set origine
            ixo = DICORIGINES[self.sens]['codes'].index(dicParams['origine'])
            self.pnlParams.SetOneValue(DICORIGINES[self.sens]['labels'][ixo])
            self.OnOrigine(None)

            # set Fournisseur et analytique
            self.pnlParams.SetOneValue('fournisseur',dicParams['fournisseur'],'param2')
            self.fournisseur = dicParams['fournisseur']
            self.pnlParams.SetOneValue('analytique',dicParams['analytique'],'param2')
            self.analytique = dicParams['analytique']

        # alimente la grille, puis création de modelObejects pr init
        self.ctrlOlv.lstDonnees = lstDonnees
        self.InitOlv()

        # les écritures reprises sont censées être valides, mais il fatu les compléter
        for track in self.ctrlOlv.modelObjects[:-1]:
            nust.CalculeLigne(self,track)
            track.valide = True
        self.ctrlOlv._FormatAllRows()

    def GetTitreImpression(self):
        tiers = ''
        if self.fournisseur: tiers += ", Fournisseur: %s"%self.fournisseur.capitalize()
        if self.analytique: tiers += ", Camp: %s"%self.analytique.capitalize()
        date = xformat.DateSqlToFr(self.date)
        return "Mouvements STOCKS %s du %s, %s%s"%(self.sens, date, self.origine,tiers)

    def OnImprimer(self,event):
        # test de présence d'écritures non valides
        lstNonValides = [x for x in self.ctrlOlv.modelObjects if not x.valide and x.IDmouvement]
        if len(lstNonValides) > 0:
            ret = wx.MessageBox('Présence de lignes non valides!\n\nCes lignes seront détruites avant impression',
                                'Confirmez pour continuer', style=wx.OK | wx.CANCEL)
            if ret != wx.OK: return
        # test de présence d'un filtre
        if len(self.ctrlOlv.innerList) != len(self.ctrlOlv.modelObjects):
            ret = wx.MessageBox('Filtre actif!\n\nDes lignes sont filtrées, seules les visibles seront rapportées',
                                'Confirmez pour continuer',style=wx.OK|wx.CANCEL)
            if ret != wx.OK: return
        # purge des lignes non valides
        self.ctrlOlv.modelObjects=[x for x in self.ctrlOlv.modelObjects if hasattr(x,'valide') and x.valide]
        # réaffichage
        self.ctrlOlv.RepopulateList()
        # impression
        self.ctrlOlv.Apercu(None)
        self.isImpress = True

    def OnClose(self,event):
        #wx.MessageBox("Traitement de sortie")
        if event:
            event.Skip()
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
