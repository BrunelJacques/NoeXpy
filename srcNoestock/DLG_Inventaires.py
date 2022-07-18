#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------
# Application:     NoeStock, gestion des stocks et prix de journée
# Module:          Gestion des inventaires (dérivé de mouvements)
# Auteur:          Jacques BRUNEL 2021-06
# Licence:         Licence GNU GPL
# ------------------------------------------------------------------

# concepts

"""A chaque lancement du programme, un calcul de l'inventaire est lançé, en cumulant les mouvements postérieurs
        à la dernière date d'un inventaire historisé. il met à jour le compteur dans l'article
    Si une correction est apportée elle génère une od mouvement au jour de l'inventaire et coche la ligne.
    en sortie si présence de lignes cochées, l'historisation partielle de l'inventaire est proposée"""

import wx
import os
import datetime
import srcNoestock.UTILS_Stocks        as nust
import xpy.xGestion_TableauEditor      as xgte
import xpy.xGestion_TableauRecherche   as xgtr
import xpy.xUTILS_Identification       as xuid
import xpy.xUTILS_DB                   as xdb
from srcNoestock                import DLG_MvtOneArticle
from srcNoestock                import DLG_Articles
from srcNoelite                 import DB_schema
from xpy.outils.ObjectListView  import ColumnDefn
from xpy.outils                 import xformat,xboutons, xdates

#---------------------- Matrices de paramétres -------------------------------------

DIC_BANDEAU = {'titre': "Suivi et ajustement de l'inventaire",
        'texte': "La saisie dans le tableau modifie la table article, voire crée un mouvement correctif de quantité",
        'hauteur': 20,
        'sizeImage': (60, 60),
        'nomImage':"xpy/Images/80x80/Inventaire.png",
        'bgColor': (220, 250, 220), }

DIC_INFOS = {
        'fournisseur': "Nom du fournisseur à enregistrer dans l'article",
        'magasin': "<F4> Choix d'un magasin",
        'rayon': "<F4> Choix d'un rayon",
        'qteConstat': "L'unité est celle  qui sert au décompte du stock\nQuantité en stock au jour de l'inventaire",
        'pxUn': "Prix dans l'inventaire d'une unité sortie",
         }

INFO_OLV = "<Suppr> <Inser> <Ctrl C> <Ctrl V>"

SAISONS = ['Saison normale', 'Saison haute','Hors saison']

# Choix des params  pour reprise de inventaires antérieurs------------------------------------------------

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
                  'hauteur': 15, 'nomImage': "xpy/Images/32x32/Zoom_plus.png",
                  'bgColor':(220, 250, 220),}

    # Composition de la matrice de l'OLV anterieurs, retourne un dictionnaire

    lstChamps = ['date', 'fournisseur', 'IDanalytique', 'COUNT(IDinventaire)']

    lstNomsColonnes = ['date', 'fournisseur', 'analytique', 'nbLignes']

    lstTypes = [ 'DATE', 'VARCHAR(32)', 'VARCHAR(32)', 'INT']
    lstCodesColonnes = [xformat.NoAccents(x).lower() for x in lstNomsColonnes]
    lstValDefColonnes = xformat.ValeursDefaut(lstNomsColonnes, lstTypes)
    lstLargeurColonnes = [100,180,180,200]
    lstColonnes = xformat.DefColonnes(lstNomsColonnes, lstCodesColonnes, lstValDefColonnes, lstLargeurColonnes)
    return {
        'lstSaisons': dlg.lstSaisons,
        'lstColonnes': lstColonnes,
        'lstChamps': lstChamps,
        'listeNomsColonnes': lstNomsColonnes,
        'listeCodesColonnes': lstCodesColonnes,
        'getDonnees': nust.SqlInvAnte,
        'dicBandeau': dicBandeau,
        'sortColumnIndex': 2,
        'sensTri': False,
        'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
        'size': (650, 400)}

# Description des paramètres de la gestion des inventaires

