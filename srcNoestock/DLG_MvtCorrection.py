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
import srcNoestock.UTILS_Stocks         as nust
import srcNoelite.UTILS_Noelite         as nung
import xpy.ObjectListView.xGTE          as xGTE
import xpy.xUTILS_Identification        as xuid
import xpy.xUTILS_DB                    as xdb
import srcNoestock.DLG_Mouvements       as ndlgmvts
from xpy.ObjectListView.ObjectListView  import ColumnDefn
from xpy.outils                         import xformat, xdates

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
         #'ctrlSize': (300,40),
         'txtSize': 125},
    ],
    ("param2", "Comptes"): [
        {'name': 'fournisseur', 'genre': 'Choice', 'label': 'Fournisseur',
         'help': "La saisie d'un fournisseurfacilite les commandes par fournisseur",
         'value': 0, 'values': ['--NoChange--',],
         'ctrlAction': 'OnFournisseur',
         'txtSize': 80,
         'ctrlMinSize': (200,30),
         },

        {'name': 'analytique', 'genre': 'Choice', 'label': 'Camp',
         'ctrlAction': 'OnAnalytique',
         'help': "Il s'agit de l'activité qui a endossé la charge de la sortie",
         'value': 0, 'values': ['--NoChange--',],
         'btnLabel': "...",
         'btnHelp': "Cliquez pour choisir l'activité de destination des mouvements",
         'btnAction': 'OnBtnAnalytique',
         'txtSize': 80,
         #'ctrlSize': (260,30),
        },
    ],
    ("param3", "Repas"): [
        {'name': 'repas', 'genre': 'Combo', 'label': 'Repas',
         'help': "La saisie du repas n'a de sens que pour les sorties cuisine",
         'value': 0, 'values': ['--NoChange--','-'] + nust.CHOIX_REPAS,
         'ctrlAction': 'OnRepas',
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
            'size':(120,35),'image':"xpy/Images/32x32/Actualiser.png",'onBtn':dlg.OnFinal},
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
                'boxesSizes': [(280, 65),(260, 60),(180, 60),None],
            }

def GetOlvColonnes(dlg):
    # retourne la liste des colonnes de l'écran principal, valueGetter correspond aux champ des tables ou calculs
    lstCol = [
            ColumnDefn("ID", 'centre', 0, 'IDmouvement'),
            ColumnDefn("Nature", 'left', 70, 'origine',),
            ColumnDefn("Date Mvt", 'left', 80, 'date',
                       valueSetter=datetime.date(1900,1,1),
                       stringConverter=xformat.FmtDate),
            ColumnDefn("Camp", 'left', 40, 'IDanalytique',),
            ColumnDefn("Repas", 'left', 60, 'repas',),
            ColumnDefn("Article", 'left', 200, 'IDarticle',
                       valueSetter="",isSpaceFilling=True),
            ColumnDefn("Quantité", 'right', 80, 'qte',
                       valueSetter=0.0, stringConverter=xformat.FmtQte),
            ColumnDefn("Prix Unit.", 'right', 80, 'prixUnit',
                       valueSetter=0.0, stringConverter=xformat.FmtDecimal),
            ColumnDefn("Mtt TTC", 'right', 80, '__mttTTC',
                       valueSetter=0.0, stringConverter=xformat.FmtDecimal, ),
            ColumnDefn("Coût Ration", 'right', 80, '__pxRation',
                       valueSetter=0.0, stringConverter=xformat.FmtDecimal, ),
            ColumnDefn("Nbre Rations", 'right', 80, 'rations',
                       valueSetter=0.0, stringConverter=xformat.FmtDecimal, ),
            ColumnDefn("Fournisseur", 'left', 170, 'fournisseur',
                       isSpaceFilling=True ),
            ColumnDefn("Saisie le", 'left', 80, 'date',
                       valueSetter=datetime.date(1900, 1, 1),
                       stringConverter=xformat.FmtDate),
            ColumnDefn("par Ordinateur", 'left', 50, 'ordi',
                       isSpaceFilling=True ),
            ColumnDefn("mofifiable", 'centre', 0, 'modifiable'),
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
        'pnl_params': None,  # Le standart GTE sera utilisé
        'pnl_corps': xGTE.PNL_corps,
        'pnl_pied': None,
        'minSize': (800, 450),
        'size': (1200, 800),
        'autoSizer': True,
    }

    #----------------------- Parties de l'écrans -----------------------------------------

