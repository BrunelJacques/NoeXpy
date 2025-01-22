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

MODULE = os.path.abspath(__file__).split("\\")[-1]
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
        'toutCocher':True,
        'toutDecocher':True,
        'msgIfEmpty': "Aucune ligne n'a été transmise au lancement",
        'dictColFooter': {"IDarticle": {"mode": "nombre", "alignement": wx.ALIGN_CENTER},
                          "qte": {"mode": "total", "alignement": wx.ALIGN_LEFT},
                          "__mttTTC": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
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
        'name': '(%s)DLG'%MODULE
    }

    #----------------------- Parties de l'écrans -----------------------------------------

def CalculeLigne(dlg,track):
    qte = round(track.qte,4)
    prixUnit = round(track.prixUnit,4)
    rations = track.rations
    if rations == 0: rations = 1
    track.__mttTTC = round(qte * prixUnit,2)
    track.__pxRation =  round(qte * prixUnit / rations,2)
    modif = False
    if dlg.origine  and dlg.origine != track.origine:
        track.origine = dlg.origine
        modif = True
    if dlg.date  and dlg.date != track.date:
        track.date = dlg.date
        modif = True
    if dlg.fournisseur != None and (dlg.fournisseur != track.fournisseur):
        track.fournisseur = dlg.fournisseur
        modif = True
    if dlg.analytique != None and dlg.analytique != track.IDanalytique:
        track.analytique = dlg.analytique
        modif = True
    if dlg.repas  and dlg.repas != track.repas:
        track.repas = dlg.repas
        modif = True
    track.modif = modif

def RowFormatter(listItem, track):
    if track.modif:
        # modif est colorée
        listItem.SetBackgroundColour(wx.Colour(220, 237, 200))
        listItem.SetTextColour(wx.BLUE)
    else:
        listItem.SetTextColour(wx.BLACK)