MATRICE_PARAMS = {
("param1", "Période"): [
    {'name': 'saison', 'genre': 'Choice', 'label': "Couleur saison",
                    'help': "Le choix de la saison détermine la couleur des lignes selon les minimums prévus par article",
                    'value':0, 'values': SAISONS,
                    'ctrlAction': 'OnSaison',
                    'size':(260,30),
                    'ctrlMaxSize': (370, 40),
                    'txtSize': 105},

    {'name': 'date', 'genre': 'anyctrl', 'label': "Date d'inventaire",
                    'help': "%s\n%s\n%s"%("Saisie JJMMAA ou JJMMAAAA possible.",
                                          "Les séparateurs ne sont pas obligatoires en saisie.",
                                          "Saisissez la date de l'inventaire, "),
                    'ctrl': xdates.CTRL_SaisieDateAnnuel,
                    'value':xformat.DatetimeToStr(datetime.date.today()),
                    'ctrlAction': 'OnDate',
                    'size':(280,30),
                    'ctrlMaxSize': (370, 40),
                    'txtSize': 100,},
],

("param2", "Quantités"): [
    {'name': 'qteZero', 'genre': 'Check', 'label': 'Avec quantités à zéro',
                    'help': "La coche fait apparaître les quantité en stock à zéro",
                    'value':True,
                    'ctrlAction':'OnQte',
                    'size':(250,30),
                    'txtSize': 150,},
    {'name': 'qteMini', 'genre': 'Check', 'label': 'Qtés supérieures au mini',
                    'help': "La coche fait apparaître les quantité supérieures au minim de saison",
                    'value':True,
                    'ctrlAction':'OnQte',
                    'size':(250,30),
                    'txtSize': 150,},
],

("param3", ""): [],

("param4", "Historique"): [
    {'name': 'rappel', 'genre': 'anyctrl','label': ' ',
                     'txtSize': 20,
                        'ctrlMaxSize':(150,50),
                     'ctrl': CtrlAnterieur,
                     'ctrlAction': 'OnBtnAnterieur',
                     },
    ],
}

def GetDicParams(dlg):
    return {
                'name':"PNL_params",
                'matrice':MATRICE_PARAMS,
                'dicBandeau':DIC_BANDEAU,
                'lblBox':True,
                'boxesSizes': [(390, 90), (200, 90), None, (160, 90)],
                'pathdata':"srcNoelite/Data",
                'nomfichier':"stparams",
                'nomgroupe':"entrees",
            }

def GetBoutons(dlg):
    return  [
        {'name': 'btnOneArticle', 'label': "Mouvements \narticle",
         'help': "Permet de visualiser les mouvements de l'article sélectionné",
         'size': (150, 35), 'onBtn': dlg.OnOneArticle},

        {'name': 'btnVerif', 'label': "Conserver cet \ninventaire",
            'help': "Confirme et historise les quantités en stock vérifiées ce jour.\nTout cocher et cliquer à l'inventaire de clôture",
            'size': (150, 35),'onBtn':dlg.OnImprimer},
        {'name': 'btnImp', 'label': "Imprimer\nl'inventaire",
            'help': "Cliquez ici pour imprimer et enregistrer la saisie de l'entrée en stock",
            'size': (120, 35), 'image': wx.ART_PRINT,'onBtn':dlg.OnImprimer},
        {'name':'btnOK','ID':wx.ID_ANY,'label':"Quitter",'help':"Cliquez ici pour sortir",
            'size':(120,35),'image':"xpy/Images/32x32/Quitter.png",'onBtn':dlg.OnClose}
    ]

def GetOlvColonnes(dlg):
    # retourne la liste des colonnes de l'écran principal, valueGetter correspond aux champ des tables ou calculs
    lstCol = [
            ColumnDefn("Article", 'left', 200, 'IDarticle', valueSetter=" ",isSpaceFilling=True,
                       isEditable=False),
            ColumnDefn("Fournisseur", 'left', 100, 'fournisseur', valueSetter=" ",isSpaceFilling=True,
                       isEditable=False),
            ColumnDefn("Magasin", 'left', 100, 'magasin', valueSetter=" ",isSpaceFilling=True,
                       isEditable=False),
            ColumnDefn("Rayon", 'left', 100, 'rayon', valueSetter=" ",isSpaceFilling=True,
                       isEditable=False),
            ColumnDefn("Qté stock", 'right', 80, 'qteConstat',  valueSetter=0.0,isSpaceFilling=False,
                                        stringConverter=xformat.FmtDecimal),
            ColumnDefn("Prix Unit Moy", 'right', 85, 'pxUn',  valueSetter=0.0,isSpaceFilling=False,
                                        stringConverter=xformat.FmtDecimal),
            ColumnDefn("Mtt TTC", 'right', 100, 'mttTTC',  valueSetter=0.0,isSpaceFilling=False,
                        isEditable=False, stringConverter=xformat.FmtDecimal, ),
            ColumnDefn("QteMini", 'right', 80, 'qteMini',  valueSetter=0.0,isSpaceFilling=False,
                        isEditable=False, stringConverter=xformat.FmtDecimal, ),
            ColumnDefn("Nbre Rations", 'right', 80, 'rations',  valueSetter=0.0,isSpaceFilling=False,
                        isEditable=False, stringConverter=xformat.FmtDecimal, ),
            ColumnDefn("Maj Prix", 'left', 80, 'lastBuy', valueSetter=datetime.date.today(),isSpaceFilling=False,
                        isEditable=False, stringConverter=xformat.FmtDate,),
            ColumnDefn("Prix Actuel", 'left', 40, 'prixActuel', valueSetter= 0.0,isSpaceFilling=False,
                        isEditable=False, stringConverter=xformat.FmtDecimal),
            ]
    return lstCol

