#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -------------------------------------------------------------
# Application :    Noelite, transposition de fichier comptable
# Usage : Reécrire dans un formatage différent avec fonctions de transposition
# Auteur:          Jacques BRUNEL
# Licence:         Licence GNU GPL
# -------------------------------------------------------------

import wx
import datetime
import xpy.xGestionConfig               as xgc
import xpy.xUTILS_SaisieParams          as xusp
from DLG_Transpose_options import Dialog as dlgOptions
import GLOBAL
from xpy.outils                 import xformat,xbandeau,ximport
from srcNoelite                 import UTILS_Compta
from xpy.ObjectListView import xGTE
from xpy.ObjectListView.ObjectListView  import ColumnDefn

#---------------------- Paramètres du programme -------------------------------------

TITRE = "Transposition de ficher avec intervention possible"
INTRO = "Importez un fichier, puis complétez l'information dans le tableau avant de l'exporter dans un autre format"

# Infos d'aide en pied d'écran
DIC_INFOS = {'date':"Flèche droite pour le mois et l'année, Entrée pour valider.\nC'est la date de réception du règlement, qui sera la date comptable",
            'compte':    "<F4> Choix d'un compte fournisseur, ou saisie directe du compte",
            'libelle':     "S'il est connu, précisez l'affectation (objet) du règlement",
            'montant':      "Montant en €",
             }

# Info par défaut
INFO_OLV = "<Suppr> <Inser> <Ctrl C> <Ctrl V>"

# Fonctions de transposition entrée à gérer pour chaque item FORMAT_xxxx pour les spécificités
def ComposeFuncImp(dicParams,donnees,champsOut,compta,table, parent=None):
    # 'in' est le fichier entrée colonnes lues, 'out' est l'OLV
    lstOut = []
    nomBanque = dicParams['fichiers']['nomBanque']
    noPiece = dicParams['p_export']['noPiece']
    champsAttendus = FORMATS_IMPORT[nomBanque]['champs']
    champsIn = dicParams.get("lstColonnesLues", None)
    # pour les fichiers non xlsx on n'a pas lu de nom de colonne
    if not champsIn:
        champsIn = [x for x in champsAttendus]

    if 'lignesentet' in FORMATS_IMPORT[nomBanque].keys():
        nblent = FORMATS_IMPORT[nomBanque]['lignesentete']
    else: nblent = 0
    xformat.NormaliseNomChamps(champsIn)
    for ix in range(len(champsIn)):
        if champsAttendus[ix].replace("-","") in champsIn[ix]:
            champsIn


    # teste la cohérence de la première ligne importée
    if nblent>0:
        if len(champsIn) != len(donnees[nblent]):
            wx.MessageBox("Problème de fichier d'origine\n\nLe paramétrage attend les colonnes suivantes:\n\t%s"%str(champsIn) \
                            + "\mais la ligne %d comporte %d champs :\n%s"%(nblent,len(donnees[nblent]),donnees[nblent]))
            return []

    ixLibelle = champsOut.index('libelle')
    ixCompte = champsOut.index('compte')
    ixAppel = champsOut.index('appel')
    ixLibCpt = champsOut.index('libcpt')

    def enrichiLigne(ligne):
        # composition des champs en liens avec la compta
        if ligne[ixLibelle]:
            record = compta.GetOneByMots(table,text=ligne[ixLibelle])
        else: record = None
        # la recherche de compte a matché
        if record:
            ligne[ixCompte] = record[0]
            ligne[ixAppel]  = record[1]
            ligne[ixLibCpt] = record[2]
        else:
            ligne[ixAppel] = compta.filtreTest

    def hasLibelle(ligne):
        # vérifie la présence d'un montant dans au moins un champ attendu en numérique
        lstIxChamps = []
        for champ in champsIn:
            if champ in ('libelle','designation'):
                lstIxChamps.append(champsIn.index(champ))
        ok = False
        for ix in lstIxChamps:
            try:
                if len(ligne[ix]) > 0:
                    ok = True
                    break
            except:
                pass
        return ok

    def hasMontant(ligne):
        # vérifie la présence d'un montant dans au moins un champ attendu en numérique
        lstIxChamps = []
        for champ in champsIn:
            if champ in ('montant','debit','credit'):
                lstIxChamps.append(champsIn.index(champ))
        ok = False
        for ix in lstIxChamps:
            try:
                xformat.ToFloat(ligne[ix])
                ok = True
                break
            except:
                pass
        return ok

    def addMontant(old,ajout,sens=+1,typeRetour=float):
        new = xformat.ToFloat(old) + (xformat.ToFloat(ajout) * sens)
        return typeRetour(new)

    # déroulé du fichier entrée
    ko = None
    txtInfo = "Traitement %d lignes..."%len(donnees[nblent:])
    image = wx.ArtProvider.GetBitmap(wx.ART_TIP, wx.ART_OTHER, (16, 16))
    parent.pnlPied.SetItemsInfos(txtInfo, image)
    for ligne in donnees[nblent:]:
        if not hasMontant(ligne) or not hasLibelle((ligne)):
            continue
        if ko: break
        ligneOut = []
        for champ in champsOut:
            valeur = None
            # traitements spécifiques selon destination
            if champ == 'date':
                if 'date' in champsIn:
                    if dicParams['typeCB']:
                        valeur = xformat.FinDeMois(ligne[champsIn.index(champ)])
                    else:
                        valeur = ligne[champsIn.index(champ)]
                        if isinstance(valeur, datetime.datetime):
                            valeur = valeur.date()
            elif champ == 'noPiece':
                    valeur = noPiece
            elif champ == 'montant':
                if 'montant' in champsIn:
                    valeur = xformat.NoLettre(ligne[champsIn.index(champ)])
                if '-debit' in champsIn:
                    valeur = addMontant(valeur,ligne[champsIn.index('-debit')],+1)
                if 'debit' in champsIn:
                    valeur = addMontant(valeur,ligne[champsIn.index('debit')],-1)
                if 'credit' in champsIn:
                    valeur = addMontant(valeur,ligne[champsIn.index('credit')],+1)
            elif champ  == 'libelle':
                if 'date' in champsIn and 'libelle' in champsIn:
                    if dicParams['typeCB']:
                        # ajout du début de date dans le libellé
                        dte = ligne[champsIn.index('date')]
                        if dte:
                            if isinstance(dte,(datetime.date,datetime.datetime)):
                                prefixe = "%02d/%02d"%(dte.day,dte.month)
                            else:
                                prefixe = dte.strip()+' '
                            if ligne[champsIn.index('libelle')]:
                                valeur = prefixe + ligne[champsIn.index('libelle')]
                            else:
                                ko = True
                                break
                    else:
                        valeur = ligne[champsIn.index('libelle')]
            # récupération des champs homonymes
            elif champ in champsIn:
                valeur = ligne[champsIn.index(champ)]
            ligneOut.append(valeur)
        if not ko:
            if compta:
                enrichiLigne(ligneOut)
            lstOut.append(ligneOut)
            txtInfo = " %d lignes traitées sur %d" %( len(lstOut),len(donnees[nblent:]))
            parent.pnlPied.SetItemsInfos(txtInfo, image)

    return lstOut

