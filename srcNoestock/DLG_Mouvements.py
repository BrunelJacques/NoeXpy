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
from xpy.outils.xformat         import Nz

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
        'getDonnees': nust.SqlMvtsAnte,
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
                'boxesSizes': [(250, 90), (250, 90), None, (160, 90)],
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
                                stringConverter=xformat.FmtQte),
            ColumnDefn(titlePrix, 'right', 80, 'pxUn', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal),
            ColumnDefn("Mtt HT", 'right', 80, 'mttHT', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal, isEditable=False),
            ColumnDefn("Mtt TTC", 'right', 80, 'mttTTC', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal, isEditable=False),
            ColumnDefn("Qté stock", 'right', 80, 'qteStock', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal, isEditable=False),
            ColumnDefn("PrixStock", 'right', 80, 'pxMoy', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal, isEditable=False),
            ColumnDefn("Nbre Rations", 'right', 80, 'nbRations', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal, isEditable=False),
            ]
    if dlg.sens == 'entrees':
        # supprime la saisie du repas
        del lstCol[1]
    if dlg.origine[:5] == 'achat':
        dlg.typeAchat = True
        for col in lstCol:
            if col.valueGetter in ('qte','pxUn'):
                col.isEditable = False
        lstColAchat = [
            ColumnDefn("Nb Unités", 'right', 80, 'nbAch', isSpaceFilling=False, valueSetter=0.0,
                       stringConverter=xformat.FmtDecimal, isEditable=True),
            ColumnDefn("Prix unité", 'right', 80, 'pxAch', isSpaceFilling=False, valueSetter=0.0,
                       stringConverter=xformat.FmtDecimal, isEditable=True),
            ColumnDefn("Qte/unité", 'right', 80, 'parAch', isSpaceFilling=False, valueSetter=1.0,
                       stringConverter=xformat.FmtQte, isEditable=True),
            ]
        lstCol = lstCol[:2] + lstColAchat + lstCol[2:]
    else: dlg.typeAchat = False
    return lstCol

def GetOlvCodesSup():
    # codes dans les données olv, mais pas dans les colonnes, attributs des tracks non visibles en tableau
    return ['dicArticle','dicMvt',]

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
        'style': wx.DEFAULT_FRAME_STYLE,
        'minSize': (700, 450),
        'size': (950, 800),
        }

    #----------------------- Parties de l'écrans -----------------------------------------

def GetAnterieur(dlg,db=None):
    # retourne un dict de params après lancement d'un tableau de choix de l'existants pour reprise
    dParams = {}
    dicOlv = GetMatriceAnterieurs(dlg)
    dlgAnte = xgtr.DLG_tableau(dlg, dicOlv=dicOlv, db=db)
    ret = dlgAnte.ShowModal()
    if ret == wx.OK and dlgAnte.GetSelection():
        donnees = dlgAnte.GetSelection().donnees
        for ix in range(len(donnees)):
            dParams[dicOlv['listeCodesColonnes'][ix]] = donnees[ix]
        dParams['sensNum'] = dlg.sensNum
    dlgAnte.Destroy()
    return dParams

def ValideParams(pnl,dParams,mute=False):
    # vérifie la saisie des paramètres
    pnlFournisseur = pnl.GetPnlCtrl('fournisseur', codebox='param2')
    pnlAnalytique = pnl.GetPnlCtrl('analytique', codebox='param2')
    valide = True

    # normalisation none ''
    if dParams['fournisseur']  == None:
        dParams['fournisseur'] = ''
    if dParams['analytique'] == None:
        dParams['analytique'] = ''

    if dParams['origine'] in ('retour','camp'):
        if (dParams['analytique'] == '00') and len(pnl.lanceur.codesAnalytiques)>1:
            valide = False
            if not mute:
                wx.MessageBox("Veuillez saisir un camp pour affecter les coûts!")
                default = pnl.lanceur.codesAnalytiques[-1]
                pnl.lanceur.SetAnalytique(default)
                pnlAnalytique.SetFocus()
    return valide

