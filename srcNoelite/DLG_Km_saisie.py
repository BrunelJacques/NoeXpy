#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------------
# Application :    Noelite, grille de saisie des conso de km
# Usage : import d'un saisie excel, puis export d'écritures compables analystiques
# Auteur:          Jacques BRUNEL
# Licence:         Licence GNU GPL
# --------------------------------------------------------------------------------------

import wx
import datetime
import xpy.xGestion_TableauEditor       as xgte
import xpy.xGestionConfig               as xgc
import xpy.xUTILS_SaisieParams          as xusp
import srcNoelite.UTILS_Noegest         as nunoegest
import srcNoelite.UTILS_Compta          as nucompta
import srcNoelite.UTILS_Utilisateurs    as nuutil
from xpy.outils.ObjectListView  import ColumnDefn, CellEditor
from xpy.outils                 import xformat,xbandeau,ximport,xexport

#---------------------- Paramètres du programme -------------------------------------
MODULE = 'DLG_Transposition_fichier'
TITRE = "Saisie des consommations de km"
INTRO = "Importez un fichier ou saisissez les consommations de km, avant de l'exporter dans un autre format"

# Infos d'aide en pied d'écran
DIC_INFOS = {'date':"Flèche droite pour le mois et l'année, Entrée pour valider.\nC'est la date",
            'vehicule':    "<F4> Choix d'un véhicule, ou saisie directe de l'abrégé",
            'IDtiers':    "<F4> Choix d'une section ou d'un tiers pour l'affectation du coût",
            'dtkmdeb':     "formats date acceptés : j/m/a jjmmaa jjmmaaaa",
            'dtkmfin':     "formats date acceptés : j/m/a jjmmaa jjmmaaaa",
            'observation':     "S'il y a lieu précisez des circonstances particulières",
            'montant':      "Montant en €",
             }

# Info par défaut
INFO_OLV = "<Suppr> <Inser> <Ctrl C> <Ctrl V>"

# Fonctions de transposition entrée à gérer pour chaque item FORMAT_xxxx pour les spécificités
def ComposeFuncImp(dlg,entete,donnees):
    # Fonction import pour composition
    colonnesIn =    ["Code Véhicule       ","Date Début     ","Membre        ","Partenaire  ","Activité ",
                     "KM Début       ","KM Fin   "]
    champsIn =      ['vehicule','dtkmdeb','membre','partenaire','activite','kmdeb','kmfin']
    lstOut = [] # sera composé selon champs out
    champsOut = dlg.ctrlOlv.lstCodesColonnes
    # teste la cohérence de la première ligne importée
    mess = "Vérification des champs trouvés,\n\n"
    mess += '{:_<22} '.format('ATTENDU') + 'TROUVÉ\n\n'
    for ix in range(len(colonnesIn)):
        mess += '{:_<26} '.format(colonnesIn[ix] ) + str(entete[ix])+'\n'
    ret = wx.MessageBox(mess,"Confirmez le fichier ouvert...",style=wx.YES_NO)
    if ret != wx.YES:
        return lstOut
    # déroulé du fichier entrée, composition des lignes de sortie
    for ligneIn in donnees:
        if len(champsIn) < len(ligneIn):
            # ligneIn batarde ignorée
            continue
        ligneOut = [None,]*len(champsOut)
        #champs communs aux listIn et listOut
        for champ in ('vehicule','dtkmdeb','kmdeb','kmfin'):
            value = ligneIn[champsIn.index(champ)]
            if isinstance(value,datetime.datetime):
                value = datetime.date(value.year,value.month,value.day)
            ligneOut[champsOut.index(champ)] = value
        # calcul auto d'une date fin de mois
        findemois = xformat.FinDeMois(ligneIn[champsIn.index('dtkmdeb')])
        ligneOut[champsOut.index('dtkmfin')] = findemois
        # recherche champ libellé véhicule
        dicVehicule = dlg.noegest.GetVehicule(mode='auto',filtre=ligneIn[champsIn.index('vehicule')])
        if dicVehicule:
            ligneOut[champsOut.index('IDvehicule')] = dicVehicule['idanalytique']
            ligneOut[champsOut.index('vehicule')] =  dicVehicule['abrege']
            ligneOut[champsOut.index('nomvehicule')] = dicVehicule['nom']
        # détermine le type de tiers
        if ligneIn[champsIn.index('activite')]:
            ligneOut[champsOut.index('typetiers')] = 'A'
            ligneOut[champsOut.index('IDtiers')] =  ligneIn[champsIn.index('activite')]
            dicActivite = dlg.noegest.GetActivite(mode='auto', filtre=ligneIn[champsIn.index('activite')])
            if dicActivite:
                ligneOut[champsOut.index('IDtiers')] = dicActivite['idanalytique']
                ligneOut[champsOut.index('nomtiers')] = dicActivite['nom']
        elif ligneIn[champsIn.index('partenaire')]:
            ligneOut[champsOut.index('typetiers')] = 'P'
            ligneOut[champsOut.index('nomtiers')] = ligneIn[champsIn.index('partenaire')]
        elif ligneIn[champsIn.index('membre')]:
            ligneOut[champsOut.index('typetiers')] = 'C'
            ligneOut[champsOut.index('nomtiers')] = ligneIn[champsIn.index('membre')]
        # calcul conso
        kmdeb = xformat.Nz(ligneOut[champsOut.index('kmdeb')])
        kmfin = xformat.Nz(ligneOut[champsOut.index('kmfin')])
        if kmdeb <= kmfin and kmdeb > 0:
            ligneOut[champsOut.index('conso')] = kmfin - kmdeb
        lstOut.append(ligneOut)
    return lstOut

