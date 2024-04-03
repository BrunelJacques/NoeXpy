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
import srcNoelite.UTILS_Noelite        as nung
import xpy.ObjectListView.xGTR as xGTR
import xpy.xUTILS_DB                   as xdb
from srcNoestock                import DLG_Effectifs, DLG_Mouvements, DLG_PrixJourDetail
from xpy.ObjectListView.ObjectListView import ColumnDefn
from xpy.outils                 import xformat,xbandeau,xboutons,xdates

#---------------------- Matrices de paramétres -------------------------------------

LIMITSQL = 100
TITRE = "Suivi des Prix de journée"
INTRO = "Ce tableau fait ressortir le prix des repas selon les sorties de stock " \
        + "rapproché des effectifs servis ou payants seuls, à compléter par le bouton 'saisie'. Le matin se rattache au soir de la veille"

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
    {'name': 'cuisine', 'genre': 'Check', 'label': 'Repas préparés en cuisine     ',
                    'help': "Les repas préparés en cuisine ne sont pas différenciés par camp servi, seules les sorties identifiés sont affectées aux camps",
                    'value':True,
                    'ctrlAction':'OnCuisine',
                    'txtSize': 150,
                    'ctrlMaxSize': (220, 25)},
    {'name': 'analytique', 'genre': 'Choice', 'label': 'Activité',
                    'ctrlAction':'OnAnalytique',
                    'help': "Il s'agit de l'activité qui a endossé la charge de la sortie",
                    'value':'','values':[''],
                    'btnLabel': "...", 'btnHelp': "Cliquez pour choisir l'activité de destination des mouvements",
                    'btnAction': 'OnBtnAnalytique',
                    'txtSize': 50,
                    'ctrlMaxSize': (220,30),
                    },
    {'name': 'matinj1', 'genre': 'Check', 'label': "PtDèj avec effectif soir J-1  ",
     'help': "Les effectifs du soir sont en général présents le matin, sinon on prendra l'effectif midi du jour",
     'value': False,
     'ctrlAction': 'OnMatinJ1',
     'txtSize': 157,
     'ctrlMaxSize': (220, 25)},
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

def GetDicPnlParams():
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
                {'name': 'btnImp', 'label': "Imprimer\nla période",
                    'help': "Cliquez ici pour imprimer et enregistrer la saisie de l'entrée en stock",
                    'size': (120, 35), 'image': wx.ART_PRINT,'onBtn':dlg.OnImprimerPeriode},
                {'name':'btnOK','ID':wx.ID_ANY,'label':"Quitter",'help':"Cliquez ici pour sortir",
                    'size':(120,35),'image':"xpy/Images/32x32/Quitter.png",'onBtn':dlg.OnFermer}
            ]

def GetOlvColonnes(dlg):
    # retourne la liste des colonnes de l'écran principal, valueGetter correspond aux champ des tables ou calculs
    return [
            ColumnDefn("pbImpress", 'right', 0,'pbImp', valueSetter=''),
            ColumnDefn("Date", 'right', 150, 'IDdate', valueSetter=datetime.date.today(),stringConverter=xformat.FmtDate),
            ColumnDefn("NbRepas", 'right', 80, 'nbRepas', valueSetter=0, stringConverter=xformat.FmtInt,isSpaceFilling=False),
            ColumnDefn("NbClients", 'right', 80, 'nbClients', valueSetter=0, stringConverter=xformat.FmtInt,isSpaceFilling=False),
            ColumnDefn("PrixParRepas", 'right', 100,'prixRepas', valueSetter=0, stringConverter=xformat.FmtDecimal,isSpaceFilling=False),
            ColumnDefn("PrixJourClient", 'right', 100, 'prixClient', valueSetter=0, stringConverter=xformat.FmtDecimal,isSpaceFilling=False),
            ColumnDefn("Coût global", 'right', 100, 'cout', valueSetter=0, stringConverter=xformat.FmtDecimal,isSpaceFilling=False),
            ColumnDefn("Dont OD sorties", 'right', 100, 'od', valueSetter=0, stringConverter=xformat.FmtDecimal,isSpaceFilling=False),
            ]

def GetOlvCodesSup():
    # codes dans les tracks, mais pas dans les colonnes, ces attributs sont non visibles à l'écran
    return []

