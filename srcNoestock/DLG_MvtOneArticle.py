#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------
# Application:     NoeStock, gestion des stocks et prix de journée
# Module:          Saisie des mouvements d'un article
# Auteur:          Jacques BRUNEL 2022-07
# Licence:         Licence GNU GPL
# ------------------------------------------------------------------

import wx
import os
import datetime
import srcNoestock.DLG_Mouvements      as dlgMvts
import srcNoestock.DLG_Articles        as dlgArt
import srcNoestock.UTILS_Stocks        as nust
import xpy.xUTILS_DB                   as xdb
from xpy.outils.xformat                         import Nz
from xpy.outils.ObjectListView.ObjectListView   import ColumnDefn
from xpy.outils.ObjectListView.CellEditor       import ChoiceEditor
from xpy.outils                                 import xformat,xbandeau


MATRICE_PARAMS = {
("param0", "Article"): [
    {'name': 'article', 'genre': 'texte', 'label': 'Article',
                    'help': "Le choix de l'article génère la liste ci-dessous'",
                    'value':0,
                    'ctrlAction':'OnArticle',
                     'btnLabel': "...", 'btnHelp': "Cliquez pour choisir un article",
                     'btnAction': 'OnBtnArticle',
                    'size':(250,28),
                    'ctrlMaxSize':(250,28),
                    'txtSize': 50,
     },
    {'name': 'tous', 'genre': 'check', 'label': 'Tous',
                    'help': "Cochez pour prendre tous les articles, la date 'Après le' détermine le nombre de lignes!",
                    'value':False,
                    'ctrlAction':'OnTous',
                    'size':(250,25),
                    'ctrlMaxSize':(250,25),
                    'txtSize': 50,
     },
    ],
# param2 pour periode car interaction avec super (DLG_Mouvements)
("param2", "Periode"): [
    {'name': 'postDate', 'genre': 'Texte', 'label': "Après le",
                    'help': "%s\n%s\n%s"%("Saisie JJMMAA ou JJMMAAAA possible.",
                                          "Les séparateurs ne sont pas obligatoires en saisie.",
                                          "Saisissez la date de l'entrée en stock sans séparateurs, "),
                    'value':'',
                    'ctrlAction': 'OnPostDate',
                    'ctrlMaxSize':(150,35),
                    'txtSize': 50},
    ],
("param1", "Origine"): [
    {'name': 'origine', 'genre': 'Choice', 'label': "Mouvements",
                    'help': "Le choix de la nature filtrera les lignes sur une valeur",
                    'value':0, 'values':[],
                    'ctrlAction': 'OnOrigine',
                    'ctrlMaxSize':(350,35),
                    'txtSize': 120},
    ],
}

def GetDicParams(*args):
    matrice = xformat.CopyDic(MATRICE_PARAMS)
    xformat.SetItemInMatrice(matrice,'origine','values', dlgMvts.DICORIGINES['article']['values'])
    xformat.SetItemInMatrice(matrice,'origine','label', dlgMvts.DICORIGINES['article']['label'])
    return {
                'name':"PNL_params",
                'matrice':matrice,
                'lblBox':None,
                'boxesSizes': [(300,50), (250, 50),(250, 50), None],
                'pathdata':"srcNoelite/Data",
                'nomfichier':"stparams",
                'nomgroupe':"article",
            }

def ValideParams(*arg,**kwds):
    return True

def ValideLigne(dlg, track):
    # validation de la ligne de mouvement
    track.valide = True
    track.messageRefus = "Saisie incomplète\n\n"
    CalculeLigne(dlg, track)

    # IDmouvement manquant
    if track.IDmouvement in (None, 0):
        track.messageRefus += "L'IDmouvement n'a pas été déterminé\n"

    # Repas non renseigné
    if dlg.sens == 'sorties' and track.repas in (None, 0, ''):
        track.messageRefus += "Le repas pour imputer la sortie n'est pas saisi\n"

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

    # envoi de l'erreur
    if track.messageRefus != "Saisie incomplète\n\n":
        track.valide = False
    else:
        track.messageRefus = ""

    """ret  = wx.MessageBox("Enregistrement de la modification","Confirmez!",style=wx.YES_NO)
    if ret == wx.YES:
        return True
    else: return False"""

