#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------
# Application:     NoeStock, gestion des stocks et prix de journée
# Module:          Saisie des entrées de stocks
# Auteur:          Jacques BRUNEL 2021-02
# Licence:         Licence GNU GPL
# ------------------------------------------------------------------

import wx
import os
import datetime
import srcNoestock.UTILS_Stocks        as nust
import srcNoelite.UTILS_Noegest        as nung
import xpy.xGestion_TableauEditor      as xgte
import xpy.xGestion_TableauRecherche   as xgtr
import xpy.xUTILS_Identification       as xuid
import xpy.xUTILS_SaisieParams         as xusp
import xpy.xUTILS_DB                   as xdb
from srcNoestock                import DLG_Articles
from xpy.outils.ObjectListView  import ColumnDefn, CellEditor
from xpy.outils                 import xformat,xbandeau,xboutons

#---------------------- Matrices de paramétres -------------------------------------

TITRE = {'entrees':"Entrées en stock",'sorties':"Sorties de stock"}
INTRO = {'entrees':"Gestion des entrées dans le stock, par livraison, retour ou autre ",
        'sorties':"Gestion des sorties du stock, par repas multicamp, pour un camp ou autre ",}

DICORIGINES = {
                'entrees':{'codes': ['achat','retour','od_in'],
                           'label':"Nature  entrée",
                           'values': ['achat livraison', 'retour camp', 'od entrée']},
                'sorties': {'codes': ['repas', 'camp', 'od_out'],
                           'label':"Nature  sortie",
                           'values': ['vers cuisine', 'revente ou camp', 'od sortie']}}

DICDATE = {     'entrees':{'label':"Date d' entrée"},
                'sorties':{'label':"Date de sortie",}}

DIC_INFOS = {
            'IDarticle': "<F4> Choix d'un article, ou saisie directe de son code",
            'qte': "L'unité est en général précisée dans le nom de l'article\nNbre dans le plus petit conditionnements, pas par carton complet",
            'pxUn': "HT ou TTC selon le choix en haut d'écran\nPrix d'une unité telle qu'on la sort du stock, pas celui du carton complet",
             }

INFO_OLV = "<Suppr> <Inser> <Ctrl C> <Ctrl V>"

# Choix des params  pour reprise de mouvements antérieurs------------------------------------------------

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

def GetMatriceAnterieurs(dlg):
    dicBandeau = {'titre': "Rappel d'un anterieur existant",
                  'texte': "les mots clés du champ en bas permettent de filtrer d'autres lignes et d'affiner la recherche",
                  'hauteur': 15, 'nomImage': "xpy/Images/32x32/Zoom_plus.png"}

    # Composition de la matrice de l'OLV anterieurs, retourne un dictionnaire

    lstChamps = ['origine', 'date', 'fournisseur', 'IDanalytique', 'COUNT(IDmouvement)']

    lstNomsColonnes = ['origine', 'date', 'fournisseur', 'analytique', 'nbLignes']

    lstTypes = ['VARCHAR(8)', 'DATE', 'VARCHAR(32)', 'VARCHAR(32)', 'INT']
    lstCodesColonnes = [xformat.SupprimeAccents(x).lower() for x in lstNomsColonnes]
    lstValDefColonnes = xformat.ValeursDefaut(lstNomsColonnes, lstTypes)
    lstLargeurColonnes = [100,100,180,180,200]
    lstColonnes = xformat.DefColonnes(lstNomsColonnes, lstCodesColonnes, lstValDefColonnes, lstLargeurColonnes)
    return {
        'codesOrigines': dlg.origines,
        'lstColonnes': lstColonnes,
        'lstChamps': lstChamps,
        'listeNomsColonnes': lstNomsColonnes,
        'listeCodesColonnes': lstCodesColonnes,
        'getDonnees': nust.SqlAnterieurs,
        'dicBandeau': dicBandeau,
        'sortColumnIndex': 2,
        'sensTri': False,
        'style': wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES,
        'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
        'size': (650, 400)}

# Description des paramètres de la gestion des mouvements

