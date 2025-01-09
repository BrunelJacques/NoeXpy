#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------
# Application:     Noelite et autre pouvant lancer ce module partagé
# Module:          Gestion des codes analytiques
# Auteur:          Jacques BRUNEL 2024-04
# Licence:         Licence GNU GPL
# ------------------------------------------------------------------

import wx
import os
import datetime
import srcNoestock.UTILS_Stocks        as nust
import srcNoelite.UTILS_Noelite        as nung
import xpy.ObjectListView.xGTE as xGTE
import xpy.xUTILS_Identification       as xuid
import xpy.xUTILS_DB                   as xdb
from xpy.ObjectListView.ObjectListView import ColumnDefn
from xpy.outils                 import xformat, xdates

#---------------------- Matrices de paramétres -------------------------------------

DIC_BANDEAU = {'titre': "Correction d'écritures en lot",
        'texte': "Les nouvelles valeurs saisies ci-dessous s'appliqueront aux écritures en sortie d'écran"+
                    "\n sur les seules écritures cochées ou sur toutes si aucune n'est cochée",
        'hauteur': 20,
        'sizeImage': (32, 32),
        'nomImage':"xpy/Images/32x32/Depannage.png",
        'bgColor': (230, 220, 240), }

DIC_INFOS = {
        'IDanalytique': "Ce code est attribué par Matthania, clé d'accès 8car",
        'abrege': "nom court de 16 caractères maxi",
        'nom': "nom détaillé 200 caractères possibles",
        'params': "Infos complémentaires sous forme balise xml, dictionnaire à respecter",
        'axe': "16 caractères, non modifiable",
         }

INFO_OLV = "Selectionner un lot d'écriture pour les modifier, sinon toutes le seront"

# Description des paramètres

VALUESORIGINES = ['--NoChange--','achat livraison', 'retour camp', 'od entrée',
                  'vers cuisine', 'revente ou camp', 'od sortie']
CODESORIGINES = [None,'achat','retour','od_in','repas', 'camp', 'od_out']
SENS =          [1,     1,      1,         1,     -1,     -1,      -1]

MATRICE_PARAMS = {
    ("param1", "Origine-Date"): [
        {'name': 'origine', 'genre': 'Choice', 'label': "Nature du mouvement",
         'help': "Le choix de la nature détermine le sens de l'écriture, il peut s'inverser",
         'value': 0, 'values': VALUESORIGINES,
         'ctrlAction': 'OnOrigine',
         'txtSize': 130},

        {'name': 'date', 'genre': 'anyctrl', 'label': "Date du mouvement",
         'ctrl': xdates.CTRL_SaisieDateAnnuel,
         'help': "%s\n%s\n%s" % ("Saisie JJMMAA ou JJMMAAAA possible.",
                                 "Les séparateurs ne sont pas obligatoires en saisie.",
                                 "Saisissez la date du mouvement de stock sans séparateurs, "),
         'value': "--NoChange--",
         'ctrlAction': 'OnDate',
         'ctrlSize': (300,40),
         'txtSize': 125},
    ],
    ("param2", "Comptes"): [
        {'name': 'fournisseur', 'genre': 'Combo', 'label': 'Fournisseur',
         'help': "La saisie d'un fournisseurfacilite les commandes par fournisseur",
         'value': 0, 'values': ['--NoChange--'],
         'ctrlAction': 'OnFournisseur',
         'btnLabel': "...", 'btnHelp': "Cliquez pour choisir un compte pour l'origine",
         'btnAction': 'OnBtnFournisseur',
         'txtSize': 80,
         'ctrlSize': (500,30),
         'ctrlMinSize': (200,30),
         },
        {'name': 'analytique', 'genre': 'Choice', 'label': 'Activité',
         'ctrlAction': 'OnAnalytique',
         'help': "Il s'agit de l'activité qui a endossé la charge de la sortie",
         'value': '--NoChange--', 'values': [''],
         'btnLabel': "...",
         'btnHelp': "Cliquez pour choisir l'activité de destination des mouvements",
         'btnAction': 'OnBtnAnalytique',
         'txtSize': 80,
         'ctrlSize': (200,30),
        },
    ],
    ("param3", "Repas"): [
        {'name': 'repas', 'genre': 'Combo', 'label': 'Repas',
         'help': "La saisie du repas n'a de sens que pour les sorties cuisine ou od_out",
         'value': 0, 'values': ['--NoChange--'],
         'ctrlAction': 'OnFournisseur',
         'btnLabel': "...", 'btnHelp': "Cliquez pour choisir un compte pour l'origine",
         'btnAction': 'OnBtnFournisseur',
         'size': (250, 40),
         'ctrlMinSize': (250,30),
         'txtSize': 50,
         },
        {'name': '', 'genre': None, }
    ],
    ("espace", ""): [
        {'name': 'vide', 'genre': None, }
    ],
}

