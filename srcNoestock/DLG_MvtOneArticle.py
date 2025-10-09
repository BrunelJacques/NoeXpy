#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------
# Application:     NoeStock, gestion des stocks et prix de journée
# Module:          Saisie des mouvements d'un article
# Auteur:          Jacques BRUNEL 2022-07
# Licence:         Licence GNU GPL
# ------------------------------------------------------------------
import copy

import wx
import os
import datetime
import srcNoestock.DLG_Mouvements      as dlgMvts
import srcNoestock.DLG_Articles        as dlgArt
import srcNoestock.UTILS_Stocks        as nust
import xpy.xUTILS_SaisieParams         as xusp
from srcNoelite                                 import DB_schema
from xpy.outils.xformat                         import Nz
from xpy.ObjectListView.ObjectListView   import ColumnDefn
from xpy.ObjectListView.CellEditor       import ChoiceEditor
from xpy.outils                          import xformat,xbandeau,xchoixListe, xdates

MODULE = os.path.abspath(__file__).split("\\")[-1]

class CTRL_calcul(xchoixListe.CTRL_Solde):
    def __init__(self,parent,):
        super().__init__(parent,size=(80,35))

MATRICE_PARAMS = {
('param1', "Article"): [
    {'name': 'article', 'genre': 'texte', 'label': 'Article',
                    'help': "Le choix de l'article génère la liste ci-dessous'",
                    'value':'0',
                    'ctrlAction':'OnArticle',
                     'btnLabel': "...", 'btnHelp': "Cliquez pour choisir un article",
                     'btnAction': 'OnBtnArticle',
                    'size':(300,28),
                    'ctrlMaxSize':(350,28),
                    'txtSize': 50,
     },
    {'name': 'tous', 'genre': 'check', 'label': 'Tous',
                    'help': "Cochez pour prendre tous les articles, la date 'Après le' détermine le nombre de lignes!",
                    'value':False,
                    'ctrlAction':'OnTous',
                    'size':(280,35),
                    'ctrlMaxSize':(250,35),
                    'txtSize': 50,
     },
    ],

# param2 pour periode car interaction avec super (DLG_Mouvements)
("param2", "Periode"): [
    {'name': 'anteDate',
             'genre': 'anyctrl',
             'label': "Après  le",
             'help': "%s\n%s\n%s" % ("Saisie JJMMAA ou JJMMAAAA possible.",
                                     "Les séparateurs ne sont pas obligatoires en saisie.",
                                     "Saisissez la date de l'entrée en stock sans séparateurs, "),
             'ctrl': xdates.CTRL_SaisieDateAnnuel,
             'value': xformat.DatetimeToStr(datetime.date.today()),
             'ctrlAction': 'OnAnteDate',
             'size': (280, 35),
             'ctrlMaxSize': (370, 40),
             'txtSize': 55},
    {'name': 'endDate',
            'genre': 'anyctrl',
            'label': "Jusqu'au",
            'help': "%s\n%s\n%s"%("Saisie JJMMAA ou JJMMAAAA possible.",
                                  "Les séparateurs ne sont pas obligatoires en saisie.",
                                  "Saisissez la date de l'inventaire, "),
            'ctrl': xdates.CTRL_SaisieDateAnnuel,
            'value':xformat.DatetimeToStr(datetime.date.today()),
            'ctrlAction': 'OnLastDate',
            'size':(280,35),
            'ctrlMaxSize': (370, 40),
            'txtSize': 55,},
],

("param3", "Origine"): [
    {'name': 'origine', 'genre': 'Choice', 'label': "Mouvements",
                    'help': "Le choix de la nature filtrera les lignes sur une valeur",
                    'value':0, 'values':[],
                    'ctrlAction': 'OnOrigine',
                    'ctrlMaxSize':(350,35),
                    'txtSize': 120},
    {'name': '', 'genre': None,}
    ],
}

HELP_CALCULS = "de tous les mouvements ou seulement des codhés"

MATRICE_CALCULS = {
("param_calcVide", ""): [],
("param_calc0", "Prix"): [
    {'name': 'pxAchatsStock', 'genre': 'anyctrl', 'label': 'Px achats en StockFin',
                     'txtSize': 140,
                     'ctrlMaxSize': (250,35),
                     'help': "Prix moyen des achats, %s" % HELP_CALCULS,
                     'ctrl': CTRL_calcul,
     },
    {'name': 'pxMoyenStock', 'genre': 'anyctrl','label': 'PxMoyen calculé',
                    'txtSize': 140,
                    'ctrlMaxSize':(250,35),
                    'help': "Prix moyen des achats qui ont été consommés" ,
                    'ctrl': CTRL_calcul,},
    ],
("param_calc1", "Mouvements"): [
    {'name': 'mttStock', 'genre': 'anyctrl','label': 'Valeur du Stock',
                    'txtSize': 120,
                    'ctrlMaxSize':(240,35),
                    'help': "Valeur du stock au prix de l'article, %s" % HELP_CALCULS,
                    'ctrl': CTRL_calcul,
                     },
    {'name': 'erreur', 'genre': 'anyctrl', 'label': 'Erreur sur sorties',
                     'txtSize': 120,
                     'ctrlMaxSize': (240,35),
                     'help': "Différence entre le total mouvements et la valeur du stock",
                     'ctrl': CTRL_calcul,
     },
    ],
}

