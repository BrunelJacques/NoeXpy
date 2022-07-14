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
import srcNoestock.DLG_Mouvements      as DLG_Mouvements
import srcNoestock.UTILS_Stocks        as nust
import xpy.xUTILS_DB                   as xdb
from xpy.outils                 import xformat,xbandeau
from xpy.outils.ObjectListView  import ColumnDefn

MATRICE_PARAMS = {
("param1", "Paramètres"): [
    {'name': 'article', 'genre': 'Choice', 'label': 'Article',
                    'help': "Le choix de l'article génère la liste ci-dessous'",
                    'value':0,'values':[''],
                    'ctrlAction':'OnArticle',
                     'btnLabel': "...", 'btnHelp': "Cliquez pour choisir un article",
                     'btnAction': 'OnBtnArticle',
                    'size':(250,35),
                    'ctrlMaxSize':(250,35),
                    'txtSize': 70,
     },
    ],
}

def GetDicParams(dlg):
    matrice = xformat.CopyDic(MATRICE_PARAMS)
    return {
                'name':"PNL_params",
                'matrice':matrice,
                'lblBox':None,
                'boxesSizes': [(350, 50),None,],
                'pathdata':"srcNoelite/Data",
                'nomfichier':"stparams",
                'nomgroupe':"article",
            }

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




class DLG(DLG_Mouvements.DLG):
    # ------------------- Composition de l'écran de gestion----------
    def __init__(self,sens='article',**kwds):
        # gestion des deux sens possibles 'entrees' et 'sorties'
        self.sens = sens
        kwds['sens'] = self.sens
        super().__init__(None,**kwds)

    def Init(self):
        self.db = xdb.DB()
        # définition de l'OLV
        self.ctrlOlv = None

        # boutons de bas d'écran - infos: texte ou objet window.  Les infos sont  placées en bas à gauche
        self.txtInfo =  "Ici de l'info apparaîtra selon le contexte de la grille de saisie"
        lstInfos = [ wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)),self.txtInfo]
        dicPied = {'lstBtns': DLG_Mouvements.GetBoutons(self), "lstInfos": lstInfos}

        # lancement de l'écran en blocs principaux
        self.pnlBandeau = xbandeau.Bandeau(self, DLG_Mouvements.TITRE[self.sens],
                                           DLG_Mouvements.INTRO[self.sens], hauteur=20,
                                           nomImage="xpy/Images/80x80/Loupe.png",
                                           sizeImage=(60, 40))
        self.pnlBandeau.SetBackgroundColour(wx.Colour(250, 216, 53))
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

#------------------------ Lanceur de test  -------------------------------------------

if __name__ == '__main__':
    app = wx.App(0)
    os.chdir("..")
    dlg = DLG(sens='article')
    dlg.ShowModal()
    app.MainLoop()
