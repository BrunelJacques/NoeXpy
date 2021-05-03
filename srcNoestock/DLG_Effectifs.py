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

# Description des paramètres à choisir en haut d'écran

class CtrlSynchro(wx.Panel):
    # controle inséré dans la matrice_params qui suit. De genre AnyCtrl pour n'utiliser que le bind bouton
    def __init__(self,parent):
        super().__init__(parent,wx.ID_ANY)
        kwd = {'label':"Synchroniser\nle prévu",
               'name':'synchro',
               'image':wx.ArtProvider.GetBitmap(wx.ART_FIND,size=(24,24)),
               'help':"Pour reprendre les effectifs prévus par synchronisation avec les incriptions",
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

MATRICE_PARAMS = {
("param1", "Paramètres période"): [
    {'name': 'periode', 'genre': 'anyctrl', 'label': " Période ",
                    'help': "%s\n%s\n%s"%("Saisie JJMMAA ou JJMMAAAA possible.",
                                          "Les séparateurs ne sont pas obligatoires en saisie.",
                                          "Saisissez début et fin de la période, "),
                    'ctrl':xdates.CTRL_Periode,
                    'size':(200,80),},
    ],
("param2", "Comptes"): [
    {'name': 'repas', 'genre': 'Check', 'label': 'Repas préparés en cuisine',
                    'help': "Les repas préparés en cuisine ne sont pas différenciés par camp servi, seules les sorties identifiés sont affectées aux camps",
                    'value':True,
                    'ctrlAction':'OnRepas',
                    'size':(250,30),
                    'txtSize': 70,
     },
    {'name': 'analytique', 'genre': 'Choice', 'label': 'Activité',
                    'ctrlAction':'OnAnalytique',
                    'help': "Il s'agit de l'activité qui a endossé la charge de la sortie",
                    'value':'','values':[''],
                    'btnLabel': "...", 'btnHelp': "Cliquez pour choisir l'activité de destination des mouvements",
                    'btnAction': 'OnBtnAnalytique',
                    'size':(250,30),
                    'txtSize': 70,}
],
("param3", ""): [
    {'name': 'vide','genre':None,}
    ],
("param4", "Boutons actions"): [
    {'name': 'rappel', 'genre': 'anyctrl','label': ' ',
                     'txtSize': 20,
                        'ctrlMaxSize':(150,50),
                     'ctrl': CtrlSynchro,
                     'ctrlAction': 'OnBtnSynchro',
                     },
    ],
}

def GetDicParams(dlg):
    matrice = MATRICE_PARAMS
    return {
                'name':"PNL_params",
                'matrice':matrice,
                'lblBox':None,
                'boxesSizes': [(300, 90), (400, 90), (100, 90), (100, 90)],
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
                    'size':(120,35),'image':"xpy/Images/32x32/Quitter.png",'onBtn':dlg.OnClose}
            ]

def GetOlvColonnes(dlg):
    # retourne la liste des colonnes de l'écran principal, valueGetter correspond aux champ des tables ou calculs
    return [
            ColumnDefn("PourTri", 'left', 60,  'dateAnsi',valueSetter='',),
            ColumnDefn("Date", 'left', 60,      'date', valueSetter=datetime.date.today()),
            ColumnDefn("RepasMidi", 'right', 30, 'midiRepas', valueSetter=0, stringConverter=xformat.FmtInt),
            ColumnDefn("ClientsMidi", 'right', 30,'midiclients', valueSetter=0, stringConverter=xformat.FmtInt),
            ColumnDefn("RepasSoir", 'right', 30,   'soirRepas', valueSetter=0, stringConverter=xformat.FmtInt),
            ColumnDefn("ClientsSoir", 'right', 30, 'soirClients', valueSetter=0, stringConverter=xformat.FmtInt),
            ColumnDefn("PrévuInscrits", 'right', 30, 'prevuRepas', valueSetter=0, stringConverter=xformat.FmtInt),
            ColumnDefn("PrévuClients", 'right', 30, 'prevuClients', valueSetter=0, stringConverter=xformat.FmtInt),
            ]

def GetOlvCodesSup():
    # codes dans les tracks, mais pas dans les colonnes, ces attributs sont non visibles à l'écran
    return ['analytique',]