INFO_OLV = "txtROUGE: Stock négatif, fondVERT: entrée_od, ROSE: sortie_od, JAUNE: achat"

def GetDicPnlParams(*args):
    matrice = xformat.CopyDic(MATRICE_PARAMS)
    xformat.SetItemInMatrice(matrice,'origine','values', dlgMvts.DICORIGINES['article']['values'])
    xformat.SetItemInMatrice(matrice,'origine','label', dlgMvts.DICORIGINES['article']['label'])
    return {
                'name':"PNL_params",
                'matrice':matrice,
                'lblBox':None,
                'boxesSizes': [(320,60), (250, 65),(250, 30), None],
                'pathdata':"srcNoelite/Data",
                'nomfichier':"stparams",
                'nomgroupe':"article",
            }

def GetDicCalculs(*args):
    matrice = xformat.CopyDic(MATRICE_CALCULS)
    return {
            'name':"PNL_calculs",
            'matrice':matrice,
            'lblBox':None,
            'boxesSizes': [None,(300, 95),(300, 95)],
            }

def ValideParams(*arg,**kwds):
    return True

def GetBoutons(dlg):
    return  [
        {'name': 'btnAjuste', 'label': "Ajustement\nPrix out",
         'help': "Cliquez ici pour Ajuster les prix d'od ou sorties, selon les prix d'achat ou inventaire",
         'size': (120, 35),
         'onBtn': dlg.OnBtnAjuste,
         'image': "xpy/Images/32x32/Actualiser.png"},
        {'name': 'btnCorrections', 'label': "Correction\npar lot",
         'help': "Cliquez ici pour changer la date, la nature... de lignes sélectionnées",
         'size': (120, 35),
         'onBtn': dlg.OnBtnCorrections,
         'image': "xpy/Images/32x32/Depannage.png"},
        {'name': 'btnImp', 'label': "Imprimer\npour contrôle",
            'help': "Cliquez ici pour imprimer et enregistrer la saisie de l'entrée en stock",
            'size': (120, 35), 'image': wx.ART_PRINT,'onBtn':dlg.OnImprimer},
        {'name':'btnOK','ID':wx.ID_ANY,'label':"Quitter",'help':"Cliquez ici pour sortir",
            'size':(120,35),'image':"xpy/Images/32x32/Quitter.png",'onBtn':dlg.OnFermer}
    ]

def GetOlvColonnes(dlg):
    # retourne la liste des colonnes de l'écran principal, valueGetter correspond aux champ des tables ou calculs
    titlePrix = "Prix Unit."
    lstCol = [
            ColumnDefn("ID", 'centre', 0, 'IDmouvement',
                       isEditable=False),
            ColumnDefn("Date Mvt", 'left', 80, 'date',valueSetter=datetime.date(1900,1,1),
                       isEditable=True, isSpaceFilling=False,
                       stringConverter=xformat.FmtDate),
            ColumnDefn("Origine", 'left', 50, 'origine',
                                cellEditorCreator=ChoiceEditor,isEditable=True),
            ColumnDefn("Repas", 'left', 40, 'repas', valueSetter="",
                                cellEditorCreator=ChoiceEditor,isEditable=True),
            ColumnDefn("Article", 'left', 200, 'IDarticle', valueSetter="",
                       isSpaceFilling=True, isEditable=True),
            ColumnDefn("Qté", 'right', 50, 'qte', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtQte),
            ColumnDefn(titlePrix, 'right', 60, 'pxUn', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal),
            ColumnDefn("P.ration", 'right', 50, 'pxRation', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal, isEditable=False),
            ColumnDefn("Nbre Rations", 'right', 70, 'nbRations', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal, isEditable=False),
            ColumnDefn("Mtt TTC", 'right', 70, 'mttTTC', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal, isEditable=False),
            ColumnDefn("Stock Mtt", 'right', 70, 'cumMtt', isSpaceFilling=False, valueSetter=0.0,
                       stringConverter=xformat.FmtDecimal, isEditable=False),
            ColumnDefn("Stock Qté", 'right', 70, 'cumQte', isSpaceFilling=False, valueSetter=0.0,
                       stringConverter=xformat.FmtDecimal, isEditable=False),
            ColumnDefn("MoyPU", 'right', 55, 'cumPu', isSpaceFilling=False, valueSetter=0.0,
                       stringConverter=xformat.FmtDecimal, isEditable=False),
            ColumnDefn("Fournisseur", 'left', 80, 'fournisseur', valueSetter="",
                       isEditable=True),
            ColumnDefn("Saisie", 'left', 80, 'dateSaisie', isSpaceFilling=False,
                       stringConverter=xformat.FmtDate, isEditable=False),
            ColumnDefn("Ordi", 'left', 120, 'ordi', valueSetter="",isSpaceFilling=False,
                       isEditable=False)
            ]
    return lstCol