# Description des paramètres à choisir en haut d'écran
MATRICE_PARAMS = {
("filtres","Filtre des données"): [
    {'name': 'cloture', 'genre': 'Enum', 'label': 'Exercice clôturant',
                    'help': "Choisir un exercice ouvert pour pouvoir saisir, sinon il sera en consultation", 'value':0,
                    'values': [],
                    'ctrlAction':'OnCloture',
                    'size':(300,30)},
    {'name': 'datefact', 'genre': 'Enum', 'label': 'Date facturation',
                    'help': "Date de facturation pour l'export ou pour consulter l'antérieur",
                    'value':0,
                    'values':[],
                    'ctrlAction': 'OnDateFact',
                    'size':(300,30)},
    {'name': 'vehicule', 'genre': 'Enum', 'label': "Véhicule",
                    'help': "Pour filtrer les écritures d'un seul véhicule, saisir sa clé d'appel",
                    'value':0, 'values':['',],
                    'ctrlAction': 'OnDateFact',
                    'size':(300,30)},
    ],
("compta", "Paramètres export"): [
    {'name': 'formatexp', 'genre': 'Enum', 'label': 'Format export',
                    'help': "Le choix est limité par la programmation", 'value':0,
                    'values':[x for x in nucompta.FORMATS_EXPORT.keys()],
                    'ctrlAction':'OnChoixExport',
                    'size':(300,30)},
    {'name': 'journal', 'genre': 'Combo', 'label': 'Journal','ctrlAction':'OnCtrlJournal',
                    'help': "Code journal utilisé dans la compta",'size':(350,30),
                    'value':'CI','values':['CI','OD'],
                    'btnLabel': "...", 'btnHelp': "Cliquez pour choisir un journal",
                    'btnAction': 'OnBtnJournal'},
    {'name': 'forcer', 'genre': 'Bool', 'label': 'Exporter les écritures déjà transférées','value':False,
     'help': "Pour forcer un nouvel export d'écritures déjà transférées!", 'size': (250, 30)},
    ],
("comptes", "Comptes à mouvementer"): [
    {'name': 'revente', 'genre': 'String', 'label': 'Vente interne km',
     'help': "Code comptable du compte crédité de la rétrocession", 'size': (250, 30),
     'btnLabel': "...", 'btnHelp': "Cliquez pour choisir un compte comptable",
     'btnAction': 'OnBtnCompte'},
    {'name': 'achat', 'genre': 'String', 'label': 'Achat interne km',
     'help': "Code comptable du compte débité de la rétrocession interne", 'size': (250, 30),
     'btnLabel': "...", 'btnHelp': "Cliquez pour choisir un compte comptable",
     'btnAction': 'OnBtnCompte'},
    {'name': 'tiers', 'genre': 'string', 'label': 'km faits par tiers',
     'help': "Code comptable du compte crédité de la rétrocession à refacturer aux clients", 'size': (250, 30),
     'btnLabel': "...", 'btnHelp': "Cliquez pour choisir un compte comptable",
     'btnAction': 'OnBtnCompte'},

]}

