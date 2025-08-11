#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Application :    Noelite, Validation des fichiers compta à importer
# Usage : Ouvre le fichier d'import et teste la faisobilité de l'import
# Auteur:          Jacques BRUNEL 08/2025
# Licence:         Licence GNU GPL
# --------------------------------------------------------------------

import wx, os
import datetime
import xpy.xGestionConfig as xgc
import xpy.xUTILS_SaisieParams as xusp
from xpy.outils import xformat, xbandeau, xdates, ximport
from xpy.ObjectListView import xGTE
from xpy.ObjectListView.ObjectListView import ColumnDefn
import GLOBAL

FORMATS_IMPORT = GLOBAL.GetFormatsImport()

# --------------------- Paramètres du programme -------------------------------------
GRISBLEU = wx.Colour(215, 225, 250)
GRISVERT = wx.Colour(200, 240, 200)
GRISVERTCLAIR = wx.Colour(215, 255, 215)
GRISROSE = wx.Colour(240, 200, 200)
GRISJAUNE = wx.Colour(255, 255, 220)

TITRE = "Validation des options d'importation"
INTRO = "Avant l'importation, vérifiez ici les champs à importer,"
INTRO += "les options possibiles avant de l'ancer l'import dans l'écran précédent"

# Info par défaut en bas de l'écran
INFO_OLV = "Les options ne sont pas valides"


class CTRL_RadioBox(wx.Panel):

    def __init__(self, parent, **kwds):
        name = kwds.pop('name', "CTRL_RadioBox")
        size = kwds.pop('size', (60,80))
        label = kwds.pop('label',"choisir une option")
        choices = kwds.pop('choices',[' Option 1', ' Option 2',' Option autre'])
        self.choices = choices

        wx.Panel.__init__(self, parent, id=-1, name=name)
        self.rbox = wx.RadioBox(self,id=wx.ID_ANY,
                                label = label,
                                size = size,
                                choices=choices,
                                majorDimension=1,
                                style=wx.RA_SPECIFY_COLS)
        # Sizer
        grid_sizer = wx.FlexGridSizer(rows=1, cols=1, vgap=5, hgap=5)
        grid_sizer.Add(self.rbox, 0, 0, 0)
        self.SetSizer(grid_sizer)

    def GetValue(self):
        return self.rbox.GetStringSelection()

    def SetValue(self):
        self.rbox.SetString()

    def SetValues(self,choices):
        # synonyme de Set pour analogies avec d'autres types
        nb = self.rbox.GetRowCount()
        label = ""
        for ix in range(nb):
            if ix > len(self.choices):
                break
            elif ix <= len(choices)-1:
                label = choices[ix]
                self.rbox.ShowItem(ix,True)
            else:
                label = ""
                self.rbox.ShowItem(ix,False)
            self.rbox.SetString(ix,label)
            self.choices[ix] = label


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
    {'name': 'nomFichier','genre': 'dirfile','label': "Fichier d'origine",'value': "*.xlsx",
                     'help': "Pointez le fichier contenant les valeurs à transposer",
                    'ctrlAction':'OnFichier',
                    'btnAction': 'inutile',# redirigé vers ctrlAction (car genre dirfile)
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
     'ctrlSize': (250,40),
     'txtSize': 55,
     'boxMinSize': (250,60)

    },
    ],
("vide", ""): []
}


def GetDicPnlParams():
    return {'name':"PNL_params (DLG_Transpose_options)",
            'matrice': MATRICE_PARAMS,
            'lblBox': "Paramètres à saisir",
            'boxesSizes': [(450,80), (150, 80), (230, 40),(50,50)],
            'pathdata':"srcNoelite/Data",
            'nomfichier':"stparams",
            'nomgroupe':"transposeoptions",
            }

# retourne les paramètres de l'écran de départ
def GetDicDialogParams(parent):
    listArbo = os.path.abspath(__file__).split("\\")
    kwds = {}
    kwds['name'] = 'DLG_Transpose_options.Dialog'
    kwds['title'] = listArbo[-1] + "/" + parent.__class__.__name__
    kwds['minSize'] = (900, 550)
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
            'minSize': (500,50),
            'checkColonne': False,
            'recherche': True,
            'autoAddRow':False,
            'msgIfEmpty':"Fichier non encore importé!",
            'dictColFooter': {"libelle": {"mode": "nombre", "alignement": wx.ALIGN_CENTER},
                              "montant": {"mode": "total"}, }
    }