def GetOlvCodesSup():
    # codes dans les données olv, mais pas dans les colonnes, attributs des tracks non visibles en tableau
    return ['qteMvts','qteAchats','mttAchats',
            'artRations']

def GetOlvOptions(dlg):
    # Options paramètres de l'OLV ds PNLcorps
    return {
        'recherche': True,
        'autoAddRow': False,
        'toutCocher':True,
        'toutDecocher':True,
        'msgIfEmpty': "Aucun article présent (avec les options ci dessus)",
        'dictColFooter': {"magasin": {"mode": "nombre", "alignement": wx.ALIGN_CENTER},
                        "qteStock": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                        "mttTTC": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                        "rations": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                          },
    }

def GetDlgOptions(dlg):
    # Options du Dlg de lancement
    return {
        'minSize': (700, 450),
        'size': (1150, 800),
        'autoSizer': False
        }

    #----------------------- Parties de l'écrans -----------------------------------------

def GetAnterieur(dlg,db=None):
    # retourne un dict de params après lancement d'un tableau de choix de l'existants pour reprise
    dParams = {}
    dicOlv = GetMatriceAnterieurs(dlg)
    dlg = xgtr.DLG_tableau(dlg, dicOlv=dicOlv, db=db)
    ret = dlg.ShowModal()
    if ret == wx.OK and dlg.GetSelection():
        donnees = dlg.GetSelection().donnees
        for ix in range(len(donnees)):
            dParams[dicOlv['listeCodesColonnes'][ix]] = donnees[ix]
    dlg.Destroy()
    return dParams

def CalculeLigne(dlg,track):
    try: qte = float(track.qteConstat)
    except: qte = 0.0
    try: pu = float(track.pxUn)
    except: pu = 0.0
    track.mttTTC = qte * pu
    track.rations = qte * track.artRations
    track.valide = dlg.date
    deltaQte =  qte - track.qteMvts
    track.deltaQte = deltaQte

def ValideLigne(dlg,track):

    CalculeLigne(dlg,track)

    # validation de la ligne de inventaire
    track.valide = True
    track.messageRefus = "Saisie incorrecte\n\n"

    # qte négative
    try:
        track.qteConstat = float(track.qteConstat)
    except:
        track.qteConstat = 0.0
    if track.qteConstat < 0.0:
        track.messageRefus += "La quantité ne peut être négative\n"

    # pxUn null
    try:
        track.pxUn = float(track.pxUn)
    except:
        track.pxUn = None
    if not track.pxUn or track.pxUn == 0.0:
        track.messageRefus += "Le pxUnitaire est à zéro\n"

    # envoi de l'erreur
    if track.messageRefus != "Saisie incorrecte\n\n":
        track.valide = False
    else: track.messageRefus = ""
    return

