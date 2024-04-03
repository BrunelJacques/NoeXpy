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
import xpy.ObjectListView.xGTE as xGTE
import xpy.xGestionConfig               as xgc
import xpy.xUTILS_SaisieParams          as xusp
from srcNoelite import UTILS_Noelite
from srcNoelite import UTILS_Compta
import srcNoelite.UTILS_Utilisateurs    as nuutil
from xpy.ObjectListView.ObjectListView import ColumnDefn, CellEditor
from xpy.outils                 import xformat,xbandeau,ximport,xexport

#---------------------- Paramètres du programme -------------------------------------
MODULE = 'DLG_Km_saisie'
TITRE = "Saisie des consommations de km"
INTRO = "Importez un fichier ou saisissez les consommations de km, avant de l'exporter dans un autre format"

# Infos d'aide en pied d'écran
DIC_INFOS = {'date':"Flèche droite pour le mois et l'année, Entrée pour valider.\nC'est la date",
            'vehicule':    "<F4> Choix d'un véhicule, ou saisie directe de l'abrégé",
            'idactivite':    "<F4> Choix d'une section pour l'affectation du coût",
            'datekmdeb':     "formats date acceptés : j/m/a jjmmaa jjmmaaaa",
            'datekmfin':     "formats date acceptés : j/m/a jjmmaa jjmmaaaa",
            'observation':     "S'il y a lieu précisez des circonstances particulières",
            'montant':      "Montant en €",
             }

# Info par défaut
INFO_OLV = "<Suppr> <Inser> <Ctrl C> <Ctrl V>"

# Fonctions de transposition entrée à gérer pour chaque item FORMAT_xxxx pour les spécificités
def ComposeFuncImp(dlg,entete,donnees):
    # Fonction import pour composition
    colonnesIn =    ["Code Véhicule       ","Date Fin     ","Membre        ","Activité ",
                     "KM Début       ","KM Fin   "]
    champsIn =      ['idvehicule','datekmfin','membre','activite','kmdeb','kmfin']
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
        if len(champsIn) > len(ligneIn):
            # ligneIn batarde ignorée
            continue
        ligneOut = [None,]*len(champsOut)
        #champs communs aux listIn et listOut
        for champ in ('idvehicule','datekmfin','kmdeb','kmfin'):
            value = ligneIn[champsIn.index(champ)]
            if isinstance(value,datetime.datetime):
                value = datetime.date(value.year,value.month,value.day)
            ligneOut[champsOut.index(champ)] = value
        # calcul auto d'une date fin de mois
        findemois = xformat.FinDeMois(ligneIn[champsIn.index('datekmfin')])
        ligneOut[champsOut.index('datekmfin')] = findemois
        # recherche champ libellé véhicule
        dicVehicule = dlg.uNoelite.GetVehicule(mode='auto',filtre=ligneIn[champsIn.index('idvehicule')])
        if dicVehicule:
            ligneOut[champsOut.index('idvehicule')] = dicVehicule['idanalytique']
            ligneOut[champsOut.index('vehicule')] =  dicVehicule['abrege']
            #ligneOut[champsOut.index('nomvehicule')] = dicVehicule['nom']
        else:
            mess = "params véhicule non trouvé pour ligne:\n\n"
            mess += str(ligneIn)
            wx.MessageBox(mess,"Erreur bloquante")
        # appel des éléments détaillés de l'activité saisie
        dicActivite = None
        if ligneIn[champsIn.index('activite')]:
            idactivite = ("00" + str(ligneIn[champsIn.index('activite')]))[-2:]
            dicActivite = dlg.uNoelite.GetActivite(mode='auto', filtre=idactivite, axe=None)
        # préparation de variables utiles
        nomTiers = str(ligneIn[champsIn.index('membre')])
        if 'None' in nomTiers or '???' in nomTiers or len(nomTiers.strip()) == 0:
            nomTiers = 'Inconnu'
        libelle = (str(ligneIn[champsIn.index('activite')]) + nomTiers).lower()
        # calcul conso
        try:
            kmdeb = int(ligneIn[champsIn.index('kmdeb')])
            if kmdeb == 0: kmdeb = None
        except: kmdeb = None
        try:
            kmfin = int(ligneIn[champsIn.index('kmfin')])
            if kmfin == 0: kmfin = None
        except: kmfin = None
        try:
            nbkm = kmfin - kmdeb
        except: nbkm = None
        if nbkm and nbkm > 0:
            ligneOut[champsOut.index('conso')] = nbkm

        # le code activité est bien une activité pas un véhicule, c'est le cas général
        if dicActivite and dicActivite['axe'] == 'ACTIVITES':
            ligneOut[champsOut.index('typetiers')] = 'A'
            ligneOut[champsOut.index('idactivite')] =  dicActivite['idanalytique']
            ligneOut[champsOut.index('nomtiers')] = dicActivite['abrege']
        # le libelle contient l'item 'fact' c'est un partenaire
        elif 'fact' in libelle:
            ligneOut[champsOut.index('typetiers')] = 'P'
            ligneOut[champsOut.index('idactivite')] = dicVehicule['idanalytique']
            ligneOut[champsOut.index('nomtiers')] = nomTiers
        # le code activité est celui d'un véhicule
        elif dicActivite and dicActivite['axe'] == 'VEHICULES':
            ligneOut[champsOut.index('typetiers')] = 'T'
            ligneOut[champsOut.index('idactivite')] = dicVehicule['idanalytique']
            ligneOut[champsOut.index('nomtiers')] = nomTiers
        # ni activité ni membre
        else:
            ligneOut[champsOut.index('typetiers')] = 'S'
            ligneOut[champsOut.index('idactivite')] = '00'
            ligneOut[champsOut.index('nomtiers')] = nomTiers

        lstOut.append(ligneOut)
    return lstOut