def GetBoutons(dlg):
    return  [
        {'name': 'btnImp', 'label': "Imprimer\npour contrôle",
            'help': "Cliquez ici pour imprimer et enregistrer la saisie de l'entrée en stock",
            'size': (120, 35), 'image': wx.ART_PRINT,'onBtn':dlg.OnImprimer},
        {'name':'btnOK','ID':wx.ID_OK,'label':"Enregistrer\n et Fermer",'help':"Cliquez ici pour sortir et corriger",
            'size':(120,35),'image':"xpy/Images/32x32/Actualiser.png",'onBtn':dlg.OnAction},
        {'name': 'btnAbandon', 'ID': wx.ID_CANCEL, 'label': "Abandon",
         'help': "Cliquez ici pour fermer sans modifs",
         'size': (120, 36), 'image': "xpy/Images/16x16/Abandon.png",
         'onBtn': dlg.OnFermer},
    ]

def GetDicPnlParams(dlg):
    return {
                'name':"PNL_params",
                'matrice':MATRICE_PARAMS,
                'dicBandeau':DIC_BANDEAU,
                'lblBox': False,
                'boxesSizes': [(280, 65),None,(200, 60),None],
            }

def GetOlvColonnes(dlg):
    # retourne la liste des colonnes de l'écran principal, valueGetter correspond aux champ des tables ou calculs
    lstCol = [
            ColumnDefn("ID", 'centre', 0, 'IDmouvement'),
            ColumnDefn("Nature", 'left', 70, 'origine',),
            ColumnDefn("Date Mvt", 'left', 80, 'date',valueSetter=datetime.date(1900,1,1),
                        stringConverter=xformat.FmtDate),
            ColumnDefn("Camp", 'left', 40, 'analytique',),
            ColumnDefn("Repas", 'left', 60, 'repas',),
            ColumnDefn("Article", 'left', 200, 'IDarticle', valueSetter="",isSpaceFilling=True),
            ColumnDefn("Quantité", 'right', 80, 'qte',  valueSetter=0.0,
                                stringConverter=xformat.FmtQte),
            ColumnDefn("Prix Unit.", 'right', 80, 'pxUn',  valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal),
            ColumnDefn("Mtt TTC", 'right', 80, 'mttTTC',  valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal, ),
            ColumnDefn("Coût Ration", 'right', 80, 'pxRation',  valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal, ),
            ColumnDefn("Nbre Rations", 'right', 80, 'nbRations',  valueSetter=0.0,
                                stringConverter=xformat.FmtDecimal, ),
            ColumnDefn("Fournisseur", 'left', 170, 'fournisseur', isSpaceFilling=True ),
            ColumnDefn("Saisie le", 'left', 80, 'date', valueSetter=datetime.date(1900, 1, 1),
                        stringConverter=xformat.FmtDate),
            ColumnDefn("par Ordinateur", 'left', 50, 'ordi',isSpaceFilling=True ),
    ]
    return lstCol

def GetOlvOptions(dlg):
    # Options paramètres de l'OLV ds PNLcorps
    return {
        'recherche': True,
        'autoAddRow': False,
        'checkColonne': True,
        'recherche': True,
        'toutCocher':True,
        'toutDecocher':True,
        'msgIfEmpty': "Aucune ligne n'a été transmise au lancement",
        'dictColFooter': {"IDarticle": {"mode": "nombre", "alignement": wx.ALIGN_CENTER},
                          "qte": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                          "mttHT": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                          "mttTTC": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                          },
    }

def GetDlgOptions(dlg):
    # Options du Dlg de lancement
    return {
        'minSize': (800, 450),
        'size': (1200, 800),
        'autoSizer': True,
    }

    #----------------------- Parties de l'écrans -----------------------------------------