def RowFormatter(listItem, track):
    if not track.qte:
        track.qte = 0.0
    if not track.cumQte:
        track.cumQte = 0.0
    listItem.SetBackgroundColour(wx.Colour(255, 255, 255))
    listItem.SetTextColour(wx.Colour(0, 0, 0))
    if track.origine in ('inventaire', 'achat'):
        # achats en fond jaune
        listItem.SetBackgroundColour(wx.Colour(255, 245, 160))
    if track.origine in ('od_in', 'od_out') and track.qte > 0:
        # entrées autres en fond vert
        listItem.SetBackgroundColour(wx.Colour(200, 230, 130))
    if track.origine in ('od_in', 'od_out') and track.qte < 0:
        # sorties autres en fond rose
        listItem.SetBackgroundColour(wx.Colour(255, 230, 225))
    if track.cumQte < 0:
        # stock négatif sur cette ligne
        listItem.SetTextColour(wx.RED)

def MAJ_calculs(dlg):
    # calcul des zones totaux en bas d'écran, cumuls progressifs rafraîchis
    ctrlOlv = dlg.ctrlOlv
    lstChecked = ctrlOlv.GetCheckedObjects()
    if len(lstChecked) == 0:
        lstChecked = ctrlOlv.innerList
    lstChecked = [ x for x in lstChecked if x.dicMvt]

    # lecture des lignes
    mttMvts, qteMvts = 0.0, 0.0
    mttStock = 0.0
    cumQte = 0.0
    cumMtt = 0.0
    for track in lstChecked:
        cumQte += track.qte
        if not track.pxUn:
            pass
        cumMtt += track.qte * track.pxUn
        track.cumQte = cumQte
        track.cumMtt = cumMtt
        if cumQte != 0:
            track.cumPu = cumMtt / cumQte
        else: track.cumPu = 0.0
        qteMvts += track.qte
        mttMvts += track.qte * track.pxUn

    # calcul prix d'achat moyen pour stock
    pxAchatsStock = nust.PxAchatsStock(lstChecked)
    if not pxAchatsStock:
        pxAchatsStock = 0
    pxMoyenStock = 0.0
    if qteMvts != 0:
        pxMoyenStock = mttMvts / qteMvts

    erreur = (Nz(pxAchatsStock) * Nz(qteMvts)) - Nz(mttMvts)

    mttStock = cumQte * pxAchatsStock

    # Inscription dans l'écran
    if pxAchatsStock != 0:
        dlg.pnlCalculs.GetPnlCtrl('mttStock').SetValue(mttStock)
        dlg.pnlCalculs.GetPnlCtrl('pxAchatsStock').SetValue(pxAchatsStock)
    else: erreur = 0

    dlg.pnlCalculs.GetPnlCtrl('pxMoyenStock').SetValue(pxMoyenStock)

    # gestion de la couleur de l'erreur
    if abs(erreur) <= 0.01:
        bgCouleur = wx.Colour(220, 237, 200)  # vert null
        fgCouleur = wx.Colour(553,90,11) # vert sombre
    elif abs(erreur) < 1:
        bgCouleur = wx.Colour(220, 237, 200)  # vert null
        fgCouleur = wx.BLUE
    elif abs(erreur) < 5:
        bgCouleur = wx.Colour(255, 205, 210)  # Rouge positif
        fgCouleur = wx.RED
    else:
        bgCouleur = wx.Colour(255, 61, 0)
        fgCouleur = wx.BLACK

    # force la couleur unique déterminée ci dessus
    dlg.pnlCalculs.GetPnlCtrl('erreur').ctrl.bgCouleurs = [bgCouleur,] * 3
    dlg.pnlCalculs.GetPnlCtrl('erreur').ctrl.ctrl_solde.SetForegroundColour(fgCouleur)
    dlg.pnlCalculs.GetPnlCtrl('erreur').SetValue(erreur)

def CalculeLigne(dlg, track):
    for attr in ['qte','pxUn','pxRation','nbRations']:
        value = getattr(track, attr)
        if value == None:
            setattr(track, attr, Nz(value))
    # après chaque saisie d'une valeur on recalcule les champs dépendants
    if not hasattr(track, 'dicArticle') or not track.dicArticle:
        return
    try:
        qte = float(track.qte)
    except:
        qte = 0.0
    try:
        rations = track.dicArticle['rations']
    except:
        rations = 1

    try: pxUn = float(track.pxUn)
    except: pxUn = 0.0

    txTva = track.dicArticle['txTva']
    track.mttTTC = dlgMvts.PxUnToTTC(dlg.ht_ttc,txTva) * pxUn * qte
    track.prixTTC = round(dlgMvts.PxUnToTTC(dlg.ht_ttc,txTva) * pxUn,6)
    #track.qteStock = track.dicArticle['qteStock']
    lstCodesColonnes = dlg.ctrlOlv.lstCodesColonnes
    track.nbRations = qte * rations
    if track.nbRations >0:
        track.pxRation = track.mttTTC / track.nbRations
    else: track.pxRation = 0.0
    for ix in range(len(lstCodesColonnes)):
        codecol = lstCodesColonnes[ix]
        if len(codecol) > 0:
            track.donnees[ix] = eval("track.%s"%codecol)
        else: track.donnees[ix] = None

