#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------
# Application:     NoeStock, gestion des stocks et prix de journée
# Module:          Restitution des prix de journée
# Auteur:          Jacques BRUNEL 2021-06
# Licence:         Licence GNU GPL
# ------------------------------------------------------------------

import wx
import os
import datetime
import srcNoestock.UTILS_Stocks        as nust
import srcNoelite.UTILS_Noegest        as nung
import xpy.xGestion_TableauRecherche   as xgtr
import xpy.xUTILS_DB                   as xdb
from srcNoestock                import DLG_Effectifs, DLG_Mouvements
from xpy.outils.ObjectListView  import ColumnDefn
from xpy.outils                 import xformat,xbandeau,xboutons,xdates

#---------------------- Matrices de paramétres -------------------------------------

LIMITSQL = 100
TITRE = "Prix de journée détaillé"
INTRO = "Détail du calcul du prix d'une journée "

BTN_EFFECTIFS = {'label':"Effectifs",
                'name':'effectifs',
                'help':"Pour saisir les effectifs présents indispensables au calcul des prix rations",
                'sizeFont': 12,
                'size' : (120,35)}

BTN_MOUVEMENTS = {'label':"Sorties",
                'name':'mouvements',
                'help':"Pour saisir les sorties de stock, consommations des repas",
                'sizeFont': 12,
                'size' : (120,35)}

class CtrlEffectifs(wx.Panel):
    # controle inséré dans la matrice_params qui suit. De genre AnyCtrl pour n'utiliser que le bind bouton
    def __init__(self,parent):
        super().__init__(parent,wx.ID_ANY)
        kwd = {'image':wx.ArtProvider.GetBitmap(wx.ART_FIND,size=(20,20)),}
        kwd.update(BTN_EFFECTIFS)
        self.btn = xboutons.BTN_action(self,**kwd)
    def SetValue(self,value):
        return
    def GetValue(self):
        return None

class CtrlMouvements(wx.Panel):
    # controle inséré dans la matrice_params qui suit. De genre AnyCtrl pour n'utiliser que le bind bouton
    def __init__(self,parent):
        super().__init__(parent,wx.ID_ANY)
        kwd = {'image':wx.ArtProvider.GetBitmap(wx.ART_FIND,size=(20,20)),}
        kwd.update(BTN_MOUVEMENTS)
        self.btn = xboutons.BTN_action(self,**kwd)
    def SetValue(self,value):
        return
    def GetValue(self):
        return None

# Description des paramètres à choisir en haut d'écran

MATRICE_PARAMS = {
("param1", "Paramètres période"): [
    {'name': 'periode', 'genre': 'anyctrl', 'label': "",
                    'help': "%s\n%s\n%s"%("Saisie JJMMAA ou JJMMAAAA possible.",
                                          "Les séparateurs ne sont pas obligatoires en saisie.",
                                          "Saisissez début et fin de la période, "),
                    'ctrl':xdates.CTRL_Periode,
                    'ctrlAction': 'OnPeriode',
                    'txtSize':0,
                    'ctrlMaxSize':(210,90)},
    ],
("param2", "Comptes"): [
    {'name': 'cuisine', 'genre': 'Check', 'label': 'Repas préparés en cuisine',
                    'help': "Les repas préparés en cuisine ne sont pas différenciés par camp servi, seules les sorties identifiés sont affectées aux camps",
                    'value':True,
                    'ctrlAction':'OnCuisine',
                    'txtSize': 150,
                    'ctrlMaxSize': (210, 40)},

    {'name': 'analytique', 'genre': 'Choice', 'label': 'Activité',
                    'ctrlAction':'OnAnalytique',
                    'help': "Il s'agit de l'activité qui a endossé la charge de la sortie",
                    'value':'','values':[''],
                    'btnLabel': "...", 'btnHelp': "Cliquez pour choisir l'activité de destination des mouvements",
                    'btnAction': 'OnBtnAnalytique',
                    'txtSize': 50,
                    'ctrlMaxSize': (220,30),
                    }
],
("param3", "Circadien"): [
    {'name': 'midi', 'genre': 'Check', 'label': 'Midi',
                'help': "Retenir les sorties pour le repas de midi",
                'value':True,
                'ctrlAction':'OnMidi',
                'txtSize': 60,
                'ctrlMaxSize': (100, 25)},
    {'name': 'soir', 'genre': 'Check', 'label': 'Soir',
                 'help': "Les effectifs soir et matin(J+1) vont ensemble. \nCocher Retiens les sorties pour le repas du soir",
                 'value': True,
                 'ctrlAction': 'OnSoir',
                 'txtSize': 60,
                 'ctrlMaxSize': (100, 25)},
    {'name': 'matin', 'genre': 'Check', 'label': '5e+PtDèj',
                 'help': "Retenir les sorties pour le petit-dej du lendemain (J+1) et le 5eme de J\nen plus de celles du soir",
                 'value': True,
                 'ctrlAction': 'OnMatin',
                 'txtSize': 60,
                 'ctrlMaxSize': (100, 25)},

],
("param4", "Boutons actions"): [
    {'name': 'rappel', 'genre': 'anyctrl','label': ' ',
                     'txtSize': 1,
                     'ctrlMaxSize':(150,50),
                     'ctrl': CtrlEffectifs,
                     'ctrlAction': 'OnBtnEffectifs',
                     },
    {'name': 'rappel2', 'genre': 'anyctrl','label': ' ',
                     'txtSize': 1,
                     'ctrlMaxSize':(150,50),
                     'ctrl': CtrlMouvements,
                     'ctrlAction': 'OnBtnMouvements',
                     },
    ],
}

