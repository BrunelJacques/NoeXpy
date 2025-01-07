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
import srcNoelite.UTILS_Noelite        as nung
import xpy.ObjectListView.xGTE as xGTE
import xpy.ObjectListView.xGTR as xGTR
import xpy.xUTILS_Identification       as xuid
import xpy.xUTILS_SaisieParams         as xusp
import xpy.xUTILS_DB                   as xdb
from srcNoestock                import DLG_Articles
from xpy.ObjectListView.ObjectListView  import ColumnDefn, CellEditor
from xpy.outils                 import xformat,xbandeau,xboutons
from xpy.outils.xformat         import Nz,DateSqlToDatetime

#---------------------- Matrices de paramétres -------------------------------------

TITRE = {'entrees':"Entrées en stock",
         'sorties':"Sorties de stock",
         'article':"Détail des mouvements"}

INTRO = {'entrees':"Gestion des entrées dans le stock, par livraison, retour ou autre ",
         'sorties':"Gestion des sorties du stock, par repas multicamp, pour un camp ou autre ",
         'article':"Détail des mouvements d'un article, avec possibilité de corriger ou supprimer des lignes.",}

DICORIGINES = {
                'entrees':{'codes': ['achat','retour','od_in'],
                           'label':"Nature  entrée",
                           'values': ['achat livraison', 'retour camp', 'od entrée']},
                'sorties': {'codes': ['repas', 'camp', 'od_out'],
                           'label':"Nature  sortie",
                           'values': ['vers cuisine', 'revente ou camp', 'od sortie']},
                'article': {'codes': [  'tous','achat','retour','od_in',
                                        'repas', 'camp', 'od_out'
                                        'entrees','sorties'],
                            'label': "Nature Mouvements",
                            'values': ['tous...','achat livraison', 'retour camp', 'od entrée',
                                       'vers cuisine', 'revente ou camp', 'od sortie',
                                       'Entrées','Sorties']},
                }

DICDATE = {     'entrees':{'label':"Date d' entrée"},
                'sorties':{'label':"Date de sortie",},
                'article': {'label': "xxxxx", }
                }

DIC_INFOS = {
            'IDarticle': "<F4> Choix d'un article, ou saisie directe de son code",
            'qte': "L'unité est en général précisée dans le nom de l'article\nNbre dans le plus petit conditionnements, pas par carton complet",
            'pxUn': "HT ou TTC selon le choix en haut d'écran\nPrix d'une unité telle qu'on la sort du stock, pas celui du carton complet",
             }

INFO_OLV = "Possibles sur des lignes: <Suppr> <Inser> <Ctrl C> <Ctrl X> <Ctrl V>"

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

    lstChamps = ['origine', 'date', 'fournisseur', 'IDanalytique',
                 'COUNT(IDmouvement)','SUM(qte * prixUnit)']

    lstNomsColonnes = ['origine', 'date', 'fournisseur', 'analytique', 'nbLignes','montant']

    lstTypes = ['varchar(8)', 'date', 'varchar(32)', 'varchar(32)', 'int', 'float']
    lstCodesColonnes = [xformat.NoAccents(x).lower() for x in lstNomsColonnes]
    lstValDefColonnes = xformat.ValeursDefaut(lstNomsColonnes, lstTypes)
    lstLargeurColonnes = [70,90,120,80,60,100]
    lstColonnes = xformat.DefColonnes(lstNomsColonnes, lstCodesColonnes, lstValDefColonnes, lstLargeurColonnes)
    return {
        'codesOrigines': dlg.codesOrigines,
        'lstColonnes': lstColonnes,
        'lstChamps': lstChamps,
        'listeNomsColonnes': lstNomsColonnes,
        'listeCodesColonnes': lstCodesColonnes,
        'getDonnees': nust.SqlMvtsAnte,
        'dicBandeau': dicBandeau,
        'sortColumnIndex': 1,
        'sensTri': False,
        'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
        'size': (650, 400),
        'dateEnCours':dlg.date}

# Description des paramètres de la gestion des mouvements

