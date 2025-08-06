#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Application :    Noelite, Validation des fichiers compta à importer
# Usage : Ouvre le fichier d'import et teste la faisobilité de l'import
# Auteur:          Jacques BRUNEL 08/2025
# Licence:         Licence GNU GPL
# --------------------------------------------------------------------

import wx
import datetime
import xpy.xGestionConfig               as xgc
import xpy.xUTILS_SaisieParams          as xusp
from xpy.outils                 import xformat,xbandeau,xdates,xboutons
from xpy.ObjectListView import xGTE
from xpy.ObjectListView.ObjectListView  import ColumnDefn
from DLG_Transpose_fichier import FORMATS_IMPORT


#---------------------- Paramètres du programme -------------------------------------
GRISBLEU =wx.Colour(215, 225, 250)
GRISVERT =wx.Colour(200, 240, 200)
GRISVERTCLAIR =wx.Colour(215, 255, 215)
GRISROSE =wx.Colour(240, 200, 200)
GRISJAUNE =wx.Colour(255, 255, 220)

TITRE = "Validation des options d'importation"
INTRO = "Avant l'importation, vérifiez ici les champs à importer, les options possibiles avant de l'ancer l'import dans l'écran précédent"

# Info par défaut en bas de l'écran
INFO_OLV = "Les options ne sont pas valides"


class CTRL_RadioBox(wx.Panel):
    def __init__(self, parent, **kwds):
        name = kwds.pop('name', "CTRL_RadioBox")
        label = kwds.pop('label',"choisir une option")
        choices = kwds.pop('choices',[' Option 1', ' Option 2',' Option autre'])

        wx.Panel.__init__(self, parent, id=-1, name=name)
        self.rbox = wx.RadioBox(self,id=wx.ID_ANY,
                                label = label,
                                choices=choices,
                                majorDimension=1,
                                style=wx.RA_SPECIFY_COLS)
        # Sizer
        grid_sizer = wx.FlexGridSizer(rows=1, cols=1, vgap=5, hgap=5)
        grid_sizer.Add(self.rbox, 0, 0, 0)
        self.SetSizer(grid_sizer)
        #grid_sizer.Fit(self)

    def GetValue(self):
        return self.rbox.GetStringSelection()

    def SetValue(self):
        self.rbox.SetString()

class CTRL_RadioGroup(wx.Panel):
    def __init__(self, parent, **kwds):
        name = kwds.pop("name", "CTRL_RadioButtonGroup")
        self.choices = kwds.pop("choices",['Option1','Option2'])
        self.lstButton = []
        self.value = None

        wx.Panel.__init__(self, parent, id=-1, name=name)

        style = wx.RB_GROUP
        grid_sizer = wx.FlexGridSizer(rows=len(self.choices), cols=1, vgap=5, hgap=5)
        for item in self.choices:
            button = wx.RadioButton(self, -1,label=" "+item,style=style)
            self.lstButton.append(button)
            grid_sizer.Add(button,0, 0, 0)
            style = 0
        self.SetSizer(grid_sizer)

    def GetValue(self):
        # Contrairement au GetValue booleen du bouton, ici on retourne le label
        value = self.value
        for button in self.lstButton:
            if button.GetValue():
                value = self.choices[self.lstButton.index(button)]
        return value

    def SetValue(self, value):
        self.value = value
        for item in self.choices:
            if value == item:
                ix = self.choices.index(item)
                button  = self.lstButton[ix]
                button.SetValue(True)
                self.value = value
                break

    def SetValues(self,choices):
        # synonyme de Set pour analogies avec d'autres types
        self.Set(choices)

    def Set(self,choices):
        if len(choices) != len(self.choices):
            raise Exception("Le CTRL_RadioGroup n'a pas été initialisé avec ce nombre d'item")
        ix = 0
        for button in self.lstButton:
            button.SetLabel(choices[ix])
            self.choices[ix] = choices[ix]
            ix += 1