INFOS = ["Double clic sur une ligne pour accéder aux effectifs du jour.\nSeul les jours ayant des sorties de stock sont affichés",]

def GetDicParams():
    return {
                'name':"PNL_params",
                'matrice':MATRICE_PARAMS,
                'lblBox':None,
                'boxesSizes': [(220, 70), (240, 90), None, (150, 95)],
                'pathdata':"srcNoelite/Data",
                'nomfichier':"stparams",
                'nomgroupe':"prixJour",
            }

def GetBoutons(dlg):
    return  [
                {'name': 'btnImp', 'label': "Imprimer\npour contrôle",
                    'help': "Cliquez ici pour imprimer et enregistrer la saisie de l'entrée en stock",
                    'size': (120, 35), 'image': wx.ART_PRINT,'onBtn':dlg.OnImprimer},
                {'name':'btnOK','ID':wx.ID_ANY,'label':"Quitter",'help':"Cliquez ici pour sortir",
                    'size':(120,35),'image':"xpy/Images/32x32/Quitter.png",'onBtn':dlg.OnFermer}
            ]

def GetOlvColonnes(dlg):
    # retourne la liste des colonnes de l'écran principal, valueGetter correspond aux champ des tables ou calculs
    return [
            ColumnDefn("pbImpress", 'right', 0,'pbImp', valueSetter=''),
            ColumnDefn("Article", 'left', 200, 'IDarticle', valueSetter="", isSpaceFilling=True),
            ColumnDefn("Rayon", 'left', 80, 'rayon', valueSetter="", isSpaceFilling=False),
            ColumnDefn("Qté", 'right', 80, 'qte', valueSetter=0, stringConverter=xformat.FmtDecimal,isSpaceFilling=False),
            ColumnDefn("PrixUn", 'right', 80, 'prixUn', valueSetter=0, stringConverter=xformat.FmtDecimal,isSpaceFilling=False),
            ColumnDefn("Coût", 'right', 80, 'cout', valueSetter=0, stringConverter=xformat.FmtDecimal,isSpaceFilling=False),
            ColumnDefn("NbRepas", 'right', 80, 'nbRepas', valueSetter=0, stringConverter=xformat.FmtInt,isSpaceFilling=False),
            ColumnDefn("PrixParRepas", 'right', 80,'prixRepas', valueSetter=0, stringConverter=xformat.FmtDecimal,isSpaceFilling=False),
            ColumnDefn("NbClients", 'right', 80, 'nbClients', valueSetter=0, stringConverter=xformat.FmtInt,isSpaceFilling=False),
            ColumnDefn("PrixJourClient", 'right', 80, 'prixClient', valueSetter=0, stringConverter=xformat.FmtDecimal,isSpaceFilling=False),
            ]

def GetOlvCodesSup():
    # codes dans les tracks, mais pas dans les colonnes, ces attributs sont non visibles à l'écran
    return []

def GetOlvOptions(dlg):
    # Options paramètres de l'OLV ds PNLcorps
    return {
            'checkColonne': False,
            'sortColumnIndex':2,
            'recherche': True,
            'getDonnees': dlg.GetDonnees,
            'dictColFooter': {"IDdate": {"mode": "nombre", "alignement": wx.ALIGN_CENTER},
                              "nbRepas": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                              "nbClients": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                              "prixRepas": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                              "prixClient": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                              "cout": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                              },
            'orientationImpression': wx.PORTRAIT,
    }

def GetDlgOptions(dlg):
    # Options du Dlg de lancement
    return {
        'style': wx.DEFAULT_FRAME_STYLE,
        'minSize': (700, 550),
        'size': (850, 800),
        }

#----------------------- Parties de l'écran -----------------------------------------