def GetOlvOptions(dlg):
    # Options paramètres de l'OLV ds PNLcorps
    return {
            'checkColonne': False,
            'recherche': False,
            'getDonnees': dlg.GetDonnees,
            'dictColFooter': {"IDdate": {"mode": "nombre", "alignement": wx.ALIGN_CENTER},
                              "nbRepas": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                              "nbClients": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                              "prixRepas": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                              "prixClient": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                              "cout": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                              },
            'orientationImpression': wx.PORTRAIT,
            'lstNomsBtns': ['modifier'],
    }

def GetDlgOptions(dlg):
    # Options du Dlg de lancement
    return {
        'style': wx.DEFAULT_FRAME_STYLE,
        'minSize': (700, 550),
        'size': (850, 600),
        }

#----------------------- Parties de l'écran -----------------------------------------

class PNL_corps(xGTR.PNL_corps):
    #panel olv avec habillage optionnel pour des boutons actions (à droite) des infos (bas gauche) et boutons sorties
    def __init__(self, parent, dicOlv,*args, **kwds):
        xGTR.PNL_corps.__init__(self,parent,dicOlv,*args,**kwds)

    def OnDblClick(self,event):
        self.OnModifier(event)

    def OnModifier(self, event):
        # fonction modifier détournée pour imprimer ou saisir effectif
        olv = self.ctrlOlv
        if olv.GetSelectedItemCount() == 0:
            mess = "Vous n'avez pas sélectionné une ligne\n\n"
            mess += "Vous ne souhaitez pas l'édition du détail d'un jour ?"
            dlg = wx.MessageDialog(self,mess,"Information")
            ret = dlg.ShowModal()
            del dlg
            if ret != wx.ID_YES:
                return

        ligne = olv.GetSelectedObject()
        ixLigne = olv.modelObjects.index(ligne)
        dte = ligne.IDdate
        analytique = self.parent.analytique

        if ligne.nbRepas == 0.0:
            # lancement de la gestion effectif
            DLG_Effectifs.EffectifUnJour(self.db,dte,analytique)
            self.ctrlOlv.MAJ(ixLigne)
        dlg = DLG_PrixJourDetail.DLG(dteJour=ligne.IDdate)
        dlg.ShowModal()