MATRICE_PARAMS = {
    ("param1", "Paramètres"): [
        {'name': 'origine', 'genre': 'Choice', 'label': "",
         'help': "Le choix de la nature modifie certains contrôles",
         'value': 0, 'values': [],
         'ctrlAction': 'OnOrigine',

         'txtSize': 90},
        {'name': 'date', 'genre': 'Texte', 'label': "",
         'help': "%s\n%s\n%s" % ("Saisie JJMMAA ou JJMMAAAA possible.",
                                 "Les séparateurs ne sont pas obligatoires en saisie.",
                                 "Saisissez la date du mouvement de stock sans séparateurs, "),
         'value': "",
         'ctrlAction': 'OnDate',

         'txtSize': 90},
    ],
    ("param2", "Comptes"): [
        {'name': 'fournisseur', 'genre': 'Combo', 'label': 'Fournisseur',
         'help': "La saisie d'un fournisseurfacilite les commandes par fournisseur",
         'value': 0, 'values': [''],
         'ctrlAction': 'OnFournisseur',
         'btnLabel': "...", 'btnHelp': "Cliquez pour choisir un compte pour l'origine",
         'btnAction': 'OnBtnFournisseur',
         'size': (250, 25),
         'txtSize': 70,
         },
        {'name': 'analytique', 'genre': 'Choice', 'label': 'Activité',
         'ctrlAction': 'OnAnalytique',
         'help': "Il s'agit de l'activité qui a endossé la charge de la sortie",
         'value': '', 'values': [''],
         'btnLabel': "...",
         'btnHelp': "Cliquez pour choisir l'activité de destination des mouvements",
         'btnAction': 'OnBtnAnalytique',
         'txtSize': 70, }
    ],
    ("param3", "saisie"): [
        {'name': 'ht_ttc', 'genre': 'Choice', 'label': 'Saisie de la TVA',
         'help': "Choix du mode de saisie HT ou TTC selon le plus facile pour vous",
         'value': 1, 'values': ['TTC', 'HT'],
         'ctrlAction': 'OnHt_ttc',
         'txtSize': 70,
         },
        {'name': '', 'genre': None, }
    ],
    ("espace", "vide"): [
        {'name': 'vide', 'genre': None, }
    ],
    ("param4", "Compléments"): [
        {'name': 'rappel', 'genre': 'anyctrl', 'label': ' ',
         'txtSize': 20,
         'ctrl': CtrlAnterieur,
         'ctrlAction': 'OnBtnAnterieur',
         },
    ],
}

def GetDicPnlParams(dlg):
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
                'boxesSizes': [(250, 60), (250, 60),(160, 60), None, (160, 60)],
                'pathdata':"srcNoelite/Data",
                'nomfichier':"stparams",
                'nomgroupe':"entrees",
            }

def GetParams(pnl):
    return {
        'lstOrigines': pnl.parent.GetOrigines(),
        'date': pnl.parent.date,
        'fournisseur': pnl.GetOneValue('fournisseur', codeBox='param2'),
        'analytique': pnl.parent.analytique,
        'ht_ttc': pnl.GetOneValue('ht_ttc', codeBox='param3'),
        'sensNum': pnl.sensNum}