# description des boutons en pied d'écran et de leurs actions
def GetBoutons(dlg):
    return  [
                {'name': 'btnImp', 'label': "Importer\nfichier",
                    'help': "Cliquez ici pour lancer l'importation du fichier de km consommés",
                    'size': (120, 35), 'image': wx.ART_UNDO,'onBtn':dlg.OnImporter},
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
            ColumnDefn("IDconso", 'centre', 0, 'IDconso',
                       isEditable=False),
            ColumnDefn("IDvehicule", 'centre', 0, 'IDvehicule',
                       isEditable=False),
            ColumnDefn("Véhicule", 'center', 70, 'vehicule', isSpaceFilling=False,),
            ColumnDefn("Nom Véhicule", 'left', 120, 'nomvehicule',
                       isSpaceFilling=True, isEditable=False),
            ColumnDefn("Type Tiers", 'center', 40, 'typetiers', isSpaceFilling=False,valueSetter='A',
                       cellEditorCreator=CellEditor.ChoiceEditor,choices=['A analytique','C client','P partenaire' ] ),
            ColumnDefn("Activité", 'center', 60, 'IDtiers', isSpaceFilling=False),
            ColumnDefn("Nom tiers/activité", 'left', 130, 'nomtiers',
                       isSpaceFilling=True, isEditable=False),
            ColumnDefn("Date Début", 'center', 85, 'dtkmdeb',
                       stringConverter=xformat.FmtDate, isSpaceFilling=False),
            ColumnDefn("KM début", 'right', 90, 'kmdeb', isSpaceFilling=False,valueSetter=0,
                       stringConverter=xformat.FmtInt),
            ColumnDefn("Date Fin", 'center', 85, 'dtkmfin',
                       stringConverter=xformat.FmtDate, isSpaceFilling=False),
            ColumnDefn("KM fin", 'right', 90, 'kmfin', isSpaceFilling=False,valueSetter=0,
                       stringConverter=xformat.FmtInt),
            ColumnDefn("KM conso", 'right', 80, 'conso', isSpaceFilling=False,valueSetter=0,
                       stringConverter=xformat.FmtInt, isEditable=False),
            ColumnDefn("Observation", 'left', 150, 'observation',
                       isSpaceFilling=True),
            ]

# paramètre les options de l'OLV
def GetOlvOptions(dlg):
    return {
            'minSize': (600,300),
            'checkColonne': False,
            'recherche': True,
            'autoAddRow':True,
            'msgIfEmpty':"Saisir ou importer un fichier !",
            'dictColFooter': {'tiers': {"mode": "nombre", "alignement": wx.ALIGN_CENTER},
                              'observation': {"mode": "texte", "alignement": wx.ALIGN_LEFT, "texte": 'km imputés'},
                              'conso': {"mode": "total"}, }
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
                'lblBox':None,
                'pathdata':"srcNoelite/Data",
                'nomfichier':"params",
                'nomgroupe':"saisieKM"
                }
        kwds['matrice'][("filtres","Filtre des données")][0]['values'] = nunoegest.GetClotures(tip="ansi")
        kwds['matrice'][("filtres","Filtre des données")][1]['values'] = nunoegest.GetDatesFactKm()
        super().__init__(parent, **kwds)
        self.Init()