class DLG(xGTE.DLG_tableau):
    # ------------------- Composition de l'écran de gestion----------
    def __init__(self,parent, **kwd):
        self.tracksOrigine = kwd.get('donnees',[])

        self.lstIDmvts = [x.IDmouvement for x in self.tracksOrigine]
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
        kwds = GetDlgOptions(self)
        kwds['dicParams'] = GetDicPnlParams(self)
        kwds['dicOlv'] = self.dicOlv
        kwds['dicPied'] = dicPied
        kwds['db'] = self.db
        kwds['lanceur'] = self

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
        else:
            # pour lancement de test on limite à 100 mouvements
            where = '1 LIMIT 100'
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
        self.CocheAnomalies()

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
        self.GetDonnees()

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
        self.GetDonnees()

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
        self.GetDonnees()

    def OnAnalytique(self,event):
        if event: event.Skip()
        self.analytique = self.GetAnalytique()
        self.GetDonnees()

    def OnBtnAnalytique(self,event):
        # Appel du choix d'un camp via un écran complet
        noegest = nung.Noelite(self)
        dicAnalytique = noegest.GetActivite(mode='dlg')
        if dicAnalytique:
            codeAct = dicAnalytique['idanalytique']
            valAct = dicAnalytique['abrege']
            self.pnlParams.SetOneValue('analytique',valAct,codeBox='param2')
            self.analytique = codeAct
        self.GetDonnees()

    def OnRepas(self,event):
        saisie = self.pnlParams.GetOneValue('repas','param3')
        if 'NoChange' in saisie:
            self.repas = None
        elif '-' == saisie:
            self.repas = 0
        else:
            self.repas = nust.CHOIX_REPAS.index(saisie) + 1
        self.GetDonnees()

    def OnImprimer(self,event):
        self.ctrlOlv.Apercu(None)

    def CocheAnomalies(self):
        for track in self.ctrlOlv.innerList:
            self.ctrlOlv.SetCheckState(track,track.modif)

    def Sauve(self,donnees):
        self.IDmouvement = 0
        codesChamps = ['IDmouvement','origine','date','repas','fournisseur','analytique']
        newValues = [self.IDmouvement,self.origine,self.date,self.repas,self.fournisseur,self.analytique]
        # les values NoChange sont à None donc ignorées
        ixValues = [newValues.index(x) for x in newValues if x != None]

        # Voici les deux listes qui seront envoyées à la mise à jour
        lstChamps = [codesChamps[x] for x in ixValues]
        llDonnees=[]
        lstIdModifies= []
        mess = "Erreur sur ReqMAJ, DLG_MvtCorrection.Sauve"
        ableChgSens = False
        chgSens = 1
        if 'origine' in lstChamps:
            mess ="Vous demandez de changer la nature des mouvements\n\n"
            mess += "faut-il inverser le sens des quantités?\n\n"
            mess += "répondez 'NON pour laisser idem, OUI pour inverser les qtes"
            ret = wx.MessageBox(mess,"Confirmez",wx.YES_NO|wx.ICON_WARNING)
            if ret == wx.YES:
                ableChgSens = True
                chgSens = -1

        # composition des listes pour mise à jour dans db
        for track in donnees:
            IDmouvement = track.IDmouvement
            values = []
            for ix in ixValues:
                values.append(newValues[ix])
                #modif de la track pour le retour éventuel
                exec("track.%s = self.%s "%(codesChamps[ix],codesChamps[ix]))
            track.IDmouvement = IDmouvement
            values[0] = IDmouvement
            # Inversion possible des quantités
            if ableChgSens:
                values.append(track.qte * chgSens)
                exec("track.%s = track.%s * %d"%('qte','qte',chgSens))
            track.ordi = self.ordi
            track.dateSaisie = datetime.date.today()
            values.append(track.ordi)
            values.append(track.dateSaisie)
            llDonnees.append(values)
            lstIdModifies.append(track.IDmouvement )
        # Fixe la liste des champs (envoyé une seule fois pour toutes les values)
        if ableChgSens:
            lstChamps.append('qte')
        lstChamps += ['ordi', 'dateSaisie']

        # modif des tracks d'origine
        for lstValues in llDonnees:
            retReqMAJ = self.db.ReqMAJ(
                nomTable= 'stMouvements',
                nomChampID=lstChamps[0],
                ID=lstValues[0],
                lstValues=lstValues[1:],
                lstChamps=lstChamps[1:],
                mess=mess)
            if retReqMAJ != 'ok':
                break
        if retReqMAJ == 'ok':
            # mise à jour des tracks d'origine
            if self.tracksOrigine != []:
                for track in self.tracksOrigine:
                    if track.IDmouvement in lstIdModifies:
                        newTrack = donnees[lstIdModifies.index(track.IDmouvement)]
                        for champ in lstChamps:
                            exec("track.%s = newTrack.%s" % (champ,champ))
        return retReqMAJ

    def OnFinal(self,event):
        # analyse du lot à modifier
        nbNonModifiables = 0
        for track in self.ctrlOlv.GetCheckedObjects():
            # Décoche les lignes sans modification
            if track.modif != True:
                self.ctrlOlv.SetCheckState(track, False)
            # Les lignes modifiées sont-elles modifiables
            elif track.modifiable != 1 or track.date <= self.lastInventaire:
                    nbNonModifiables +=1
            self.ctrlOlv.RefreshObjects()
        if nbNonModifiables > 0:
            mess = "%d Mouvements ne sont pas modifiables\n\n"%nbNonModifiables
            mess += "Il peut s'agir de dates antérieures au dernier inventaire conservé\n"
            mess += "ou d'écritures marquées comme non modifiables dans la base\n\n"
            mess += "Vous pouvez passez outre en cliquant sur 'oui'"
            ret = wx.MessageBox(mess,'NON bloquant, mais confirmez',wx.YES_NO|wx.ICON_WARNING)
            if ret != wx.YES:
                return
        # Constitution du lot à traiter
        donnees = [x for x in self.ctrlOlv.GetCheckedObjects()]
        nb = len(donnees)
        if nb == 0:
            mess = "Aucune ligne à traiter\n\n"
            mess += "car aucune modification n'est proposée dans la sélection\n"
            mess += "les lignes cochées non colorées ont été décochées\n\n"
            mess += "'OUI' pour sortir sans modif, 'NON' pour retourner'"
            ret = wx.MessageBox(mess,"Sortie ou retour",wx.YES_NO)
            if ret != wx.YES:
                return
        # lancement du traitement
        else:
            if nb > 1: s = "s"
            else: s=""
            mess = "Traitement de %d ligne%s qui vont être modifiée%s\n\n"%(nb,s,s)
            mess += "Le 'non' vous fait retourner, le bouton 'abandon' permettra sortir"
            ret = wx.MessageBox(mess,"Confirmez",wx.YES_NO|wx.ICON_WARNING)
            if ret == wx.YES:
                ok = self.Sauve(donnees)
                if ok == 'ok':
                    mess = "Traitement terminé, au revoir!"
                else:
                    mess = ok
                wx.MessageBox(mess, "Résultat", wx.OK)
            else:
                return
        # sortie normale ok
        self.OnFermer(None)

#------------------------ Lanceur de test  -------------------------------------------

if __name__ == '__main__':
    app = wx.App(0)
    os.chdir("..")
    dlg = DLG(None)
    dlg.ShowModal()
    app.MainLoop()