class PNL_corps(xgtr.PNL_corps):
    #panel olv avec habillage optionnel pour des boutons actions (à droite) des infos (bas gauche) et boutons sorties
    def __init__(self, parent, dicOlv,*args, **kwds):
        xgtr.PNL_corps.__init__(self,parent,dicOlv,*args,**kwds)

    def OnDblClick(self,event):
        self.OnModifier(event)

    def OnModifier(self, event):
        # Action du clic sur l'icone sauvegarde renvoie au parent
        olv = self.ctrlOlv
        if olv.GetSelectedItemCount() == 0:
            wx.MessageBox("Pas de sélection faite, pas de modification possible !" ,
                                'Problème de double clic?', wx.OK | wx.ICON_INFORMATION)
            return

        ligne = olv.GetSelectedObject()
        ixLigne = olv.modelObjects.index(ligne)
        dte = ligne.IDdate
        analytique = self.parent.analytique
        # lancemetn de la gestion effectif
        DLG_Effectifs.EffectifUnJour(self.db,dte,analytique)
        self.ctrlOlv.MAJ(ixLigne)

class DLG(xgtr.DLG_tableau):
    # ------------------- Composition de l'écran de gestion----------
    def __init__(self,dteJour=None):
        # boutons de bas d'écran - infos: texte ou objet window.  Les infos sont  placées en bas à gauche
        lstInfos = [ wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)),]
        lstInfos += INFOS
        dicPied = {'lstBtns': GetBoutons(self), "lstInfos": lstInfos}

        # Propriétés du corps de l'écran
        self.dicOlv = {'lstColonnes': GetOlvColonnes(self)}
        self.dicOlv.update({'lstCodesSup': GetOlvCodesSup()})
        self.dicOlv.update(GetOlvOptions(self))

        # variables gérées par l'écran paramètres
        self.today = datetime.date.today()
        if not dteJour:
            dteJour = self.today
        else: dteJour = xformat.DateSqlToDatetime(dteJour)
        self.periode = (dteJour,dteJour)
        self.cuisine = True
        self.analytique = '00'
        self.midi = True
        self.soir = True
        self.matin = True

        # Propriétés de l'écran global type Dialog
        kwds = GetDlgOptions(self)
        kwds['autoSizer'] = False
        kwds['dicParams'] = GetDicParams()
        #kwds['dicOlv'] = self.dicOlv
        kwds['dicPied'] = dicPied
        kwds['db'] = xdb.DB()

        super().__init__(None, **kwds)
        self.pnlOlv = PNL_corps(self, self.dicOlv,  **kwds )
        self.ctrlOlv = self.pnlOlv.ctrlOlv

        ret = self.Init()
        if ret == wx.ID_ABORT: self.Destroy()
        self.Sizer()
        self.ctrlOlv.MAJ()
        self.ctrlOlv.SetFocus()

    def Init(self):
        # lancement de l'écran en blocs principaux
        self.pnlBandeau = xbandeau.Bandeau(self,TITRE,INTRO, hauteur=20,
                                           nomImage="xpy/Images/80x80/Loupe.png",
                                           sizeImage=(60,60))
        self.pnlBandeau.SetBackgroundColour(wx.Colour(220, 250, 220))

       # charger les valeurs de pnl_params
        self.pnlParams.SetOneValue('periode',self.periode,'param1')
        self.pnlParams.SetOneValue('cuisine',self.cuisine,'param2')
        self.pnlParams.SetOneValue('midi',self.midi,'param3')
        self.pnlParams.SetOneValue('soir',self.soir,'param3')
        self.pnlParams.SetOneValue('matin',self.matin,'param3')
        self.lstAnalytiques = nust.SqlAnalytiques(self.db,'ACTIVITES')
        self.btnAnalytique = self.pnlParams.GetPnlCtrl('analytique','param2').btn
        self.btnAnalytique.Enable(False)
        self.OnCuisine(None)
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
        self.ctrlOlv.lstColonnes = GetOlvColonnes(self)
        self.ctrlOlv.lstCodesColonnes = self.ctrlOlv.GetLstCodesColonnes()
        self.ctrlOlv.InitObjectListView()
        self.Refresh()

    def OnPeriode(self,event):
        self.periode = self.pnlParams.GetOneValue('periode','param1')
        self.ctrlOlv.MAJ()
        if event: event.Skip()

    def OnCuisine(self,event):
        self.cuisine =  self.pnlParams.GetOneValue('cuisine','param2')
        if self.cuisine:
            self.pnlParams.SetOneValue('analytique','','param2')
            self.valuesAnalytique = ['', ]
            if event: event.Skip()
        else:
            self.valuesAnalytique = ['', ] + [nust.MakeChoiceActivite(x) for x in self.lstAnalytiques]
            self.btnAnalytique.SetFocus()
        self.pnlParams.SetOneSet('analytique', values=self.valuesAnalytique, codeBox='param2')
        self.btnAnalytique.Enable(not self.cuisine)
        self.pnlParams.GetPnlCtrl('analytique','param2').txt.Enable(not self.cuisine)
        self.pnlParams.GetPnlCtrl('analytique','param2').ctrl.Enable(not self.cuisine)
        self.analytique = '00'
        self.ctrlOlv.MAJ()

    def OnAnalytique(self,event):
        choixAnalytique = self.pnlParams.GetOneValue('analytique',codeBox='param2')
        if len(choixAnalytique) > 0:
            ix = self.valuesAnalytique.index(choixAnalytique)-1
            self.analytique = self.lstAnalytiques[ix][0]
        else: self.analytique = '00'
        self.ctrlOlv.MAJ()
        if event: event.Skip()

    def OnBtnAnalytique(self,event):
        # Appel du choix d'un camp via un écran complet
        noegest = nung.Noegest(self)
        dicAnalytique = noegest.GetActivite(mode='dlg')
        codeAct = nust.MakeChoiceActivite(dicAnalytique)
        self.pnlParams.SetOneValue('analytique',codeAct,codeBox='param2')
        self.OnAnalytique(event)

    def OnMidi(self,event):
        self.midi =  self.pnlParams.GetOneValue('midi','param3')
        self.ctrlOlv.MAJ()
        if event: event.Skip()

    def OnSoir(self,event):
        self.soir =  self.pnlParams.GetOneValue('soir','param3')
        self.matin = self.soir
        self.pnlParams.SetOneValue('matin', bool(self.soir),'param3')
        ctrlMatin = self.pnlParams.GetPnlCtrl('midi','param3')
        ctrlMatin.SetFocus()
        self.ctrlOlv.MAJ()
        if event: event.Skip()

    def OnMatin(self,event):
        self.matin =  self.pnlParams.GetOneValue('matin','param3')
        self.ctrlOlv.MAJ()
        if event: event.Skip()

    def OnBtnEffectifs(self,event):
        # lancement de l'écran des effectifs
        dlg = DLG_Effectifs.DLG()
        dlg.ShowModal()
        if event: event.Skip()

    def OnBtnMouvements(self,event):
        # lancement de l'écran des effectifs
        if self.ctrlOlv.GetSelectedObject() != None:
            date = self.ctrlOlv.GetSelectedObject().IDdate
        else: date = datetime.date.today()
        dlg = DLG_Mouvements.DLG(sens='sorties',date=date)
        dlg.ShowModal()
        if event: event.Skip()

    def GetDonnees(self,**kwd):
        # rafraîchissement des données de l'Olv principal suite à changement de params
        # periode est construite dans DLG.Init les accès en cours de construction sont ignorés
        lstDonnees = []
        if hasattr(self,'periode'):
            self.params = self.pnlParams.GetValues()
            kwd['db'] = self.db
            lstDonnees = nust.GetPxJourDetail(self, **kwd)
        return lstDonnees

    def GetTitreImpression(self):
        datedeb = xformat.DateSqlToFr(self.periode[0])
        datefin = xformat.DateSqlToFr(self.periode[1])
        if datedeb == datefin:
            titre = "Prix journée %s"%datedeb
        else:
            titre = "Prix Jour du %s au %s"%(datedeb, datefin)

        tiers = "en Cuisine"
        if self.analytique != "00" : tiers = "Camp: %s"%self.analytique.capitalize()

        repas = ""
        if self.params['param3']['midi']: repas += "Midi,"
        if self.params['param3']['soir']: repas += "Soir,"
        if self.params['param3']['matin']: repas += "5e+ptDej,"

        return "%s, %s, Repas: %s"%( titre, tiers, repas)

    def GetIntroImpression(self):
        return "et patata..."

    def GetTotalImpression(self):
        return "Total cumulé :"

    def ValideSaisie(self,dlgSaisie,*args,**kwd):
        #Relais de l'appel de l'écran de saisie en sortie
        kwd['periode'] = self.periode
        kwd['cuisine'] = self.cuisine
        return DLG_Effectifs.ValideSaisie(dlgSaisie,**kwd)

    def OnImprimer(self,event):
        self.ctrlOlv.Apercu(None)

#------------------------ Lanceur de test  -------------------------------------------

if __name__ == '__main__':
    app = wx.App(0)
    os.chdir("..")
    dlg = DLG(dteJour="2021-07-04")
    dlg.ShowModal()
    app.MainLoop()