class PNL_corps(xgte.PNL_corps):
    #panel olv avec habillage optionnel pour des boutons actions (à droite) des infos (bas gauche) et boutons sorties
    def __init__(self, parent, dicOlv,*args, **kwds):
        xgte.PNL_corps.__init__(self,parent,dicOlv,*args,**kwds)
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
            test = self.parent.noegest.ValideLigne(track)
            if test:
                track.valide = True
                self.oldRow = row
            else:
                track.valide = False
        track = self.ctrlOlv.GetObjectAt(row)
        if code == 'typetiers':
            if track.vehicule != track.donnees[self.ctrlOlv.lstCodesColonnes.index('vehicule')]:
                track.vehicule = track.donnees[self.ctrlOlv.lstCodesColonnes.index('vehicule')]
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

        # si pas de saisie on passe
        if (not value) or track.oldValue == value:
            self.flagSkipEdit = False
            return

        # l'enregistrement de la ligne se fait à chaque saisie pour gérer les montées et descentes
        okSauve = False

        # Traitement des spécificités selon les zones
        if code == 'vehicule':
            # vérification de l'unicité du code saisi
            dicVehicule = self.parent.noegest.GetVehicule(filtre=value)
            if dicVehicule:
                track.IDvehicule = dicVehicule['idanalytique']
                track.vehicule = dicVehicule['abrege']
                track.nomvehicule = dicVehicule['nom']
            else:
                track.vehicule = ''
                track.IDvehicule = ''
                track.nomvehicule = ''
            if parent:
                # la modification de la cellule éditée ne doit pas être écrasée par le finish
                parent.valeur = track.vehicule
                parent.event.cellValue = track.vehicule
            track.donnees[col] = track.vehicule
            self.ctrlOlv.Refresh()

        if code == 'IDtiers':
            # vérification de l'unicité du code saisi
            dicActivite = self.parent.noegest.GetActivite(filtre=value)
            if dicActivite:
                track.IDtiers = dicActivite['idanalytique']
                track.nomtiers = dicActivite['nom']
            else:
                track.IDtiers = ''
                track.nomtiers = ''
            self.ctrlOlv.Refresh()

        if code == 'typetiers':
            ixtiers = self.ctrlOlv.lstCodesColonnes.index('IDtiers')
            ixnomtiers = self.ctrlOlv.lstCodesColonnes.index('nomtiers')
            if value[:1]!='A':
                self.ctrlOlv.lstColonnes[ixtiers].isEditable = False
                self.ctrlOlv.lstColonnes[ixnomtiers].isEditable = True
            else:
                self.ctrlOlv.lstColonnes[ixtiers].isEditable = True
                self.ctrlOlv.lstColonnes[ixnomtiers].isEditable = False
            if parent:
                parent.valeur = value[0]

        if code in ['kmdeb','kmfin']:
            kmdeb,kmfin = 9999999,0
            if track.kmdeb:
                kmdeb = int(track.kmdeb)
            if track.kmfin:
                kmfin = int(track.kmfin)
            if code == 'kmdeb':
                kmdeb = int(value)
                track.kmdeb = kmdeb
            else:
                kmfin = int(value)
                track.kmfin = kmfin
            if kmdeb and kmfin:
                if kmdeb <= kmfin:
                    conso = kmfin - kmdeb
                    track.conso = conso
                    self.ctrlOlv.Refresh()

        # l'enregistrement de la ligne se fait à chaque saisie pour gérer les montées et descentes
        self.parent.noegest.ValideLigne(track)
        self.parent.noegest.SauveLigne(track)


        # enlève l'info de bas d'écran
        self.parent.pnlPied.SetItemsInfos( INFO_OLV,wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)))
        self.flagSkipEdit = False

    def OnDelete(self,noligne,track,parent=None):
        self.parent.noegest.DeleteLigne(track)

    def OnEditFunctionKeys(self,event):
        row, col = self.ctrlOlv.cellBeingEdited
        track = self.ctrlOlv.GetObjectAt(row)
        code = self.ctrlOlv.lstCodesColonnes[col]
        if event.GetKeyCode() == wx.WXK_F4 and code == 'vehicule':
            # F4 Choix
            dict = self.parent.noegest.GetVehicule(filtre=track.vehicule,mode='F4')
            if dict:
                self.OnEditFinishing('vehicule',dict['abrege'])
                track.vehicule = dict['abrege']
                track.nomvehicule = dict['nom']
                track.IDvehicule = dict['idanalytique']
        elif event.GetKeyCode() == wx.WXK_F4 and code == 'IDtiers':
            # F4 Choix
            dict = self.parent.noegest.GetActivite(filtre=track.IDtiers,mode='f4')
            if dict:
                self.OnEditFinishing('IDtiers',dict['idanalytique'])
                track.IDtiers = dict['idanalytique']
                track.nomtiers = dict['nom']