def ConvTva(valeur,taux,modeOut='HT',modeIn='TTC'):
    # retourne la valeur transposée
    if modeIn == modeOut : return valeur
    if float(taux) == 0.0 : return
    if not modeOut in ('TTC','HT'): raise Exception("ConvTVA  %s %s impossible!!!"%(modeIn,modeOut))
    if modeIn == 'TTC': return round(float(valeur) / (1 + float(taux)/100),2)
    if modeIn == 'HT': return round(float(valeur) * (1+ float(taux)/100),2)

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
    dIxCol = {}
    if dParams['origine'] == 'achat':
        for code in ('nbAch', 'parAch', 'pxAch','pxUn','qte'):
            dIxCol[code] = lstCodesCol.index(code)

    # Enrichissement des lignes pour olv à partir des mouvements remontés
    for dMvt in ldMouvements:
        donnees = []
        dArticle = ddArticles[dMvt['IDarticle']]
        # alimente les données des colonnes
        for code in lstCodesCol:
            # ajout de la donnée dans le mouvement
            if code == 'qte' :
                donnees.append(dMvt['qte']* dlg.sensNum)
                continue
            if code == 'pxUn' :
                donnees.append(ConvTva(dMvt['prixUnit'],dArticle['txTva'],dlg.ht_ttc))
                continue
            if code == 'pxMoy':
                donnees.append(ConvTva(dArticle['prixMoyen'],dArticle['txTva'],dlg.ht_ttc))
                continue
            if code in dMvt.keys():
                donnees.append(dMvt[code])
                continue
            # ajout de l'article associé
            if code in dArticle.keys():
                donnees.append(dArticle)
                continue

            donnees.append(None)
            continue
        # codes supplémentaires de track non affichés('prixTTC','IDmouvement','dicArticle','dicMvt) dlg.dicOlv['lstCodesSup']
        donnees += [dArticle,
                    dMvt,]
        # correctif si présence des colonnes spéciales Achat

        if 'parAch' in lstCodesCol:
            donnees[dIxCol['parAch']] = 1
            donnees[dIxCol['nbAch']] = donnees[dIxCol['qte']]
            donnees[dIxCol['pxAch']] = donnees[dIxCol['pxUn']]
        lstDonnees.append(donnees)
    return lstDonnees

def PxUnToTTC(ht_ttc,txTva):
    # retourne le taux de conversion de la saisie vers le ttc
    if ht_ttc == 'HT':
        return 1 + (txTva / 100)
    else: return 1

def PxUnToHT(ht_ttc, txTva):
    # retourne le taux de conversion de la saisie vers le ht
    if ht_ttc == 'HT':
        return 1
    else:
        return 1 / (1+ (txTva / 100))

def CalculeLigne(dlg,track):
    if not hasattr(track,'dicArticle'): return
    if dlg.typeAchat:
        track.qte = track.nbAch * track.parAch
        if track.parAch == 0.0: track.parAch = 1
        track.pxUn = round(Nz(track.pxAch) / Nz(track.parAch),2)
    try: qte = float(track.qte)
    except: qte = 0.0

    try: pxUn = float(track.pxUn)
    except: pxUn = 0.0

    try: rations = track.dicArticle['rations']
    except: rations = 1
    txTva = track.dicArticle['txTva']
    track.mttHT = PxUnToHT(dlg.ht_ttc,txTva) * pxUn * qte
    track.mttTTC = PxUnToTTC(dlg.ht_ttc,txTva) * pxUn * qte
    track.prixTTC = round(PxUnToTTC(dlg.ht_ttc,txTva) * pxUn,2)
    track.qteStock = track.dicArticle['qteStock'] + (Nz(track.qte) * dlg.sensNum)

    if isinstance(track.IDmouvement,int):
        # Le mouvement est déjà comptabilisé dans le stock
        qteStock = dlg.ctrlOlv.buffArticles[track.IDarticle]['qteStock']
        if hasattr(track,'dicMvt') and track.IDarticle != track.dicMvt['IDarticle']:
            # le mouvement chargé n'est plus celui de l'article
            track.qteStock = qteStock + track.qte * dlg.sensNum
        elif hasattr(track,'dicMvt'):
            # le mouvement est celui de la ligne
            track.qteStock = qteStock + (track.qte * dlg.sensNum) - track.dicMvt['qte']
        else: track.qteStock = qteStock

    lstCodesColonnes = dlg.ctrlOlv.lstCodesColonnes
    track.nbRations = (track.qteStock) * rations
    for ix in range(len(lstCodesColonnes)):
        track.donnees[ix] = eval("track.%s"%lstCodesColonnes[ix])

