#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------
# Application:     NoeStock, gestion des stocks et prix de journée
# Module:          Saisie des entrées de stocks
# Auteur:          Jacques BRUNEL 2021-02
# Licence:         Licence GNU GPL
# ------------------------------------------------------------------

import wx
import os
import datetime
import srcNoestock.UTILS_Stocks        as nus
import xpy.xGestion_TableauEditor      as xgte
import xpy.xUTILS_DB                   as xdb
from srcNoelite.DB_schema       import DB_TABLES
from xpy.outils.ObjectListView  import ColumnDefn, CellEditor
from xpy.outils                 import xformat,xbandeau,xboutons
import xpy.xGestionConfig               as xgc
import xpy.xUTILS_SaisieParams          as xusp

#---------------------- Matrices de paramétres -------------------------------------

TITRE = "Entrées en stock"
INTRO = "Gestion des entrées dans le stock, par livraison, retour ou autre "
DIC_INFOS = {
            'article': "<F4> Choix d'un article, ou saisie directe de son code",
            'qte': "L'unité est précisée dans le nom de l'article",
            'montant': "Prix remisé en €",
             }

INFO_OLV = "<Suppr> <Inser> <Ctrl C> <Ctrl V>"

# Description des paramètres à choisir en haut d'écran

class CtrlRappel(wx.Panel):
    # Exemple d'un controle pour s'insérer dans une matrice 'genre':'anyctrl', 'ctrl':'MyAnyCtrl'
    def __init__(self,parent):
        super().__init__(parent,wx.ID_ANY)
        kwd = {'label':"Rappeler\nl'antérieur",
               'name':'rappel',
               'image':wx.ArtProvider.GetBitmap(wx.ART_FIND,size=(24,24)),
               'help':"Pour reprendre une saisie antérieurement validée",
               'size' : (130,40)}
        self.btn = xboutons.BTN_action(self,**kwd)
        #self.SetMinSize((40,50))
        self.Sizer()

    def Sizer(self):
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.btn,1,wx.EXPAND, 0)
        self.SetSizer(box)

    def SetValue(self,value):
        self.value = value

    def GetValue(self):
        return self.value

    def Set(self,values):
        # valeurs multiples
        return

MATRICE_PARAMS = {
("param1", "Paramètres"): [
    {'name': 'origine', 'genre': 'Choice', 'label': "Nature d'entrée",
                    'help': "Le choix de la nature modifie certains contrôles",
                    'value':0, 'values':['achat livraison', 'retour camp', 'od autre'],
                    'ctrlAction': 'OnOrigine',
                    'size':(200,30),
                    'txtSize': 90},
    {'name': 'date', 'genre': 'Texte', 'label': "Date d'entrée",
                    'help': "%s\n%s\n%s"%("Saisie JJMMAA ou JJMMAAAA possible.",
                                          "Les séparateurs ne sont pas obligatoires.",
                                          "Saisissez la date de l'entrée en stock sans séparateurs, "),
                    'value':xformat.DatetimeToStr(datetime.date.today()),
                    'ctrlAction': 'OnDate',
                    'size':(200,30),
                    'txtSize': 90},
    ],
("param2", "Comptes"): [
    {'name': 'fournisseur', 'genre': 'Combo', 'label': 'Fournisseur',
                    'help': "Il s'agit de la provenance de la marchandise qui déterminera le compte crédité, ce peut être un camp",
                    'value':0,'values':[''],
                    'ctrlAction':'OnFournisseur',
                     'btnLabel': "...", 'btnHelp': "Cliquez pour choisir un compte pour l'origine",
                     'btnAction': 'OnBtnFournisseur',
                    'size':(250,30),
                    'txtSize': 70,
     },
    {'name': 'destinataire', 'genre': 'Choice', 'label': 'Activité',
                    'ctrlAction':'OnDestinataire',
                    'help': "Il s'agit de la destination de la marchandise imputé à son débit",
                    'value':'','values':[''],
                    'btnLabel': "...", 'btnHelp': "Cliquez pour choisi un compte de destination",
                    'btnAction': 'OnBtnDestinataire',
                    'size':(250,30),
                    'txtSize': 70,}
],
("param3", "saisie"): [
    {'name': 'ht_ttc', 'genre': 'Choice', 'label': 'Saisie',
                     'help': "Choix du mode de saisie HT ou TTC selon le plus facile pour vous",
                     'value': 0, 'values': ['TTC', 'HT'],
                     'txtSize': 40,
                     'ctrlMaxSize': (130,30),
                     },
    {'name': 'vide','genre':None,}
    ],

("param4", "Compléments"): [
    {'name': 'rappel', 'genre': 'anyctrl','label': ' ',
                     'txtSize': 20,
                        'ctrlMaxSize':(150,50),
                     'ctrl': CtrlRappel,
                     'ctrlAction': 'OnBtnRappel',
                     },
    ],
}