class PNL_pied(xgte.PNL_pied):
    #panel infos (gauche) et boutons sorties(droite)
    def __init__(self, parent, dicPied, **kwds):
        xgte.PNL_pied.__init__(self,parent, dicPied, **kwds)

class Dialog(xusp.DLG_vide):
    # ------------------- Composition de l'écran de gestion----------
    def __init__(self):
        super().__init__(None,name=MODULE)
        self.ctrlOlv = None
        self.txtInfo =  "Non connecté à une compta"
        self.dicOlv = self.GetParamsOlv()
        self.noegest = nunoegest.Noegest(self)
        self.IDutilisateur = nuutil.GetIDutilisateur()
        if (not self.IDutilisateur) or not nuutil.VerificationDroitsUtilisateurActuel('facturation_factures','creer'):
            self.Destroy()
        self.Init()
        self.Sizer()
        self.exercice = None

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
        # connexion compta et affichage bas d'écran
        self.compta = self.GetCompta()
        self.table = self.GetTable()
        self.Bind(wx.EVT_CLOSE,self.OnFermer)
        self.pnlParams.SetOneValue('forcer',False)
        self.OnCloture(None)

    def Sizer(self):
        sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=0, hgap=0)
        sizer_base.Add(self.pnlBandeau, 1, wx.TOP | wx.EXPAND, 3)
        sizer_base.Add(self.pnlParams, 1, wx.TOP | wx.EXPAND, 3)
        sizer_base.Add(self.pnlOlv, 1, wx.TOP | wx.EXPAND, 3)
        sizer_base.Add(self.pnlPied, 0, wx.ALL | wx.EXPAND, 3)
        sizer_base.AddGrowableCol(0)
        sizer_base.AddGrowableRow(1)
        self.CenterOnScreen()
        self.SetSizerAndFit(sizer_base)
        self.CenterOnScreen()

    # ------------------- Gestion des actions -----------------------

    def OnCloture(self,evt):
        # Met à jour self.cloture
        box = self.pnlParams.GetBox('filtres')
        self.noegest.cloture = box.GetOneValue('cloture')
        lClotures = [x for y, x in self.noegest.GetExercices()]
        self.exercice = ''
        try:
            self.exercice = self.noegest.ltExercices[0]
            self.exercice = self.noegest.ltExercices[lClotures.index(self.noegest.cloture)]
        except: pass
        self.lstVehicules = [x[0] for x in self.noegest.GetVehicules(lstChamps=['abrege'])]
        box.SetOneSet('vehicule',self.lstVehicules)
        self.ctrlOlv.dicChoices[self.ctrlOlv.lstCodesColonnes.index('vehicule')]= self.lstVehicules
        self.lstActivites = [x[0]+" "+x[1] for x in self.noegest.GetActivites(lstChamps=['IDanalytique','nom'])]
        self.noegest.GetConsosKm()

    def OnDateFact(self,evt):
        # Charge l'éventuelle saisie antérieure sur cette date
        self.noegest.GetConsosKm()

    def OnVehicule(self,evt):
        # Charge l'éventuelle saisie antérieure sur cette date
        self.noegest.GetConsosKm()

    def OnCtrlJournal(self,evt):
        # tronque pour ne garder que le code journal sur trois caractères maxi
        box = self.pnlParams.GetBox('compta')
        valeur = self.pnlParams.lstBoxes[1].GetOneValue('journal')
        valeur = valeur[:3].strip()
        box.SetOneValue('journal', valeur)
        if self.compta:
            item = self.compta.GetOneAuto(table='journOD',filtre=valeur)
            if item:
                self.pnlParams.SetOneValue('journal',valeur,'compta')

    def OnBtnJournal(self,evt):
        if self.compta:
            item = self.compta.ChoisirItem(table='journOD')
            if item:
                self.pnlParams.SetOneValue('journal',item[0],'compta')

    def OnBtnCompte(self,evt):
        nameBtn = evt.EventObject.nameBtn
        lstName = nameBtn.split('.')
        if self.compta:
            item = self.compta.ChoisirItem(table='cpt3car')
            if item:
                self.pnlParams.SetOneValue(lstName[1],item[0],lstName[0])

    def OnChoixExport(self,evt):
        self.compta = self.GetCompta()
        self.table = self.GetTable()

    def InitOlv(self):
        self.pnlParams.GetValues()
        self.ctrlOlv.lstColonnes = GetOlvColonnes(self)
        self.ctrlOlv.lstCodesColonnes = self.ctrlOlv.GetLstCodesColonnes()
        self.ctrlOlv.InitObjectListView()
        self.Refresh()

    def GetDonneesIn(self,nomFichier):
        # importation des donnéees du fichier entrée
        entrees = None
        if nomFichier[-4:].lower() == 'xlsx':
            entrees = ximport.GetFichierXlsx(nomFichier,maxcol=7)
        elif nomFichier[-3:].lower() == 'xls':
            entrees = ximport.GetFichierXls(nomFichier,maxcol=7)
        else: wx.MessageBox("Il faut choisir un fichier .xls ou .xlsx",'NomFichier non reconnu')
        # filtrage des premières lignes incomplètes
        entete = None
        if entrees:
            for ix in range(len(entrees)):
                sansNull= [x for x in entrees[ix] if x]
                if len(sansNull)>5:
                    entete = entrees[ix]
                    entrees = entrees[ix + 1:]
                    break
        if not entete:
            wx.MessageBox("Fichier non reconnu!\n\n"+
                          "Aucune ligne avec 6 cellules non nulles définissant une entête des colonnes!")
            entrees = None
        return entete,entrees

    def GetCompta(self):
        dic = self.pnlParams.GetValues()
        formatExp = dic['compta']['formatexp']
        compta = None
        if formatExp in nucompta.FORMATS_EXPORT.keys() :
            nomCompta = nucompta.FORMATS_EXPORT[formatExp]['compta']
            compta = nucompta.Compta(self, compta=nomCompta)
            if not compta.db: compta = None
        if not compta:
            txtInfo = "Echec d'accès à la compta associée à %s!!!"%formatExp
            image = wx.ArtProvider.GetBitmap(wx.ART_ERROR, wx.ART_OTHER, (16, 16))
        else:
            txtInfo = "Connecté à la compta %s..."%nomCompta
            image = wx.ArtProvider.GetBitmap(wx.ART_TIP, wx.ART_OTHER, (16, 16))
        self.pnlPied.SetItemsInfos(txtInfo,image)
        # appel des journaux
        if compta:
            lstJournaux = compta.GetJournaux(table='journOD')
            lstLibJournaux = [(x[0]+"   ")[:3]+' - '+x[1] for x in lstJournaux]
            box = self.pnlParams.GetBox('compta')
            valeur = self.pnlParams.lstBoxes[1].GetOneValue('journal')
            box.SetOneSet('journal',lstLibJournaux)
            box.SetOneValue('journal',valeur)
        pnlJournal = self.pnlParams.GetPnlCtrl('journal', 'compta')
        x = False
        if compta : x = True
        pnlJournal.btn.Enable(x)
        return compta

    def GetTable(self):
        return None

    def OnImporter(self,event):
        """ Open a file"""
        self.dirname = ''
        dlg = wx.FileDialog(self, "Choisissez un fichier à importer", self.dirname)
        nomFichier = None
        if dlg.ShowModal() == wx.ID_OK:
            nomFichier = dlg.GetPath()
        dlg.Destroy()
        if not nomFichier: return
        entete,donnees = self.GetDonneesIn(nomFichier)
        if donnees:
            donExist = [x.donnees for x in self.ctrlOlv.modelObjects]
            if len(donExist)>0:
                ix = self.ctrlOlv.lstCodesColonnes.index('conso')
                if xformat.Nz(donExist[-1][ix]) == 0:
                    del donExist[-1]
                    del self.ctrlOlv.modelObjects[-1]
            donNew = ComposeFuncImp(self,entete,donnees)
            self.ctrlOlv.lstDonnees = donExist + donNew
            # ajout de la ligne dans olv
            self.ctrlOlv.AddTracks(donNew)
            # test de validité pour changer la couleur de la ligne
            for object in self.ctrlOlv.modelObjects:
                self.noegest.ValideLigne(object)
                self.noegest.SauveLigne(object)
            self.ctrlOlv._FormatAllRows()
            self.ctrlOlv.Refresh()

    def OnExporter(self,event):
        dicParams = self.pnlParams.GetValues()
        dicParams['compta']['typepiece'] = 'I'
        dicParams['fichiers']={}
        dicParams['fichiers']['formatexp']= dicParams['compta']['formatexp']
        champsIn = self.ctrlOlv.lstCodesColonnes
        toc = nunoegest.ToComptaKm(dicParams,champsIn,self.noegest)
        champsInExp = toc.champsIn
        lstDonnees = []
        # calcul des débit et crédit des pièces
        totDebits, totCredits = 0.0, 0.0
        nonValides = 0
        # constitution de la liste des données à exporter
        for track in self.ctrlOlv.innerList:
            if not track.valide:
                nonValides +=1
                continue
            if track.conso == 0: continue
            lstDonnees.append(track.donnees)

        ixmtt = champsInExp.index('montant')
        for donnees in lstDonnees:
            toc.AddDonnees(donnees)
            if donnees[ixmtt] > 0.0:
                totCredits += donnees[ixmtt]
            else:
                totDebits -= donnees[ixmtt]


        if nonValides > 0:
            ret = wx.MessageBox("%d lignes non valides!\n\nelles ne seront pas transférées"%nonValides,
                          "Confirmez ou abandonnez",style= wx.YES_NO)
            if not ret == wx.YES:
                return wx.CANCEL

        exp = nucompta.Export(self,self.compta)
        ret = exp.Exporte(dicParams,
                          lstDonnees,
                          champsInExp)
        if not ret == wx.OK:
            return ret

        # affichage résultat
        wx.MessageBox("Fin de transfert\n\nDébits: %s\nCrédits:%s"%(xformat.FmtMontant(totDebits,lg=12),
                                                                     xformat.FmtMontant(totCredits,lg=12)))

    def Final(self):
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
