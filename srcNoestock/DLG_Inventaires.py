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
        'qteStock': "L'unité est celle  qui sert au décompte du stock\nQuantité en stock au jour de l'inventaire",
        'pxUnit': "Prix dans l'inventaire d'une unité sortie",
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

    lstChamps = ['origine', 'date', 'fournisseur', 'IDanalytique', 'COUNT(IDinventaire)']

    lstNomsColonnes = ['origine', 'date', 'fournisseur', 'analytique', 'nbLignes']

    lstTypes = ['VARCHAR(8)', 'DATE', 'VARCHAR(32)', 'VARCHAR(32)', 'INT']
    lstCodesColonnes = [xformat.NoAccents(x).lower() for x in lstNomsColonnes]
    lstValDefColonnes = xformat.ValeursDefaut(lstNomsColonnes, lstTypes)
    lstLargeurColonnes = [100,100,180,180,200]
    lstColonnes = xformat.DefColonnes(lstNomsColonnes, lstCodesColonnes, lstValDefColonnes, lstLargeurColonnes)
    return {
        'lstSaisons': dlg.lstSaisons,
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

# Description des paramètres de la gestion des inventaires

MATRICE_PARAMS = {
("param1", "Période"): [
    {'name': 'saison', 'genre': 'Choice', 'label': "Couleur saison",
                    'help': "Le choix de la saison détermine la couleur des lignes selon les minimums prévus par article",
                    'value':0, 'values': SAISONS,
                    'ctrlAction': 'OnSaison',
                    'size':(120,30),
                    'ctrlMaxSize': (260, 40),
                    'txtSize': 110},

    {'name': 'date', 'genre': 'anyctrl', 'label': "Date d'inventaire",
                    'help': "%s\n%s\n%s"%("Saisie JJMMAA ou JJMMAAAA possible.",
                                          "Les séparateurs ne sont pas obligatoires en saisie.",
                                          "Saisissez la date de l'inventaire, "),
                    'ctrl': xdates.CTRL_SaisieDateAnnuel,
                    'value':xformat.DatetimeToStr(datetime.date.today()),
                    'ctrlAction': 'OnDate',
                    'size':(150,30),
                    'ctrlMaxSize': (270, 40),
                    'txtSize': 105,},
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
                'boxesSizes': [(290, 90), (200, 90), None, (160, 90)],
                'pathdata':"srcNoelite/Data",
                'nomfichier':"stparams",
                'nomgroupe':"entrees",
            }

def GetBoutons(dlg):
    return  [
                {'name': 'btnVerif', 'label': "Confirmer les qtés\ndes lignes cochées",
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
            ColumnDefn("Fournisseur", 'left', 100, 'fournisseur', valueSetter=" ",isSpaceFilling=True),
            ColumnDefn("Magasin", 'left', 100, 'magasin', valueSetter=" ",isSpaceFilling=True),
            ColumnDefn("Rayon", 'left', 100, 'rayon', valueSetter=" ",isSpaceFilling=True),
            ColumnDefn("Qté stock", 'right', 80, 'qteStock',  valueSetter=0.0,isSpaceFilling=False,
                                        stringConverter=xformat.FmtDecimal),
            ColumnDefn("Prix Unit", 'right', 80, 'pxUn',  valueSetter=0.0,isSpaceFilling=False,
                                        stringConverter=xformat.FmtDecimal),
            ColumnDefn("Mtt TTC", 'right', 100, 'mttTTC',  valueSetter=0.0,isSpaceFilling=False,
                            isEditable=False, stringConverter=xformat.FmtDecimal, ),
            ColumnDefn("Vérifié le", 'left', 80, 'IDdate', valueSetter=datetime.date.today(),isSpaceFilling=False,
                            isEditable=False, stringConverter=xformat.FmtDate,),
            ColumnDefn("Nbre Rations", 'right', 80, 'rations',  valueSetter=0.0,isSpaceFilling=False,
                            isEditable=False, stringConverter=xformat.FmtDecimal, ),
            ]
    return lstCol

def GetOlvCodesSup():
    # codes dans les données olv, mais pas dans les colonnes, attributs des tracks non visibles en tableau
    return ['qteConstat','qteMvt','mttMvt','qteInv', 'pxMoyInv','pxActInv','qteArt','qteMini','qteSaison','pxMoyArt']

def GetOlvOptions(dlg):
    # Options paramètres de l'OLV ds PNLcorps
    return {
        'checkColonne': True,
        'recherche': True,
        'autoAddRow': False,
        'toutCocher':True,
        'toutDecocher':True,
        'msgIfEmpty': "Aucun article présent (avec les options ci dessus)",
        'minSize': (600, 300),
        'dictColFooter': {"magasin": {"mode": "nombre", "alignement": wx.ALIGN_CENTER},
                        "qteStock": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                        "mttTTC": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                        "rations": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                          },
    }

def GetDlgOptions(dlg):
    # Options du Dlg de lancement
    return {
        'style': wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        'minSize': (700, 450),
        'size': (1150, 800),
        'autoSizer': False,
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
    return

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
    # validation de la ligne de inventaire
    track.valide = True
    track.messageRefus = "Saisie incorrecte\n\n"

    # qte négative
    try:
        track.qte = float(track.qte)
    except:
        track.qte = None
    if not track.qte or track.qte < 0.0:
        track.messageRefus += "La quantité ne peut être négative\n"

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

        # travaux avant saisie

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
        nust.SauveInventaire(self.db,self.Parent,track)

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
        """
        self.flagSkipEdit = False
        self.oldRow = None
        """

    # ------------------- Gestion des actions -----------------------

    def InitOlv(self):
        self.ctrlOlv.lstColonnes = GetOlvColonnes(self)
        self.ctrlOlv.lstCodesColonnes = self.ctrlOlv.GetLstCodesColonnes()
        self.ctrlOlv.InitObjectListView()

    def OnDate(self,event):
        saisie = self.pnlParams.GetOneValue('date',codeBox='param1')
        saisie = xformat.DateFrToDatetime(xformat.FmtDate(saisie))
        if self.date != saisie:
            self.GetDonnees()
            self.date = saisie
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
        lstDonnees = nust.SqlInventaire(self, dParams)

        ixModif = len(DB_schema.DB_TABLES['stArticles'])-1
        lstNoModif = [1 for rec in  lstDonnees if not (rec[-ixModif])]
        # présence de lignes déjà transférées compta
        if len(lstNoModif) >0:
            self.ctrlOlv.cellEditMode = self.ctrlOlv.CELLEDIT_NONE
            self.pnlPied.SetItemsInfos("NON MODIFIABLE: enregistrements transféré ",
                                       wx.ArtProvider.GetBitmap(wx.ART_ERROR, wx.ART_OTHER, (16, 16)))
        # l'appel des données peut avoir retourné d'autres paramètres, il faut mettre à jour l'écran
        if len(lstDonnees) > 0:
            # set date du lot importé
            self.pnlParams.SetOneValue('date',xformat.DateSqlToDatetime(dParams['date']),'param1')
            self.date = dParams['date']

        # alimente la grille, puis création de modelObejects pr init
        self.ctrlOlv.lstDonnees = lstDonnees
        self.ctrlOlv.MAJ()
        # les écritures reprises sont censées être valides, mais il faut les compléter
        for track in self.ctrlOlv.modelObjects[:-1]:
            CalculeLigne(self,track)
            track.valide = True
        self.ctrlOlv._FormatAllRows()
        self.oldParams = None

    def GetTitreImpression(self):
        date = xformat.DateSqlToFr(self.date)
        mini = 'Sans'
        if self.qteMini: mini = 'Avec'
        zer = 'Sans'
        if self.qteZero: zer = 'Avec'
        return "Inventaire STOCKS du %s, Qtés à zéro: %s, Qtés au dessus du minimum: %s"%(date, zer, mini)


    def OnImprimer(self,event):
        self.ctrlOlv.Apercu(None)

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