def CalculeLigne(dlg, track):
    if not hasattr(track, 'dicArticle'): return
    try:
        qte = float(track.qte)
    except:
        qte = 0.0
    try:
        rations = track.dicArticle['rations']
    except:
        rations = 1
    track.qteStock = track.dicArticle['qteStock'] + (Nz(track.qte))

    try: pxUn = float(track.pxUn)
    except: pxUn = 0.0

    try: rations = track.dicArticle['rations']
    except: rations = 1
    txTva = track.dicArticle['txTva']
    track.mttHT = dlgMvts.PxUnToHT(dlg.ht_ttc,txTva) * pxUn * qte
    track.mttTTC = dlgMvts.PxUnToTTC(dlg.ht_ttc,txTva) * pxUn * qte
    track.prixTTC = round(dlgMvts.PxUnToTTC(dlg.ht_ttc,txTva) * pxUn,6)
    track.qteStock = track.dicArticle['qteStock'] + (Nz(track.qte) * dlg.sensNum)

    if isinstance(track.IDmouvement,int) and track.IDarticle.strip() != '':
        # Le mouvement est déjà comptabilisé dans le stock
        qteStock = dlg.ctrlOlv.buffArticles[track.IDarticle]['qteStock']
        if hasattr(track, 'dicMvt') and track.IDarticle != track.dicMvt['IDarticle']:
            # le mouvement chargé n'est plus celui de l'article
            track.qteStock = qteStock + track.qte * dlg.sensNum
        elif hasattr(track, 'dicMvt'):
            # le mouvement est celui de la ligne
            track.qteStock = qteStock + (track.qte * dlg.sensNum) - track.dicMvt[
                'qte']
        else:
            track.qteStock = qteStock

    lstCodesColonnes = dlg.ctrlOlv.lstCodesColonnes
    track.nbRations = qte * rations
    if track.nbRations > 0:
        track.pxRation = track.prixTTC / track.nbRations
    else:
        track.pxRation = 0.0
    for ix in range(len(lstCodesColonnes)):
        track.donnees[ix] = eval("track.%s" % lstCodesColonnes[ix])

def GetOlvColonnes(dlg):
    # retourne la liste des colonnes de l'écran principal, valueGetter correspond aux champ des tables ou calculs
    titlePrix = "Prix Unit."
    lstCol = [
            ColumnDefn("ID", 'centre', 0, 'IDmouvement',
                       isEditable=False),
            ColumnDefn("Date Mvt", 'left', 80, 'date', isSpaceFilling=False,
                       stringConverter=xformat.FmtDate),
            ColumnDefn("Mouvement", 'left', 80, 'origine',
                                cellEditorCreator=ChoiceEditor),
            ColumnDefn("Repas", 'left', 60, 'repas',
                                cellEditorCreator=ChoiceEditor),
            ColumnDefn("Article", 'left', 200, 'IDarticle', valueSetter="",isSpaceFilling=True),
            ColumnDefn("Quantité", 'right', 80, 'qte', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtQte),
            ColumnDefn(titlePrix, 'right', 80, 'pxUn', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal),
            ColumnDefn("Coût Ration", 'right', 80, 'pxRation', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal, isEditable=False),
            ColumnDefn("Nbre Rations", 'right', 80, 'nbRations', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal, isEditable=False),
            ColumnDefn("Mtt TTC", 'right', 80, 'mttTTC', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal, isEditable=False),
            ColumnDefn("PrixStock", 'right', 80, 'pxMoy', isSpaceFilling=False, valueSetter=0.0,
                   stringConverter=xformat.FmtDecimal, isEditable=False),
            ColumnDefn("Qté stock", 'right', 80, 'qteStock', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal, isEditable=False),
            ]
    return lstCol

