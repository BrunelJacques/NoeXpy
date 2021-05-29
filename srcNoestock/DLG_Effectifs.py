#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------
# Application:     NoeStock, gestion des stocks et prix de journée
# Module:          Saisie des effectifs présents
# Auteur:          Jacques BRUNEL 2021-04
# Licence:         Licence GNU GPL
# ------------------------------------------------------------------

import wx
import os
import datetime
import srcNoestock.UTILS_Stocks        as nust
import srcNoelite.UTILS_Noegest        as nung
import xpy.xGestion_TableauRecherche   as xgtr
#import xpy.xUTILS_Identification       as xuid
#import xpy.xUTILS_SaisieParams         as xusp
import xpy.xUTILS_DB                   as xdb
from xpy.outils.ObjectListView  import ColumnDefn
from xpy.outils                 import xformat,xbandeau,xboutons,xdates

#---------------------- Matrices de paramétres -------------------------------------

LIMITSQL = 100
TITRE = "Suivi des effectifs quotidiens"
INTRO = "La saisie des effectifs quotidiens réels permet de déterminer le prix de journée, il est rapprocché " \
        + "du nombre d'inscrits payants et non payants"

class CtrlSynchro(wx.Panel):
    # controle inséré dans la matrice_params qui suit. De genre AnyCtrl pour n'utiliser que le bind bouton
    def __init__(self,parent):
        super().__init__(parent,wx.ID_ANY)
        kwd = {'label':"Synchroniser\nle prévu",
               'name':'synchro',
               'image':wx.ArtProvider.GetBitmap(wx.ART_FIND,size=(24,24)),
               'help':"Pour reprendre les effectifs prévus par synchronisation avec les incriptions",
               'size' : (150,40)}
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
    {'name': 'repas', 'genre': 'Check', 'label': 'Repas préparés en cuisine',
                    'help': "Les repas préparés en cuisine ne sont pas différenciés par camp servi, seules les sorties identifiés sont affectées aux camps",
                    'value':True,
                    'ctrlAction':'OnRepas',
                    'txtSize': 150,
                    'ctrlMaxSize': (210, 40)},

    {'name': 'analytique', 'genre': 'Choice', 'label': 'Activité',
                    'ctrlAction':'OnAnalytique',
                    'help': "Il s'agit de l'activité qui a endossé la charge de la sortie",
                    'value':'','values':[''],
                    'btnLabel': "...", 'btnHelp': "Cliquez pour choisir l'activité de destination des mouvements",
                    'btnAction': 'OnBtnAnalytique',
                    'txtSize': 50,
                    'ctrlMaxSize': (310, 35)}
],
("param4", "Boutons actions"): [
    {'name': 'rappel', 'genre': 'anyctrl','label': ' ',
                     'txtSize': 1,
                        'ctrlMaxSize':(200,50),
                     'ctrl': CtrlSynchro,
                     'ctrlAction': 'OnBtnSynchro',
                     },
    ],
}

def GetDicParams():
    return {
                'name':"PNL_params",
                'matrice':MATRICE_PARAMS,
                'lblBox':None,
                'boxesSizes': [(220, 80), (260, 80), (200, 80)],
                'pathdata':"srcNoelite/Data",
                'nomfichier':"stparams",
                'nomgroupe':"effectifs",
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
            ColumnDefn("Date", 'left', 90,      'ID', valueSetter=datetime.date.today(),stringConverter=xformat.FmtDate),
            ColumnDefn("RepasMidi", 'right', 72, 'midiRepas', valueSetter=0, stringConverter=xformat.FmtInt,isSpaceFilling=True),
            ColumnDefn("ClientsMidi", 'right', 72,'midiClients', valueSetter=0, stringConverter=xformat.FmtInt,isSpaceFilling=True),
            ColumnDefn("RepasSoir", 'right', 72,   'soirRepas', valueSetter=0, stringConverter=xformat.FmtInt,isSpaceFilling=True),
            ColumnDefn("ClientsSoir", 'right', 72, 'soirClients', valueSetter=0, stringConverter=xformat.FmtInt,isSpaceFilling=True),
            ColumnDefn("PrévuInscrits", 'right', 72, 'prevuRepas', valueSetter=0, stringConverter=xformat.FmtInt,isSpaceFilling=True),
            ColumnDefn("PrévuClients", 'right', 72, 'prevuClients', valueSetter=0, stringConverter=xformat.FmtInt,isSpaceFilling=True),
            ]

def GetOlvCodesSup():
    # codes dans les tracks, mais pas dans les colonnes, ces attributs sont non visibles à l'écran
    return ['IDanalytique','modifiable']