def GetBoutons(dlg):
    return  [
        {'name': 'btnCorrections', 'label': "Correction\nde saisie",
         'help': "Cliquez ici pour changer la date, la nature... de lignes sélectionnées",
         'size': (120, 35), 'onBtn': dlg.OnBtnCorrections},
        {'name': 'btnImp', 'label': "Imprimer\npour contrôle",
            'help': "Cliquez ici pour imprimer et enregistrer la saisie de l'entrée en stock",
            'size': (120, 35), 'image': wx.ART_PRINT,'onBtn':dlg.OnImprimer},
        {'name':'btnOK','ID':wx.ID_ANY,'label':"Quitter",'help':"Cliquez ici pour sortir",
            'size':(120,35),'image':"xpy/Images/32x32/Quitter.png",'onBtn':dlg.OnFermer}
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
            ColumnDefn("Coût Ration", 'right', 80, 'pxRation', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal, isEditable=False),
            ColumnDefn("Nbre Rations", 'right', 80, 'nbRations', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal, isEditable=False),
            ColumnDefn("Mtt HT", 'right', 80, 'mttHT', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal, isEditable=False),
            ColumnDefn("Mtt TTC", 'right', 80, 'mttTTC', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal, isEditable=False),
            ColumnDefn("PrixStock", 'right', 80, 'pxMoy', isSpaceFilling=False, valueSetter=0.0,
                   stringConverter=xformat.FmtDecimal, isEditable=False),
            ColumnDefn("Qté stock", 'right', 80, 'qteStock', isSpaceFilling=False, valueSetter=0.0,
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
    codesOrigines = DICORIGINES[dlg.sens]['codes']
    return {
            'codesOrigines': codesOrigines,
            'checkColonne': False,
            'recherche': True,
            'minSize': (600, 100),
            'dictColFooter': {"IDarticle": {"mode": "nombre", "alignement": wx.ALIGN_CENTER},
                                  "qte": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                                  "mttHT": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                                  "mttTTC": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                                  },
    }

def GetDlgOptions(dlg):
    # Options du Dlg de lancement
    return {
        'style': wx.DEFAULT_FRAME_STYLE,
        'minSize': (700, 450),
        'size': (1150, 800),
        }

    #----------------------- Parties de l'écrans -----------------------------------------

def GetParamsAnterieur(dlg, db=None):
    # retourne un dict de params après lancement d'un tableau de choix de l'existants pour reprise
    dParams = {}
    dicOlv = GetMatriceAnterieurs(dlg)
    dlgAnte = xGTR.DLG_tableau(dlg, dicOlv=dicOlv, db=db,
                               title='xGTR par DLG_Mouvements.GetAnterieur')
    ret = dlgAnte.ShowModal()
    if ret == wx.OK and dlgAnte.GetSelection():
        donnees = dlgAnte.GetSelection().donnees
        for ix in range(len(donnees)):
            dParams[dicOlv['listeCodesColonnes'][ix]] = donnees[ix]
        dParams['sensNum'] = dlg.sensNum
        dParams['date'] = DateSqlToDatetime(dParams['date'])
    dlgAnte.Destroy()
    dParams['lstOrigines'] = [dParams['origine'],]
    return dParams

def GetEnSaisie(dlg,db=None):
    # Façon GetAnterieur retourne un dict de params de la dernière saisie du jour
    dParams = {}
    dicOlv = xformat.CopyDic(GetMatriceAnterieurs(dlg))
    getDonnees = dicOlv['getDonnees']
    dicOlv['lstChamps'][-1] =  'MAX(IDmouvement)'
    encours = str(datetime.date.today())
    lstDonnees = getDonnees(dicOlv=dicOlv,db=db,encours=encours)
    if len(lstDonnees) > 0:
        donnees = lstDonnees[0]
        for ix in range(len(donnees)):
            if dicOlv['lstChamps'][ix] == 'IDanalytique':
                dicOlv['lstChamps'][ix] = 'analytique'
            dParams[dicOlv['lstChamps'][ix]] = donnees[ix]
        dParams['sensNum'] = dlg.sensNum
    return dParams

def ValideParams(pnl,dParams,mute=False):
    # vérifie la saisie des paramètres
    pnlFournisseur = pnl.GetPnlCtrl('fournisseur', codebox='param2')
    pnlAnalytique = pnl.GetPnlCtrl('analytique', codebox='param2')
    pnlDate = pnl.GetPnlCtrl('date', codebox='param1')
    valide = True

    # normalisation none ''
    if dParams['fournisseur']  == None:
        dParams['fournisseur'] = ''
    if dParams['analytique'] == None:
        dParams['analytique'] = ''

    mess = None
    if not dParams['date']  or dParams['date'] == "":
        mess = "Veuillez saisir une date"
    if not mess:
        ddt = xformat.DateFrToDatetime(dParams['date'],mute=True)
        if ddt == None:
            mess = "La date saisie est incorrecte"
    if mess:
        if not mute:
            wx.MessageBox(mess)
        valide = False
        pnlDate.SetFocus()

    if dParams['lstOrigines'][0] in ('retour','camp'):
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
    if modeIn == 'TTC': return round(float(valeur) / (1 + float(taux)/100),6)
    if modeIn == 'HT': return round(float(valeur) * (1+ float(taux)/100),6)

def GetMouvements(dlg, dParams):
    # retourne la liste des données de l'OLv de DlgEntree
    ctrlOlv = dlg.ctrlOlv

    ldMouvements = nust.GetMvtsByDate(dlg.db, dParams)
    # appel des dicArticles des mouvements
    lstArticles = [x['IDarticle'] for x in ldMouvements]
    ddArticles = nust.SqlDicArticles(dlg.db, dlg.ctrlOlv,lstArticles )

    # composition des données
    lstDonnees = []
    lstCodesCol = ctrlOlv.GetLstCodesColonnes()
    dIxCol = {}
    if dParams['lstOrigines'][0] == 'achat':
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
    if not hasattr(track,'dicArticle') or not track.dicArticle: return
    if dlg.typeAchat:
        track.qte = track.nbAch * track.parAch
        if track.parAch == 0.0: track.parAch = 1
        track.pxUn = round(Nz(track.pxAch) / Nz(track.parAch),6)
    try: qte = float(track.qte)
    except: qte = 0.0
    try: pxUn = float(track.pxUn)
    except: pxUn = 0.0

    try: rations = track.dicArticle['rations']
    except:
        rations = 1
    txTva = track.dicArticle['txTva']
    track.mttHT = PxUnToHT(dlg.ht_ttc,txTva) * pxUn * qte
    track.mttTTC = PxUnToTTC(dlg.ht_ttc,txTva) * pxUn * qte
    track.prixTTC = round(PxUnToTTC(dlg.ht_ttc,txTva) * pxUn,6)
    # cas de base, stock précédent corrigé du mouvement
    track.qteStock = track.dicArticle['qteStock'] + (Nz(track.qte) * dlg.sensNum)
    if hasattr(track, 'dicMvt') and track.dicMvt and track.dicMvt['IDarticle']:
        # Le mouvement de cet article est déjà comptabilisé dans le stock (correction)
        track.qteStock -= track.dicMvt['qte']

    lstCodesColonnes = dlg.ctrlOlv.lstCodesColonnes
    track.nbRations = qte * rations
    if track.nbRations >0:
        track.pxRation = track.prixTTC / track.nbRations
    else: track.pxRation = 0.0
    for ix in range(len(lstCodesColonnes)):
        track.donnees[ix] = eval("track.%s"%lstCodesColonnes[ix])

def ValideLigne(dlg,track):
    # validation de la ligne de mouvement
    track.valide = True
    track.valide = ValideParams(dlg.pnlParams,GetParams(dlg.pnlParams),True)
    if not track.valide:
        wx.MessageBox = "les paramètres du haut d'écran ne sont pas valides"
        return
    track.messageRefus = "Saisie incomplète\n\n"
    CalculeLigne(dlg,track)

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

class PNL_params(xGTE.PNL_params):
    #panel de paramètres de l'application
    def __init__(self, parent, **kwds):
        self.parent = parent
        kwds = parent.GetDicPnlParams(parent)
        super().__init__(parent, **kwds)
        if hasattr(parent,'lanceur'):
            self.lanceur = parent.lanceur
        else: self.lanceur = parent

class PNL_corps(xGTE.PNL_corps):
    #panel olv avec habillage optionnel pour des boutons actions (à droite) des infos (bas gauche) et boutons sorties
    def __init__(self, parent, dicOlv,*args, **kwds):
        xGTE.PNL_corps.__init__(self,parent,dicOlv,*args,**kwds)
        self.Name = "%s.PNL_corps"%self.parent.Name
        self.db = parent.db
        self.lstNewReglements = []
        self.flagSkipEdit = False
        self.oldRow = None
        self.dicArticle = None

    def InitTrackVierge(self,track,modelObject):
        #track.creer = True
        track.repas = None

    def ValideParams(self):
        pnl = self.parent.pnlParams
        dParams = GetParams(pnl)
        ret = ValideParams(pnl,dParams)

    def OnCollerTrack(self, track):
        # avant de coller une track, raz de certains champs et recalcul
        track.IDmouvement = None
        if hasattr(track,'dicMvt'):
            del track.dicMvt # ceci pour créer une différence avec tracK.qte
        self.ValideLigne(None,track)
        CalculeLigne(self.lanceur,track)
        self.SauveLigne(track)

    def OnDeleteTrack(self, track):
        CalculeLigne(self.lanceur,track)
        nust.DelMouvement(self.parent.db,self.ctrlOlv,track)

    def OnEditStarted(self,code,track=None,editor=None):
        # affichage de l'aide
        if code in DIC_INFOS.keys():
            self.parent.pnlPied.SetItemsInfos( DIC_INFOS[code],
                                               wx.ArtProvider.GetBitmap(wx.ART_FIND,
                                                                        wx.ART_OTHER,
                                                                        (16, 16)))
        else:
            self.parent.pnlPied.SetItemsInfos(INFO_OLV,
                                              wx.ArtProvider.GetBitmap(wx.ART_INFORMATION,
                                                                       wx.ART_OTHER,
                                                                       (16, 16)))
        # travaux avant saisie
        if self.parent.sens == 'sorties' and track.repas == None :
            # choix par défaut selon l'heure
            h = datetime.datetime.now().hour
            ch=3
            if h < 8: ch=1
            if h < 17: ch=2
            track.repas = nust.CHOIX_REPAS[ch-1]

        if code == 'origine':
            lstChoix = DICORIGINES[self.parent.sens]['codes'][1:]
            editor.Set(lstChoix)
            if self.parent.sens != 'article':
                if track.origine:
                    editor.SetStringSelection(track.origine)
                else:
                    editor.SetSelection(0)

        if code == 'repas':
            editor.Set(nust.CHOIX_REPAS)
            if track.repas:
                editor.SetStringSelection(track.repas)
            else:
                editor.SetSelection(1)

        try:
            IDmvt = int(track.IDmouvement)
        except: IDmvt = 0
        if code == 'IDarticle' and IDmvt >0:
            # ligne déjà enregistrée saisie de l'article à gérer comme suppression puis recréation
            track.oldIDarticle = track.IDarticle
            track.oldDicArticle = track.dicArticle

        #if code == 'pxUn':

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
            track.IDarticle = value
            if value:
                ddArticles = nust.SqlDicArticles(self.db, self.ctrlOlv, [value,])
                track.dicArticle = ddArticles[value]
                track.nbRations = track.dicArticle['rations']
                track.qteStock = track.dicArticle['qteStock']
                track.pxUn = track.dicArticle['prixMoyen'] / PxUnToTTC(self.lanceur.ht_ttc,track.dicArticle['txTva'])
                track.pxMoy = track.pxUn
                # stock négatif
                if self.lanceur.sens == "sorties" and (Nz(track.qteStock)) < 0:
                    ret = wx.MessageBox("Le Stock est vide! Erreur d'article ou Entrée manquante")
                if event: event.Veto(False)
            else:
                if event: event.Veto(True)

        if code == 'qte':
            # saisie négative en sortie
            if self.lanceur.sens == "sorties" and (Nz(value)) <= 0:
                wx.MessageBox("On ne garde que le positif dans les sorties!", "Problème saisie")
                value = abs(Nz(value))

            # stock négatif
            if self.lanceur.sens == "sorties" and (Nz(track.qteStock)- Nz(value)) < 0:
                wx.MessageBox("Simple remarque!\n\nAvec cette sortie le Stock deviendra négatif", "Problème stock")

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

    def CalculeLigne(self,code,track):
        # Relais de l'appel par par GetDonnnees
        CalculeLigne(self.parent,track)

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

class PNL_pied(xGTE.PNL_pied):
    #panel infos (gauche) et boutons sorties(droite)
    def __init__(self, parent, dicPied, **kwds):
        xGTE.PNL_pied.__init__(self,parent, dicPied, **kwds)

class DLG(xGTE.DLG_tableau):
    # ------------------- Composition de l'écran de gestion----------
    def __init__(self,sens='sorties',date=None,**kwd):
        # gestion des deux sens possibles 'entrees' et 'sorties'
        if not sens: sens = 'article'
        self.sens = sens
        self.sensNum = 1
        if self.sens == "sorties":
            self.sensNum = -1
        self.GetDicPnlParams = GetDicPnlParams
        kwds = GetDlgOptions(self)
        listArbo=os.path.abspath(__file__).split("\\")
        kwds['title'] = kwd.pop('title',listArbo[-1] + "/" + self.__class__.__name__)
        super().__init__(None,**kwds)
        # l'appel des colonnes se fera dans OnOrigine
        self.dicOlv = {'lstCodesSup': GetOlvCodesSup()}
        self.dicOlv.update(GetOlvOptions(self))
        self.dicOlv['db'] = xdb.DB()
        self.lastInventaire = nust.GetDateLastInventaire(self.dicOlv['db'])
        self.codesOrigines = self.dicOlv.pop("codesOrigines",[])
        self.ordi = xuid.GetNomOrdi()
        self.today = datetime.date.today()
        self.date = date
        self.origine = None
        self.analytique = '00'
        self.fournisseur = ''
        self.ht_ttc = 'TTC'
        if sens == "entrees":  self.htTTC = 'HT'
        self.oldParams = {}

        ret = self.Init()
        if ret == wx.ID_ABORT: self.Destroy()
        try:
            self.ht_ttc = self.GetTva()
            self.origine = self.GetOrigines()
            self.OnOrigine(None)
        except:
            pass
        self.pnlParams.sensNum = self.sensNum
        self.GetDonnees()
        pnlDate = self.pnlParams.GetPnlCtrl('date')
        if pnlDate:
            pnlDate.SetValue("-")
        self.Sizer()
        if pnlDate:
            pnlDate.SetValue("")

    def Init(self):
        self.db = xdb.DB()
        # définition de l'OLV
        self.ctrlOlv = None
        # boutons de bas d'écran - infos: texte ou objet window.  Les infos sont  placées en bas à gauche
        lstInfos = [ wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)),INFO_OLV]
        dicPied = {'lstBtns': GetBoutons(self), "lstInfos": lstInfos}

        # lancement de l'écran en blocs principaux
        if self.sens == 'entrees':
            self.pnlBandeau = xbandeau.Bandeau(self,TITRE[self.sens],INTRO[self.sens], hauteur=20,
                                               nomImage="xpy/Images/80x80/Entree.png",
                                               sizeImage=(60,40))
            self.pnlBandeau.SetBackgroundColour(wx.Colour(220, 250, 220))
        elif self.sens == 'article':
            self.pnlBandeau = xbandeau.Bandeau(self, TITRE[self.sens],
                                               INTRO[self.sens], hauteur=20,
                                               nomImage="xpy/Images/80x80/Loupe.png",
                                               sizeImage=(60, 40))
            self.pnlBandeau.SetBackgroundColour(wx.Colour(250, 216, 53))
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
        self.fournisseurs = nust.SqlFournisseurs(self.db)
        self.pnlParams.SetOneSet('fournisseur',values=self.fournisseurs,codeBox='param2')
        self.lstAnalytiques = nust.SqlAnalytiques(self.db,'ACTIVITES')
        self.valuesAnalytiques = ['',] + [nust.MakeChoiceActivite(x) for x in self.lstAnalytiques]
        self.codesAnalytiques = [x[:2] for x in self.valuesAnalytiques]
        self.codesAnalytiques[0] = '00'
        if len(self.codesAnalytiques) == 1:
            wx.MessageBox("Aucune activité définie!\n\nLes affectations analytiques ne seront pas possibles par camp")
        self.pnlParams.SetOneSet('analytique',values=self.valuesAnalytiques,codeBox='param2')
        self.SetAnalytique('00')
        self.pnlParams.SetOneValue('origine',valeur=DICORIGINES[self.sens]['values'][0],codeBox='param1')
        self.Bind(wx.EVT_CLOSE,self.OnFermer)

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
        self.origine = self.GetOrigines()
        self.ctrlOlv.lstColonnes = GetOlvColonnes(self)
        self.ctrlOlv.lstCodesColonnes = self.ctrlOlv.GetLstCodesColonnes()
        self.ctrlOlv.InitObjectListView()
        self.Refresh()

    # gestion des ctrl choices avec codes différents des items

    def GetTva(self):
        return self.pnlParams.GetOneValue('ht_ttc', codeBox='param3')

    def GetOrigines(self):
        lblOrigine = self.pnlParams.GetOneValue('origine')
        ixo = DICORIGINES[self.sens]['values'].index(lblOrigine)
        origine =  DICORIGINES[self.sens]['codes'][ixo]
        if origine in ('entrees','sorties'):
            lstOrigines = DICORIGINES[origine]['codes']
        else:
            lstOrigines = [origine,]
        return lstOrigines

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
        if not code or code == '':
            code = "00"
        value = self.valuesAnalytiques[self.codesAnalytiques.index(code)]
        self.pnlParams.SetOneValue('analytique',valeur=value,codeBox='param2')
        self.analytique = code

    def GetDate(self):
        saisie = self.pnlParams.GetOneValue('date',codeBox='param1')
        saisie = xformat.FmtDate(saisie)
        self.date = xformat.DateFrToDatetime(saisie)
        if not saisie:
            return None
        else: return self.date

    # gestion des actions ctrl
    def OnOrigine(self,event):
        if event:
            self.ctrlOlv.lstDonnees = []
            self.oldParams = {}
        self.origine = self.GetOrigines()
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
            self.analytique = '00'
            self.pnlParams.SetOneValue('analytique',"", codeBox='param2')
        elif ('retour' in self.origine) or ('camp' in self.origine)  :
            setEnable('fournisseur',False)
            self.fournisseur = ''
            self.pnlParams.SetOneValue('fournisseur',"", codeBox='param2')
            setEnable('analytique',True)
            if len(self.valuesAnalytiques) >0:
                self.pnlParams.SetOneValue('analytique',self.valuesAnalytiques[0], codeBox='param2')
        elif ('od' in self.origine) or ('repas' in self.origine) :
            self.pnlParams.SetOneValue('fournisseur',"", codeBox='param2')
            setEnable('fournisseur',False)
            self.fournisseur = ''
            self.pnlParams.SetOneValue('analytique',"", codeBox='param2')
            setEnable('analytique',False)
            self.analytique = '00'
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
        if saisie:
            if saisie <= self.lastInventaire:
                wx.MessageBox("La date saisie est dans un exercice antérieur",
                              "NON bloquant",wx.ICON_WARNING)
            if saisie - self.lastInventaire > datetime.timedelta(days=366):
                wx.MessageBox("Le dernier inventaire date de '%s'"%self.lastInventaire,
                              "VERIFICATION",wx.ICON_INFORMATION)
            self.pnlParams.SetOneValue('date',valeur=xformat.FmtDate(saisie),codeBox='param1')
            self.GetDonnees()
        if event: event.Skip()

    def OnHt_ttc(self,event):
        self.ht_ttc = self.pnlParams.GetOneValue('ht_ttc',codeBox='param3')
        self.GetDonnees()
        if event: event.Skip()

    def OnFournisseur(self,event):
        fournisseur = self.pnlParams.GetOneValue('fournisseur',codeBox='param2')
        fournisseur = fournisseur.strip().upper()
        lg = min(len(fournisseur),7)
        lstChoix = [x for x in self.fournisseurs if x[:lg] == fournisseur[:lg]]
        if len(fournisseur) ==0: pass
        elif len(fournisseur) < 3:
            # moins de trois caractères c'est trop court, mieux vaut rien
            mess = "Identiant fournisseur trop court\n\n"
            mess = "Soit à blanc fournisseur soit au moins trois caractères pour un fournisseur!"
            wx.MessageBox(mess,"Refus")
            return
        elif len(lstChoix) == 1:
            # un seul item fournisseur correspond, on le choisit
            fournisseur = lstChoix[0]
        elif len(lstChoix) == 0:
            # nouvel item à confirmer
            mess = "'%s' est-il bien un nouveau fournisseur à créer?\n\n"%fournisseur
            if len(fournisseur) < 7:
                # permetra un autre fournisseur avec le même début
                fournisseur += "_"
            ret = wx.MessageBox(mess,"Confirmez",style=wx.OK|wx.CANCEL)
            if ret != wx.OK:
                self.pnlParams.SetOneValue('fournisseur', None, codeBox='param2')
                return
        elif len(lstChoix) > 1:
            from xpy.outils  import  xchoixListe
            dlg = xchoixListe.DialogAffiche(lstDonnees=lstChoix,
                lstColonnes=['nom_fournisseur',],
                titre="Précisez  votre choix",
                intro="Sinon créez un nouveau fournisseur avec un nom plus long")
            ret = dlg.ShowModal()
            choix = dlg.choix
            getch = dlg.GetChoix()
            if ret == wx.OK:
                fournisseur = dlg.GetChoix()
            else: fournisseur = ''
            dlg.Destroy()
        self.fournisseur = fournisseur
        self.pnlParams.SetOneValue('fournisseur', fournisseur, codeBox='param2')
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
            ix = self.valuesAnalytiques.index(choixAnalytique) -1
            if isinstance(ix,int) and ix <= len(self.lstAnalytiques):
                self.analytique = self.lstAnalytiques[ix][0]
            else: return
        self.GetDonnees()

    def OnBtnAnalytique(self,event):
        # Appel du choix d'un camp via un écran complet
        noegest = nung.Noelite(self)
        dicAnalytique = noegest.GetActivite(mode='dlg')
        if dicAnalytique:
            codeAct = nust.MakeChoiceActivite(dicAnalytique)
            self.pnlParams.SetOneValue('analytique',codeAct,codeBox='param2')

    def OnBtnAnterieur(self,event):
        if event:
            # lancement de la recherche d'un lot antérieur, on enlève le cellEdit pour éviter l'écho des double clics
            self.ctrlOlv.cellEditMode = self.ctrlOlv.CELLEDIT_NONE
            # choix d'un lot de lignes définies par des params
            dParams = GetParamsAnterieur(self, db=self.db)
            self.ctrlOlv.cellEditMode = self.ctrlOlv.CELLEDIT_DOUBLECLICK # gestion du retour du choix dépot réactive dblClic
        else:
            # cas du lancement par __init
            dParams = GetEnSaisie(self,db=self.db)

        if not 'date' in dParams.keys(): return

        self.pnlParams.SetOneValue('date',dParams['date'],'param1')
        self.pnlParams.SetOneValue('fournisseur',dParams['fournisseur'],'param2')
        self.SetOrigine(dParams['lstOrigines'][0])
        self.oldParams = {}
        self.GetDonnees(dParams)
        if event: event.Skip()

    def OnBtnCorrections(self,event):
        objects = self.ctrlOlv.GetSelectedObjects()
        if len(objects) == 0:
            mess = "Sélectionnez un groupe de lignes.\n\n"
            mess += "Pour cela utilisez <shift> ou <ctrl> + clic gauche souris"
            mess += "Pour tout selectionnez, utilisez <ctrl> <A>"
            wx.MessageBox(mess, "Selection vide",style=wx.ICON_INFORMATION|wx.OK)
            return

    def ParamsIdem(self,oldParams,dParams):
        idem = True
        if self.oldParams == None :
            idem = False
        else:
            for key in ('origine','date','analytique','fournisseur','ht_ttx'):
                if not key in self.oldParams.keys(): idem = False
                elif not key in dParams.keys(): idem = False
                elif self.oldParams[key] != dParams[key]: idem = False
        return idem

    def GetDonnees(self,dParams=None):
        if not dParams:
            dParams = GetParams(self.pnlParams)
        if self.ParamsIdem(self.oldParams,dParams):
            return
        valide = ValideParams(self.pnlParams,dParams, mute=True)
        # forme la grille, puis création d'un premier modelObjects par init
        self.InitOlv()

        # appel des données de l'Olv principal à éditer
        self.oldParams = xformat.CopyDic(dParams)

        if valide:
            self.ctrlOlv.lstDonnees = [x for x in GetMouvements(self,dParams)]
        else:
            self.ctrlOlv.lstDonnees = []
        lstNoModif = [1 for rec in  self.ctrlOlv.lstDonnees if not (rec[-1])]

        # présence de lignes déjà transférées compta
        if len(lstNoModif) >0:
            self.ctrlOlv.cellEditMode = self.ctrlOlv.CELLEDIT_NONE
            self.pnlPied.SetItemsInfos("NON MODIFIABLE: enregistrements transféré ",
                                       wx.ArtProvider.GetBitmap(wx.ART_ERROR, wx.ART_OTHER, (16, 16)))

        # l'appel des données peut avoir retourné d'autres paramètres, il faut mettre à jour l'écran
        if len(self.ctrlOlv.lstDonnees) > 0:
            # set origine

            ixo = DICORIGINES[self.sens]['codes'].index(dParams['lstOrigines'][0])
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

    def GetTitreImpression(self):
        tiers = ''
        if self.fournisseur: tiers += ", Fournisseur: %s"%self.fournisseur.capitalize()
        if self.analytique: tiers += ", Camp: %s"%self.analytique.capitalize()
        date = xformat.DateSqlToFr(self.date)
        return "Mouvements STOCKS %s du %s, %s%s"%(self.sens, date, self.origine,tiers)

    def ValideImpress(self):
        # test de présence d'écritures non valides
        lstNonValides = [x for x in self.ctrlOlv.modelObjects if not x.valide and x.IDmouvement]
        if len(lstNonValides) > 0:
            ret = wx.MessageBox('Présence de lignes non valides!\n\nCes lignes seront détruites avant impression',
                                'Confirmez pour continuer', style=wx.OK | wx.CANCEL)
            if ret != wx.OK: return False
        # test de présence d'un filtre
        if len(self.ctrlOlv.innerList) != len(self.ctrlOlv.modelObjects):
            ret = wx.MessageBox('Filtre actif!\n\nDes lignes sont filtrées, seules les visibles seront rapportées',
                                'Confirmez pour continuer',style=wx.OK|wx.CANCEL)
            if ret != wx.OK: return False
        # purge des lignes non valides
        self.ctrlOlv.modelObjects=[x for x in self.ctrlOlv.modelObjects if hasattr(x,'valide') and x.valide]
        # réaffichage
        self.ctrlOlv.RepopulateList()
        return True

    def OnImprimer(self,event):
        self.ctrlOlv.Apercu(None)

#------------------------ Lanceur de test  -------------------------------------------

if __name__ == '__main__':
    app = wx.App(0)
    os.chdir("..")
    dlg = DLG()
    dlg.ShowModal()
    app.MainLoop()