def GetMouvements(dlg, dParams):
    # retourne la liste des données de l'OLv de DlgEntree
    ctrlOlv = dlg.ctrlOlv
    ldMouvements = nust.GetMvtsOneArticle(dlg.db, dParams)
    # appel des dicArticles des mouvements
    ddArticles = {}
    for dMvt in ldMouvements:
        ddArticles[dMvt['IDarticle']] = nust.SqlDicArticle(dlg.db,dlg.ctrlOlv,dMvt['IDarticle'])

    # composition des données
    lstDonnees = []
    lstCodesCol = ctrlOlv.GetLstCodesColonnes()

    # Enrichissement des lignes pour olv à partir des mouvements remontés
    for dMvt in ldMouvements:
        donnees = []
        dArticle = ddArticles[dMvt['IDarticle']]
        # alimente les données des colonnes
        for code in lstCodesCol:
            # ajout de la donnée dans le mouvement
            if code == 'pxUn' :
                donnees.append(dArticle['prixMoyen'])
                continue
            if code == 'pxMoy':
                donnees.append(dArticle['prixMoyen'])
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
        lstDonnees.append(donnees)
    return lstDonnees

class DLG(dlgMvts.DLG):
    # ------------------- Composition de l'écran de gestion-----------------------------
    def __init__(self,sens='article',  **kwds):
        # gestion des deux sens possibles 'entrees' et 'sorties'
        kwds['sens'] = sens
        listArbo=os.path.abspath(__file__).split("\\")
        kwds['title'] = listArbo[-1] + "/" + self.__class__.__name__
        super().__init__(**kwds)

    def Init(self):
        self.db = xdb.DB()
        self.GetDicParams = GetDicParams
        # définition de l'OLV
        self.ctrlOlv = None
        self.typeAchat = None
        self.article = None
        self.origine = 'tous'
        today = datetime.date.today()

        # boutons de bas d'écran - infos: texte ou objet window.  Les infos sont  placées en bas à gauche
        self.txtInfo =  "Ici de l'info apparaîtra selon le contexte de la grille de saisie"
        lstInfos = [ wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)),self.txtInfo]
        dicPied = {'lstBtns': dlgMvts.GetBoutons(self), "lstInfos": lstInfos}

        # lancement de l'écran en blocs principaux
        self.pnlBandeau = xbandeau.Bandeau(self, dlgMvts.TITRE[self.sens],
                                           dlgMvts.INTRO[self.sens], hauteur=20,
                                           nomImage="xpy/Images/80x80/Validation.png",
                                           sizeImage=(60, 40))
        self.pnlBandeau.SetBackgroundColour(wx.Colour(250, 250, 180))

        self.pnlParams = dlgMvts.PNL_params(self)
        self.pnlOlv = dlgMvts.PNL_corps(self, self.dicOlv)
        self.pnlOlv.ValideParams = self.ValideParams
        self.pnlOlv.ValideLigne = self.ValideLigne
        self.pnlPied = dlgMvts.PNL_pied(self, dicPied)
        self.ctrlOlv = self.pnlOlv.ctrlOlv
        self.ctrlOlv.DeleteAllItems()
        # charger les valeurs de pnl_params
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        self.postDate = nust.GetLastInventaire(today, lstChamps=['IDdate',],
                                             retourLignes=False)
        self.pnlParams.SetOneValue('postDate',valeur=xformat.FmtDate(self.postDate),
                                   codeBox='param2')

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

    # ------------------- Gestion des actions ------------------------------------------

    def InitOlv(self):
        self.ctrlOlv.lstColonnes = GetOlvColonnes(self)
        self.ctrlOlv.lstCodesColonnes = self.ctrlOlv.GetLstCodesColonnes()
        self.ctrlOlv.InitObjectListView()
        self.Refresh()

    def ValideParams(self):
        ValideParams(None,None)


    def ValideLigne(self,code,track):
        # Relais de l'appel par cellEditor à chaque colonne
        ValideLigne(self,track)

    def CalculeLigne(self,code,track):
        # Relais de l'appel par par GetDonnnees
        CalculeLigne(self,track)

    def GetParams(self):
        dParams = {'article':self.article,
                   'origine': self.origine,
                   'postDate': self.postDate}
        return dParams

    def GetDonnees(self,dParams=None):

        # forme la grille, puis création d'un premier modelObjects par init
        self.InitOlv()
        if not dParams:
            return
        # appel des données de l'Olv principal à éditer
        self.ctrlOlv.lstDonnees = [x for x in GetMouvements(self,dParams)]
        self.ctrlOlv.MAJ()

    # gestion des actions évènements sur les ctrl

    def GetOneArticle(self,saisie):
        # recherche d'un article, Désactive cellEdit pour éviter l'écho des double clics
        self.ctrlOlv.cellEditMode = self.ctrlOlv.CELLEDIT_NONE
        article = dlgArt.GetOneIDarticle(self.db, saisie.upper())
        self.ctrlOlv.cellEditMode = self.ctrlOlv.CELLEDIT_DOUBLECLICK #réactive dblClic
        return article

    def OnArticle(self,event):
        # éviter la redondance de l'évènement 'Enter'
        if event and event.EventType != wx.EVT_KILL_FOCUS.evtType[0]:
            return
        saisie = self.pnlParams.GetOneValue('article',codeBox='param0')
        # vérification de m'éxistance et choix si nécessaire
        self.article = self.GetOneArticle(saisie.upper())
        if self.article:
            self.pnlParams.SetOneValue('article', self.article, codeBox='param0')
            self.GetDonnees(self.GetParams())

    def OnBtnArticle(self,event):
        # Appel du choix d'un ARTICLE via un écran complet
        # id = DLG_Articles.GetOneIDarticle(db,value,f4=f4)
        self.article = self.GetOneArticle("")
        self.pnlParams.SetOneValue('article',self.article,codeBox='param0')
        if self.article:
            self.GetDonnees(self.GetParams())

    def OnTous(self,event):
        # éviter la redondance de l'évènement 'Check' et kill focus
        if event and event.EventType == wx.EVT_KILL_FOCUS.evtType[0]:
            return
        self.tous = self.pnlParams.GetOneValue('tous', codeBox='param0')
        if self.tous:
            self.article = 'Tous'
            flag = False
        else:
            self.article = ''
            flag = True
        self.pnlParams.SetOneValue('article', self.article, codeBox='param0')
        pnlCtrl = self.pnlParams.GetPnlCtrl('article', codebox='param0')
        # active ou désactive le choix de l'article
        pnlCtrl.txt.Enable(flag)
        pnlCtrl.ctrl.Enable(flag)
        pnlCtrl.btn.Enable(flag)
        if self.tous:
            self.GetDonnees(self.GetParams())

    def OnPostDate(self,event):
        # éviter la redondance de l'évènement 'Enter'
        if event and event.EventType != wx.EVT_KILL_FOCUS.evtType[0]:
            return
        saisie = self.pnlParams.GetOneValue('postDate',codeBox='param2')
        saisie = xformat.FmtDate(saisie)
        self.postDate = xformat.DateFrToDatetime(saisie)
        lastInvent = xformat.DateSqlToDatetime(nust.GetLastInventaire(None, lstChamps=['IDdate',],
                                             retourLignes=False))
        self.pnlParams.SetOneValue('postDate',valeur=xformat.FmtDate(saisie),codeBox='param2')
        if self.postDate < lastInvent:
            self.ctrlOlv.cellEditMode = self.ctrlOlv.CELLEDIT_NONE
            mess = "Désactivation des modifications\n\n"
            mess += "Un inventaire a été archivé au '%s', "% xformat.FmtDate(lastInvent)
            mess += "la modification de mouvements pouvant être antérieurs n'est pas possible"
            mess += ", mais vous pouvez les consulter."
            wx.MessageBox(mess,"Information",style = wx.ICON_INFORMATION)
        else:
            self.ctrlOlv.cellEditMode = self.ctrlOlv.CELLEDIT_DOUBLECLICK  # réactive dblClic
        if self.article:
            self.GetDonnees(self.GetParams())

    def OnOrigine(self,event):
        if event:
            self.ctrlOlv.lstDonnees = []
            self.oldParams = {}
        self.origine = self.GetOrigine()
        self.dicOlv.update({'lstColonnes': GetOlvColonnes(self)})
        if event: event.Skip()
        if self.article:
            self.GetDonnees(self.GetParams())

#------------------------ Lanceur de test  -------------------------------------------

if __name__ == '__main__':
    app = wx.App(0)
    os.chdir("..")
    dlg = DLG(sens='article')
    dlg.ShowModal()
    app.MainLoop()