def GetOlvOptions(dlg):
    # Options paramètres de l'OLV ds PNLcorps
    return {
            'checkColonne': False,
            'recherche': True,
            'getDonnees': dlg.GetDonnees,
            'dictColFooter': {"date": {"mode": "nombre", "alignement": wx.ALIGN_CENTER},
                                  "midiRepas": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                                  "midiClients": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                                  "prevuRepas": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                                  "prevuClients": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                                  },
            'orientationImpression': wx.PORTRAIT,
            'lstNomsBtns': ['creer', 'modifier','supprimer'],
    }

def GetMatriceSaisie(dlg):
    # utile pour personaliser la saisie avec des contrôles particuliers, sinon ignorer cette étape
    dicRetour = {}
    key = ("saisie", "")
    matrice = xformat.DicOlvToMatrice(key, dlg.dicOlv)
    # mise en place d'un contrôle sur la date saisie via la matrice
    # matrice[key][0]['ctrlAction'] = dlg.VerifieDate
    dicRetour['matriceSaisie'] = matrice
    dicRetour['sizeSaisie'] = (200,420)
    return dicRetour

def GetDlgOptions(dlg):
    # Options du Dlg de lancement
    return {
        'style': wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        'minSize': (300, 450),
        'size': (650, 600),
        }

#----------------------- Parties de l'écran -----------------------------------------

class Saisie(object):
    # ------------------- Composition de l'écran de gestion----------
    def __init__(self):
        # Lanceur de l'écran de saisie d'un nouvelle ligne d'effectif
        # Propriétés identiques au DLG de gestion pour simuler un passage via l'écran DLG
        self.dicOlv = {'lstColonnes': GetOlvColonnes(self)}
        self.dicOlv.update({'lstCodesSup': GetOlvCodesSup()})
        self.dicOlv.update(GetOlvOptions(self))
        self.dicOlv.update(GetMatriceSaisie(self))

        # l'ajout d'une ligne nécessite d'appeler un écran avec les champs en lignes
        dlgSaisie = xgtr.DLG_saisie(self,self.dicOlv)
        ret = dlgSaisie.ShowModal()
        if ret == wx.OK:
            #récupération des valeurs saisies puis ajout dans les données
            ddDonnees = dlgSaisie.pnl.GetValues()
            nomsCol, donnees = xformat.DictToList(ddDonnees)
            self.GereDonnees(nomsCol=nomsCol, donnees=donnees)

    def GetDonnees(self,**kwd):
        # censées être les données d'un OLV non créé
        return []

    def GereDonnees(self,**kwd):
            # Appelé en retour de saisie, gère l'enregistrement
            donnees = kwd.pop('donnees', None)
            db = xdb.DB()

            lstDonnees = [('IDdate', donnees[0]),
                          ('IDanalytique', self.analytique),
                          ('midiRepas', donnees[1]),
                          ('midiClients', donnees[2]),
                          ('soirRepas', donnees[3]),
                          ('soirClients', donnees[4]),
                          ('prevuRepas', donnees[5]),
                          ('prevuClients', donnees[6]),
                          ]
            ret = db.ReqInsert('stEffectifs', lstDonnees=lstDonnees, mess="Insert Effectifs")
            if ret == 'ok':
                if ixligne and ixligne < len(donneesOlv):
                    self.ctrlOlv.lstDonnees = donneesOlv[:ixligne] + [donnees, ] + donneesOlv[ixligne:]
                else:
                    self.ctrlOlv.lstDonnees.append(donnees)