# formats possibles des fichiers en entrées, utiliser les mêmes codes des champs pour les 'UtilCompta.ComposeFuncExp'
FORMATS_IMPORT = GLOBAL.GetFormatsImport(ComposeFuncImp)

# Description des paramètres à choisir en haut d'écran
MATRICE_PARAMS = {
("fichiers","Fichier à Importer"): [
    {'name': 'nomFichier', 'genre': 'dirfile', 'label': "Fichier d'origine",'value': "*.xlsx",
         'help': "Pointez le fichier contenant les valeurs à transposer",
         'ctrlAction': 'OnFichier',
         #'btnAction': 'inutile', # redirigé vers ctrlAction (car genre dirfile)
         'size':(450,30)},
    {'name': 'nomBanque', 'genre': 'Enum', 'label': 'Banque importée',
                    'help': "La banque détermine le format d'import", 'value':0,
                    'values':[x for x in FORMATS_IMPORT.keys()],
                    'size':(350,30)},
    ],
("p_compta", "Compta en ligne"): [
    {'name': 'compta', 'genre': 'Combo', 'label': 'Compta','ctrlAction':'OnCtrlCompta',
                    'help': "Compta choisie parmi les connexions gérées par la gestion des bases",'size':(230,30),
                    'values':UTILS_Compta.GetLstComptas(), 'txtSize': 50,},
    {'name': 'journal', 'genre': 'Combo', 'label': 'Journal','ctrlAction':'OnCtrlJournal',
     'help': "Code journal utilisé dans la compta",'size':(250,30),'value':'BQ',
     'values':['BQ','CM','LCL','LBP','CCP'], 'txtSize': 50,
     'btnLabel': "...", 'btnHelp': "Cliquez pour choisir un journal",
     'btnAction': 'OnBtnJournal'},
    ],
("p_export", "Destination Export"): [
    {'name': 'noPiece',
     'genre': 'String',
     'label': 'No de pièce commun',
     'ctrlAction': "OnPiece",
     'txtSize': 130,
     'help': "Préciser avant l'import le dernier numéro de pièce à incrémenter",'size':(250,30)},
    {'name': 'contrepartie', 'genre': 'String', 'label': 'Contrepartie',
     'help': "Code comptable du compte de contrepartie de la banque",'size':(250,30)},
    {'name': 'formatexp', 'genre': 'Enum', 'label': 'Format export',
         'help': "Le choix est limité par la programmation", 'value':0,
         'values':[x for x in UTILS_Compta.FORMATS_EXPORT.keys()],
         'ctrlAction':'OnChoixExport',
         'size':(300,30)}
    ],
("vide", ""): [
    ]
}