class DLG(xGTE.DLG_tableau):
    # ------------------- Composition de l'écran de gestion----------
    def __init__(self,date=None,**kwd):
        kwds = GetDlgOptions(self)
        self.dicOlv = {'lstColonnes': GetOlvColonnes(self)}
        self.dicOlv.update(GetOlvOptions(self))
        self.checkColonne = self.dicOlv.get('checkColonne',False)
        self.dicOlv['lstCodes'] = xformat.GetCodesColonnes(GetOlvColonnes(self))
        self.db = xdb.DB()
        self.dicOlv['db'] = self.db

        # boutons de bas d'écran - infos: texte ou objet window.  Les infos sont  placées en bas à gauche
        lstInfos = [ wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)),INFO_OLV]
        dicPied = {'lstBtns': GetBoutons(self), "lstInfos": lstInfos}

        # Propriétés de l'écran global type Dialog
        kwds['dicParams'] = GetDicPnlParams(self)
        kwds['dicOlv'] = self.dicOlv
        kwds['dicPied'] = dicPied
        self.db = xdb.DB()
        kwds['db'] = self.db

        super().__init__(None, **kwds)

        self.ordi = xuid.GetNomOrdi()
        self.today = datetime.date.today()
        self.date = date

        ret = self.Init()
        if ret == wx.ID_ABORT: self.Destroy()
        self.ctrlOlv.cellEditMode = self.ctrlOlv.CELLEDIT_NONE
        # appel des données
        self.oldParams = None
        self.GetDonnees()

    def Init(self):
        self.Bind(wx.EVT_CLOSE, self.OnFermer)
        self.InitOlv()

    # ------------------- Gestion des actions -----------------------

    def InitOlv(self):
        self.ctrlOlv.lstColonnes = GetOlvColonnes(self)
        self.ctrlOlv.lstCodesColonnes = self.ctrlOlv.GetLstCodesColonnes()
        self.ctrlOlv.InitObjectListView()

    def GetDonnees(self,dParams=None):
        # test si les paramètres ont changé
        if not dParams:
            dParams = self.pnlParams.GetValues(fmtDD=False)
        idem = True
        if self.oldParams == None :
            idem = False
        else:
            for key in ('axe',):
                if not key in self.oldParams: idem = False
                elif not key in dParams: idem = False
                elif self.oldParams[key] != dParams[key]: idem = False
        if idem : return

        attente = wx.BusyInfo("Recherche des données...", None)
        # appel des données de l'Olv principal à éditer
        lstDonnees = []

        # alimente la grille, puis création de modelObejects pr init
        self.ctrlOlv.lstDonnees = lstDonnees
        self.ctrlOlv.MAJ()
        self.oldParams = None
        del attente

    # gestion des actions ctrl
    def OnOrigine(self, event):
        if event:
            self.ctrlOlv.lstDonnees = []
            self.oldParams = {}
        self.lstOrigines = self.GetOrigines()
        self.dicOlv.update({'lstColonnes': GetOlvColonnes(self)})

        # grise les ctrl inutiles
        def setEnable(namePnlCtrl, flag):
            pnlCtrl = self.pnlParams.GetPnlCtrl(namePnlCtrl, codebox='param2')
            pnlCtrl.txt.Enable(flag)
            pnlCtrl.ctrl.Enable(flag)
            pnlCtrl.btn.Enable(flag)

        # 'achat livraison', 'retour camp', 'od_in'
        if 'achat' in self.lstOrigines:
            setEnable('fournisseur', True)
            setEnable('analytique', False)
            self.analytique = '00'
            self.pnlParams.SetOneValue('analytique', "", codeBox='param2')
        elif ('retour' in self.lstOrigines) or ('camp' in self.lstOrigines):
            setEnable('fournisseur', False)
            self.fournisseur = ''
            self.pnlParams.SetOneValue('fournisseur', "", codeBox='param2')
            setEnable('analytique', True)
            if len(self.valuesAnalytiques) > 0:
                self.pnlParams.SetOneValue('analytique', self.valuesAnalytiques[0],
                                           codeBox='param2')
        elif ('od' in self.lstOrigines) or ('repas' in self.lstOrigines):
            self.pnlParams.SetOneValue('fournisseur', "", codeBox='param2')
            setEnable('fournisseur', False)
            self.fournisseur = ''
            self.pnlParams.SetOneValue('analytique', "", codeBox='param2')
            setEnable('analytique', False)
            self.analytique = '00'
        else:
            setEnable('fournisseur', True)
            setEnable('analytique', True)

        self.pnlParams.Refresh()
        if event: event.Skip()
        self.ctrlOlv.lstColonnes = GetOlvColonnes(self)
        self.ctrlOlv.lstCodesColonnes = self.ctrlOlv.GetLstCodesColonnes()
        if event:
            self.GetDonnees()

    def OnDate(self, event):
        saisie = self.GetDate()
        if saisie:
            if saisie <= self.lastInventaire:
                wx.MessageBox("La date saisie est dans un exercice antérieur",
                              "NON bloquant", wx.ICON_WARNING)
            if saisie - self.lastInventaire > datetime.timedelta(days=366):
                wx.MessageBox("Le dernier inventaire date de '%s'" % self.lastInventaire,
                              "VERIFICATION", wx.ICON_INFORMATION)
            self.pnlParams.SetOneValue('date', valeur=saisie, codeBox='param1')
            self.GetDonnees()
        if event: event.Skip()

    def OnFournisseur(self,event):
        fournisseur = self.pnlParams.GetOneValue('fournisseur',codeBox='param2')
        if fournisseur == self.fournisseur:
            return
        fournisseur = fournisseur.strip().upper()
        lg = min(len(fournisseur),7)
        lstChoix = [x for x in self.fournisseurs if x[:lg] == fournisseur[:lg]]
        if len(fournisseur) ==0: pass
        elif len(fournisseur) < 3:
            # moins de trois caractères c'est trop court, mieux vaut rien
            mess = "Identiant fournisseur trop court\n\n"
            mess = "Soit à blanc fournisseur soit au moins trois caractères pour un fournisseur!"
            wx.MessageBox(mess,"Refus")
            return
        elif len(lstChoix) == 1:
            # un seul item fournisseur correspond, on le choisit
            fournisseur = lstChoix[0]
        elif len(lstChoix) == 0:
            # nouvel item à confirmer
            mess = "'%s' est-il bien un nouveau fournisseur à créer?\n\n"%fournisseur
            if len(fournisseur) < 7:
                # permetra un autre fournisseur avec le même début
                fournisseur += "_"
            ret = wx.MessageBox(mess,"Confirmez",style=wx.OK|wx.CANCEL)
            if ret != wx.OK:
                self.pnlParams.SetOneValue('fournisseur', None, codeBox='param2')
                return
        elif len(lstChoix) > 1:
            from xpy.outils  import  xchoixListe
            dlg = xchoixListe.DialogAffiche(lstDonnees=lstChoix,
                lstColonnes=['nom_fournisseur',],
                titre="Précisez  votre choix",
                intro="Sinon créez un nouveau fournisseur avec un nom plus long")
            ret = dlg.ShowModal()
            choix = dlg.choix
            getch = dlg.GetChoix()
            if ret == wx.OK:
                fournisseur = dlg.GetChoix()
            else: fournisseur = ''
            dlg.Destroy()
        self.fournisseur = fournisseur
        self.pnlParams.SetOneValue('fournisseur', fournisseur, codeBox='param2')
        self.GetDonnees()
        if event: event.Skip()

    def OnBtnFournisseur(self,event):
        # Simple message explication
        mess = "Choix FOURNISSEURS\n\n"
        mess += "Les fournisseurs proposés sont cherchés dans les utilisations précédentes,\n"
        mess += "Il vous suffit de saisir un nouveau nom pour qu'il vous soit proposé la prochaine fois"
        wx.MessageBox(mess,"Information",style=wx.ICON_INFORMATION|wx.OK)
        if event: event.Skip()

    def OnAnalytique(self,event):
        self.analytique = self.GetAnalytique()
        choixAnalytique = self.pnlParams.GetOneValue('analytique',codeBox='param2')
        if len(choixAnalytique) > 0:
            ix = self.valuesAnalytiques.index(choixAnalytique) -1
            if isinstance(ix,int) and ix <= len(self.lstAnalytiques):
                self.analytique = self.lstAnalytiques[ix][0]
            else: return
        self.GetDonnees()

    def OnBtnAnalytique(self,event):
        # Appel du choix d'un camp via un écran complet
        noegest = nung.Noelite(self)
        dicAnalytique = noegest.GetActivite(mode='dlg')
        if dicAnalytique:
            codeAct = nust.MakeChoiceActivite(dicAnalytique)
            self.pnlParams.SetOneValue('analytique',codeAct,codeBox='param2')

    def OnRepas(self,event):
        pass

    def OnImprimer(self,event):
        self.ctrlOlv.Apercu(None)

    def OnAction(self,event):
        self.OnFermer()

#------------------------ Lanceur de test  -------------------------------------------

if __name__ == '__main__':
    app = wx.App(0)
    os.chdir("..")
    dlg = DLG()
    dlg.ShowModal()
    app.MainLoop()