def ValideLigne(dlg,track):
    # validation de la ligne de mouvement
    track.valide = True
    track.messageRefus = "Saisie incomplète\n\n"
    CalculeLigne(dlg,track)

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
        track.messageRefus += "La quantité est à zéro, mouvement inutile à supprimer\n"

    # pxUn null
    try:
        track.pxUn = float(track.pxUn)
    except:
        track.pxUn = None
    if not track.pxUn or track.pxUn == 0.0:
        track.messageRefus += "Le pxUn est à zéro, indispensable pour le prix de journée, fixez un prix!\n"

    # envoi de l'erreur
    if track.messageRefus != "Saisie incomplète\n\n":
        track.valide = False
    else: track.messageRefus = ""
    return

class PNL_params(xgte.PNL_params):
    #panel de paramètres de l'application
    def __init__(self, parent, **kwds):
        self.parent = parent
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
        dParams = {'origine': self.parent.GetOrigine(),
                     'date': self.parent.GetDate(),
                     'fournisseur': pnl.GetOneValue('fournisseur',codeBox='param2'),
                     'analytique': pnl.GetOneValue('analytique',codeBox='param2'),
                     'ht_ttc': pnl.GetOneValue('ht_ttc',codeBox='param3')}
        ret = ValideParams(pnl,dParams)

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

        try:
            IDmvt = int(track.IDmouvement)
        except: IDmvt = 0
        if code == 'IDarticle' and IDmvt >0:
            # ligne déjà enregistrée saisie de l'article à gérer comme suppression puis recréation
            track.oldIDarticle = track.IDarticle
            track.oldDicArticle = track.dicArticle

        if code == 'zzzzpxUn':
            if not hasattr(track, 'oldPu'):
                CalculeLigne(self.parent,track)
                track.oldPu = track.prixTTC

    def OnEditFinishing(self,code=None,value=None,event=None):
        self.parent.pnlPied.SetItemsInfos( INFO_OLV,wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)))
        # flagSkipEdit permet d'occulter les évènements redondants. True durant la durée du traitement
        if self.flagSkipEdit : return
        self.flagSkipEdit = True

        (row, col) = self.ctrlOlv.cellBeingEdited
        track = self.ctrlOlv.GetObjectAt(row)

        # Traitement des spécificités selon les zones
        if code == 'IDarticle':
            value = self.GetOneIDarticle(self.db,value)
            if value:
                track.IDarticle = value
                track.dicArticle = nust.SqlDicArticle(self.db,self.ctrlOlv,value)
                track.nbRations = track.dicArticle['rations']
                track.qteStock = track.dicArticle['qteStock']
                track.pxUn = track.dicArticle['prixMoyen'] / PxUnToTTC(self.lanceur.ht_ttc,track.dicArticle['txTva'])
                track.pxMoy = track.pxUn
                # stock négatif
                if self.lanceur.sens == "sorties" and (Nz(track.qteStock)) <= 0:
                    ret = wx.MessageBox("Le Stock est vide! Procédure à suivre: Luc 9:13", "Problème stock")

        if code == 'qte':
            # saisie négative en sortie
            if self.lanceur.sens == "sorties" and (Nz(value)) <= 0:
                wx.MessageBox("On ne garde que le positif dans les sorties!", "Problème saisie")
                value = abs(Nz(value))

            # stock négatif
            if self.lanceur.sens == "sorties" and (Nz(track.qteStock)- Nz(value)) < 0:
                wx.MessageBox("Le Stock deviendrait négatif sauf entrée à saisir: Luc 9:13", "Problème stock")

        if code in ('qte','pxUn','nbAch','pxAch','parAch'):
            # force la tentative d'enregistrement et le calcul même en l'absece de saisie
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
            IDarticle = self.GetOneIDarticle(self.db,self.ctrlOlv.GetObjectAt(row).IDarticle,f4=True)
            #self.ctrlOlv.GetObjectAt(row).IDarticle = IDarticle
            if IDarticle:
                ret = self.OnEditFinishing('IDarticle',IDarticle)

    def GetOneIDarticle(self,db,value,f4=False):
        # enlève temporairement le cellEdit pour éviter l'écho double clic
        self.ctrlOlv.cellEditMode = self.ctrlOlv.CELLEDIT_NONE
        id = DLG_Articles.GetOneIDarticle(db,value,f4=f4)
        self.ctrlOlv.cellEditMode = self.ctrlOlv.CELLEDIT_DOUBLECLICK
        return id

class PNL_pied(xgte.PNL_pied):
    #panel infos (gauche) et boutons sorties(droite)
    def __init__(self, parent, dicPied, **kwds):
        xgte.PNL_pied.__init__(self,parent, dicPied, **kwds)