MATRICE_PARAMS = {
("param1", "Paramètres"): [
    {'name': 'origine', 'genre': 'Choice', 'label': "",
                    'help': "Le choix de la nature modifie certains contrôles",
                    'value':0, 'values':[],
                    'ctrlAction': 'OnOrigine',
                    'size':(205,30),
                    'txtSize': 90},
    {'name': 'date', 'genre': 'Texte', 'label': "",
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
                    'help': "La saisie d'un fournisseurfacilite les commandes par fournisseur, on peut mettre 'NONAME'",
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
                    'value': 1, 'values': ['TTC', 'HT'],
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

def GetDicParams(dlg):
    matrice = xformat.CopyDic(MATRICE_PARAMS)
    if dlg.sens == 'sorties':
        # force la saisie en TTC par défaut
        matrice[("param3", "saisie")][0]['value'] = 0
    xformat.SetItemInMatrice(matrice,'origine','values', DICORIGINES[dlg.sens]['values'])
    xformat.SetItemInMatrice(matrice,'origine','label', DICORIGINES[dlg.sens]['label'])
    xformat.SetItemInMatrice(matrice,'date','label', DICDATE[dlg.sens]['label'])
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
                {'name':'btnOK','ID':wx.ID_ANY,'label':"Quitter",'help':"Cliquez ici pour sortir",
                    'size':(120,35),'image':"xpy/Images/32x32/Quitter.png",'onBtn':dlg.OnClose}
            ]

def GetOlvColonnes(dlg):
    # retourne la liste des colonnes de l'écran principal, valueGetter correspond aux champ des tables ou calculs
    if dlg.sens == 'entrees':
        titlePrix = "PxParPièce"
    else: titlePrix = "Prix Unit."
    lstCol = [
            ColumnDefn("ID", 'centre', 0, 'IDmouvement',
                       isEditable=False),
            ColumnDefn("Repas", 'left', 60, 'repas',
                                cellEditorCreator=CellEditor.ChoiceEditor),
            ColumnDefn("Article", 'left', 200, 'IDarticle', valueSetter="",isSpaceFilling=True),
            ColumnDefn("Quantité", 'right', 80, 'qte', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal),
            ColumnDefn(titlePrix, 'right', 80, 'pxUn', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal),
            ColumnDefn("Mtt HT", 'right', 80, 'mttHT', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal, isEditable=False),
            ColumnDefn("Mtt TTC", 'right', 80, 'mttTTC', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal, isEditable=False),
            ColumnDefn("Qté stock", 'right', 80, 'qteStock', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal, isEditable=False),
            ColumnDefn("Nbre Rations", 'right', 80, 'nbRations', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal, isEditable=False),
            ]
    if dlg.sens == 'entrees':
        # supprime la saisie du repas
        del lstCol[1]
    return lstCol

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

def GetAnterieur(dlg,db=None):
    # retourne un dict de params après lancement d'un tableau de choix de l'existants pour reprise
    dicParams = {}
    dicOlv = GetMatriceAnterieurs(dlg)
    dlg = xgtr.DLG_tableau(dlg, dicOlv=dicOlv, db=db)
    ret = dlg.ShowModal()
    if ret == wx.OK and dlg.GetSelection():
        donnees = dlg.GetSelection().donnees
        for ix in range(len(donnees)):
            dicParams[dicOlv['listeCodesColonnes'][ix]] = donnees[ix]
    dlg.Destroy()
    return dicParams

def ValideParams(pnl,dicParams,mute=False):
    # vérifie la saisie des paramètres
    pnlFournisseur = pnl.GetPnlCtrl('fournisseur', codebox='param2')
    pnlAnalytique = pnl.GetPnlCtrl('analytique', codebox='param2')
    valide = True

    # normalisation none ''
    if dicParams['fournisseur']  == None:
        dicParams['fournisseur'] = ''
    if dicParams['analytique'] == None:
        dicParams['analytique'] = ''

    if 'achat' in dicParams['origine']:
        if (not dicParams['fournisseur']):
            if not mute:
                wx.MessageBox("Veuillez saisir un fournisseur!")
                pnlFournisseur.SetFocus()
            valide = False
    elif 'retour' in dicParams['origine']:
        if (not dicParams['analytique']):
            if not mute:
                wx.MessageBox("Veuillez saisir un camp pour le retour de marchandise!")
                pnlAnalytique.SetFocus()
            valide = False
    return valide

def GetMouvements(dlg, dParams):
    # retourne la liste des données de l'OLv de DlgEntree
    ctrlOlv = dlg.ctrlOlv

    ldMouvements = nust.SqlMouvements(dlg.db,dParams)
    # appel des dicArticles des mouvements
    ddArticles = {}
    for dMvt in ldMouvements:
        ddArticles[dMvt['IDarticle']] = nust.SqlDicArticle(dlg.db,dlg.ctrlOlv,dMvt['IDarticle'])

    # composition des données
    lstDonnees = []
    lstCodesCol = ctrlOlv.GetLstCodesColonnes()

    # autant de lignes dans l'olv que de mouvements remontés
    for dMvt in ldMouvements:
        donnees = []
        dArticle = ddArticles[dMvt['IDarticle']]
        # alimente les premières données des colonnes
        for code in lstCodesCol:
            # ajout de la donnée dans le mouvement
            if code in dMvt.keys():
                donnees.append(dMvt[code])
                continue
            # ajout de l'article associé
            if code in dArticle.keys():
                donnees.append(dArticle)
                continue
            if code in ('pxUn','mttHT','mttTTC','nbRations'):
                convTva = (1+(dArticle['txTva'] / 100))
                if code == 'pxUn':
                    if dlg.ht_ttc == 'HT':
                        donnees.append(round( dMvt['prixUnit'] / convTva,6))
                    else:
                        donnees.append(dMvt['prixUnit'])

                elif code == 'mttHT':
                    donnees.append(round(dMvt['prixUnit'] * dMvt['qte'] / convTva ,2))
                elif code == 'mttTTC':
                    donnees.append(dMvt['prixUnit'] * dMvt['qte'])
                elif code == 'nbRations':
                    donnees.append(dArticle['rations'] * dMvt['qte'])
                else:
                    raise("code: %s Erreur de programmation en UTILS_Stocks.GetMouvements"%code)
                continue

        # codes supplémentaires ('prixTTC','IDmouvement','dicArticle') dlg.dicOlv['lstCodesSup']
        donnees += [dMvt['prixUnit'],
                    dMvt['IDmouvement'],
                    dArticle]
        lstDonnees.append(donnees)
    return lstDonnees

def CalculeLigne(dlg,track):
    if not hasattr(track,'dicArticle'): return
    try: qte = float(track.qte)
    except: qte = 0.0
    if not hasattr(track,'oldQte'):
        track.oldQte = track.qte
    try: pxUn = float(track.pxUn)
    except: pxUn = 0.0
    try: txTva = track.dicArticle['txTva']
    except: txTva = 0.0
    try: rations = track.dicArticle['rations']
    except: rations = 1
    if dlg.ht_ttc == 'HT':
        mttHT = qte * pxUn
        mttTTC = round(mttHT * (1 + (txTva / 100)),2)
        prixTTC = round(pxUn * (1 + (txTva / 100)),6)
    elif dlg.ht_ttc == 'TTC':
        mttTTC = qte * pxUn
        mttHT = round(mttTTC / (1 + (txTva / 100)),2)
        prixTTC = pxUn
    else: raise("Taux TVA de l'article non renseigné")
    track.mttHT = mttHT
    track.mttTTC = mttTTC
    track.prixTTC = prixTTC
    track.nbRations = track.qte * rations
    track.qteStock = track.dicArticle['qteStock']

def ValideLigne(dlg,track):
    # validation de la ligne de mouvement
    track.valide = True
    track.messageRefus = "Saisie incomplète\n\n"

    # IDmouvement manquant
    if track.IDmouvement in (None,0) :
        track.messageRefus += "L'IDmouvement n'a pas été déterminé\n"

    # Repas non renseigné
    if dlg.sens == 'sorties' and track.repas in (None,0,'') :
        track.messageRefus += "Le repas pour imputer la sortie n'est pas saisi\n"

    # article manquant
    if track.IDarticle in (None,0,'') :
        track.messageRefus += "L'article n'est pas saisi\n"

    # qte null
    try:
        track.qte = float(track.qte)
    except:
        track.qte = None
    if not track.qte or track.qte == 0.0:
        track.messageRefus += "La quantité est à zéro, ligne inutile à supprimer\n"

    # pxUn null
    try:
        track.pxUn = float(track.pxUn)
    except:
        track.pxUn = None
    if not track.pxUn or track.pxUn == 0.0:
        track.messageRefus += "Le pxUn est à zéro\n"

    # envoi de l'erreur
    if track.messageRefus != "Saisie incomplète\n\n":
        track.valide = False
    else: track.messageRefus = ""

    CalculeLigne(dlg,track)
    return

class PNL_params(xgte.PNL_params):
    #panel de paramètres de l'application
    def __init__(self, parent, **kwds):
        self.parent = parent
        #('pos','size','style','name','matrice','donnees','lblBox')
        kwds = GetDicParams(parent)
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
        track.repas = None

    def ValideParams(self):
        pnl = self.parent.pnlParams
        dicParams = {'origine': self.parent.GetOrigine(),
                     'date': self.parent.GetDate(),
                     'fournisseur': pnl.GetOneValue('fournisseur',codeBox='param2'),
                     'analytique': pnl.GetOneValue('analytique',codeBox='param2'),
                     'ht_ttc': pnl.GetOneValue('ht_ttc',codeBox='param3')}
        ret = ValideParams(pnl,dicParams)

    def OnCtrlV(self,track):
        # avant de coller une track, raz de certains champs et recalcul
        track.IDmouvement = None
        self.ValideLigne(None,track)
        self.SauveLigne(track)

    def OnDelete(self,track):
        nust.DelMouvement(self.parent.db,self.ctrlOlv,track)

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

        if self.parent.sens == 'sorties' and track.repas == None :
            # choix par défaut selon l'heure
            h = datetime.datetime.now().hour
            ch=3
            if h < 8: ch=1
            if h < 17: ch=2
            track.repas = nust.CHOIX_REPAS[ch-1]

        if code == 'repas':
            editor.Set(nust.CHOIX_REPAS)
            editor.SetStringSelection(track.repas)

        if code == 'qte':
            if not hasattr(track,'oldQte'):
                track.oldQte = track.qte

        if code == 'pxUn':
            if not hasattr(track, 'oldPu'):
                CalculeLigne(self.parent,track)
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
            value = DLG_Articles.GetOneIDarticle(self.db,value)
            if value:
                track.IDarticle = value
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
        # Relais de l'appel par cellEditor à chaque colonne
        ValideLigne(self.parent,track)

    def SauveLigne(self,track):
        nust.SauveMouvement(self.db,self.Parent,track)

    def OnEditFunctionKeys(self,event):
        row, col = self.ctrlOlv.cellBeingEdited
        code = self.ctrlOlv.lstCodesColonnes[col]
        if event.GetKeyCode() == wx.WXK_F4 and code == 'IDarticle':
            # Choix article
            IDarticle = DLG_Articles.GetOneIDarticle(self.db,self.ctrlOlv.GetObjectAt(row).IDarticle,f4=True)
            #self.ctrlOlv.GetObjectAt(row).IDarticle = IDarticle
            if IDarticle:
                ret = self.OnEditFinishing('IDarticle',IDarticle)

class PNL_pied(xgte.PNL_pied):
    #panel infos (gauche) et boutons sorties(droite)
    def __init__(self, parent, dicPied, **kwds):
        xgte.PNL_pied.__init__(self,parent, dicPied, **kwds)

class DLG(xusp.DLG_vide):
    # ------------------- Composition de l'écran de gestion----------
    def __init__(self,sens='sorties',date=None,**kwd):
        self.sens = sens
        kwds = GetDlgOptions(self)
        super().__init__(None,**kwds)
        self.dicOlv = {'lstColonnes': GetOlvColonnes(self)}
        self.dicOlv.update({'lstCodesSup': GetOlvCodesSup()})
        self.dicOlv.update(GetOlvOptions(self))
        self.dicOlv['db'] = xdb.DB()
        self.origines = self.dicOlv.pop("codesOrigines",[])
        self.ordi = xuid.GetNomOrdi()
        self.today = datetime.date.today()
        if not date:
            date = self.today
        self.date = date
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
        self.valuesAnalytique = [nust.MakeChoiceActivite(x) for x in self.lstAnalytiques]
        self.valuesAnalytique.append("")
        self.pnlParams.SetOneSet('analytique',values=self.valuesAnalytique,codeBox='param2')
        self.pnlParams.SetOneValue('origine',valeur=DICORIGINES[self.sens]['values'][0],codeBox='param1')
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
        ixo = DICORIGINES[self.sens]['values'].index(lblOrigine)
        return DICORIGINES[self.sens]['codes'][ixo]

    def GetDate(self,fr=False):
        saisie = self.pnlParams.GetOneValue('date',codeBox='param1')
        saisie = xformat.FmtDate(saisie)
        self.date = xformat.DateFrToSql(saisie)
        if fr: return saisie
        else: return self.date

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
            self.pnlParams.SetOneValue('analytique',"", codeBox='param2')
        elif ('retour' in self.origine) or ('camp' in self.origine)  :
            setEnable('fournisseur',False)
            self.pnlParams.SetOneValue('fournisseur',"", codeBox='param2')
            setEnable('analytique',True)
            if len(self.valuesAnalytique) >0:
                self.pnlParams.SetOneValue('analytique',self.valuesAnalytique[0], codeBox='param2')
        elif ('od' in self.origine) or ('repas' in self.origine) :
            self.pnlParams.SetOneValue('fournisseur',"", codeBox='param2')
            setEnable('fournisseur',False)
            self.pnlParams.SetOneValue('analytique',"", codeBox='param2')
            setEnable('analytique',False)
        else:
            setEnable('fournisseur',True)
            setEnable('analytique',True)

        self.pnlParams.Refresh()
        if event: event.Skip()

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

    def OnBtnAnalytique(self,event):
        # Appel du choix d'un camp via un écran complet
        noegest = nung.Noegest(self)
        dicAnalytique = noegest.GetActivite(mode='dlg')
        codeAct = nust.MakeChoiceActivite(dicAnalytique)
        self.pnlParams.SetOneValue('analytique',codeAct,codeBox='param2')

    def OnBtnAnterieur(self,event):
        # lancement de la recherche d'un lot antérieur, on enlève le cellEdit pour éviter l'écho des clics
        self.ctrlOlv.cellEditMode = self.ctrlOlv.CELLEDIT_NONE
        # choix d'un lot de lignes définies par des params
        dicParams = GetAnterieur(self,db=self.db)
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
        valide = ValideParams(self.pnlParams,dicParams, mute=True)
        if not valide: return

        # appel des données de l'Olv principal à éditer
        lstDonnees = GetMouvements(self,dicParams)
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
            self.pnlParams.SetOneValue(DICORIGINES[self.sens]['values'][ixo])
            self.OnOrigine(None)

            # set Fournisseur et analytique
            self.pnlParams.SetOneValue('fournisseur',dicParams['fournisseur'],'param2')
            self.fournisseur = dicParams['fournisseur']
            self.pnlParams.SetOneValue('analytique',dicParams['analytique'],'param2')
            self.analytique = dicParams['analytique']

        # alimente la grille, puis création de modelObejects pr init
        self.ctrlOlv.lstDonnees = lstDonnees
        self.InitOlv()

        # les écritures reprises sont censées être valides, mais il faut les compléter
        for track in self.ctrlOlv.modelObjects[:-1]:
            CalculeLigne(self,track)
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