def GetParamsOptions(dlg):
    return {
                'name':"PNL_params",
                'matrice':MATRICE_PARAMS,
                'lblBox':None,
                'boxesSizes': [(300, 90), (400, 90), (100, 90), (100, 90)],
                'pathdata':"srcNoelite/Data",
                'nomfichier':"stparams",
                'nomgroupe':"entrees",
            }

def GetBoutons(dlg):
    return  [
                {'name': 'btnImp', 'label': "Imprimer\npour contrôle",
                    'help': "Cliquez ici pour imprimer et enregistrer la saisie de l'entrée en stock",
                    'size': (120, 35), 'image': wx.ART_PRINT,'onBtn':dlg.OnImprimer},
                {'name':'btnOK','ID':wx.ID_ANY,'label':"Quitter",'help':"Cliquez ici pour fermer la fenêtre",
                    'size':(120,35),'image':"xpy/Images/32x32/Quitter.png",'onBtn':dlg.OnClose}
            ]

def GetOlvColonnes(dlg):
    # retourne la liste des colonnes de l'écran principal
    return [
            ColumnDefn("ID", 'centre', 0, 'IDmouvementt',
                       isEditable=False),
            ColumnDefn("Article", 'left', 200, 'article', valueSetter="",isSpaceFilling=True),
            ColumnDefn("Quantité", 'right', 110, 'qte', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal),
            ColumnDefn("Pr.Unit.", 'right', 110, 'prixUnit', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal),
            ColumnDefn("MttHT", 'right', 110, 'mttHT', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal, isEditable=False),
            ColumnDefn("MttTTC", 'right', 110, 'mttTTC', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal, isEditable=False),
            ColumnDefn("Qté stock", 'right', 110, 'qteStock', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal, isEditable=False),
            ColumnDefn("Rations", 'right', 110, 'rations', isSpaceFilling=False, valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal, isEditable=False),
            ]

def GetOlvCodesSup(dlg):
    return ['origine','date','fournisseur','analytique','ht_ttc']

def GetOlvOptions(dlg):
    # retourne les paramètres de l'OLV del'écran général
    champOrigine = [x for x in DB_TABLES['stMouvements'] if x[0] == 'origine'][0]
    choixOrigine = champOrigine[2].split(';')
    return {
            'choicesorigine': choixOrigine,
            'checkColonne': False,
            'recherche': True,
            'minSize': (600, 100),
            'dictColFooter': {"article": {"mode": "nombre", "alignement": wx.ALIGN_CENTER},
                                  "mttHT": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                                  "mttTTC": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                                  },
    }

def GetDlgOptions(dlg):
    return {
        'style': wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        'minSize': (700, 450),
        'size': (850, 550),
        }

    #----------------------- Parties de l'écrans -----------------------------------------

class PNL_params(xgc.PNL_paramsLocaux):
    #panel de paramètres de l'application
    def __init__(self, parent, **kwds):
        self.parent = parent
        #('pos','size','style','name','matrice','donnees','lblBox')
        kwds = GetParamsOptions(self)
        super().__init__(parent, **kwds)
        if hasattr(parent,'lanceur'):
            self.lanceur = parent.lanceur
        else: self.lanceur = parent

        self.Init()