# description des boutons en pied d'écran et de leurs actions
def GetBoutons(dlg):
    return  [
        {'name': 'btnImp', 'label': "Importer\nRelevé",
         'help': "Cliquez ici pour lancer l'importation du fichier date = date comptable",
         'size': (120, 35), 'image': wx.ART_UNDO, 'onBtn': dlg.OnImporter},
        {'name': 'btnExp', 'label': "Exporter\nfichier",
            'help': "Cliquez ici pour lancer l'exportation du fichier selon les paramètres que vous avez défini",
            'size': (120, 35), 'image': wx.ART_REDO,'onBtn':dlg.OnExporter},
        {'name':'btnOK','ID':wx.ID_ANY,'label':"Quitter",'help':"Cliquez ici pour fermer la fenêtre",
            'size':(120,35),'image':"xpy/Images/32x32/Quitter.png",'onBtn':dlg.OnFermer}
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
        #('pos','size','style','name','matrice','donnees','lblBox')
        kwds = {
                'name':"PNL_params",
                'matrice':MATRICE_PARAMS,
                'lblBox':"Paramètres à saisir",
                'boxesSizes': [None, (200, 80), (240, 110),None],
                'pathdata':"srcNoelite/Data",
                'nomfichier':"compta",
                'nomgroupe':"transpose"
                }
        super().__init__(parent, **kwds)
        self.Init()

class PNL_corps(xGTE.PNL_corps):
    #panel olv avec habillage optionnel pour des boutons actions (à droite) des infos (bas gauche) et boutons sorties
    def __init__(self, parent, dicOlv,*args, **kwds):
        xGTE.PNL_corps.__init__(self,parent,dicOlv,*args,**kwds)
        self.ctrlOlv.Choices={}
        self.flagSkipEdit = False
        self.oldRow = None

    def OnEditStarted(self,code,track=None,editor=None):
        # affichage de l'aide
        if code in DIC_INFOS.keys():
            self.parent.pnlPied.SetItemsInfos( DIC_INFOS[code],
                                               wx.ArtProvider.GetBitmap(wx.ART_FIND, wx.ART_OTHER, (16, 16)))
        else:
            self.parent.pnlPied.SetItemsInfos( INFO_OLV,wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)))
        row, col = self.ctrlOlv.cellBeingEdited
        if not self.oldRow: self.oldRow = row
        if row != self.oldRow:
            track = self.ctrlOlv.GetObjectAt(self.oldRow)
            track.valide = True
        track = self.ctrlOlv.GetObjectAt(row)

        # conservation de l'ancienne valeur
        track.oldValue = None
        try:
            eval("track.oldValue = track.%s"%code)
        except: pass

    def OnEditFinishing(self,code=None,value=None,parent=None):
        self.parent.pnlPied.SetItemsInfos( INFO_OLV,wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)))
        # flagSkipEdit permet d'occulter les évènements redondants. True durant la durée du traitement
        row, col = self.ctrlOlv.cellBeingEdited
        if self.flagSkipEdit : return
        self.flagSkipEdit = True
        track = self.ctrlOlv.GetObjectAt(row)
        ret = None

        # si pas de saisie on passe
        if (not value) or track.oldValue == value:
            self.flagSkipEdit = False
            return

        # Traitement des spécificités selon les zones
        if code == 'compte':
            record = self.parent.compta.GetOneAuto('comptes',value)
            # tentative de recherche mannuelle
            newfiltre = self.parent.compta.filtreTest
            if not record:
                record = self.parent.compta.ChoisirItem('comptes',newfiltre)
            # alimente les champs ('compte','appel','libelle'), puis répand l'info
            def majuscule(value):
                if not value: value = ""
                return value.upper()

            if record:
                ret = majuscule(record[0])
                track.compte = majuscule(record[0])
                track.exappel = track.appel
                track.appel = majuscule(record[1])
                track.libcpt = record[2]
                # la valeur d'origine va être strockée par parent  pour cellEditor
                if parent:
                    parent.valeur = track.compte
                self.ctrlOlv.Refresh()
            else:
                track.appel = ''
                track.libcpt = ''
        # enlève l'info de bas d'écran
        self.parent.pnlPied.SetItemsInfos( INFO_OLV,wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)))
        self.flagSkipEdit = False
        return ret

    def OnEditFunctionKeys(self,event):
        row, col = self.ctrlOlv.cellBeingEdited
        code = self.ctrlOlv.lstCodesColonnes[col]
        if event.GetKeyCode() == wx.WXK_F4 and code == 'compte':
            # F4 Choix compte
            track = self.ctrlOlv.GetObjectAt(row)
            value = track.compte
            item = self.parent.compta.ChoisirItem(table='comptes',filtre=value)
            if item:
                track.compte = item[0]
                self.OnEditFinishing('compte',item[0])

    def SauveLigne(self,*args,**kwds):
        return True