# Description des paramètres à choisir en haut d'écran
MATRICE_PARAMS = {
("filtres","Filtre des données"): [
    {'name': 'dateCout', 'genre': 'Choice', 'label': 'Appliquer les coûts véhicules au',
                    'help': "Choisir un exercice ouvert pour pouvoir saisir, sinon il sera en consultation", 'value':0,
                    'values': [],# cf PNL_params.__init__
                    'ctrlAction':'OnDateCout',
                    'txtSize': 100,
                    'size':(210,30)},
    {'name': 'dateOD', 'genre': 'Enum', 'label': 'Date des écritures générées',
                    'help': "Date de facturation pour l'export ou pour consulter l'antérieur",
                    'value':0,
                    'values':[],# cf PNL_params.__init__
                    'ctrlAction': 'OnDateOD',
                    'txtSize': 100,
                    'size':(210,30)},
    {'name': 'vehicule', 'genre': 'Choice', 'label': "Véhicule",
                    'help': "Pour filtrer les écritures d'un seul véhicule, saisir sa clé d'appel",
                    'value':0, 'values':['',],
                    'ctrlAction': 'OnVehicule',
                    'txtSize': 60,
                    'size':(300,30)},
    ],
("compta", "Paramètres export"): [
    {'name': 'formatexp', 'genre': 'Choice', 'label': 'Format export',
                    'help': "Le choix est limité par la programmation", 'value':0,
                    'values':[x for x in UTILS_Compta.FORMATS_EXPORT.keys()],
                    'ctrlAction':'OnChoixExport',
                    'txtSize': 80,
                    'size':(240,30)},
    {'name': 'journal', 'genre': 'Combo', 'label': 'Journal','ctrlAction':'OnCtrlJournal',
                    'help': "Code journal utilisé dans la compta",
                    'txtSize': 80,
                    'size':(270,30),
                    'value':'CI','values':['CI','OD'],
                    'btnLabel': "...", 'btnHelp': "Cliquez pour choisir un journal",
                    'btnAction': 'OnBtnJournal'},
    {'name': 'forcer', 'genre': 'Bool', 'label': 'Exporter les écritures déjà transférées','value':False,
     'help': "Pour forcer un nouvel export d'écritures déjà transférées!",
     'txtSize': 100,
     'size': (300, 30)},
    ],
("comptes", "Comptes à mouvementer"): [
    {'name': 'revente', 'genre': 'String', 'label': 'Vente interne km',
     'value':'790',
     'help': "Code comptable du compte crédité de la rétrocession", 'size': (250, 30),
     'btnLabel': "...", 'btnHelp': "Cliquez pour choisir un compte comptable",
     'btnAction': 'OnBtnCompte'},
    {'name': 'achat', 'genre': 'String', 'label': 'Achat interne km',
     'value':'693',
     'help': "Code comptable du compte débité de la rétrocession interne", 'size': (250, 30),
     'btnLabel': "...", 'btnHelp': "Cliquez pour choisir un compte comptable",
     'btnAction': 'OnBtnCompte'},
    {'name': 'tiers', 'genre': 'string', 'label': 'km faits par tiers',
     'value':'691',
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
            ColumnDefn("IDvehicule", 'centre', 50, 'idvehicule', isEditable=True),
            ColumnDefn("Véhicule", 'center', 90, 'vehicule', isSpaceFilling=False,isEditable=False),
            ColumnDefn("Type Tiers", 'center', 40, 'typetiers', isSpaceFilling=False,valueSetter='A',
                       cellEditorCreator=CellEditor.ChoiceEditor,
                       choices=['A activité','T tiers','P partenaire','S structure']),
            ColumnDefn("Activité", 'center', 60, 'idactivite', isSpaceFilling=False),
            ColumnDefn("Nom tiers/activité", 'left', 100, 'nomtiers',
                       isSpaceFilling=True, isEditable=False),
            ColumnDefn("Date Deb", 'center', 85, 'datekmdeb',
                       stringConverter=xformat.FmtDate, isSpaceFilling=False),
            ColumnDefn("KM début", 'right', 90, 'kmdeb', isSpaceFilling=False,valueSetter=0,
                       stringConverter=xformat.FmtInt),
            ColumnDefn("Date Fin", 'center', 85, 'datekmfin',
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
            'minSize': (1200,300),
            'checkColonne': False,
            'recherche': True,
            'autoAddRow':True,
            'sortColumnIndex': 0,
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

        # remplissages des values[]
        uNoelite = UTILS_Noelite.Noelite()
        lDatesOD = uNoelite.GetDatesOD()
        lDatesCouts = uNoelite.GetDatesCoutsKm()
        for dte in lDatesOD:
            if not dte in lDatesCouts:
                lDatesCouts.append(dte)
        uNoelite.db.Close()
        del uNoelite

        #('pos','size','style','name','matrice','donnees','lblBox')
        kwds = {
                'name':"PNL_params",
                'matrice':MATRICE_PARAMS,
                'lblBox':None,
                'boxesSizes': [(250, 90), (290, 80)],
                'pathdata':"srcNoelite/Data",
                'nomfichier':"params",
                'nomgroupe':"saisieKM"
                }
        kwds['matrice'][("filtres",
                         "Filtre des données",
                         )][0]['values'] = sorted(lDatesCouts,reverse=True)
        kwds['matrice'][("filtres",
                         "Filtre des données",
                         )][1]['values'] = sorted(lDatesOD,reverse=True)
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
            test = self.parent.uNoelite.ValideLigne(track)
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

    def OnEditFinishing(self,code=None,value=None,event=None):
        self.parent.pnlPied.SetItemsInfos( INFO_OLV,wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)))
        # flagSkipEdit permet d'occulter les évènements redondants. True durant la durée du traitement
        if self.flagSkipEdit : return
        self.flagSkipEdit = True

        (row, col) = self.ctrlOlv.cellBeingEdited
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
            dicVehicule = self.parent.uNoelite.GetVehicule(filtre=value)
            if dicVehicule:
                track.idvehicule = dicVehicule['idanalytique']
                track.vehicule = dicVehicule['abrege']
                track.nomvehicule = dicVehicule['nom']
            else:
                track.vehicule = ''
                track.idvehicule = ''
                track.nomvehicule = ''
            track.donnees[col] = track.vehicule
            value = track.idvehicule

        if code == 'idactivite':
            # vérification de l'unicité du code saisi
            dicActivite = self.parent.uNoelite.GetActivite(filtre=value, axe=None)
            if dicActivite:
                track.idactivite = dicActivite['idanalytique']
                track.nomtiers = dicActivite['nom']
            else:
                track.idactivite = ''
                track.nomtiers = ''
            self.ctrlOlv.Refresh()

        if code == 'typetiers':
            value = value[0]

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
        self.parent.uNoelite.ValideLigne(track)
        self.parent.uNoelite.SauveLigne(track)


        # enlève l'info de bas d'écran
        self.parent.pnlPied.SetItemsInfos( INFO_OLV,wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)))
        self.flagSkipEdit = False
        return value

    def OnDelete(self,track):
        self.parent.uNoelite.DeleteLigne(track)

    def OnEditFunctionKeys(self,event):
        row, col = self.ctrlOlv.cellBeingEdited
        track = self.ctrlOlv.GetObjectAt(row)
        code = self.ctrlOlv.lstCodesColonnes[col]
        if event.GetKeyCode() == wx.WXK_F4 and code == 'vehicule':
            # F4 Choix
            dict = self.parent.uNoelite.GetVehicule(filtre=track.vehicule,mode='F4')
            if dict:
                self.OnEditFinishing('vehicule',dict['abrege'])
                track.vehicule = dict['abrege']
                track.nomvehicule = dict['nom']
                track.idvehicule = dict['idanalytique']
        elif event.GetKeyCode() == wx.WXK_F4 and code == 'idactivite':
            # F4 Choix
            dict = self.parent.uNoelite.GetActivite(filtre=track.idactivite,mode='f4')
            if dict:
                self.OnEditFinishing('idactivite',dict['idanalytique'])
                track.idactivite = dict['idanalytique']
                track.nomtiers = dict['nom']