def RowFormatter(listItem, track):
    #if track.IDarticle == "AROME MAGGI BT":
    #    test
    anomalie = None

    pxAct = track.prixActuel
    if track.qteAchats != 0:
        puAchats = round(track.mttAchats/track.qteAchats,6)
    else: puAchats = track.pxUn
    if abs(1 - (track.pxUn / puAchats)) >= 0.10:
        # Prix mouvements diffère de 5% du prix moyen derniers achats
        anomalie = 1
    elif pxAct and pxAct != 0.0 and ((track.pxUn / pxAct) > 5 or (track.pxUn / pxAct < 0.2)):
        # ¨Prix mouvements diffère du dernier achat rapport 1 à 5
        anomalie = 2
    elif track.pxUn <= 0:
        # prix Négatif
        anomalie = 3
    if anomalie:
        # anomalie rouge / fushia
        listItem.SetTextColour(wx.RED)
        listItem.SetBackgroundColour(wx.Colour(255, 180, 200))
    elif track.qteConstat < 0 or track.rations > 1000:
        # stock négatif ou plus de 1000 rations: écrit en rouge
        listItem.SetTextColour(wx.RED)
    elif track.qteMini > 0 and track.qteConstat < track.qteMini:
        # niveau de stock  inférieur au minimum saison: fond jaune
        listItem.SetBackgroundColour(wx.Colour(255, 245, 160))
    elif track.qteConstat == 0:
        # stock à zero: fond vert
        listItem.SetBackgroundColour(wx.Colour(220, 237, 200))

class PNL_corps(xgte.PNL_corps):
    #panel olv avec habillage optionnel pour des boutons actions (à droite) des infos (bas gauche) et boutons sorties
    def __init__(self, parent, dicOlv,*args, **kwds):
        xgte.PNL_corps.__init__(self,parent,dicOlv,*args,**kwds)
        self.db = parent.db

    def ValideParams(self):
        return

    def OnCtrlV(self,track):
        # avant de coller une track, raz de certains champs et recalcul
        track.IDinventaire = None
        self.ValideLigne(None,track)
        self.SauveLigne(track)

    def OnDelete(self,track):
        nust.DelInventaire(self.parent.db,self.ctrlOlv,track)

    def OnNewRow(self,row,track):
        pass

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
        if track.qteAchats > 0:
            lstDonnees += [('prixActuel',track.mttAchats / track.qteAchats),
                              ('ordi',self.parent.ordi),
                              ('dateSaisie',self.parent.today)]
        mess = "MAJ article '%s'"%track.IDarticle
        db.ReqMAJ('stArticles',lstDonnees,'IDarticle',track.IDarticle,mess=mess,IDestChaine=True)

    def OnEditFunctionKeys(self,event):
        row, col = self.ctrlOlv.cellBeingEdited
        code = self.ctrlOlv.lstCodesColonnes[col]
        if event.GetKeyCode() == wx.WXK_F4 and code == 'IDarticle':
            # Choix article
            IDarticle = DLG_Articles.GetOneIDarticle(self.db,self.ctrlOlv.GetObjectAt(row).IDarticle,f4=True)
            #self.ctrlOlv.GetObjectAt(row).IDarticle = IDarticle
            if IDarticle:
                ret = self.OnEditFinishing('IDarticle',IDarticle)