def ValideLigne(dlg, track):
    # validation de la ligne de mouvement
    track.valide = True
    track.messageRefus = "Saisie incomplète\n\n"
    CalculeLigne(dlg, track)

    # Repas non renseigné
    if dlg.sens == 'sorties' and track.repas in (None, 0, ''):
        track.messageRefus += "Le repas pour imputer la sortie n'est pas saisi\n"

    # date hors plage
    if track.date in (None, 0, ''):
        track.messageRefus += "La date n'est pas saisie\n"
    elif track.date < dlg.anteDate or track.date > dlg.endDate:
        track.messageRefus += "La date est hors de la plage de date en cours\n"

    # article manquant
    if track.IDarticle in (None, 0, ''):
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

    # modif bloquée selon nature
    if track.origine in ('achat', 'inventaire'):
        mess = None
        if track.origine == 'inventaire':
            mess = "La modification de l'inventaire est impossible ici\n"
            track.messageRefus = "Modification inventaire non autorisée"
        if track.origine == 'achat':
            mess = "Modif des achats = Distorsion possible avec un montant comptable\n"
            mess += "Vérifiez la nature de cette ligne et son origine\n"
        if mess:
            wx.MessageBox(mess,"Info",style=wx.ICON_INFORMATION)
    # envoi de l'erreur
    if track.messageRefus != "Saisie incomplète\n\n":
        track.valide = False
    else:
        track.messageRefus = ""

def ComposeDonnees(db,dlg,ldMouvements):
    # retourne la liste des données de l'OLv
    ctrlOlv = dlg.ctrlOlv

    # liste des articles contenus dans les lignes (un ou tous)
    lstArticles = [x['IDarticle'] for x in ldMouvements]
    ddArticles = nust.SqlDicArticles(dlg.db, dlg.ctrlOlv,lstArticles)

    # composition des données
    lstDonnees = []
    lstCodesCol = ctrlOlv.GetLstCodesColonnes()

    # Enrichissement des lignes pour olv à partir des mouvements remontés
    cumQte = 0.0
    cumMtt = 0.0
    for dMvt in ldMouvements:
        donnees = []
        dArticle = ddArticles[dMvt['IDarticle']]
        # alimente les données des colonnes
        for code in lstCodesCol:
            # ajout de la donnée dans le mouvement
            if code == 'pxUn':
                donnees.append(dMvt['prixUnit'])
            elif code == 'mttTTC':
                donnees.append(round(dMvt['prixUnit'] * dMvt['qte'],2))
            elif code == 'cumMtt':
                cumMtt += dMvt['prixUnit'] * dMvt['qte']
                donnees.append(cumMtt)
            elif code == 'cumQte':
                cumQte += dMvt['qte']
                donnees.append(cumQte)
            #elif code == 'pxMoyen':
            #    donnees.append(dArticle['prixMoyen'])
            elif code in dMvt:
                donnees.append(dMvt[code])
            elif code in dArticle:
                donnees.append(dArticle)
            else:
                donnees.append(None)
        # codes supplémentaires de track non affichés
        donnees += [dArticle, dMvt,dMvt['modifiable']]
        lstDonnees.append(donnees)
    return lstDonnees

class PNL_calculs(xusp.TopBoxPanel):
    def __init__(self, parent, *args, **kwds):
        kwdsTopBox = {}
        kwds = GetDicCalculs(parent)
        for key in xusp.OPTIONS_TOPBOX:
            if key in kwds: kwdsTopBox[key] = kwds[key]
        super().__init__(parent, *args, **kwdsTopBox)
        self.parent = parent