class PNL_pied(xGTE.PNL_pied):
    #panel infos (gauche) et boutons sorties(droite)
    def __init__(self, parent, dicPied, **kwds):
        xGTE.PNL_pied.__init__(self,parent, dicPied, **kwds)

class Dialog(xusp.DLG_vide):
    # ------------------- Composition de l'écran de gestion----------
    def __init__(self):
        super().__init__(None,name=MODULE)
        self.ctrlOlv = None
        self.txtInfo =  "Non connecté à une compta"
        self.dicOlv = self.GetParamsOlv()
        self.uNoelite = UTILS_Noelite.Noelite(self)
        self.uNoelite = UTILS_Noelite.Noelite(self)
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
        self.OnDateOD(None)

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

    def OnDateCout(self, evt):
        # Met à jour self.dateCout
        box = self.pnlParams.GetBox('filtres')
        self.uNoelite.dateCout = box.GetOneValue('dateCout')
        ldateCouts = [x for y, x in self.uNoelite.GetExercices()]
        self.exercice = ''
        try:
            self.exercice = self.uNoelite.ltExercices[0]
            self.exercice = self.uNoelite.ltExercices[ldateCouts.index(self.uNoelite.dateCout)]
        except: pass
        self.lstVehicules = [x[0] for x in self.uNoelite.GetVehicules(lstChamps=['nom'])]
        self.lstVehicules.append('--Tous--')
        self.lstVehicules.sort()
        box.SetOneSet('vehicule',self.lstVehicules)
        box.SetOneValue('vehicule',self.lstVehicules[0])
        self.ctrlOlv.dicChoices[self.ctrlOlv.lstCodesColonnes.index('vehicule')]= self.lstVehicules
        self.lstActivites = [x[0]+" "+x[1] for x in self.uNoelite.GetActivites(lstChamps=['IDanalytique','nom'])]
        self.uNoelite.GetConsosKm()

    def OnDateOD(self, evt):
        # Charge l'éventuelle saisie antérieure sur cette date
        self.uNoelite.GetConsosKm()
        dte = self.pnlParams.GetOneValue('dateOD')
        self.pnlParams.SetOneValue('dateCout',dte)

    def OnVehicule(self,evt):
        # Charge l'éventuelle saisie antérieure sur cette date
        self.uNoelite.GetConsosKm()

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
                if len(sansNull)>4:
                    entete = entrees[ix]
                    entrees = entrees[ix + 1:]
                    break
        if not entete:
            wx.MessageBox("Fichier non reconnu!\n\n"+
                          "Aucune ligne avec 5 cellules non nulles définissant une entête des colonnes!")
            entrees = None
        return entete,entrees

    def GetCompta(self):
        dic = self.pnlParams.GetValues()
        formatExp = dic['compta']['formatexp']
        compta = None
        if formatExp in UTILS_Compta.FORMATS_EXPORT.keys() :
            nomCompta = None
            if 'compta' in UTILS_Compta.FORMATS_EXPORT[formatExp].keys():
                nomCompta = UTILS_Compta.FORMATS_EXPORT[formatExp]['compta']
            compta = UTILS_Compta.Compta(self, nomCompta=nomCompta)
            if not compta.db: compta = None
        if not compta:
            txtInfo = "Pas d'accès à la compta!!!"
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
        # accès à la compta abandonné car impossible avec Quadra en Windows 10
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
                self.uNoelite.ValideLigne(object)
                self.uNoelite.SauveLigne(object)
            self.ctrlOlv._FormatAllRows()
            self.ctrlOlv.Refresh()

    def OnExporter(self,event):
        dicParams = self.pnlParams.GetValues()
        dicParams['compta']['typepiece'] = 'I'
        dicParams['fichiers']={}
        dicParams['fichiers']['formatexp']= dicParams['compta']['formatexp']
        champsIn = self.ctrlOlv.lstCodesColonnes
        toc = UTILS_Noelite.ToComptaKm(dicParams,champsIn,self.uNoelite)
        champsInExp = toc.champsIn
        lstDonnees = []
        # calcul des débit et crédit des pièces
        totDebits, totCredits = 0.0, 0.0
        nonValides = 0
        lstVehicules = []
        # constitution de la liste des données à exporter
        for track in self.ctrlOlv.innerList:
            if not track.valide and not track.vierge:
                nonValides +=1
                continue
            if track.conso == 0: continue
            lstDonnees.append(track.donnees)
            lstVehicules.append(track.idvehicule)
        lstPrixManquants = []
        dicPrix = self.uNoelite.GetdicPrixVteKm()
        for ID in lstVehicules:
            if ID in dicPrix:
                continue
            lstPrixManquants.append(ID)
        if len(lstPrixManquants) > 0:
            mess = "%d véhicules n'ont pas de prix KM renseigné\n\n"%len(lstPrixManquants)
            mess += "La date choisie était %s"
            ret = wx.MessageBox(mess,style= wx.ID_CANCEL)
            return wx.CANCEL

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

        exp = UTILS_Compta.Export(self,self.compta)
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