class PNL_corpsReglements(xgte.PNL_corps):
    #panel olv avec habillage optionnel pour des boutons actions (à droite) des infos (bas gauche) et boutons sorties
    def __init__(self, parent, dicOlv,*args, **kwds):
        xgte.PNL_corps.__init__(self,parent,dicOlv,*args,**kwds)
        self.ctrlOlv.Choices={}
        self.lstNewReglements = []
        self.flagSkipEdit = False
        self.oldRow = None

    def InitTrackVierge(self,track,modelObject):
        # reprise de la valeur 'mode' et date de la ligne précédente
        if len(modelObject)>0:
            trackN1 = modelObject[-1]
            track.mode = trackN1.mode
            track.date = trackN1.date
        track.creer = True


    def OnCtrlV(self,track):
        # raz de certains champs à recomposer
        (track.IDreglement, track.date, track.IDprestation, track.IDpiece,track.compta) = (None,)*5

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
        if code == 'IDfamille':
            try:
                value = int(value)
            except:
                self.flagSkipEdit = False
                return
            track.IDfamille = value

        if code == 'mode':
            # rend non éditable les champs suivants si pas d'option possible
            IDmode = self.parent.dicModesChoices[value]['IDmode']
            emetteurs = sorted(self.parent.dlEmetteurs[IDmode])
            if len(emetteurs) == 0:
                isedit = False
                track.emetteur = None
                track.numero = None
            else: isedit = True
            self.ctrlOlv.columns[self.ctrlOlv.lstCodesColonnes.index('emetteur')].isEditable = isedit
            self.ctrlOlv.columns[self.ctrlOlv.lstCodesColonnes.index('numero')].isEditable = isedit



        # enlève l'info de bas d'écran
        self.parent.pnlPied.SetItemsInfos( INFO_OLV,wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)))
        self.flagSkipEdit = False

    def ValideLigne(self,code,track):
        nus.ValideLigne(self.Parent.db,track)

    def OnEditFunctionKeys(self,event):
        row, col = self.ctrlOlv.cellBeingEdited
        code = self.ctrlOlv.lstCodesColonnes[col]
        if event.GetKeyCode() == wx.WXK_F4 and code == 'IDfamille':
            # Choix famille
            IDfamille = nus.GetFamille(self.parent.db)
            self.OnEditFinishing('IDfamille',IDfamille)
            self.ctrlOlv.GetObjectAt(row).IDfamille = IDfamille

    def OnDelete(self,noligne,track,parent=None):
        pass

class PNL_pied(xgte.PNL_pied):
    #panel infos (gauche) et boutons sorties(droite)
    def __init__(self, parent, dicPied, **kwds):
        xgte.PNL_pied.__init__(self,parent, dicPied, **kwds)