def GetOlvOptions(dlg):
    # Options paramètres de l'OLV ds PNLcorps
    return {
            'checkColonne': False,
            'recherche': True,
            'minSize': (600, 100),
            'getDonnees': GetEffectifs,
            'dictColFooter': {"date": {"mode": "nombre", "alignement": wx.ALIGN_CENTER},
                                  "repasMidi": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                                  "clientsMidi": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                                  "prevuInscrits": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                                  "prevuClients": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                                  },
    }

def GetDlgOptions(dlg):
    # Options du Dlg de lancement
    return {
        'style': wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        'minSize': (700, 450),
        'size': (850, 550),
        }

def GetEffectifs(olv,**kwd):
    # ajoute les données effectifs
    dicOlv = kwd.get('dicOlv', None)
    db = kwd.get('db', None)
    nbreFiltres = kwd.pop('nbreFiltres', 0)

    # en présence d'autres filtres: tout charger pour filtrer en mémoire par predicate.
    # cf self.listeFiltresColonnes  à gérer avec champs au lieu de codes colonnes
    limit = ''
    if nbreFiltres == 0:
        limit = "LIMIT %d" % LIMITSQL

    where = ""
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
            dic['IDanalytique'],]
        lstDonnees.append(ligne)
    dicOlv['lstDonnees'] = lstDonnees
    return lstDonnees

#----------------------- Parties de l'écrans -----------------------------------------

class PNL_params(xgtr.PNL_params):
    #panel de paramètres de l'application
    def __init__(self, parent, **kwds):
        self.parent = parent
        #('pos','size','style','name','matrice','donnees','lblBox')
        kwds = GetDicParams(parent)
        super().__init__(parent, **kwds)
        if hasattr(parent,'lanceur'):
            self.lanceur = parent.lanceur
        else: self.lanceur = parent