#----------------------- Parties de l'écran -----------------------------------------

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
        self.radioSheets = CTRL_RadioBox(self,label=label,choices=choices,size=(150,180))
        self.labelChklstColonnesLues = wx.StaticText(self,-1,"Colonnes Présentes")
        self.chklstColonnesLues = wx.CheckListBox(self, -1,choices=["-",])
        self.chklstColonnesOlv = wx.CheckListBox(self, -1, choices=["-"])
        self.txtInfoPeriode = wx.StaticText(self, -1, "Période trouvée")
        self.periode = xdates.CTRL_AffichePeriode(self,withStaticBox=False)
        self.txtValide = wx.StaticText(self,-1,"-------------")

    def __set_properties(self):
        self.SetBackgroundColour(GRISVERT)
        self.staticbox_droite.SetBackgroundColour(GRISROSE)
        self.radioSheets.SetBackgroundColour(GRISJAUNE)
        self.chklstColonnesLues.Bind(wx.EVT_CHECKLISTBOX, self.OnDisabledChklstColonnes)
        self.chklstColonnesLues.SetBackgroundColour(GRISVERTCLAIR)
        self.chklstColonnesOlv.Bind(wx.EVT_CHECKLISTBOX, self.OnDisabledChklstColonnes)
        self.chklstColonnesOlv.SetBackgroundColour(GRISROSE)
        self.SetValide(False)

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=1, cols=2, vgap=3, hgap=3)

        # gauche
        sttbox_gauche_sizer = wx.StaticBoxSizer(self.staticbox_gauche, wx.VERTICAL)
        grid_sizer_gauche = wx.FlexGridSizer(rows=2, cols=2, vgap=15, hgap=18)
        grid_sizer_gauche.Add(self.radioSheets,1,wx.LEFT | wx.TOP | wx.EXPAND, 14)

        grid_sizer_col_presentes = wx.FlexGridSizer(rows=2, cols=1, vgap=15, hgap=3)
        grid_sizer_col_presentes.Add(self.labelChklstColonnesLues, 1, wx.LEFT | wx.EXPAND, 0)
        grid_sizer_col_presentes.Add(self.chklstColonnesLues, 1,
                                     wx.LEFT | wx.EXPAND, 0)
        grid_sizer_gauche.Add(grid_sizer_col_presentes, 1, wx.LEFT | wx.TOP | wx.EXPAND, 14)
        grid_sizer_gauche.Add(self.txtInfoPeriode, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 0)
        grid_sizer_gauche.Add(self.periode, 0, wx.ALIGN_LEFT, 0)

        sttbox_gauche_sizer.Add(grid_sizer_gauche, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        # droite
        grid_sizer_droite = wx.FlexGridSizer(rows=1, cols=1, vgap=20, hgap=25)
        sttbox_droite_sizer = wx.StaticBoxSizer(self.staticbox_droite, wx.VERTICAL)
        sttbox_droite_sizer.Add((220,10),0,0,0)
        sttbox_droite_sizer.Add(self.chklstColonnesOlv, 1, wx.LEFT | wx.EXPAND, 0)
        sttbox_droite_sizer.Add(self.txtValide, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        grid_sizer_droite.Add(sttbox_droite_sizer, 1, wx.LEFT | wx.TOP | wx.EXPAND, 30)
        grid_sizer_base.Add(sttbox_gauche_sizer,1,wx.ALL | wx.EXPAND,5)
        grid_sizer_base.Add(grid_sizer_droite,1,wx.ALL | wx.EXPAND,5)

        grid_sizer_col_presentes.AddGrowableRow(1)
        grid_sizer_gauche.AddGrowableRow(0)
        grid_sizer_droite.AddGrowableRow(0)
        grid_sizer_base.AddGrowableCol(1)
        grid_sizer_base.AddGrowableRow(0)

        self.SetSizer(grid_sizer_base)

    def SetValide(self,ok = False):
        self.txtValide.SetBackgroundColour(GRISROSE)
        font = self.txtValide.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        if ok:
            self.txtValide.SetLabel("Options correctes")
            self.txtValide.SetForegroundColour(wx.Colour(0,200, 100))
            self.txtValide.SetBackgroundColour(GRISVERTCLAIR)
        else:
            self.txtValide.SetLabel("Colonnes manquantes")
            self.txtValide.SetBackgroundColour(GRISROSE)
            self.txtValide.SetForegroundColour(wx.Colour(255, 0, 0))
        self.txtValide.SetFont(font)

    def SetValuesChklst(self,ctrl,choices):
        ctrl.Clear()
        try:
            for item in choices:
                if item:
                    ctrl.Append(item)
        except Exception as err:
            print(err)

    def ChkValuesChklst(self,ctrl,items):
        # coche les noms de colonne dans ctrl si présence dans la liste des items d'un autre
        nbl = ctrl.GetCount()
        allItems = [ctrl.GetString(ix) for ix in range(nbl)]
        for ix in range(nbl):
            ok = allItems[ix] in items
            ctrl.Check(ix,ok)

    def OnDisabledChklstColonnes(self,event):
        # Immediately revert the change, disable whithout graying
        index = event.GetInt()
        obj = event.GetEventObject()
        obj.Check(index, not obj.IsChecked(index))

class PNL_pied(xGTE.PNL_pied):
    #panel infos (gauche) et boutons sorties(droite)
    def __init__(self, parent, dicPied, **kwds):
        xGTE.PNL_pied.__init__(self,parent, dicPied, **kwds)

class Dialog(xusp.DLG_vide):
    # ------------------- Composition de l'écran de gestion----------
    def __init__(self,parent,nomFichier='', nomBanque='',ixSheet=0,typeCB=False,**kwd):
        self.parent = parent
        self.txtInfo = INFO_OLV
        self.ctrlOlv = None
        self.nomFichier = nomFichier
        self.nomBanque = nomBanque
        self.ixSheet = ixSheet
        self.lstNomsSheets = []
        self.dateMax = None
        self.nbLignes = 0
        self.typeCB = typeCB
        kwds = GetDicDialogParams(self)
        super().__init__(self.parent,**kwds)  # self supprimé
        self.Init()
        self.SetBackgroundColour(GRISBLEU)
        self.Sizer()
        self.DeclareVariables()
        self.SetInitialValues()

    # Initialisation des panels
    def Init(self):
        dicParams = GetDicPnlParams()
        # Boutons de bas d'écran - infos: texte ou objet window.  Les infos sont  placées en bas à gauche
        lstInfos = [ wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER,
                                              (16, 16)),self.txtInfo]
        dicPied = {'lstBtns': GetBoutons(self), "lstInfos": lstInfos}

        # lancement de l'écran en blocs principaux
        self.pnlBandeau = xbandeau.Bandeau(self,TITRE,INTRO,nomImage="xpy/Images/32x32/Restaurer.png")
        self.pnlParams = PNL_params(self,**dicParams)
        self.pnlCorps = PNL_corps(self)
        self.pnlPied = PNL_pied(self, dicPied)
        self.Bind(wx.EVT_CLOSE,self.OnFermer)

    def Sizer(self,pnl=None):
        sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=0, hgap=0)
        sizer_base.Add(self.pnlBandeau, 1, wx.TOP | wx.EXPAND, 3)
        sizer_base.Add(self.pnlParams, 1, wx.TOP | wx.EXPAND, 3)
        sizer_base.Add(self.pnlCorps, 1,  wx.EXPAND, 3)
        sizer_base.Add(self.pnlPied, 1, wx.ALL | wx.EXPAND, 3)
        sizer_base.AddGrowableCol(0)
        sizer_base.AddGrowableRow(2)
        self.SetSizer(sizer_base)

    def DeclareVariables(self):
        # Déclaration de toutes les variables découlant de la gestion de l'écran
        self.fichierIn = None
        self.isXlsx = False
        self.paramsBanque = None
        self.dicMatchColonnes = { 'olv':{}, 'lues':{} }
        self.lstColonnesOlv = []
        self.lstColonnesLues = []
        self.valide = False
        self.dicCtrls = {}

    def SetInitialValues(self):
        # accès simplifiés aux controles par leur pointeur dans dicCtrls
        for box in MATRICE_PARAMS:
            for dicCtrl in MATRICE_PARAMS[box]:
                name = dicCtrl['name']
                self.dicCtrls[name] = self.pnlParams.GetPnlCtrl(name,box[0])
        self.dicCtrls['chklstColonnesLues'] = self.pnlCorps.chklstColonnesLues
        self.dicCtrls['chklstColonnesOlv'] = self.pnlCorps.chklstColonnesOlv
        self.dicCtrls['radioSheets'] = self.pnlCorps.radioSheets
        self.dicCtrls['periode'] = self.pnlCorps.periode
        self.dicCtrls['txtInfoPeriode'] = self.pnlCorps.txtInfoPeriode
        self.dicCtrls['txtValide'] = self.pnlCorps.txtValide

        # Binds renvoyant en local
        self.dicCtrls['typeCarte'].Bind(wx.EVT_RADIOBUTTON, self.OnTypeCarte)
        self.dicCtrls['radioSheets'].rbox.Bind(wx.EVT_RADIOBOX,self.OnSheets)

        # récupère les values d'un anyctrl pour le Set qui n'est pas automatique
        ctrlTypeCarte = self.dicCtrls['typeCarte']
        ctrlTypeCarte.SetValues(ctrlTypeCarte.values)
        ctrlTypeCarte.SetValue(ctrlTypeCarte.values[self.typeCB])

        # autres controles à initialiser
        self.pnlParams.SetOneValue('nomFichier',self.nomFichier)
        self.pnlParams.SetOneValue('nomBanque',self.nomBanque)
        self.dicCtrls['radioSheets'].rbox.SetSelection(self.ixSheet)
        self.dicCtrls['btnOk'] = self.pnlPied.itemsBtns[1][0]
        self.OnBanque(None)
        self.OnFichier(None)
        self.OnTypeCarte(None)

    # ------------------- Gestion des actions -----------------------

    def OnFichier(self,event):
        # Nouveau nom de fichier, on ouvre le fichier et lit les feuilles présentes
        self.isXlsx = False
        self.nomFichier = self.pnlParams.GetOneValue('nomFichier')
        (typeFichier, self.fichierIn) = ximport.OpenFile(self.nomFichier)

        if typeFichier == 'xlsx':
            self.isXlsx = True
            choices = ximport.GetSheetNames(self.fichierIn)
            self.dicCtrls['radioSheets'].SetValues(choices)
            self.lstNomsSheets = [x for x in choices]
            self.OnSheets(None)
        else:
            # Les autres types de fichier seront gérés en aveugle lors de l'import
            self.isXlsx = False
            lstCol = ["-", ]
            self.pnlCorps.SetValuesChklst(self.dicCtrls['chklstColonnesLues'], lstCol)
            self.lstColonnesLues = []
            self.valide = True
            self.MatchColonnes()

    def OnBanque(self, event):
        # remet la première banque si banque saisie inconnue
        self.nomBanque = self.dicCtrls['nomBanque'].GetValue()
        if not self.nomBanque in self.dicCtrls['nomBanque'].values:
            self.nomBanque = self.dicCtrls['nomBanque'].values[0]
            self.pnlParams.SetOneValue('nomBanque', self.nomBanque)
        self.OnSheets(None)

    def OnTypeCarte(self,event):
        # gère les propriétées liées au type de carte
        typeCarte = self.dicCtrls['typeCarte'].GetValue()
        if typeCarte == self.dicCtrls['typeCarte'].values[0]:
            self.dicCtrls['dateCpta'].Enable(False)
            self.typeCB = False
        else:
            self.dicCtrls['dateCpta'].Enable(True)
            self.typeCB = True
            if self.dateMax:
                self.dicCtrls['dateCpta'].SetValue(self.dateMax)
        self.OnSheets(None)

    def OnForcerdte(self,event):
        self.dateMax = self.dicCtrls['dateCpta'].SetValue(self.dateMax)

    def OnSheets(self,event):
        # Ouverture de la feuille excel choisie, cherche les noms de colonnes à importer
        if not self.isXlsx:
            self.AfficheInfos()
            return
        # lit la feuille excel choisie
        nomSheet = self.dicCtrls['radioSheets'].GetValue()
        if len(nomSheet) > 1:
            sheet = ximport.GetOneSheet(self.fichierIn,nomSheet)
            lstCol = ximport.GetNomsCols(sheet,11)
            self.ixSheet = self.lstNomsSheets.index(nomSheet)
            self.pnlCorps.SetValuesChklst(self.dicCtrls['chklstColonnesLues'],lstCol)
            self.lstColonnesLues = lstCol
            self.MatchColonnes()

            cellDate = ximport.GetFirstCell(sheet,'date')
            self.GetDataProperties(sheet,cellDate)
        self.MatchColonnes()

    def GetFormats(self):
        try:
            self.lstColonnesOlv = FORMATS_IMPORT[self.nomBanque]['champs']
        except Exception as err:
            print(err)
            return
        if self.typeCB and 'champsCB' in FORMATS_IMPORT[self.nomBanque]:
            self.lstColonnesOlv = FORMATS_IMPORT[self.nomBanque]['champsCB']
        self.pnlCorps.SetValuesChklst(self.dicCtrls['chklstColonnesOlv'],
                                      self.lstColonnesOlv)

    def MatchColonnes(self):
        self.GetFormats()
        lstLues = [x for x in self.lstColonnesLues]
        lstOlv = self.lstColonnesOlv
        xformat.NormaliseNomChamps(lstLues)
        dic = { 'olv':{}, 'lues':{} }
        echec = False
        if len(lstOlv) == 0: echec = True
        for colOlv in lstOlv:
            if not colOlv: continue
            testCol = False
            for colLue in lstLues:
                if not colLue or not isinstance(colLue, str): continue
                if xformat.Supprespaces(colOlv.replace("-","")).lower() in colLue:
                    dic['olv'][colOlv] = colLue
                    dic['lues'][self.lstColonnesLues[lstLues.index(colLue)]] = colLue
                    testCol = True
                    break
            if testCol == False:
                echec = True
        self.valide = not echec
        self.pnlCorps.SetValide(self.valide)
        self.dicCtrls['btnOk'].Enable(self.valide)
        self.dicMatchColonnes = dic
        ctrlLues = self.dicCtrls['chklstColonnesLues']
        ctrlOlv =  self.dicCtrls['chklstColonnesOlv']
        self.pnlCorps.ChkValuesChklst(ctrlLues,list(dic['lues'].keys()))
        self.pnlCorps.ChkValuesChklst(ctrlOlv,list(dic['olv'].keys()))
        self.AfficheInfos()

    def GetDataProperties(self,sheet,cell):
        # Ajuste les infos concernant le fichier lu
        typ = datetime.datetime
        nbCells,dteMin,dteMax =ximport.GetOneColCellsProp(sheet,cell,typ=typ)
        if nbCells:
            self.dicCtrls['txtInfoPeriode'].SetLabel(f"{nbCells} lignes trouvées, période")
            self.nbLignes = nbCells
        if dteMin and dteMax:
            dteMin = dteMin.date()
            dteMax = dteMax.date()
            self.dicCtrls['periode'].SetValues((dteMin,dteMax))
            self.dicCtrls['dateCpta'].SetValue(f"{dteMax}")
            self.dateMax = dteMax

    def AfficheInfos(self):
        if self.valide:
            txtInfo = "Vous pouvez valider pour retourner à l'écran précédent"
        elif not self.isXlsx:
            txtInfo = "Vous pouvez abandonner pour retourner à l'écran précédent"
        else:
            txtInfo = INFO_OLV
        self.pnlPied.SetItemsInfos(txtInfo)
        return self.valide

    def UpdateDicOptions(self,dicOptions):
        # Appellé par externe pour retourner les params
        dicOptions['nomFichier'] = self.nomFichier
        dicOptions['isXlsx'] = self.isXlsx
        dicOptions['ixSheet'] = self.ixSheet
        dicOptions['nomBanque'] = self.nomBanque
        dicOptions['typeCB'] = self.typeCB
        dicOptions['lstColonnesLues'] = self.lstColonnesLues
        dicOptions['dateMax'] = self.dateMax
        dicOptions['nbLignes'] = self.nbLignes

#------------------------ Lanceur de test  -------------------------------------------
if __name__ == '__main__':
    app = wx.App(0)
    os.chdir("..")
    fichier = "C:\\temp\\RELEVE.xlsx"
    dlg = Dialog(None,nomFichier=fichier, nomBanque='Crédit Mutuel',
                 ixSheet=0,typeCB=True)
    dlg.ShowModal()
    app.MainLoop()