def CalculeLigne(dlg,track):
    dlg = dlg.parent
    qte = round(track.qte,4)
    prixUnit = round(track.prixUnit,4)
    rations = track.rations
    if rations == 0: rations = 1
    track.__mttTTC = round(qte * prixUnit,2)
    track.__pxRation =  round(qte * prixUnit / rations,2)
    anomalie = None
    if dlg.origine  and dlg.origine != track.origine:
        anomalie = True
    if dlg.date  and dlg.date != track.date:
        anomalie = True
    if dlg.fournisseur  and dlg.fournisseur != track.fournisseur:
        anomalie = True
    if dlg.analytique and dlg.analytique != track.IDanalytique:
        anomalie = True
    if dlg.repas  and dlg.repas != track.repas:
        anomalie = True
    track.anomalie = anomalie

def RowFormatter(listItem, track):
    if track.anomalie:
        # anomalie est colorée
        listItem.SetBackgroundColour(wx.Colour(220, 237, 200))
        listItem.SetTextColour(wx.BLUE)
    else:
        #listItem.SetBackgroundColour(wx.Colour(220, 237, 200))
        listItem.SetTextColour(wx.BLACK)
        pass
class DLG(xGTE.DLG_tableau):
    # ------------------- Composition de l'écran de gestion----------
    def __init__(self,parent, **kwd):
        tracks = kwd.get('donnees',[])
        self.lstIDmvts = [x.IDmouvement for x in tracks]
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
        kwds['db'] = self.db

        super().__init__(self, **kwds)

        self.ordi = xuid.GetNomOrdi()
        self.today = datetime.date.today()
        self.date = None

        self.Init()
        self.ctrlOlv.cellEditMode = self.ctrlOlv.CELLEDIT_NONE
        self.GetDonnees()

    def Init(self):
        # charger les valeurs de pnl_params
        self.fournisseurs = (['--NoChange--','-'] + nust.SqlFournisseurs(self.db))
        self.fournisseur = None
        self.lstAnalytiques = nust.SqlAnalytiques(self.db,'ACTIVITES')
        self.analytique = None
        lstAnalytiques = [(None,'--NoChange--'),('00','-')]
        lstAnalytiques += nust.SqlAnalytiques(self.db,'ACTIVITES')
        self.valuesAnalytiques = [x[1] for x in lstAnalytiques]
        self.codesAnalytiques = [x[0] for x in lstAnalytiques]
        self.lastInventaire = nust.GetDateLastInventaire(self.db)

        pnl = self.pnlParams.GetPnlCtrl('fournisseur','param2')
        pnl.SetValues(self.fournisseurs)
        pnl.SetValue(self.fournisseurs[0])
        pnl = self.pnlParams.GetPnlCtrl('analytique','param2')
        pnl.SetValues(self.valuesAnalytiques)
        pnl.SetValue(self.valuesAnalytiques[0])

        self.repas = None
        self.origine = None

        self.pnlOlv.CalculeLigne = CalculeLigne
        self.pnlOlv.parent = self
        self.Bind(wx.EVT_CLOSE, self.OnFermer)
        self.InitOlv()

    # ------------------- Gestion des actions -----------------------

    def InitOlv(self):
        self.ctrlOlv.lstColonnes = GetOlvColonnes(self)
        self.ctrlOlv.lstCodesColonnes = self.ctrlOlv.GetLstCodesColonnes()
        self.ctrlOlv.InitObjectListView()
        self.ctrlOlv.rowFormatter = RowFormatter

    def GetAnalytique(self):
        choixAnalytique = self.pnlParams.GetOneValue('analytique',codeBox='param2')
        if len(choixAnalytique) > 0:
            ix = self.valuesAnalytiques.index(choixAnalytique)
            code = self.codesAnalytiques[ix]
        else: code = '00'
        return code

    def GetDonnees(self):
        # appel des données selon les ID reçus
        lstCodesCol = self.dicOlv['lstCodes']
        lstChamps = []
        # les champs calculés ne sont pas appelés dans sql
        for x in lstCodesCol:
            if x.startswith('__'):
                lstChamps.append('0')
            elif x in ('IDarticle','fournisseur','ordi'):
                lstChamps.append('stMouvements.%s'%x)
            else:
                lstChamps.append(x)

        if len(self.lstIDmvts) > 0:
            where = 'IDmouvement in (%s)'% str(self.lstIDmvts)[1:-1]
        else: where = ''
        dicOlv = {
            'table': ' stMouvements INNER JOIN stArticles ON stMouvements.IDarticle = stArticles.IDarticle',
            'lstChamps': lstChamps,
            'where': where,
        }
        kwds = {'db' : self.db,'dicOlv': dicOlv}
        lstDonnees = nust.SqlTable(**kwds)
        # alimente la grille, puis création de modelObjects pr init
        self.ctrlOlv.lstDonnees = lstDonnees
        self.ctrlOlv.MAJ()

    # gestion des actions ctrl
    def OnOrigine(self, event):
        lblOrigine = self.pnlParams.GetOneValue('origine')
        if 'NoChange' in lblOrigine:
            self.origine = None
            self.lstOrigines = [None,]
            self.sens = None
        else:
            self.origine = CODESORIGINES[VALUESORIGINES.index(lblOrigine)]
            self.lstOrigines = [self.origine,]
            self.sens = SENS[VALUESORIGINES.index(lblOrigine)]
        self.dicOlv.update({'lstColonnes': GetOlvColonnes(self)})
        ndlgmvts.GriseCtrlsParams(self, self.lstOrigines)
        self.ctrlOlv.MAJ()

    def OnDate(self, event):
        saisie = self.pnlParams.GetOneValue('date',codeBox='param1')
        saisie = xformat.DateFrToDatetime(saisie,mute=True)
        if saisie == self.date:
            return
        if saisie:
            if saisie <= self.lastInventaire:
                wx.MessageBox("La date saisie est dans un exercice antérieur",
                              "NON bloquant", wx.ICON_WARNING)
            if saisie - self.lastInventaire > datetime.timedelta(days=366):
                wx.MessageBox("Le dernier inventaire date de '%s'" % self.lastInventaire,
                              "VERIFICATION", wx.ICON_INFORMATION)
            self.pnlParams.SetOneValue('date', valeur=saisie, codeBox='param1')
            self.date = saisie
        else:
            self.date = None
            self.pnlParams.SetOneValue('date', valeur='--NoChange--', codeBox='param1')
        if event: event.Skip()
        self.ctrlOlv.MAJ()

    def OnFournisseur(self,event):
        if event: event.Skip()
        fournisseur = self.pnlParams.GetOneValue('fournisseur',codeBox='param2')
        if fournisseur == self.fournisseur:
            return
        if fournisseur == self.fournisseurs[0]:
            fournisseur = None
        elif len(fournisseur) < 3:
            fournisseur = ''
        self.fournisseur = fournisseur
        self.ctrlOlv.MAJ()


    def OnAnalytique(self,event):
        if event: event.Skip()
        self.analytique = self.GetAnalytique()
        self.ctrlOlv.MAJ()


    def OnBtnAnalytique(self,event):
        # Appel du choix d'un camp via un écran complet
        noegest = nung.Noelite(self)
        dicAnalytique = noegest.GetActivite(mode='dlg')
        if dicAnalytique:
            codeAct = dicAnalytique['idanalytique']
            valAct = dicAnalytique['abrege']
            self.pnlParams.SetOneValue('analytique',valAct,codeBox='param2')
            self.analytique = codeAct
        self.ctrlOlv.MAJ()

    def OnRepas(self,event):
        saisie = self.pnlParams.GetOneValue('repas','param3')
        if 'NoChange' in saisie:
            self.repas = None
        elif '-' == saisie:
            self.repas = 0
        else:
            self.repas = nust.CHOIX_REPAS.index(saisie) + 1
        self.ctrlOlv.MAJ()

    def OnImprimer(self,event):
        self.ctrlOlv.Apercu(None)

    def OnFinal(self,event):
        donnees = [x for x in self.ctrlOlv.GetSelectedObjects() if x.IDmouvement > 0]
        if len(donnees) == 0:
            donnees = self.ctrlOlv.innerList
        self.OnFermer(None)

#------------------------ Lanceur de test  -------------------------------------------

if __name__ == '__main__':
    app = wx.App(0)
    os.chdir("..")
    dlg = DLG(None)
    dlg.ShowModal()
    app.MainLoop()