# Description des paramètres à choisir en haut d'écran
MATRICE_PARAMS = {
("fichier","Fichier à Importer"): [
    {'name': 'nomFichier','genre': 'dirfile',  'label': "Fichier d'origine",'value': "*.xlsx",
                     'help': "Pointez le fichier contenant les valeurs à transposer",
                    'ctrlAction':'OnFichier',
                    'size':(600,30),},
    {'name': 'nomBanque', 'genre': 'enum', 'label': 'Banque importée',
                    'help': "La banque détermine le format d'import", 'value':0,
                    'values':[x for x in FORMATS_IMPORT.keys()],
                    'ctrlAction':'OnBanque',
                    'size':(350,30)},
    ],
("format", "Format d'import"): [
    {'name': 'typeCarte', 'genre':'anyctrl','label':"",
     'ctrl': CTRL_RadioGroup,
     'help': "%s" % "Selon le type de carte et la banque les champs attendus peuvent varier",
     'values': ['Relevé Banque','Détail cartes CB'],
     #'ctrlAction': 'OnTypeCarte',
     'ctrlSize':(130,50)
    },

    ],
("date", "Option pour CB"): [
    {'name': 'dateCpta', 'genre': 'anyctrl', 'label': "DateCpta",
     'ctrl': xdates.CTRL_SaisieDateAnnuel,
     'help': "%s\n%s\n%s" % ("Saisie JJMMAA ou JJMMAAAA possible.",
                             "Cette date sera appliquée à l'ensemble des écritures",
                             "Saisissez sans séparateurs, "),
     'ctrlAction': 'OnForcerdte',
     'ctrlSize':(250,40),
     'txtSize':55,
     'boxMinSize':(250,60)

    },
    ],
("vide", ""): []
}

def GetDicPnlParams(*args):
    return {    'name':"PNL_params (DLG_Transpose_options)",
                'matrice': MATRICE_PARAMS,
                'lblBox': "Paramètres à saisir",
                'boxesSizes': [(450,80), (150, 80), (230, 40),(50,50)],
                'pathdata':"srcNoelite/Data",
                'nomfichier':"stparams",
                'nomgroupe':"transposeoptions",
                }

def GetDicDialogParams(parent,*args):
    listArbo = os.path.abspath(__file__).split("\\")
    kwds = {}
    kwds['name'] = 'DLG_Transpose_options.Dialog'
    kwds['title'] = listArbo[-1] + "/" + parent.__class__.__name__
    kwds['size'] = (900, 600)
    return kwds

# description des boutons en pied d'écran et de leurs actions
def GetBoutons(dlg):
    return  [
        {'name': 'btnAbort', 'label': "Abandon",
         'help': "Cliquez ici pour renoncer et revenir à l'écran précédent",
         'size': (110, 27), 'image': "xpy/Images/32x32/Annuler.png",
         'onBtn': dlg.OnEsc},
        {'name':'btnOK','ID':wx.ID_ANY,'label':"Valider",
         'help':"Cliquez ici pour enregistrer et fermer la fenêtre",
            'size':(120,35),'image':"xpy/Images/32x32/Valider.png",'onBtn':dlg.OnFermer},
        ]

# description des colonnes de l'OLV (données affichées)
def GetOlvColonnes(dlg):
    # retourne la liste des colonnes de l'écran principal
    return [
            ColumnDefn("Date", 'center', 85, 'date', valueSetter="",isSpaceFilling=False,
                            isEditable=True, stringConverter=xformat.FmtDate),
            ColumnDefn("Cpt No", 'left', 90, 'compte',valueSetter='',isSpaceFilling=False,
                            isEditable=True),
            ColumnDefn("Cpt Appel", 'left', 90, 'appel',valueSetter='',isSpaceFilling=False,
                            isEditable=False),
            ColumnDefn("Cpt Libellé ", 'left', 150, 'libcpt',valueSetter='',isSpaceFilling=False,
                            isEditable=False),
            ColumnDefn("NoPièce", 'left', 80, 'noPiece', isSpaceFilling=False),
            ColumnDefn("Libelle", 'left', 200, 'libelle', valueSetter='', isSpaceFilling=True),
            ColumnDefn("Montant", 'right',90, "montant", isSpaceFilling=False, valueSetter=0.0,
                            stringConverter=xformat.FmtDecimal),
            ]

# paramètre les options de l'OLV
def GetOlvOptions(dlg):
    return {
            'minSize': (500,150),
            'checkColonne': False,
            'recherche': True,
            'autoAddRow':False,
            'msgIfEmpty':"Fichier non encore importé!",
            'dictColFooter': {"libelle": {"mode": "nombre", "alignement": wx.ALIGN_CENTER},
                              "montant": {"mode": "total"}, }
    }

#----------------------- Parties de l'écrans -----------------------------------------

class PNL_params(xgc.PNL_paramsLocaux):
    #panel de paramètres de l'application
    def __init__(self, parent, **kwds):
        self.parent = parent
        super().__init__(parent, **kwds)
        self.SetBackgroundColour(GRISJAUNE)
        self.Init()