class DLG(dlgMvts.DLG):
    # ------------------- Composition de l'écran de gestion-----------------------------
    def __init__(self, **kwd):
        # récupération d'un code transmis par un éventuel parent'
        self.article = kwd.pop('article',None)

        listArbo=os.path.abspath(__file__).split("\\")
        self.GetDicPnlParams = GetDicPnlParams

        self.sens = 'article'
        dicOlv = {}
        dicOlv.update(dlgMvts.GetOlvOptions(self))
        dicOlv['lstColonnes'] = GetOlvColonnes(self)
        dicOlv['lstCodes'] = xformat.GetCodesColonnes(GetOlvColonnes(self))
        dicOlv['lstCodesSup'] = dlgMvts.GetOlvCodesSup()
        dicOlv['checkColonne']= True


        lstInfos = [ wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)),INFO_OLV]
        dicPied = {'lstBtns': GetBoutons(self), "lstInfos": lstInfos}

        # spécificités structure écran à transmettre au super
        kwds = {}
        kwds['name'] = '(%s)DLG'% MODULE
        kwds['sens'] = 'article'
        kwds['title'] = listArbo[-1] + "/" + self.__class__.__name__
        kwds['autoSizer'] = False
        kwds['dicParams'] = GetDicPnlParams(self)
        kwds['dicOlv'] = dicOlv
        kwds['dicPied'] = dicPied
        super().__init__(**kwds)

    def Init(self):
        self.lanceur = self
        self.pnlCalculs = PNL_calculs(self)
        self.lstOrigines = ['tous',]
        today = datetime.date.today()


        # lancement de l'écran en blocs principaux
        self.pnlBandeau = xbandeau.Bandeau(self, dlgMvts.TITRE[self.sens],
                                           dlgMvts.INTRO[self.sens], hauteur=20,
                                           nomImage="xpy/Images/80x80/Validation.png",
                                           sizeImage=(60, 40))
        self.pnlBandeau.SetBackgroundColour(wx.Colour(250, 250, 180))

        self.dicOlv['checkColonne'] = True
        self.pnlOlv.ValideParams = self.ValideParams
        self.pnlOlv.ValideLigne = self.ValideLigne
        self.pnlOlv.CalculeLigne = self.CalculeLigne
        self.ctrlOlv = self.pnlOlv.ctrlOlv

        # charger les valeurs de pnl_params

        self.Bind(wx.EVT_CLOSE,self.OnFermer)
        self.anteDate = nust.GetDateLastInventaire(self.db,today)
        self.endDate = xformat.DateSqlToDatetime(nust.GetDateLastMvt(self.db))
        self.pnlParams.SetOneValue('anteDate',valeur=self.anteDate,
                                   codeBox='param2')
        self.pnlParams.SetOneValue('endDate',valeur=self.endDate,
                                   codeBox='param2')
        if self.article:
            self.pnlParams.SetOneValue('article',self.article,codeBox='param1')
            self.OnArticle()


        # le bind check item met à jour les soustotaux puis cherche MAJ_calculs
        self.ctrlOlv.MAJ_calculs = MAJ_calculs
        self.ctrlOlv.Bind(wx.EVT_LIST_COL_CLICK,self.OnSort)
        self.ctrlOlv.rowFormatter = RowFormatter

    def Sizer(self):
        self.SetSize(1230,750)
        sizer_base = wx.FlexGridSizer(rows=5, cols=1, vgap=0, hgap=0)
        sizer_base.Add(self.pnlBandeau, 0, wx.TOP | wx.EXPAND, 3)
        sizer_base.Add(self.pnlParams, 0, wx.TOP | wx.EXPAND, 3)
        sizer_base.Add(self.pnlOlv, 1, wx.TOP | wx.EXPAND, 3)
        sizer_base.Add(self.pnlCalculs, 1, wx.TOP | wx.EXPAND, 3)
        sizer_base.Add(self.pnlPied, 0, wx.ALL | wx.EXPAND, 3)
        sizer_base.AddGrowableCol(0)
        sizer_base.AddGrowableRow(2)
        self.CenterOnScreen()
        self.SetSizer(sizer_base)
        self.CenterOnScreen()

    # ------------------- Gestion des actions ------------------------------------------

    def InitOlv(self):
        self.ctrlOlv.lstColonnes = GetOlvColonnes(self)
        self.ctrlOlv.lstCodesColonnes = self.ctrlOlv.GetLstCodesColonnes()
        self.ctrlOlv.InitObjectListView()
        self.Refresh()

    def ValideParams(self):
        ValideParams(None,None)

    def ValideLigne(self,parent,track):
        # Relais de l'appel par cellEditor à chaque colonne
        ValideLigne(self,track)
        self.CalculeLigne(self,track)

    def CalculeLigne(self,parent,track):
        # Relais de l'appel par GetDonnnees
        CalculeLigne(self,track)

    def GetParams(self):
        dParams = {'article':self.article,
                   'lstOrigines': self.GetOrigines(),
                   'anteDate': self.anteDate,
                   'endDate': self.endDate,}
        return dParams

    def GetDonnees(self,dParams=None):
        # cas de db.Close() par le super en fin
        if not self.db.connexion.is_connected():
            return []
        if not dParams:
            return
        # forme la grille, puis création d'un premier modelObjects par init
        if dParams == {}:
            dParams = self.GetParams()
        if self.ParamsIdem(self.oldParams,dParams):
            return
        attente = wx.BusyInfo("Recherche des données de l'article", None)
        self.InitOlv()
        # appel des données de l'Olv principal à éditer
        dParams['lstChamps'] = xformat.GetLstChampsTable('stMouvements',DB_schema.DB_TABLES)
        ldMouvements = []
        origines = self.GetOrigines()
        nb = 0
        for origine in dlgMvts.DICORIGINES['entrees']['codes']:
            if origine in origines:
                nb +=1
        if nb == len(dlgMvts.DICORIGINES['entrees']['codes']):
            ldMouvements = [x for x in nust.GetLastInventForMvts(self.db, dParams)]
        ldMouvements += [x for x in nust.GetMvtsByArticles(self.db, dParams)]
        lstDonnees = ComposeDonnees(self.db,self,ldMouvements)
        self.oldParams = copy.deepcopy(dParams)

        ixIDarticle = self.ctrlOlv.lstCodesColonnes.index('IDarticle')
        ixDate = self.ctrlOlv.lstCodesColonnes.index('date')
        ixQte = self.ctrlOlv.lstCodesColonnes.index('qte')
        fnSort = lambda don: (don[ixIDarticle], str(don[ixDate]), -don[ixQte])
        self.ctrlOlv.lstDonnees = sorted(lstDonnees,key=fnSort)
        self.ctrlOlv.MAJ()
        if self.article:
            MAJ_calculs(self)
        del attente

    # -------- gestion des actions évènements sur les ctrl -------------------------------

    def GetOneArticle(self,saisie):
        # recherche d'un article, Désactive cellEdit pour éviter l'écho des double clics
        self.ctrlOlv.cellEditMode = self.ctrlOlv.CELLEDIT_NONE
        article = dlgArt.GetOneIDarticle(self.db, saisie.upper())
        self.ctrlOlv.cellEditMode = self.ctrlOlv.CELLEDIT_DOUBLECLICK #réactive dblClic
        return article

    def GetFournisseur(self):
        # désactiver dans le superClass
        pass

    def GetTva(self):
        # désactiver dans le superClass
        pass

    def OnArticle(self,event=None):
        # éviter la redondance de l'évènement 'Enter'
        if event and event.EventType != wx.EVT_KILL_FOCUS.evtType[0]:
            return
        saisie = self.pnlParams.GetOneValue('article',codeBox='param1')
        if saisie == self.article:
            return
        # vérification de l'existence et choix si nécessaire
        self.article = self.GetOneArticle(saisie.upper())
        if self.article:
            self.pnlParams.SetOneValue('article', self.article, codeBox='param1')
            self.GetDonnees(self.GetParams())

    def OnBtnArticle(self,event):
        # Appel du choix d'un ARTICLE via un écran complet
        # id = DLG_Articles.GetOneIDarticle(db,value,f4=f4)
        self.article = self.GetOneArticle("")
        self.pnlParams.SetOneValue('article',self.article,codeBox='param1')
        if self.article:
            self.GetDonnees(self.GetParams())

    def OnTous(self,event):
        # éviter la redondance de l'évènement 'Check' et kill focus
        if event and event.EventType == wx.EVT_KILL_FOCUS.evtType[0]:
            return
        self.tous = self.pnlParams.GetOneValue('tous', codeBox='param1')
        if self.tous:
            self.article = 'Tous'
            flag = False
        else:
            self.article = ''
            flag = True
        self.pnlParams.SetOneValue('article', self.article, codeBox='param1')
        pnlCtrl = self.pnlParams.GetPnlCtrl('article', codebox='param1')
        # active ou désactive le choix de l'article
        pnlCtrl.txt.Enable(flag)
        pnlCtrl.ctrl.Enable(flag)
        pnlCtrl.btn.Enable(flag)
        if self.tous:
            self.GetDonnees(self.GetParams())

    def OnAnteDate(self, event):
        saisie = self.pnlParams.GetOneValue('anteDate',codeBox='param2')
        saisie = xformat.DateFrToDatetime(xformat.FmtDate(saisie))

        # si non nouvelle valeur saisie, on sort
        if self.anteDate == saisie:
            return

        lastInvent = nust.GetDateLastInventaire(self.db)
        if self.endDate > lastInvent:
            self.endDate = lastInvent
            self.pnlParams.SetOneValue('endDate',self.endDate,'param2')
        if saisie < lastInvent:
            self.ctrlOlv.cellEditMode = self.ctrlOlv.CELLEDIT_NONE
            mess = "Modifications d'écritures impossible\n\n"
            mess += "Un inventaire a été archivé au '%s', "% xformat.FmtDate(lastInvent)
            mess += ", vous pouvez seulement consulter."
            wx.MessageBox(mess,"Information",style = wx.ICON_INFORMATION)
        else:
            self.ctrlOlv.cellEditMode = self.ctrlOlv.CELLEDIT_DOUBLECLICK  # réactive dblClic
        if self.anteDate != saisie:
            self.anteDate = saisie
            self.GetDonnees(self.GetParams())

    def OnLastDate(self,event):
        saisie = self.pnlParams.GetOneValue('endDate',codeBox='param2')
        saisie = xformat.DateFrToDatetime(xformat.FmtDate(saisie))
        # si non nouvelle valeur saisie, on sort
        if self.endDate == saisie:
            return
        if self.endDate != saisie:
            self.endDate = saisie
            self.GetDonnees(self.GetParams())

    def OnOrigine(self,event):
        self.lstOrigines = self.GetOrigines()

        lblOrigine = self.pnlParams.GetOneValue('origine')
        if lblOrigine != dlgMvts.DICORIGINES['article']['values'][0]:

            self.ctrlOlv.rowFormatter = lambda x,y: None
        else:
            self.ctrlOlv.rowFormatter = RowFormatter

        if self.article:
            self.GetDonnees(self.GetParams())
        if event:
            event.Skip()

    def OnSort(self,event):
        event.Skip()
        MAJ_calculs(self)

    def OnBtnAjuste(self,event):
        # recalcule et modifie les prix unitaires en sorties de l'article selon FIFO
        if self.ctrlOlv.cellEditMode == self.ctrlOlv.CELLEDIT_NONE:
            mess = "Modifications impossibles\n\n"
            mess += "Les lignes ne sont pas éditables, cf plage de dates"
            wx.MessageBox(mess,"Bloquant",wx.ICON_STOP)
            return
        cumQte = 0.0
        cumMtt = 0.0
        cumQteAch = 0.0
        cumMttAch = 0.0
        cumQteEnt = 0.0
        cumCorr = 0.0
        lstAjuster = []
        dAchats =  {}
        lstIDachats = []
        lstIDtracks = []
        self.nbPxMoyAchSortis = 0

        fnSort = lambda trk: (trk.IDarticle, trk.date, -trk.qte)
        modelObjects = sorted([x for x in self.ctrlOlv.GetObjects() if x.qte not in (0,None)],
                              key=fnSort)
        majorerAchats = 0.0

        # Création d'un récap historique d'achats et odIn
        for track in modelObjects:
            lstIDtracks.append(track.IDmouvement)
            cumQte += track.qte
            cumMtt += track.qte * track.pxUn
            if track.origine not in ('achat', 'inventaire','od_in'):
                continue

            # pour les od_in on ne garde que les vraies entrées.
            if track.origine in ('od_in') and track.qte < 0:
                continue

            if track.origine in ('achat','inventaire'):
                cumQteAch += track.qte
                cumMttAch += track.qte * track.pxUn
            else:
                cumQteEnt += track.qte

            # cas normal d'une entrée correcte, ajoute cet achat à l'historique
            if track.qte > 0:
                lstIDachats.append(track.IDmouvement)
                dAch = {
                    'IDmouvement': track.IDmouvement,
                    'date': track.date,
                    'origine': track.origine,
                    'qte': track.qte,
                    'sortis': 0,
                    'pxUn': track.pxUn}
                dAchats[track.IDmouvement] = dAch

            # cas d'un achat correctif, va déduire les précédents
            if track.qte < 0:
                qte = -track.qte
                dAch = dAchats[lstIDachats[-1]]
                nbcorr = min(qte, dAch['qte'])
                # boucle en remontant les achats précédents
                while qte > 0 and len(lstIDachats) > 0:
                    # si le retour d'achat a un prix différent de l'original
                    if abs(dAch['pxUn'] - track.pxUn) > 0.01:
                        # imputera le différentiel ensuite sur tous les achats
                        majorerAchats += (dAch['pxUn'] - track.pxUn) * nbcorr
                    # diminution de la quantité achetée précédement
                    dAch['qte'] -= nbcorr
                    qte -= nbcorr

                    # suppression  de l'entrée précédente si vidée
                    if dAch['qte'] == 0:
                        del dAchats[lstIDachats[-1]]
                        del lstIDachats[-1]
                        # pour le while
                        dAch = dAchats[lstIDachats[-1]]
                        nbcorr = min(qte, dAch['qte'])

                # Il y avait moins d'achats positifs que de négatifs
                if qte > 0:
                    majorerAchats += qte * track.pxUn

        # calcul du prix moyen achat et sortir des achats sortis, les qtes tjrs en stock
        mttStock = 0.0
        pxMoyStock = None
        qteStock = cumQte # le cumQte est le nb en stock final (renommé pour facilité)
        if cumQte > 0:
            qte = cumQte
            while qte > 0:
                for IDmouvement in sorted(lstIDachats,reverse=True):
                    if dAchats[IDmouvement]['origine'] not in ('achat','inventaire'):
                        continue
                    dAch = dAchats[IDmouvement]
                    nbcorr = min(qte, dAch['qte'])
                    dAch['sortis'] += nbcorr
                    mttStock += nbcorr * dAch['pxUn']
                    qte -= nbcorr
            pxMoyStock = mttStock / cumQte

        # Détermine le prix moyen des achats sortis pour appliquer aux od
        if  not pxMoyStock:
            pxMoyAchSortis = round(cumMttAch / cumQteAch,4)
        elif (cumQteAch - qteStock) > 0:
            pxMoyAchSortis = (cumMttAch -  pxMoyStock * qteStock) /(cumQteAch - qteStock)
        elif cumQteAch > 0:
            pxMoyAchSortis = round(cumMttAch / cumQteAch, 2)
        else:
            mess = "%d en stock à l'arrivée, %d achaté ou report!\n\n"%(qteStock,cumQteAch)
            mess +="Habituellement ce sont les pains et les poissons qui se multiplient..."
            wx.MessageBox(mess,"calcul impossible")
            return

        # synthèse l'info sur le total des achats
        sumQteAch = 0
        sumMttAch = 0.0
        for ID in lstIDachats:
            sumQteAch += dAchats[ID]['qte']
            sumMttAch += dAchats[ID]['qte'] * dAchats[ID]['pxUn']
        if sumQteAch == 0:
            mess = "Aucun achat trouvé avec qté >0"
            wx.MessageBox(mess, "anomalie", style=wx.OK)
            return

        # lissage du prix des ODin par le prix moyen achat
        for IDmouvement, dAch in dAchats.items():
            if dAch['origine'] in ('achat','inventaire'):
                continue
            if abs(dAch['pxUn'] - pxMoyAchSortis) > 0.01:
                track = modelObjects[lstIDtracks.index(IDmouvement)]
                track.pxUn = pxMoyAchSortis
                lstAjuster.append(track)
            dAch['pxUn'] = pxMoyAchSortis

        # Imputation des pertes valeur sur les retours d'achats à prix différent
        if round(majorerAchats,1) != 0.0:
            sumMttAch += majorerAchats
            # différentiel entrées - sorties à imputer
            if sumQteAch > 0:
                corrPu = majorerAchats / sumQteAch
                for ID in lstIDachats:
                    dAchats[ID]['pxUn'] += corrPu

        # fonction qui sort du stock en FIFO,
        def pxUnFirstIn(qteSortie):
            qteAch = 0
            mttAch =0.0
            for id in lstIDachats:
                dAch = dAchats[id]
                dispo = dAch['qte'] - dAch['sortis']
                if dispo < 1:
                    continue
                qteSort = min(qteSortie,dispo)
                dAch['sortis'] += qteSort
                qteAch += qteSort
                mttAch += qteSort * dAch['pxUn']
                qteSortie -= qteSort
                if qteSortie < 1:
                    break
            if qteSortie == 0:
                return round(mttAch / qteAch, 4)
            else:
                self.nbPxMoyAchSortis += (qteSortie - qteAch)
                return pxMoyAchSortis

        # Fonction qui rentre un retour en sotock
        def pxUnRetour(qteEntree):
            mttRet = 0.0
            qteRet = 0
            if self.nbPxMoyAchSortis > 0:
                nbcorr = min(qteEntree,self.nbPxMoyAchSortis)
                self.nbPxMoyAchSortis -= nbcorr
                qteEntree -= nbcorr
            if qteEntree == 0:
                return pxMoyAchSortis
            # on rerentre des stocks sortis
            for id in  sorted(lstIDachats,reverse=True):
                nbRet = min(qteEntree, dAchats[id]['sortis'])
                qteEntree -= nbRet
                dAchats[id]['sortis'] -= nbRet
                qteRet += nbRet
                mttRet += (nbRet * dAchats[id]['pxUn'])
                if qteEntree == 0:
                    break
            if qteRet != 0:
                pxRet = round(mttRet / qteRet, 4)
            else:
                # cas à gérer
                pxRet = round(mttRet / qteRet, 4)
            return pxRet

        # traitement des lignes de l'article qui impute les achats sur les sorties
        for track in modelObjects:
            if track.origine in ('inventaire','achat'):
                continue
            if track.qte > 0:
                continue
            if not track.qte or track.qte == 0:
                continue

            oldPU = track.pxUn

            # cas d'une sortie ou od nég, on ajuste selon Fifo ou pxMoyen
            if track.qte < 0:
                track.pxUn = pxUnFirstIn(-track.qte)
            # cas d'une entrée non achat
            else:
                track.pxUn = pxUnRetour(track.qte)

            if track.IDmouvement > 0 and abs(oldPU - track.pxUn) > 0.0001:
                # on ne sauvegardera que les modifs déjà enregisrées
                lstAjuster.append(track)
            cumQte += track.qte
            cumMtt += track.qte * track.pxUn
            cumCorr += track.qte * (track.pxUn-oldPU)

        # actualiser l'écran
        MAJ_calculs(self)
        self.Refresh()

        # mise à jour par SQL
        if lstAjuster != []:
            values = []
            for track in lstAjuster:
                ordi = track.ordi
                if ordi[:5] != 'ajust':
                    ordi = 'ajust %s' % ordi
                ordi = ordi[:16]
                info = [ordi, datetime.date.today()]
                val = [track.IDmouvement,track.pxUn,] + info
                values.append(val)
            champs = ['IDmouvement','prixUnit','ordi','dateSaisie']
            nust.MajMouvements(champs, values)

#------------------------ Lanceur de test  -------------------------------------------

if __name__ == '__main__':
    app = wx.App(0)
    os.chdir("..")
    dlg = DLG(article="ail surgele")
    dlg.ShowModal()
    app.MainLoop()
