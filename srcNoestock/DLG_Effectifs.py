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
import srcNoelite.DB_schema            as schema
import xpy.xGestion_TableauRecherche   as xgtr
import xpy.xUTILS_Identification       as xuid
import xpy.xUTILS_SaisieParams         as xusp
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

def GetDicParams(dlg):
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
            ColumnDefn("PourTri", 'left', 60,  'dateAnsi',valueSetter=''),
            ColumnDefn("Date", 'left', 80,      'date', valueSetter=datetime.date.today(),stringConverter=xformat.FmtDate),
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

def GetDlgOptions(dlg):
    # Options du Dlg de lancement
    return {
        'style': wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        'minSize': (300, 450),
        'size': (650, 600),
        }

def GetEffectifs(params,**kwd):
    # retourne les effectifs dans la table stEffectifs
    db = kwd.get('db',None)
    nbreFiltres = kwd.get('nbreFiltres', 0)
    # en présence d'autres filtres: tout charger pour filtrer en mémoire par predicate.
    limit = ''
    if nbreFiltres == 0:
        limit = "LIMIT %d" % LIMITSQL

    where = """
                WHERE (IDdate >= '%s' AND IDdate <= '%s')"""%(params['param1']['periode'][0],params['param1']['periode'][1])
    if params['param2']['repas']: where += """
                        AND ( IDanalytique = '' )"""
    else: where += """
                        AND ( IDanalytique = '%s')"""%params['param2']['analytique']

    table = schema.DB_TABLES['stEffectifs']
    lstChamps = xformat.GetLstChamps(table)

    req = """   SELECT %s
                FROM stEffectifs
                %s 
                ORDER BY IDdate DESC
                %s ;""" % (",".join(lstChamps), where, limit)
    retour = db.ExecuterReq(req, mess='GetEffectifs')
    recordset = ()
    if retour == "ok":
        recordset = db.ResultatReq()

    # composition des données du tableau à partir du recordset
    lstDonnees = []
    for record in recordset:
        dic = xformat.ListToDict(lstChamps,record)
        ligne = [
            dic['IDdate'],
            dic['IDdate'],
            dic['midiRepas'],
            dic['midiClients'],
            dic['soirRepas'],
            dic['soirClients'],
            dic['prevuRepas'],
            dic['prevuClients'],
            dic['IDanalytique'],
            dic['modifiable'],]
        lstDonnees.append(ligne)
    return lstDonnees

#----------------------- Parties de l'écrans -----------------------------------------

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

        # variables gérées par l'écran paramètres
        self.today = datetime.date.today()
        self.periode = (None,None)
        self.repas = True
        self.analytique = ''

        # Propriétés de l'écran global type Dialog
        kwds = GetDlgOptions(self)
        kwds['autoSizer'] = False
        kwds['dicParams'] = GetDicParams(self)
        kwds['dicOlv'] = self.dicOlv
        kwds['dicPied'] = dicPied

        super().__init__(None, **kwds)
        ret = self.Init()
        if ret == wx.ID_ABORT: self.Destroy()
        self.Sizer()

    def Init(self):
        self.db = xdb.DB()

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
        self.GetDonnees()
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
        self.analytique = ''
        self.GetDonnees()

    def OnAnalytique(self,event):
        choixAnalytique = self.pnlParams.GetOneValue('analytique',codeBox='param2')
        if len(choixAnalytique) > 0:
            ix = self.valuesAnalytique.index(choixAnalytique)
            self.analytique = self.lstAnalytiques[ix][0]
        self.GetDonnees()
        if event: event.Skip()

    def OnBtnAnalytique(self,event):
        # Appel du choix d'un camp via un écran complet
        noegest = nung.Noegest(self)
        dicAnalytique = noegest.GetActivite(mode='dlg')
        codeAct = nust.MakeChoiceActivite(dicAnalytique)
        self.pnlParams.SetOneValue('analytique',codeAct,codeBox='param2')

    def OnBtnSynchro(self,event):
        # lancement de la synchronisation entre base LAN et Wan
        mess = "C'est prévu...\n\nla vie est faite d'espérance"
        wx.MessageBox(mess,"Pas encore fait")
        if event: event.Skip()

    def GetDonnees(self,**kwd):
        # rafraîchissement des données de l'Olv principal suite à changement de params
        params = self.pnlParams.GetValues()
        # alimente la grille, puis création de modelObejects pr init
        if hasattr(self,'ctrlOlv'):
            # les accès en cours de construction sont ignorés
            kwd['db'] = self.db
            lstDonnees = GetEffectifs(params, **kwd)
            self.ctrlOlv.lstDonnees = lstDonnees
            self.ctrlOlv.InitObjectListView()
            self.ctrlOlv.MAJ()

    def GetTitreImpression(self):
        datedeb = xformat.DateSqlToFr(self.periode[0])
        datefin = xformat.DateSqlToFr(self.periode[1])
        tiers = "Repas en cuisine"
        if len(self.analytique) > 0 : tiers = "Camp: %s"%self.analytique.capitalize()
        return "Liste des Effectifs du %s au %s, %s"%( datedeb, datefin, tiers)

    def GereDonnees(self,**kwd):
        kwd['db'] = self.db
        nust.GereEffectif(self,**kwd)

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
    app.MainLoop()