class DLG(xgte.DLG_tableau):
    # ------------------- Composition de l'écran de gestion----------
    def __init__(self,date=None,**kwd):
        kwds = GetDlgOptions(self)
        self.dicParams = GetDicParams(self)
        self.dicOlv = {'lstColonnes': GetOlvColonnes(self)}
        self.dicOlv.update({'lstCodesSup': GetOlvCodesSup()})
        self.dicOlv.update(GetOlvOptions(self))
        self.checkColonne = self.dicOlv.get('checkColonne',False)
        self.dicOlv['lstCodes'] = xformat.GetCodesColonnes(GetOlvColonnes(self))
        self.dicOlv['db'] = xdb.DB()
        # boutons de bas d'écran - infos: texte ou objet window.  Les infos sont  placées en bas à gauche
        txtInfo =  "Ici de l'info apparaîtra selon le contexte de la grille de saisie"
        lstInfos = [ wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)),txtInfo]
        dicPied = {'lstBtns': GetBoutons(self), "lstInfos": lstInfos}


        # Propriétés de l'écran global type Dialog
        kwds = GetDlgOptions(self)
        kwds['autoSizer'] = False
        kwds['dicParams'] = GetDicParams(self)
        kwds['dicOlv'] = {}
        kwds['dicPied'] = dicPied
        kwds['db'] = xdb.DB()

        super().__init__(None, **kwds)

        self.ordi = xuid.GetNomOrdi()
        self.today = datetime.date.today()
        if not date:
            date = self.today
        self.date = date
        self.lstSaisons = SAISONS
        ret = self.Init()
        if ret == wx.ID_ABORT: self.Destroy()
        self.Sizer()
        # appel des données
        self.oldParams = None
        (self.qteZero, self.qteMini) = (True, True)
        self.OnSaison(None)

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

    def OnDate(self,event):
        saisie = self.pnlParams.GetOneValue('date',codeBox='param1')
        saisie = xformat.DateFrToDatetime(xformat.FmtDate(saisie))
        if self.date != saisie:
            self.date = saisie
            self.GetDonnees()
        if event: event.Skip()

    def OnSaison(self,event):
        self.choixSaison = self.pnlParams.GetOneValue('saison', codeBox='param1')
        ctrlQteMini = self.pnlParams.GetPnlCtrl('qteMini','param2')
        self.saisonIx = SAISONS.index(self.choixSaison)
        if self.saisonIx == 2:
            ctrlQteMini.Enable(False)
            ctrlQteMini.SetValue(True)
        else:
            ctrlQteMini.Enable(True)
        self.GetDonnees()
        if event: event.Skip()

    def OnQte(self,event):
        self.qteZero = self.pnlParams.GetOneValue('qteZero', codeBox='param2')
        self.qteMini = self.pnlParams.GetOneValue('qteMini', codeBox='param2')
        self.GetDonnees()
        if event: event.Skip()

    def OnBtnAnterieur(self,event):
        # lancement de la recherche d'un lot antérieur, on enlève le cellEdit pour éviter l'écho des clics
        self.ctrlOlv.cellEditMode = self.ctrlOlv.CELLEDIT_NONE
        # choix d'un lot de lignes définies par des params
        dParams = GetAnterieur(self,db=self.db)
        self.ctrlOlv.cellEditMode = self.ctrlOlv.CELLEDIT_DOUBLECLICK        # gestion du retour du choix dépot
        if not 'date' in dParams.keys(): return
        self.GetDonnees(dParams)
        if event: event.Skip()

    def GetDonnees(self,dParams=None):
        if not dParams:
            dParams = self.pnlParams.GetValues(fmtDD=False)
        idem = True
        if self.oldParams == None :
            idem = False
        else:
            for key in ('origine','date','analytique','fournisseur'):
                if not key in self.oldParams.keys(): idem = False
                elif not key in dParams.keys(): idem = False
                elif self.oldParams[key] != dParams[key]: idem = False
        if idem : return

        # appel des données de l'Olv principal à éditer
        ixQte = self.dicOlv['lstCodes'].index('qteConstat')
        ixMini = self.dicOlv['lstCodes'].index('qteMini')
        def filtreQte(lDonnees):
            if not self.qteZero and lDonnees[ixQte] == 0.0:
                return False
            if (not self.qteMini) and lDonnees[ixMini]:
                if lDonnees[ixQte] >= lDonnees[ixMini]:
                    return False
            return True


        lstDonnees = [x for x in nust.CalculeInventaire(self) if filtreQte(x)]

        self.mouvementsPost = nust.MouvementsPosterieurs(self)
        if self.mouvementsPost:
            self.pnlPied.SetItemsInfos("Présence de mouvements postérieurs\nLe stock dans l'article n'est pas mis à jour",
                                       wx.ArtProvider.GetBitmap(wx.ART_ERROR, wx.ART_OTHER, (16, 16)))

        # l'appel des données peut avoir retourné d'autres paramètres, il faut mettre à jour l'écran
        if len(lstDonnees) > 0:
            # set date du lot importé
            self.pnlParams.SetOneValue('date',xformat.DateSqlToDatetime(dParams['date']),'param1')
            self.date = dParams['date']

        # alimente la grille, puis création de modelObejects pr init
        self.ctrlOlv.lstDonnees = lstDonnees
        self.ctrlOlv.MAJ()
        # les écritures reprises sont censées être valides
        for track in self.ctrlOlv.modelObjects[:-1]:
            track.IDmouvement = None
        self.oldParams = None

    def GetTitreImpression(self):
        date = xformat.DateSqlToFr(self.date)
        mini = 'Sans'
        if self.qteMini: mini = 'Avec'
        zer = 'Sans'
        if self.qteZero: zer = 'Avec'
        return "Inventaire STOCKS du %s, Qtés à zéro: %s, Qtés au dessus du minimum: %s"%(date, zer, mini)

    def OnOneArticle(self,event):
        selection = self.ctrlOlv.GetSelectedObject()
        if not selection:
            wx.MessageBox("Veuillez sélectionner un article...","pas de sélection",
                          style= wx.ICON_INFORMATION)
            return
        dlg = DLG_MvtOneArticle.DLG(article=selection.IDarticle)
        dlg.ShowModal()
        #self.GetDonnees()

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