class DLG(xusp.DLG_vide):
    # ------------------- Composition de l'écran de gestion----------
    def __init__(self):
        #listArbo = os.path.abspath(__file__).split("\\")
        #titre = listArbo[-1:][0] + "/" + self.__class__.__name__
        kwds = GetDlgOptions(self)
        #super().__init__(None,title=titre, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        super().__init__(None,**kwds)
        self.lanceur = self
        self.dicOlv = {'lstColonnes': GetOlvColonnes(self)}
        self.dicOlv.update({'lstCodesSup': GetOlvCodesSup(self)})
        self.dicOlv.update(GetOlvOptions(self))
        ret = self.Init()
        if ret == wx.ID_ABORT: self.Destroy()

    def Init(self):
        self.db = xdb.DB()
        # définition de l'OLV
        self.choicesDiffere = self.dicOlv.pop('choicesDiffere',[])
        #self.SetSize(size)
        self.depotOrigine = []
        self.ctrlOlv = None
        self.withDepot = True
        # récup des modesReglements nécessaires pour passer du texte à un ID d'un mode ayant un mot en commun
        choicesMode = []
        self.libelleDefaut = ''
        for colonne in self.dicOlv['lstColonnes']:
            if 'mode' in colonne.valueGetter:
                choicesMode = colonne.choices
            if 'libelle' in colonne.valueGetter:
                self.libelleDefaut = colonne.valueSetter

                
        # appel de modes des fournisseurs
        self.ddModesRegl = nus.GetFournisseurs(self.db)
        if self.ddModesRegl == wx.ID_ABORT:
            return wx.ID_ABORT

        # constitution d'un dictionnaire de modes de règlements possibles par choices de mode (vrt chq esp)
        self.dicModesChoices = {}
        for item in choicesMode + self.choicesDiffere:
            # les descriptifs de modes de règlements ne doivent pas avoir des mots en commun
            lstMots = item.split(' ')
            self.dicModesChoices[item]={'lstMots':lstMots}
            ok = False
            for IDmode, dicMode in self.ddModesRegl.items():
                # pour un mot dans les choices
                for mot in lstMots:
                    # présent dans le label d'un mode de règlement
                    if mot.lower() in dicMode['label'].lower():
                        self.dicModesChoices[item].update(dicMode)
                        dicMode['choice'] = item
                        ok = True
                        break
                if ok: break
            if not ok:
                wx.MessageBox("Problème mode de règlement\n\n'%s' n'a aucun mot commun avec un mode de règlement paramétré!"%item)


        # boutons de bas d'écran - infos: texte ou objet window.  Les infos sont  placées en bas à gauche
        self.txtInfo =  "Ici de l'info apparaîtra selon le contexte de la grille de saisie"
        lstInfos = [ wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)),self.txtInfo]
        dicPied = {'lstBtns': GetBoutons(self), "lstInfos": lstInfos}

        # lancement de l'écran en blocs principaux
        self.pnlBandeau = xbandeau.Bandeau(self,TITRE,INTRO,nomImage="xpy/Images/32x32/Matth.png")
        self.pnlParams = PNL_params(self)
        self.pnlOlv = PNL_corpsReglements(self, self.dicOlv)
        self.pnlPied = PNL_pied(self, dicPied)
        self.ctrlOlv = self.pnlOlv.ctrlOlv

        # la grille est modifiée selon la coche sans dépôt
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
        self.SetSizer(sizer_base)
        self.CenterOnScreen()

    # ------------------- Gestion des actions -----------------------

    def SetTitreImpression(self):
        IDdepot = self.pnlParams.ctrlRef.GetValue()
        ctrl = self.pnlParams.ctrlBanque
        banque = ctrl.GetString(ctrl.GetSelection())
        dte = self.pnlParams.ctrlDate.GetValue()
        if not IDdepot: IDdepot = "___"
        self.ctrlOlv.titreImpression = "REGLEMENTS Dépot No %s, du %s, banque: %s "%(IDdepot,dte,banque)

    def InitOlv(self):
        self.ctrlOlv.lstColonnes = GetOlvColonnes(self)
        self.ctrlOlv.lstCodesColonnes = self.ctrlOlv.formerCodeColonnes()
        self.ctrlOlv.InitObjectListView()
        self.Refresh()

    def OnOrigine(self,event):
        origine = self.GetPnlCtrl('origine')
        #'achat livraison', 'retour camp', 'od autre'
        dicLib = {'acha':'Fournisseur', 'reto':'Code Camp', 'od a':'Code Comptable'}
        if origine[:4] == "acha":
            pass



    def OnDate(self,event):
        self.InitOlv()
    def OnFournisseur(self,event):
        self.InitOlv()
    def OnBtnFournisseur(self,event):
        self.InitOlv()
    def OnDestinataire(self,event):
        self.InitOlv()
    def OnBtnDestinataire(self,event):
        self.InitOlv()
    def OnBtnRappel(self,event):
        print(wx.Bell())
        self.InitOlv()

    def OnRaz(self,event):
        # effacement des lignes sur l'écran
        self.pnlParams.ctrlRef.SetValue('')
        self.ctrlOlv.lstDonnees = []
        self.ctrlOlv.MAJ()
        self.pnlPied.SetItemsInfos(INFO_OLV, wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)))
        self.pnlOlv.Refresh()

    def OnImprimer(self,event):
        # test de présence d'écritures non valides
        lstNonValides = [x for x in self.ctrlOlv.modelObjects if not x.valide and x.IDreglement]
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
        self.SetTitreImpression()
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