class DLG(xgtr.DLG_tableau):
    # ------------------- Composition de l'écran de gestion----------
    def __init__(self):
        # boutons de bas d'écran - infos: texte ou objet window.  Les infos sont  placées en bas à gauche
        self.txtInfo =  "Ici de l'info apparaîtra selon le contexte de la grille de saisie"
        lstInfos = [ wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)),self.txtInfo]
        dicPied = {'lstBtns': GetBoutons(self), "lstInfos": lstInfos}

        # Propriétés du corps de l'écran
        self.dicOlv = {'lstColonnes': GetOlvColonnes(self)}
        self.dicOlv.update({'lstCodesSup': GetOlvCodesSup()})
        self.dicOlv.update(GetOlvOptions(self))
        self.dicOlv.update(GetMatriceSaisie(self))

        # variables gérées par l'écran paramètres
        self.today = datetime.date.today()
        #self.periode = (None,None)
        self.repas = True
        self.analytique = '00'

        # Propriétés de l'écran global type Dialog
        kwds = GetDlgOptions(self)
        kwds['autoSizer'] = False
        kwds['dicParams'] = GetDicParams()
        kwds['dicOlv'] = self.dicOlv
        kwds['dicPied'] = dicPied
        kwds['db'] = xdb.DB()

        super().__init__(None, **kwds)
        ret = self.Init()
        if ret == wx.ID_ABORT: self.Destroy()
        self.Sizer()
        self.ctrlOlv.MAJ()

    def Init(self):
        # lancement de l'écran en blocs principaux
        self.pnlBandeau = xbandeau.Bandeau(self,TITRE,INTRO, hauteur=20,
                                           nomImage="xpy/Images/80x80/Famille.png",
                                           sizeImage=(60,60))
        self.pnlBandeau.SetBackgroundColour(wx.Colour(220, 250, 220))

       # charger les valeurs de pnl_params
        self.periode = xformat.PeriodeMois(self.today)
        self.pnlParams.SetOneValue('periode',self.periode,'param1')
        self.pnlParams.SetOneValue('repas',self.repas,'param2')
        self.lstAnalytiques = nust.SqlAnalytiques(self.db,'ACTIVITES')
        self.btnAnalytique = self.pnlParams.GetPnlCtrl('analytique','param2').btn
        self.btnAnalytique.Enable(False)
        self.txtAnalytique = self.pnlParams.GetPnlCtrl('analytique','param2').txt
        self.txtAnalytique.Enable(False)
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

    def OnRepas(self,event):
        self.repas =  self.pnlParams.GetOneValue('repas','param2')
        if self.repas:
            self.pnlParams.SetOneValue('analytique','','param2')
            self.valuesAnalytique = ['', ]
            if event: event.Skip()
        else:
            self.valuesAnalytique = ['', ] + [nust.MakeChoiceActivite(x) for x in self.lstAnalytiques]
            self.btnAnalytique.SetFocus()
        self.pnlParams.SetOneSet('analytique', values=self.valuesAnalytique, codeBox='param2')
        self.btnAnalytique.Enable(not self.repas)
        self.txtAnalytique.Enable(not self.repas)
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

    def OnBtnSynchro(self,event):
        # lancement de la synchronisation entre base LAN et Wan
        mess = "C'est prévu...\n\nla vie est faite d'espérance"
        wx.MessageBox(mess,"Pas encore fait")
        if event: event.Skip()

    def GetDonnees(self,**kwd):
        # rafraîchissement des données de l'Olv principal suite à changement de params
        # periode est construite dans DLG.Init les accès en cours de construction sont ignorés
        lstDonnees = []
        if hasattr(self,'periode'):
            params = self.pnlParams.GetValues()
            kwd['db'] = self.db
            lstDonnees = nust.GetEffectifs(self, **kwd)
        return lstDonnees

    def OnDblClick(self,event):
        event.Skip()
        self.pnlOlv.OnModifier(event)

    def GetTitreImpression(self):
        datedeb = xformat.DateSqlToFr(self.periode[0])
        datefin = xformat.DateSqlToFr(self.periode[1])
        tiers = "Repas en cuisine"
        if len(self.analytique) > 0 : tiers = "Camp: %s"%self.analytique.capitalize()
        return "Liste des Effectifs du %s au %s, %s"%( datedeb, datefin, tiers)

    def GereDonnees(self,**kwd):
        kwd['db'] = self.db
        nust.SetEffectifs(self,**kwd)

    def ValideSaisie(self,dlgSaisie,*args,**kwd):
        dDonnees = dlgSaisie.pnl.GetValues(fmtDD=False)
        mess = "Incohérence relevée dans les données saisies\n"
        lg = len(mess)
        if not (dDonnees['ID'] >= self.periode[0] and dDonnees['ID'] <= self.periode[1]):
            mess += "\n- La date saisie est hors période\n\nLa période a été choisie dans l'écran précédent. Corrigez\n"
        if dDonnees['midiRepas']< dDonnees['midiClients']:
            mess += "\n- S'il y a plus de clients que de repas à midi, ceux qui jeunent ne sont pas à compter\n"
        if dDonnees['soirRepas']< dDonnees['soirClients']:
            mess += "\n- S'il y a plus de clients que de repas le soir, ceux qui jeunent ne sont pas à compter\n"
        if dDonnees['prevuRepas']< dDonnees['prevuClients']:
            mess += "\n- Plus de clients que d'inscrits, n'est pas cohérent! "
        if len(mess) != lg:
            wx.MessageBox(mess,"Entrée refusée!!!",style=wx.ICON_HAND)
            return wx.NO
        return wx.OK

    def OnImprimer(self,event):
        # test de présence d'un filtre
        if len(self.ctrlOlv.innerList) != len(self.ctrlOlv.modelObjects):
            ret = wx.MessageBox('Filtre actif!\n\nDes lignes sont filtrées, seules les visibles seront rapportées',
                                'Confirmez pour continuer',style=wx.OK|wx.CANCEL)
            if ret != wx.OK: return
        # purge des lignes non valides
        self.ctrlOlv.modelObjects=[x for x in self.ctrlOlv.modelObjects]
        # réaffichage
        self.ctrlOlv.RepopulateList()
        # impression
        self.ctrlOlv.Apercu(None)
        self.isImpress = True

#------------------------ Lanceur de test  -------------------------------------------

if __name__ == '__main__':
    app = wx.App(0)
    os.chdir("..")
    dlg = DLG()
    dlg.ShowModal()
    Saisie()
    app.MainLoop()