class DLG(xusp.DLG_vide):
    # ------------------- Composition de l'écran de gestion----------
    def __init__(self,sens='sorties',date=None,**kwd):
        self.sens = sens
        self.sensNum = 1
        if self.sens == "sorties":
            self.sensNum = -1
        kwds = GetDlgOptions(self)
        listArbo=os.path.abspath(__file__).split("\\")
        kwds['title'] = listArbo[-1] + "/" + self.__class__.__name__
        super().__init__(None,**kwds)
        # l'appel des colonnes se fera dans OnOrigine
        self.dicOlv = {'lstCodesSup': GetOlvCodesSup()}
        self.dicOlv.update(GetOlvOptions(self))
        self.dicOlv['db'] = xdb.DB()
        self.origines = self.dicOlv.pop("codesOrigines",[])
        self.ordi = xuid.GetNomOrdi()
        self.today = datetime.date.today()
        if not date:
            date = self.today
        self.date = date
        self.analytique = '00'
        self.fournisseur = ''
        self.ht_ttc = 'TTC'
        self.oldParams = {}

        ret = self.Init()
        if ret == wx.ID_ABORT: self.Destroy()
        self.ht_ttc = self.pnlParams.GetOneValue('ht_ttc',codeBox='param3')
        self.origine = self.GetOrigine()
        self.OnOrigine(None)
        self.GetDonnees()
        self.Sizer()

    def Init(self):
        self.db = xdb.DB()
        # définition de l'OLV
        self.ctrlOlv = None

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
        self.valuesAnalytiques = ['',] + [nust.MakeChoiceActivite(x) for x in self.lstAnalytiques]
        self.codesAnalytiques = [x[:2] for x in self.valuesAnalytiques]
        self.codesAnalytiques[0] = '00'
        if len(self.codesAnalytiques) == 1:
            wx.MessageBox("Aucune activité définie!\n\nLes affectations analytiques ne seront pas possibles par camp")
        self.pnlParams.SetOneSet('analytique',values=self.valuesAnalytiques,codeBox='param2')
        self.SetAnalytique('00')
        self.pnlParams.SetOneValue('origine',valeur=DICORIGINES[self.sens]['values'][0],codeBox='param1')
        self.Bind(wx.EVT_CLOSE,self.OnClose)

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
        self.origine = self.GetOrigine()
        self.ctrlOlv.lstColonnes = GetOlvColonnes(self)
        self.ctrlOlv.lstCodesColonnes = self.ctrlOlv.GetLstCodesColonnes()
        self.ctrlOlv.InitObjectListView()
        self.Refresh()

    # gestion des ctrl choices avec codes différents des items

    def GetOrigine(self):
        lblOrigine = self.pnlParams.GetOneValue('origine',codeBox='param1')
        ixo = DICORIGINES[self.sens]['values'].index(lblOrigine)
        return DICORIGINES[self.sens]['codes'][ixo]

    def SetOrigine(self,code):
        ixo = DICORIGINES[self.sens]['codes'].index(code)
        value = DICORIGINES[self.sens]['values'][ixo]
        self.pnlParams.SetOneValue('origine',valeur=value,codeBox='param1')
        self.origine = code

    def GetAnalytique(self):
        choixAnalytique = self.pnlParams.GetOneValue('analytique',codeBox='param2')
        if len(choixAnalytique) > 0:
            ix = self.valuesAnalytiques.index(choixAnalytique)
            code = self.codesAnalytiques[ix]
        else: code = '00'
        return code

    def SetAnalytique(self,code):
        value = self.valuesAnalytiques[self.codesAnalytiques.index(code)]
        self.pnlParams.SetOneValue('analytique',valeur=value,codeBox='param2')
        self.analytique = code

    def GetDate(self,fr=False):
        saisie = self.pnlParams.GetOneValue('date',codeBox='param1')
        saisie = xformat.FmtDate(saisie)
        self.date = xformat.DateFrToDatetime(saisie)
        if fr: return saisie
        else: return self.date

    # gestion des actions ctrl
    def OnOrigine(self,event):
        if event:
            self.ctrlOlv.lstDonnees = []
            self.oldParams = {}
        self.origine = self.GetOrigine()
        self.dicOlv.update({'lstColonnes': GetOlvColonnes(self)})
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
            if len(self.valuesAnalytiques) >0:
                self.pnlParams.SetOneValue('analytique',self.valuesAnalytiques[0], codeBox='param2')
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
        self.ctrlOlv.lstColonnes = GetOlvColonnes(self)
        self.ctrlOlv.lstCodesColonnes = self.ctrlOlv.GetLstCodesColonnes()
        if event:
            self.GetDonnees()

    def OnDate(self,event):
        saisie = self.GetDate()
        self.pnlParams.SetOneValue('date',valeur=xformat.FmtDate(saisie),codeBox='param1')
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
        self.analytique = self.GetAnalytique()
        choixAnalytique = self.pnlParams.GetOneValue('analytique',codeBox='param2')
        if len(choixAnalytique) > 0:
            ix = self.valuesAnalytiques.index(choixAnalytique)
            self.analytique = self.lstAnalytiques[ix][0]
        self.GetDonnees()

    def OnBtnAnalytique(self,event):
        # Appel du choix d'un camp via un écran complet
        noegest = nung.Noegest(self)
        dicAnalytique = noegest.GetActivite(mode='dlg')
        codeAct = nust.MakeChoiceActivite(dicAnalytique)
        self.pnlParams.SetOneValue('analytique',codeAct,codeBox='param2')

    def OnBtnAnterieur(self,event):
        # lancement de la recherche d'un lot antérieur, on enlève le cellEdit pour éviter l'écho des double clics
        self.ctrlOlv.cellEditMode = self.ctrlOlv.CELLEDIT_NONE
        # choix d'un lot de lignes définies par des params
        dParams = GetAnterieur(self,db=self.db)
        self.ctrlOlv.cellEditMode = self.ctrlOlv.CELLEDIT_DOUBLECLICK # gestion du retour du choix dépot réactive dblClic
        if not 'date' in dParams.keys(): return
        self.pnlParams.SetOneValue('date',dParams['date'],'param1')
        self.pnlParams.SetOneValue('fournisseur',dParams['fournisseur'],'param2')
        self.SetOrigine(dParams['origine'])
        self.oldParams = {}
        self.GetDonnees(dParams)
        if event: event.Skip()

    def GetDonnees(self,dParams=None):
        if not dParams:
            dParams = {'origine':self.origine,
                         'date':self.date,
                         'fournisseur':self.fournisseur,
                         'analytique':self.analytique,
                         'ht_ttx':self.ht_ttc,
                         'sensNum': self.sensNum,}
        valide = ValideParams(self.pnlParams,dParams, mute=False)
        if not valide: return
        idem = True
        if self.oldParams == None :
            idem = False
        else:
            for key in ('origine','date','analytique','fournisseur','ht_ttx'):
                if not key in self.oldParams.keys(): idem = False
                elif not key in dParams.keys(): idem = False
                elif self.oldParams[key] != dParams[key]: idem = False
        if idem : return
        # forme la grille, puis création d'un premier modelObjects par init
        self.InitOlv()

        # appel des données de l'Olv principal à éditer
        self.oldParams = xformat.CopyDic(dParams)
        self.ctrlOlv.lstDonnees = [x for x in GetMouvements(self,dParams)]
        lstNoModif = [1 for rec in  self.ctrlOlv.lstDonnees if not (rec[-1])]

        # présence de lignes déjà transférées compta
        if len(lstNoModif) >0:
            self.ctrlOlv.cellEditMode = self.ctrlOlv.CELLEDIT_NONE
            self.pnlPied.SetItemsInfos("NON MODIFIABLE: enregistrements transféré ",
                                       wx.ArtProvider.GetBitmap(wx.ART_ERROR, wx.ART_OTHER, (16, 16)))

        # l'appel des données peut avoir retourné d'autres paramètres, il faut mettre à jour l'écran
        if len(self.ctrlOlv.lstDonnees) > 0:
            # set origine

            ixo = DICORIGINES[self.sens]['codes'].index(dParams['origine'])
            self.pnlParams.SetOneValue('origine',DICORIGINES[self.sens]['values'][ixo])
            self.OnOrigine(None)

            # set date du lot importé
            self.pnlParams.SetOneValue('date',xformat.FmtDate(dParams['date']),'param1')
            self.date = dParams['date']

            # set Fournisseur et analytique
            self.pnlParams.SetOneValue('fournisseur',dParams['fournisseur'],'param2')
            self.fournisseur = dParams['fournisseur']
            self.SetAnalytique(dParams['analytique'])

        # maj écritures reprises sont censées être valides, mais il faut les compléter
        self.ctrlOlv.MAJ()
        for track in self.ctrlOlv.modelObjects:
            CalculeLigne(self,track)
            track.valide = True
        self.ctrlOlv._FormatAllRows()
        self.ctrlOlv.MAJ()

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