class DLG(xusp.DLG_vide):
    # ------------------- Composition de l'écran de gestion----------
    def __init__(self,sens='sorties'):
        self.sens = sens
        kwds = GetDlgOptions(self)
        super().__init__(None,**kwds)
        self.lanceur = self
        self.dicOlv = {'lstColonnes': GetOlvColonnes(self)}
        self.dicOlv.update({'lstCodesSup': GetOlvCodesSup()})
        self.dicOlv.update(GetOlvOptions(self))
        self.ordi = xuid.GetNomOrdi()
        self.today = datetime.date.today()
        self.analytique = ''
        self.fournisseur = ''
        self.ht_ttc = 'TTC'
        ret = self.Init()
        if ret == wx.ID_ABORT: self.Destroy()

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

        # boutons de bas d'écran - infos: texte ou objet window.  Les infos sont  placées en bas à gauche
        self.txtInfo =  "Ici de l'info apparaîtra selon le contexte de la grille de saisie"
        lstInfos = [ wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)),self.txtInfo]
        dicPied = {'lstBtns': GetBoutons(self), "lstInfos": lstInfos}

        # lancement de l'écran en blocs principaux
        if self.sens == 'entrees':
            self.pnlBandeau = xbandeau.Bandeau(self,TITRE,INTRO, hauteur=20,
                                               nomImage="xpy/Images/80x80/Entree.png",
                                               sizeImage=(60,40))
            self.pnlBandeau.SetBackgroundColour(wx.Colour(220, 250, 220))
        else:
            self.pnlBandeau = xbandeau.Bandeau(self,TITRE,INTRO, hauteur=20,
                                                nomImage="xpy/Images/80x80/Sortie.png",
                                                sizeImage=(60,40))
            self.pnlBandeau.SetBackgroundColour(wx.Colour(250, 220, 220))
        self.pnlParams = PNL_params(self)
        self.pnlOlv = xgtr.PNL_corps(self, self.dicOlv)
        self.pnlPied = xgtr.PNL_pied(self, dicPied)
        self.ctrlOlv = self.pnlOlv.ctrlOlv

        # charger les valeurs de pnl_params
        self.pnlParams.SetOneSet('fournisseur',values=nust.SqlFournisseurs(self.db),codeBox='param2')
        self.lstAnalytiques = nust.SqlAnalytiques(self.db,'ACTIVITES')
        self.valuesAnalytique = [nust.MakeChoiceActivite(x) for x in self.lstAnalytiques]
        self.pnlParams.SetOneSet('analytique',values=self.valuesAnalytique,codeBox='param2')

        self.Bind(wx.EVT_CLOSE,self.OnClose)
        self.Sizer()

    def Sizer(self):
        sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=0, hgap=0)
        sizer_base.Add(self.pnlBandeau, 0, wx.TOP | wx.EXPAND, 3)
        sizer_base.Add(self.pnlParams, 0, wx.TOP | wx.EXPAND, 3)
        sizer_base.Add(self.pnlOlv, 1, wx.TOP | wx.EXPAND, 3)
        sizer_base.Add(self.pnlPied, 0, wx.ALL | wx.EXPAND, 3)
        sizer_base.AddGrowableCol(0)
        sizer_base.AddGrowableRow(2)
        self.CenterOnScreen()
        self.SetSizerAndFit(sizer_base)
        self.CenterOnScreen()

    # ------------------- Gestion des actions -----------------------

    def InitOlv(self):
        self.ctrlOlv.lstColonnes = GetOlvColonnes(self)
        self.ctrlOlv.lstCodesColonnes = self.ctrlOlv.GetLstCodesColonnes()
        self.ctrlOlv.InitObjectListView()
        self.Refresh()

    def OnPeriode(self,event):
        periode = self.GetPeriode(fr=True)
        self.pnlParams.SetOneValue('periode',valeur=periode,codeBox='param1')
        self.GetDonnees()
        if event: event.Skip()

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

    def OnRepas(self,event):
        self.GetDonnees()
        if event: event.Skip()


    def OnBtnSynchro(self,event):
        # lancement de la recherche d'un lot antérieur, on enlève le cellEdit pour éviter l'écho des clics
        self.ctrlOlv.cellEditMode = self.ctrlOlv.CELLEDIT_NONE
        # choix d'un lot de lignes définies par des params
        dicParams = nust.GetSynchro(self)
        self.ctrlOlv.cellEditMode = self.ctrlOlv.CELLEDIT_DOUBLECLICK        # gestion du retour du choix dépot
        if not 'periode' in dicParams.keys(): return
        self.GetDonnees(dicParams)
        if event: event.Skip()

    def GetDonnees(self,dicParams=None):
        # rafraîchissement des données de l'Olv principal suite à changement de params
        kwd = {'dicOlv': self.dicOlv,}
        lstDonnees = GetEffectifs(self.ctrlOlv,**kwd)
        # alimente la grille, puis création de modelObejects pr init
        self.InitOlv()

    def GetTitreImpression(self):
        tiers = ''
        if self.fournisseur: tiers += ", Fournisseur: %s"%self.fournisseur.capitalize()
        if self.analytique: tiers += ", Camp: %s"%self.analytique.capitalize()
        date = xformat.DateSqlToFr(self.periode)
        return "Mouvements STOCKS %s du %s, %s"%(self.sens, date, tiers)

    def OnImprimer(self,event):
        # test de présence d'écritures non valides
        lstNonValides = [x for x in self.ctrlOlv.modelObjects if not x.valide and x.IDmouvement]
        if len(lstNonValides) > 0:
            ret = wx.MessageBox('Présence de lignes non valides!\n\nCes lignes seront détruites avant impression',
                                'Confirmez pour continuer', style=wx.OK | wx.CANCEL)
            if ret != wx.OK: return
        # test de présence d'un filtre
        if len(self.ctrlOlv.innerList) != len(self.ctrlOlv.modelObjects):
            ret = wx.MessageBox('Filtre actif!\n\nDes lignes sont filtrées, seules les visibles seront rapportées',
                                'Confirmez pour continuer',style=wx.OK|wx.CANCEL)
            if ret != wx.OK: return
        # purge des lignes non valides
        self.ctrlOlv.modelObjects=[x for x in self.ctrlOlv.modelObjects if hasattr(x,'valide') and x.valide]
        # réaffichage
        self.ctrlOlv.RepopulateList()
        # impression
        self.ctrlOlv.Apercu(None)
        self.isImpress = True

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