class PNL_pied(xGTE.PNL_pied):
    #panel infos (gauche) et boutons sorties(droite)
    def __init__(self, parent, dicPied, **kwds):
        xGTE.PNL_pied.__init__(self,parent, dicPied, **kwds)

class Dialog(xusp.DLG_vide):
    # ------------------- Composition de l'écran de gestion----------
    def __init__(self,*args):
        super().__init__(self,name='DLG_Transposition_fichier',size=(1200,700))
        self.dicOptions = GLOBAL.DIC_OPTIONS
        self.ctrlOlv = None
        self.txtInfo =  "Non connecté à une compta"
        self.dicOlv = self.GetParamsOlv()
        self.Init()
        self.Sizer()


    # Récup des paramètrages pour composer l'écran
    def GetParamsOlv(self):
        # définition de l'OLV
        dicOlv = {'lstColonnes': GetOlvColonnes(self)}
        dicOlv.update(GetOlvOptions(self))
        return dicOlv

    # Initialisation des panels
    def Init(self):
        # boutons de bas d'écran - infos: texte ou objet window.  Les infos sont  placées en bas à gauche
        lstInfos = [ wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)),self.txtInfo]
        dicPied = {'lstBtns': GetBoutons(self), "lstInfos": lstInfos}

        # lancement de l'écran en blocs principaux
        self.pnlBandeau = xbandeau.Bandeau(self,TITRE,INTRO,nomImage="xpy/Images/32x32/Matth.png")
        self.pnlParams = PNL_params(self)
        self.pnlOlv = PNL_corps(self, self.dicOlv)
        self.pnlPied = PNL_pied(self, dicPied)
        self.ctrlOlv = self.pnlOlv.ctrlOlv
        # connextion compta et affichage bas d'écran
        self.compta = self.GetCompta()
        self.table = self.GetTable()
        self.Bind(wx.EVT_CLOSE,self.OnFermer)
        #self.OnFichier(None)

    def Sizer(self):
        sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=0, hgap=0)
        sizer_base.Add(self.pnlBandeau, 1, wx.TOP | wx.EXPAND, 3)
        sizer_base.Add(self.pnlParams, 1, wx.TOP | wx.EXPAND, 3)
        sizer_base.Add(self.pnlOlv, 1, wx.TOP | wx.EXPAND, 3)
        sizer_base.Add(self.pnlPied, 0, wx.ALL | wx.EXPAND, 3)
        sizer_base.AddGrowableCol(0)
        sizer_base.AddGrowableRow(2)
        self.SetSizer(sizer_base)
        self.CenterOnScreen()

    # ------------------- Gestion des actions -----------------------
    def OnFichier(self,evt):
        for param in ['nomFichier', 'nomBanque']:
            self.dicOptions[param] = self.pnlParams.GetOneValue(param) 
        dlg = dlgOptions(None,**self.dicOptions)
        ret = dlg.ShowModal()
        if ret == wx.OK:
            # Récupère les options choisies
            dlg.UpdateDicOptions(self.dicOptions)
            for param in ['nomFichier', 'nomBanque']:
                self.pnlParams.SetOneValue(param,self.dicOptions[param])
        dlg.Destroy()

    def OnPiece(self,evt):
        # la modif du numéro de pièce s'applique à toutes les lignes visibles
        valeur = self.pnlParams.GetOneValue('noPiece',codeBox='p_export')
        for track in self.ctrlOlv.innerList:
            track.noPiece = valeur
        self.ctrlOlv.RepopulateList()

    def OnCtrlJournal(self,evt):
        # tronque pour ne garder que le code journal sur trois caractères maxi
        valeur = self.pnlParams.GetOneValue('journal').upper()
        if self.compta:
            item = self.compta.GetOneAuto(table='journaux',filtre=valeur)
            if item:
                self.pnlParams.SetOneValue('journal',valeur)
                self.pnlParams.SetOneValue('contrepartie',item[2])
                self.pnlParams.Refresh()
            else:
                self.pnlParams.SetOneValue('journal',"")

    def OnBtnJournal(self,evt):
        if self.compta:
            item = self.compta.ChoisirItem(table='journaux')
            if item:
                self.pnlParams.SetOneValue('journal',item[0])
                self.pnlParams.SetOneValue('contrepartie',item[2])

    def OnCtrlCompta(self,evt):
        self.compta = self.GetCompta()

    def OnChoixExport(self,evt):
        self.compta = self.GetCompta()
        self.table = self.GetTable()

    def OnNameDB(self,evt):
        # appelé par DLG_listeConfigs (save params)
        return

    def InitOlv(self):
        self.pnlParams.GetValues()
        self.ctrlOlv.lstColonnes = GetOlvColonnes(self)
        self.ctrlOlv.lstCodesColonnes = self.ctrlOlv.GetLstCodesColonnes()
        self.ctrlOlv.InitObjectListView()
        self.ctrlOlv.MAJ()
        self.Refresh()

    def GetDonneesIn(self):
        # importation des donnéees du fichier entrée
        dic = self.pnlParams.GetValues()
        nomFichier = dic['fichiers']['nomFichier']
        lstNom = nomFichier.split('.')
        if lstNom[-1] in ('csv','txt'):
            entrees = ximport.GetFichierCsv(nomFichier)
        elif lstNom[-1] == 'xlsx':
            entrees = ximport.GetFichierXlsx(**self.dicOptions)
        elif lstNom[-1] == 'xls':
            try:
                entrees = ximport.GetFichierXls(nomFichier)
            except Exception as err:
                mess = "Echec ouverture\n\n%s" % err
                mess += "\nTentative d'ouverture en csv"
                wx.MessageBox(mess,"Anomalie")
                entrees = ximport.GetFichierCsv(nomFichier)
        else:
            mess = "Le fichier n'est pas csv, xls ou xlsx"
            wx.MessageBox(mess,"IMPOSSIBLE")
            entrees = None
        return entrees

    def GetCompta(self):
        dic = self.pnlParams.GetValues()
        nomCompta = dic['p_compta']['compta'].lower()
        compta = UTILS_Compta.Compta(self, nomCompta=nomCompta)
        if not compta.db:
            compta = None
        elif type(compta.db.erreur) == int  and compta.db.erreur > 0:
            test2 = compta.db.erreur
            compta = None
        if not compta:
            txtInfo = "Echec d'accès à la compta associée à %s!!!"%nomCompta
            image = wx.ArtProvider.GetBitmap(wx.ART_ERROR, wx.ART_OTHER, (16, 16))
        else:
            txtInfo = "Connecté à la compta %s..."%nomCompta
            image = wx.ArtProvider.GetBitmap(wx.ART_TIP, wx.ART_OTHER, (16, 16))
        self.pnlPied.SetItemsInfos(txtInfo,image)
        # appel des journaux
        if compta:
            lstJournaux = compta.GetJournaux()
            lstCodesJournaux = [x[0] for x in lstJournaux]
            box = self.pnlParams.GetBox('p_compta')
            valeur = self.pnlParams.lstBoxes[1].GetOneValue('journal')
            box.SetOneSet('journal',lstCodesJournaux)
            if len(valeur)>0 and len(lstCodesJournaux) > 0 and not valeur in lstCodesJournaux:
                possibles = [x for x in lstCodesJournaux if valeur[0] == x[0]]
                if len(possibles) > 0:
                    box.SetOneValue('journal',possibles[0])
        pnlJournal = self.pnlParams.GetPnlCtrl('journal', 'p_compta')
        x = False
        if compta : x = True
        pnlJournal.btn.Enable(x)
        return compta

    def GetTable(self):
        # récupère la table par défaut du format import choisi
        dicParams = self.pnlParams.GetValues()
        formatIn = dicParams['fichiers']['nomBanque']
        if not formatIn in FORMATS_IMPORT:
            return
        return FORMATS_IMPORT[formatIn]['table']

    def OnImporter(self,event):
        dicParams = self.pnlParams.GetValues()
        dicParams['lstColonnesLues'] = self.dicOptions['lstColonnesLues']
        dicParams['typeCB'] = self.dicOptions['typeCB']
        formatIn = dicParams['fichiers']['nomBanque']
        self.table = FORMATS_IMPORT[formatIn]['table']
        entrees = self.GetDonneesIn()
        if not entrees:
            return
        self.ctrlOlv.lstDonnees = FORMATS_IMPORT[formatIn]['fonction'](dicParams,entrees,
                                self.ctrlOlv.lstCodesColonnes,
                                self.compta,self.table, parent=self)
        self.InitOlv()

    def OnExporter(self,event):
        nbl = len(self.ctrlOlv.innerList)
        if nbl == 0:
            mess = "Aucune ligne affichée\n\nRien à exporter"
            wx.MessageBox(mess,"Export impossible")
            return mess

        params = self.pnlParams.GetValues(fmtDD=False)
        mess = "Journal '%s' - contrepartie '%s'\n\n"%(params['journal'],params['contrepartie'])
        if len(params['journal'].strip()) == 0 or len(params['contrepartie'].strip()) == 0:
            mess += "Le code journal ou la contrepartie sont mal renseignés"
            wx.MessageBox(mess,"Export impossible")
            return mess
        mess += "Confirmez-vous l'export ?"
        dlg = wx.MessageDialog(self,mess ,"Lancement de l'export")
        ret = dlg.ShowModal()
        if ret != wx.ID_OK : return "abandon"
        champsIn = self.ctrlOlv.lstCodesColonnes
        donnees = []
        # calcul des débit et crédit des pièces
        totDebits, totCredits = 0.0, 0.0
        nonValides = 0
        # constitution de la liste des données à exporter
        lstTracks = [x for x in self.ctrlOlv.innerList if x.date!="" ]
        for track in lstTracks:
            if not track.compte or len(track.compte)==0:
                track.comte = '471'
                nonValides +=1
            if isinstance(track.montant,str):
                track.montant = track.montant.replace(',', '.')
            montant = float(track.montant)
            if round(montant,2) == 0.0:
                continue
            elif montant > 0.0:
                totCredits += montant
            else:
                totDebits -= montant
            donnees.append(track.donnees)

        if nonValides > 0:
            ret = wx.MessageBox("%d lignes sans no de compte!\n\nelles seront mises en compte d'attente 471"%nonValides,
                          "Confirmez ou abandonnez",style= wx.YES_NO)
            if not ret == wx.YES:
                return wx.CANCEL

        dicParams = self.pnlParams.GetValues()
        exp = UTILS_Compta.Export(self,self.compta)
        ret = exp.Exporte(dicParams,
                          donnees,
                          champsIn)
        if not ret == wx.OK:
            return ret

        # affichage résultat
        solde = xformat.FmtMontant(totDebits - totCredits,lg=12)
        wx.MessageBox("Fin de transfert\n\nDébits  du relevé: %s\nCrédits du relevé:%s"%(xformat.FmtMontant(totDebits,lg=12),
                                                                     xformat.FmtMontant(totCredits,lg=12))+
                      "\nMouvements période:   %s"%solde)

        # sauvegarde des params
        self.pnlParams.SauveParams(close=True)

#------------------------ Lanceur de test  -------------------------------------------

if __name__ == '__main__':
    import os
    app = wx.App(0)
    os.chdir("..")
    dlg = Dialog()
    dlg.ShowModal()
    app.MainLoop()