class DLG(xGTR.DLG_tableau):
    # ------------------- Composition de l'écran de gestion----------
    def __init__(self):
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
        #self.periode = (None,None)
        self.cuisine = True
        self.analytique = ''
        self.midi = True
        self.soir = True
        self.matin = True
        self.matinj1 = False
        self.paramsOld = None

        # Propriétés de l'écran global type Dialog
        kwds = GetDlgOptions(self)
        listArbo=os.path.abspath(__file__).split("\\")
        kwds['title'] = listArbo[-1] + "/" + self.__class__.__name__
        kwds['autoSizer'] = False
        kwds['dicParams'] = GetDicPnlParams()
        #kwds['dicOlv'] = self.dicOlv
        kwds['dicPied'] = dicPied

        xdb.DB().Close()
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
        self.periode = xformat.PeriodeMois(self.today)
        self.pnlParams.SetOneValue('periode',self.periode,'param1')
        self.pnlParams.SetOneValue('cuisine',self.cuisine,'param2')
        self.pnlParams.SetOneValue('matinj1',self.matinj1,'param2')
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
        self.analytique = ''
        self.ctrlOlv.MAJ()

    def OnAnalytique(self,event):
        choixAnalytique = self.pnlParams.GetOneValue('analytique',codeBox='param2')
        if len(choixAnalytique) > 0:
            ix = self.valuesAnalytique.index(choixAnalytique)-1
            self.analytique = self.lstAnalytiques[ix][0]
        else: self.analytique = ''
        self.ctrlOlv.MAJ()
        if event: event.Skip()

    def OnBtnAnalytique(self,event):
        # Appel du choix d'un camp via un écran complet
        noegest = nung.Noelite(self)
        dicAnalytique = noegest.GetActivite(mode='dlg')
        codeAct = nust.MakeChoiceActivite(dicAnalytique)
        self.pnlParams.SetOneValue('analytique',codeAct,codeBox='param2')
        self.OnAnalytique(event)

    def OnMidi(self,event):
        self.midi =  self.pnlParams.GetOneValue('midi','param3')
        self.ctrlOlv.MAJ()
        if event: event.Skip()

    def OnMatinJ1(self,event):
        self.matinj1 =  self.pnlParams.GetOneValue('matinj1','param2')
        self.ctrlOlv.MAJ()
        if event: event.Skip()

    def OnSoir(self,event):
        self.soir =  self.pnlParams.GetOneValue('soir','param3')
        self.matin = self.soir
        self.pnlParams.SetOneValue('matin', self.soir,'param3')
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
            if str(self.params) == self.paramsOld:
                lstDonnees = self.donneesOld
            else:
                lstDonnees = nust.GetPrixJours(self, **kwd)
        self.donneesOld = [x for x in lstDonnees]
        self.paramsOld = str(self.params)
        return lstDonnees

    def GetTitreImpression(self):
        datedeb = xformat.DateSqlToFr(self.periode[0])
        datefin = xformat.DateSqlToFr(self.periode[1])
        tiers = "Repas en cuisine"
        if len(self.analytique) > 0 : tiers = "Camp: %s"%self.analytique.capitalize()
        return "Synthèse des Prix de journée du %s au %s, %s"%( datedeb, datefin, tiers)

    def GetTotalImpression(self):
        # génération d'une ligne de synthèse avec éventuellement présence de filtre
        effectifs = nust.GetEffectifs(self,)
        if len(effectifs) == 0:
            wx.MessageBox("Pas d'effectif renseignés pour ce jour")
            return
        # recherche filtres
        """
        yaFiltre = False
        filtres = self.ctrlOlv.ctrlOutils.barreRecherche.GetValue()
        if len(filtres) > 0: filtres += ", "

        for filtre in  self.ctrlOlv.listeFiltresColonnes:
            filtres += "%s %s %s, "%(filtre['titre'] , filtre['choix'], filtre['critere'])

        if len(filtres) > 0 :
            yaFiltre = True
            filtres = filtres[:-2] # enlève dernière virgule"""

        # calcul synthèse
        coutsCli, nbClients, coutsRep, nbRepas = 0.0, 0.0, 0.0, 0.0
        
        for track in self.ctrlOlv.modelObjects:
            if track.nbClients > 0:
                coutsCli += track.cout
                nbClients += track.nbClients
            if track.nbRepas > 0:
                coutsRep += track.cout
                nbRepas += track.nbRepas
        moPxRep, moPxCli = 0.0, 0.0
        if nbRepas > 0: moPxRep = round(coutsRep / nbRepas,2)
        if nbClients > 0: moPxCli = round(coutsCli / nbClients,2)
        coutsRep = round(coutsRep)
        coutsCli = round(coutsCli)

        # pas de filtre
        txt = "Coûts :  %d repas à %.2f€ = %.2f€ ,  %d clients à %.2f€ = %.2f€"%(nbRepas,moPxRep, coutsRep,
                                                                              nbClients,moPxCli, coutsCli)

        """if yaFiltre:
            innerTot, innerNbCli, innerNbRep = 0.0, 0.0, 0.0
            for track in self.ctrlOlv.innerList:
                innerTot += track.cout
                innerNbCli = max(innerNbCli, track.nbClients)
                innerNbRep = max(innerNbRep, track.nbRepas)
            innerPxRep = innerTot
            innerPxCli = innerTot
            if innerNbRep > 0: innerPxRep = round(innerTot / innerNbRep,2)
            if innerNbCli > 0: innerPxCli = round(innerTot / innerNbCli,2)
            innerTot = round(innerTot)
            # présence de filtre on affiche le filtré / non filtré
            txt = "Filtré par : %s\n"%filtres
            txt += "Coût global - filtré: %d€ - %d€,  "%(modTot,innerTot,)
            txt += "par repas servi : %.2f€ - %.2f€, par client : %.2f€ - %.2f€"%(modPxRep,innerPxRep,
                                                                                  modPxCli,innerPxCli)"""
        return txt

    def ValideSaisie(self,dlgSaisie,*args,**kwd):
        #Relais de l'appel de l'écran de saisie en sortie
        kwd['periode'] = self.periode
        kwd['cuisine'] = self.cuisine
        return DLG_Effectifs.ValideSaisie(dlgSaisie,**kwd)

    def OnImprimer(self,event):
        # lancement du détail possible via 'Modifier' détourné
        self.pnlOlv.OnModifier(None)
        self.ctrlOlv.Apercu(None)
        return

    def OnImprimerPeriode(self,event):
        self.ctrlOlv.Apercu(None)
        return


#------------------------ Lanceur de test  -------------------------------------------

if __name__ == '__main__':
    app = wx.App(0)
    os.chdir("..")
    dlg = DLG()
    dlg.ShowModal()
    app.MainLoop()