class PNL_corps(wx.Panel):
    #panel central
    def __init__(self, parent, *args, **kwds):
        wx.Panel.__init__(self,parent,*args,**kwds)

        self.__init_ecran()
        self.__set_properties()
        self.__do_layout()

    def __init_ecran(self):
        self.staticbox_gauche = wx.StaticBox(self, -1,"Contenu du fichier")
        self.staticbox_droite = wx.StaticBox(self, -1,"Colonnes attendues")
        choices =  ['Première feuille Non trouvée', '-', '-','-','-',]
        label = " Choisir une feuille "
        self.radiosheets = CTRL_RadioBox(self,label=label,choices=choices)
        self.labelChklstColonnesIn = wx.StaticText(self,-1,"Colonnes Présentes")
        self.chklstColonnesIn = wx.CheckListBox(self, -1,choices=["-",])
        self.labelPeriode = wx.StaticText(self, -1, "Période trouvée")
        self.periode = xdates.CTRL_AffichePeriode(self,withStaticBox=False)
        self.testok = wx.StaticText(self,-1,"Colonnes manquantes")

    def __set_properties(self):
        self.SetBackgroundColour(GRISVERT)
        self.staticbox_droite.SetBackgroundColour(GRISROSE)
        self.radiosheets.SetBackgroundColour(GRISJAUNE)
        self.chklstColonnesIn.SetBackgroundColour(GRISVERTCLAIR)
        self.testok.SetBackgroundColour(GRISROSE)
        font = self.testok.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.testok.SetFont(font)
        self.testok.SetForegroundColour(wx.Colour(255, 0, 0))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=1, cols=2, vgap=3, hgap=3)

        # gauche
        sttbox_gauche_sizer = wx.StaticBoxSizer(self.staticbox_gauche, wx.VERTICAL)
        grid_sizer_gauche = wx.FlexGridSizer(rows=2, cols=2, vgap=3, hgap=3)


        grid_sizer_gauche.Add(self.radiosheets,1,wx.LEFT | wx.EXPAND, 25)

        grid_sizer_col_presentes = wx.FlexGridSizer(rows=2, cols=1, vgap=3, hgap=3)
        grid_sizer_col_presentes.Add(self.labelChklstColonnesIn, 1, wx.LEFT | wx.EXPAND, 0)
        grid_sizer_col_presentes.Add(self.chklstColonnesIn, 1, wx.LEFT | wx.EXPAND, 0)

        grid_sizer_gauche.Add(grid_sizer_col_presentes, 1, wx.LEFT | wx.EXPAND, 25)
        grid_sizer_gauche.Add(self.labelPeriode, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 0)
        grid_sizer_gauche.Add(self.periode, 0, wx.ALIGN_LEFT, 0)

        sttbox_gauche_sizer.Add(grid_sizer_gauche, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        # droite
        grid_sizer_droite = wx.FlexGridSizer(rows=3, cols=1, vgap=3, hgap=3)
        sttbox_droite_sizer = wx.StaticBoxSizer(self.staticbox_droite, wx.VERTICAL)
        sttbox_droite_sizer.Add(self.testok, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        sttbox_droite_sizer.Add((20,150),1,wx.EXPAND,0)
        grid_sizer_droite.Add(sttbox_droite_sizer, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        grid_sizer_base.Add(sttbox_gauche_sizer,1,wx.ALL | wx.EXPAND,5)
        grid_sizer_base.Add(grid_sizer_droite,1,wx.ALL | wx.EXPAND,5)

        grid_sizer_gauche.AddGrowableRow(0)
        #grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.AddGrowableCol(1)
        grid_sizer_base.AddGrowableRow(0)

        self.SetSizer(grid_sizer_base)

    def SetValuesChklst(self,ctrl,choices=[]):
        ctrl.Clear()
        for item in choices:
            ctrl.Append(item)

class PNL_pied(xGTE.PNL_pied):
    #panel infos (gauche) et boutons sorties(droite)
    def __init__(self, parent, dicPied, **kwds):
        xGTE.PNL_pied.__init__(self,parent, dicPied, **kwds)

class Dialog(xusp.DLG_vide):
    # ------------------- Composition de l'écran de gestion----------
    def __init__(self,nomFichier='', nomBanque='',ixSheet=0,isCB=False):
        self.txtInfo = INFO_OLV
        self.ctrlOlv = None
        self.nomFichier = nomFichier
        self.nomBanque = nomBanque
        self.ixSheet = ixSheet
        self.isCB = isCB

        kwds = GetDicDialogParams(self)
        super().__init__(self,**kwds)
        self.Init()
        self.SetBackgroundColour(GRISBLEU)
        self.Sizer()
        self.DeclareVariables()
        self.SetInitialValues()

    # Initialisation des panels
    def Init(self):
        dicParams = GetDicPnlParams()
        # boutons de bas d'écran - infos: texte ou objet window.  Les infos sont  placées en bas à gauche
        lstInfos = [ wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)),self.txtInfo]
        dicPied = {'lstBtns': GetBoutons(self), "lstInfos": lstInfos}

        # lancement de l'écran en blocs principaux
        self.pnlBandeau = xbandeau.Bandeau(self,TITRE,INTRO,nomImage="xpy/Images/32x32/Restaurer.png")
        self.pnlParams = PNL_params(self,**dicParams)
        self.pnlCorps = PNL_corps(self)
        self.pnlPied = PNL_pied(self, dicPied)
        self.Bind(wx.EVT_CLOSE,self.OnFermer)

    def Sizer(self):
        sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=0, hgap=0)
        sizer_base.Add(self.pnlBandeau, 1, wx.TOP | wx.EXPAND, 3)
        sizer_base.Add(self.pnlParams, 1, wx.TOP | wx.EXPAND, 3)
        sizer_base.Add(self.pnlCorps, 1,  wx.EXPAND, 3)
        sizer_base.Add(self.pnlPied, 0, wx.ALL | wx.EXPAND, 3)
        sizer_base.AddGrowableCol(0)
        sizer_base.AddGrowableRow(2)
        self.SetSizer(sizer_base)

    def DeclareVariables(self):
        # Déclaration de toutes les variables découlant de la gestion de l'écran
        self.fichierIn = None
        self.paramsBanque = None
        self.dateCpta = None
        self.lstNomsSheets = []
        self.lstColonnesLues = []
        self.lstColonnesOlv = []
        self.periodeDeb = []
        self.periodeFin = []
        self.valide = False
        self.dicCtrls = {}

    def SetInitialValues(self):
        # accès simplifiés aux controles par leur pointeur dans dicCtrls
        for box in MATRICE_PARAMS:
            for dicCtrl in MATRICE_PARAMS[box]:
                name = dicCtrl['name']
                self.dicCtrls[name] = self.pnlParams.GetPnlCtrl(name,box[0])
        self.dicCtrls['chklstColonnesIn'] = self.pnlCorps.chklstColonnesIn
        #self.dicCtrls['chklstColonnesOlv'] = self.pnlCorps.chklstColonnesOlv

        # récupère les values d'un anyctrl pour le Set qui n'est pas automatique
        ctrlTypeCarte = self.dicCtrls['typeCarte']
        ctrlTypeCarte.SetValues(ctrlTypeCarte.values)
        ctrlTypeCarte.Bind(wx.EVT_RADIOBUTTON, self.OnTypeCarte)
        ctrlTypeCarte.SetValue(ctrlTypeCarte.values[self.isCB])

        # autres controles à initialiser
        self.pnlParams.SetOneValue('nomFichier',self.nomFichier)
        self.pnlParams.SetOneValue('nomBanque',self.nomBanque)
        self.OnFichier(None)
        self.OnBanque(None)
        self.OnTypeCarte(None)

        #self.dicCtrls['sheets'].SetSelection(self.ixSheet)


    # ------------------- Gestion des actions -----------------------
    def OnFichier(self,event):
        self.nomFichier = self.pnlParams.GetOneValue('nomFichier')

    def OnBanque(self, event):
        self.nomBanque = self.dicCtrls['nomBanque'].GetValue()
        self.lstColonnesOlv = FORMATS_IMPORT[self.nomBanque]['champs']
        #self.dicCtrls['chklstColonnesOlv'].SetValues(self.lstColonnesOlv)

    def OnTypeCarte(self,event):
        typeCarte = self.dicCtrls['typeCarte'].GetValue()
        if typeCarte == self.dicCtrls['typeCarte'].values[0]:
            self.dicCtrls['dateCpta'].Enable(False)
            self.isCB = False
        else:
            self.dicCtrls['dateCpta'].Enable(True)
            self.isCB = True
            if self.dateCpta:
                self.dicCtrls['dateCpta'].setValue(self.dateCpta)

    def OnForcerdte(self,event):
        print()
        pass

    def OnRadioBoxType(self,event):
        pass

    def ValideSaisie(self,event):
        pass

#------------------------ Lanceur de test  -------------------------------------------
if __name__ == '__main__':
    import os
    app = wx.App(0)
    os.chdir("..")
    fichier = "C:\\Users\\jbrun\\Desktop\\bribes\CREDIT MUT RELEVE.xlsx"
    dlg = Dialog(nomFichier=fichier, nomBanque='Crédit Mutuel',ixSheet=0,isCB=True)
    dlg.ShowModal()
    app.MainLoop()
