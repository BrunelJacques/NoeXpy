#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -------------------------------------------------------------
# Application :    NoeLITE, gestion des Reglements en lot
# Usage : Gestion de réglements créant éventuellement la prestation associée et le dépot des règlements
# Auteur:          Jacques BRUNEL
# Licence:         Licence GNU GPL
# -------------------------------------------------------------

import wx
import os
import xpy.xGestion_TableauEditor       as xgte
import xpy.xUTILS_DB                   as xdb
import srcNoelite.UTILS_Utilisateurs    as nuu
import srcNoelite.UTILS_Reglements      as nur
import srcNoelite.DLG_Reglements_ventilation      as ndrv
from xpy.outils.ObjectListView  import ColumnDefn, CellEditor
from xpy.outils                 import xformat,xbandeau

#---------------------- Matrices de paramétres -------------------------------------

TITRE = "Bordereau d'un dépôt de réglements: création, modification"
INTRO = "Définissez la banque, choisissez un numéro si c'est pour une reprise, puis saisissez les règlements dans le tableau"
DIC_INFOS = {'date':"Flèche droite pour le mois et l'année, Entrée pour valider.\nC'est la date de réception du règlement, qui sera la date comptable",
            'IDfamille':    "<F4> Choix d'une famille, ou saisie directe du no famille",
            'payeur':     "<F4> Gestion des payeurs, <UP> <DOWN> pour défiler l'existant",
            'mode':         "<UP> <DOWN> pour défiler les possibles ou première lettre, \nChèques, Chèques non déposés, Virements,Espèces",
            'numero':       "Derniers caractères du numéro du moyen de paiement ou référence externe",
            'nature':       "<UP> <DOWN> pour défiler les nature d'affectation du reglement,\n"+
                            "'Ne pas créer' pour une prestation déjà saisie dans Noethys",
            'IDarticle':   "<F4> Choix d'une affectation du réglement selon sa nature ",
            'libelle':     "S'il est connu, précisez l'affectation (objet) du règlement",
            'montant':      "Montant en €",
            'differe':     "Date future pour le dépot du chèque ou la promesse de règlement",
             }

INFO_OLV = "<Suppr> <Inser> <Ctrl C> <Ctrl V>"

def GetBoutons(dlg):
    return  [
                {'name': 'btnImp', 'label': "Imprimer\npour dépôt",
                    'help': "Cliquez ici pour imprimer et enregistrer le bordereau pour un dépôt",
                    'size': (120, 35), 'image': wx.ART_PRINT,'onBtn':dlg.OnImprimer},
                {'name':'btnOK','ID':wx.ID_ANY,'label':"Quitter",'help':"Cliquez ici pour fermer la fenêtre",
                    'size':(120,35),'image':"xpy/Images/32x32/Quitter.png",'onBtn':dlg.OnClose}
            ]

def GetOlvColonnes(dlg):
    # retourne la liste des colonnes de l'écran principal
    return [
            ColumnDefn("ID", 'centre', 0, 'IDreglement',
                       isEditable=False),
            ColumnDefn("date", 'center', 80, 'date', valueSetter=wx.DateTime.Today(),isSpaceFilling=False,
                       stringConverter=xformat.FmtDate),
            ColumnDefn("famille", 'centre', 50, 'IDfamille', valueSetter=0,isSpaceFilling=False,
                       stringConverter=xformat.FmtIntNoSpce),
            ColumnDefn("désignation famille", 'left', 180, 'designation',valueSetter='',isSpaceFilling=True,
                       isEditable=False),
            ColumnDefn("payeur", 'left', 80, "payeur", valueSetter='', isSpaceFilling=True,
                        cellEditorCreator=CellEditor.ComboEditor),
            ColumnDefn("mode", 'centre', 50, 'mode', valueSetter='',choices=['VRT virement', 'CHQ chèque','ESP espèces'],
                       isSpaceFilling=False,
                        cellEditorCreator=CellEditor.ChoiceEditor),
            ColumnDefn("n°ref", 'left', 50, 'numero', isSpaceFilling=False),
            ColumnDefn("nat", 'centre', 50, 'nature',valueSetter='Règlement',
                       choices=['Règlement','Acompte','Don','Debour','Ne pas créer'], isSpaceFilling=False,
                        cellEditorCreator=CellEditor.ChoiceEditor),
            ColumnDefn("article", 'left', 50, 'article', isSpaceFilling=False,
                        isEditable=False),
            ColumnDefn("libelle", 'left', 200, 'libelle', valueSetter='à saisir', isSpaceFilling=True),
            ColumnDefn("montant", 'right',70, "montant", isSpaceFilling=False, valueSetter=0.0,
                        stringConverter=xformat.FmtDecimal),
            ColumnDefn("créer", 'centre', 38, 'creer', valueSetter=True,
                        isEditable=False,
                        stringConverter=xformat.FmtBool),
            ColumnDefn("differé", 'center', 80, 'differe', valueSetter=wx.DateTime.Today(), isSpaceFilling=False,
                        stringConverter=xformat.FmtDate,),
            ColumnDefn("IDprestation", 'centre', 0, 'IDprestation',
                        isEditable=False),
            ]

def GetOlvOptions(dlg):
    # retourne les paramètres de l'OLV del'écran général
    return {
            'minSize': (600,200),
            'checkColonne': False,
            'recherche': True,
            'dictColFooter': {"designation": {"mode": "nombre", "alignement": wx.ALIGN_CENTER},
                              "libelle": {"mode": "texte", "alignement": wx.ALIGN_RIGHT,"texte":'Total montants: '},
                              "montant": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                              }
    }

#----------------------- Parties de l'écrans -----------------------------------------

class PNL_params(wx.Panel):
    #panel de paramètres de l'application
    def __init__(self, parent, **kwds):
        self.parent = parent
        wx.Panel.__init__(self, parent, **kwds)

        self.ldBanques = nur.GetBanquesNne(self.parent.db)
        lstBanques = [x['nom'] for x in self.ldBanques if x['code_nne'][:2]!='47']
        self.lstIDbanques = [x['IDcompte'] for x in self.ldBanques if x['code_nne'][:2]!='47']
        self.lblBanque = wx.StaticText(self,-1, label="Banque Noethys:  ",size=(130,20),style=wx.ALIGN_RIGHT)

        self.ctrlBanque = wx.Choice(self,size=(220,20),choices=lstBanques)
        self.ctrlBanque.Bind(wx.EVT_KILL_FOCUS,self.OnKillFocusBanque)

        self.btnBanque = wx.Button(self, label="...",size=(40,22))
        self.btnBanque.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_FIND,size=(16,16)))

        self.ctrlSsDepot = wx.CheckBox(self,-1," _Sans dépôt immédiat, (saisie d'encaissements futurs)")

        self.btnDepot = wx.Button(self, label="Rappeler \nun dépôt antérieur")
        self.btnDepot.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_FIND,size=(22,22)))
        self.btnDepot.Bind(wx.EVT_BUTTON,self.parent.OnGetDepot)

        self.btnRaz = wx.Button(self, label="Réinit",size=(90,20))
        self.btnRaz.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_ERROR,size=(15,15)))
        self.btnRaz.Bind(wx.EVT_BUTTON,self.parent.OnRaz)

        self.lblDate = wx.StaticText(self,-1, label="Date de saisie:  ",size=(85,20),style=wx.ALIGN_RIGHT)
        self.ctrlDate = wx.adv.DatePickerCtrl(self,-1,size=(90,20),style=wx.ALIGN_CENTRE_HORIZONTAL)
        self.lblRef = wx.StaticText(self,-1, label="No Bordereau:  ",size=(90,20),style=wx.ALIGN_RIGHT)
        self.ctrlRef = wx.TextCtrl(self,-1,size=(70,20))

        self.ToolTip()
        self.Sizer()
        self.ctrlBanque.SetFocus()

    def ToolTip(self):
        self.lblBanque.SetToolTip("Il s'agit de la banque réceptrice")
        self.ctrlBanque.SetToolTip("Choisissez le compte banque de notre comptabilité qui constatera les encaissements")
        self.ctrlSsDepot.SetToolTip("Les encaissementes seront constatés plus tard dans la compta, "+
                                    "mais ces règlements vont créditer les clients dans Noethys")
        self.btnBanque.SetToolTip("Amélioration prévue pour consulter les comptes bancaires")
        self.btnDepot.SetToolTip("Recherche d'un dépôt existant pour consultation ou modification")
        self.btnRaz.SetToolTip("Remise à zéro du tableau")

        self.lblDate.SetToolTip("Cette date de saisie servira de date de dépôt s'il est généré par validation")
        self.ctrlDate.SetToolTip("Cette date de saisie servira de date de dépôt s'il est généré par validation")
        self.lblRef.SetToolTip("Numérotation automatique en création, c'est l'identification du lot par cette référence")
        self.ctrlRef.Enable(False)

    def Sizer(self):
        #composition de l'écran selon les composants emboités progressivement
        boxBanque = wx.FlexGridSizer(rows=1, cols=3, vgap=0, hgap=0)
        boxBanque.AddMany([(self.lblBanque,0,wx.TOP,3),
                                (self.ctrlBanque,1,wx.EXPAND|wx.LEFT|wx.RIGHT,5),
                                self.btnBanque])
        boxBanque.AddGrowableCol(1)

        boxBordereau = wx.FlexGridSizer(rows=2, cols=2, vgap=8, hgap=0)
        boxBordereau.AddMany([self.lblDate,
                                   self.ctrlDate,
                                  self.lblRef,
                                  self.ctrlRef])

        sz_banque = wx.StaticBoxSizer(wx.VERTICAL, self, " Destinataire ")
        sz_banque.Add(boxBanque,1,wx.EXPAND|wx.ALL,3)
        sz_banque.Add(self.ctrlSsDepot,1,wx.ALL|wx.ALIGN_CENTRE,3)

        sz_bordereau = wx.StaticBoxSizer(wx.VERTICAL, self, " Bordereau ")
        sz_bordereau.Add(boxBordereau,1,wx.ALL|wx.ALIGN_CENTRE,3)

        sizer_base = wx.FlexGridSizer(rows=1, cols=3, vgap=0, hgap=20)
        sizer_base.Add(sz_banque,1,wx.LEFT|wx.BOTTOM|wx.EXPAND,3)
        sizer_base.Add(sz_bordereau,1,wx.LEFT|wx.BOTTOM|wx.EXPAND,3)
        sizer_btn = wx.FlexGridSizer(rows=2,cols=1,vgap=0,hgap=10)
        sizer_btn.Add(self.btnDepot,1,wx.LEFT|wx.BOTTOM|wx.EXPAND,3)
        sizer_btn.Add(self.btnRaz,1,wx.LEFT|wx.BOTTOM,3)
        sizer_base.Add(sizer_btn,0,wx.ALL|wx.ALIGN_CENTRE,10)
        sizer_base.AddGrowableCol(0)
        self.SetSizer(sizer_base)

    def OnKillFocusBanque(self,event):
        # le test de renseignement de la banque n'est passé que si on n'est pas en train de sortir
        if event.Window and self.ctrlBanque.GetSelection() == -1:
             if event.Window.Name != 'btnOK':
                mess = "Choix de la banque obligatoire\n\n'OK' pourchoisir, 'Annuler' pour abandonner"
                ret = wx.MessageBox(mess,style=wx.OK|wx.CANCEL)
                if ret == wx.OK:
                    self.ctrlBanque.SetFocusFromKbd()
                else: self.parent.OnClose(event)

class PNL_corpsReglements(xgte.PNL_corps):
    #panel olv avec habillage optionnel pour des boutons actions (à droite) des infos (bas gauche) et boutons sorties
    def __init__(self, parent, dicOlv,*args, **kwds):
        xgte.PNL_corps.__init__(self,parent,dicOlv,*args,**kwds)
        self.ctrlOlv.Choices={}
        self.lstNewReglements = []
        self.flagSkipEdit = False
        self.oldRow = None

    def InitTrackVierge(self,track,trackN1):
        # Le premier accès sur la ligne va attribuer un ID, la sauvegarde se fera après la saisie du montant != 0.0
        if track.IDreglement in (None, 0):
            track.IDreglement = nur.GetNewIDreglement(self.parent.db,self.lstNewReglements)
            self.lstNewReglements.append(track.IDreglement)
            track.ventilation = []
        # reprise de la valeur 'mode' et date de la ligne précédente
        track.mode = trackN1.mode
        track.date = trackN1.date

    def OnCtrlV(self,track):
        # raz de certains champs à recomposer
        (track.IDreglement, track.date, track.IDprestation, track.IDpiece,track.compta) = (None,)*5

    def OnEditStarted(self,code):
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
            test = nur.ValideLigne(self.parent.db,track)
            if test:
                track.valide = True
                self.oldRow = row
            else:
                track.valide = False
        track = self.ctrlOlv.GetObjectAt(row)

        if track.IDreglement in (None, 0, ''):
            track.IDreglement = nur.GetNewIDreglement(self.parent.db,self.lstNewReglements)
            self.lstNewReglements.append(track.IDreglement)
            track.ventilation = []

        # conservation de l'ancienne valeur
        track.oldValue = None
        try:
            eval("track.oldValue = track.%s"%code)
        except: pass

    def OnEditFinishing(self,code=None,value=None,parent=None):
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

        # anticipe l'enregistrement du champ montant pour réussir la validation
        if code == 'montant' and value:
            track.montant = value
        nur.ValideLigne(self.parent.db,track)

        # l'enregistrement de la ligne se fait à chaque saisie pour gérer les montées et descentes
        okSauve = False
        if track.valide:
            okSauve = nur.SauveLigne(self.parent.db,self.parent, track)

        # Traitement des spécificités selon les zones
        if code == 'IDfamille':
            try:
                value = int(value)
            except:
                self.flagSkipEdit = False
                return
            designation = nur.GetDesignationFamille(self.parent.db,value)
            track.designation = designation
            self.ldPayeurs = nur.GetPayeurs(self.parent.db,value)
            payeurs = [x['nom'] for x in self.ldPayeurs]
            if len(payeurs)==0: payeurs.append(designation)
            payeur = payeurs[0]
            track.payeur = payeur
            self.ctrlOlv.dicChoices[self.ctrlOlv.lstCodesColonnes.index('payeur')]=payeurs
        if code == 'nature':
            # actualisation du flag créer
            if value.lower() in ('don','debour') :
                # Seuls les dons et débours vont générer la prestation selon l'article
                track.creer = True
                # Choix article - code comptable
                obj = nur.Article(self.parent.db,value)
                compte = obj.GetArticle()
                track.article = compte
            else:
                track.article = ""
                track.creer = False
        if code == 'montant':
            if okSauve and track.nature in ('Règlement','Ne pas créer') and value != 0.0:
                # cas du règlement d'une prestation antérieure: appel de l'écran ventilations
                dlg = ndrv.Dialog(self,-1,None,track.IDfamille,track.IDreglement,track.montant)
                if dlg.ok:
                    ret = dlg.ShowModal()
                    if ret == wx.ID_OK:
                        # --- Sauvegarde de la ventilation ---
                        dlg.panel.Sauvegarde(track.IDreglement)
                dlg.Destroy()

        # enlève l'info de bas d'écran
        self.parent.pnlPied.SetItemsInfos( INFO_OLV,wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)))
        self.flagSkipEdit = False

    def OnEditFunctionKeys(self,event):
        row, col = self.ctrlOlv.cellBeingEdited
        code = self.ctrlOlv.lstCodesColonnes[col]
        if event.GetKeyCode() == wx.WXK_F4 and code == 'IDfamille':
            # Choix famille
            IDfamille = nur.GetFamille(self.parent.db)
            self.OnEditFinishing('IDfamille',IDfamille)
            self.ctrlOlv.GetObjectAt(row).IDfamille = IDfamille

    def OnDelete(self,noligne,track,parent=None):
        nur.DeleteLigne(self.parent.db,track)

class PNL_pied(xgte.PNL_pied):
    #panel infos (gauche) et boutons sorties(droite)
    def __init__(self, parent, dicPied, **kwds):
        xgte.PNL_pied.__init__(self,parent, dicPied, **kwds)

class Dialog(wx.Dialog):
    # ------------------- Composition de l'écran de gestion----------
    def __init__(self):
        listArbo = os.path.abspath(__file__).split("\\")
        titre = listArbo[-1:][0] + "/" + self.__class__.__name__
        wx.Dialog.__init__(self, None,-1,title=titre, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)

        self.IDutilisateur = nuu.GetIDutilisateur()
        if (not self.IDutilisateur) or not nuu.VerificationDroitsUtilisateurActuel('reglements_depots','creer'):
            self.Destroy()
        else:
            ret = self.Init()
            if ret == wx.ID_ABORT: self.Destroy()

    def Init(self):
            self.db = xdb.DB()
            # définition de l'OLV
            self.dicOlv = {'lstColonnes': GetOlvColonnes(self)}
            self.dicOlv.update(GetOlvOptions(self))
            self.depotOrigine = []
            self.ctrlOlv = None
            self.withDepot = True
            # récup des modesReglements nécessaires pour passer du texte à un ID d'un mode ayant un mot en commun
            choices = []
            self.libelleDefaut = ''
            for colonne in self.dicOlv['lstColonnes']:
                if 'mode' in colonne.valueGetter:
                    choices = colonne.choices
                if 'libelle' in colonne.valueGetter:
                    self.libelleDefaut = colonne.valueSetter
            self.dicModesRegl = {}
            ldModesDB = nur.GetModesReglements(self.db)
            if ldModesDB == wx.ID_ABORT:
                return wx.ID_ABORT

            for item in choices:
                # les descriptifs de modes de règlements ne doivent pas avoir des mots en commun
                lstMots = item.split(' ')
                self.dicModesRegl[item]={'lstMots':lstMots}
                ok = False
                for dicMode in ldModesDB:
                    for mot in lstMots:
                        if mot.lower() in dicMode['label'].lower():
                            self.dicModesRegl[item].update(dicMode)
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
            self.pnlParams.ctrlSsDepot.Bind(wx.EVT_KILL_FOCUS,self.OnSsDepot)
            self.choicesNonDiffere = self.ctrlOlv.lstColonnes[self.ctrlOlv.lstCodesColonnes.index('mode')].choices
            self.OnSsDepot(None)
            self.Bind(wx.EVT_CLOSE,self.OnClose)
            self.__Sizer()

    def __Sizer(self):
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
    def IsSaisie(self):
        # Une seule ligne a été crée
        if len(self.depotOrigine) == 0 and len(self.ctrlOlv.innerList) ==1:
            # la saisie d'un champ a initialisé la validation
            if not hasattr(self.ctrlOlv.innerList[0],'valide'):
                return False
            else : return True
        # Cas d'une reprise de bordereau - depôt
        if len(self.ctrlOlv.innerList) != len(self.depotOrigine):
            return True
        saisie = False
        # test de la modif de chaque ligne
        for ix in range(len(self.depotOrigine)):
            if self.ctrlOlv.innerList[ix].donnees != self.depotOrigine[ix].donnees:
                saisie = True
                break
        return saisie

    def GetIDbanque(self):
        ix = self.pnlParams.ctrlBanque.GetSelection()
        return self.pnlParams.lstIDbanques[ix]

    def SetTitreImpression(self):
        IDdepot = self.pnlParams.ctrlRef.GetValue()
        ctrl = self.pnlParams.ctrlBanque
        banque = ctrl.GetString(ctrl.GetSelection())
        dte = self.pnlParams.ctrlDate.GetValue()
        if not IDdepot: IDdepot = "___"
        self.ctrlOlv.titreImpression = "REGLEMENTS Dépot No %s, du %s, banque: %s "%(IDdepot,dte.FormatDate(),banque)

    def InitOlv(self,withDiffere=False):
        self.ctrlOlv.lstColonnes = GetOlvColonnes(self)
        self.ctrlOlv.lstCodesColonnes = self.ctrlOlv.formerCodeColonnes()
        ixMode = self.ctrlOlv.lstCodesColonnes.index('mode')
        ixDiffere= self.ctrlOlv.lstCodesColonnes.index('differe')
        if not withDiffere:
            del self.ctrlOlv.lstCodesColonnes[ixDiffere]
            del self.ctrlOlv.lstColonnes[ixDiffere]
            self.ctrlOlv.lstColonnes[ixMode].choices = self.choicesNonDiffere
        else:
            self.ctrlOlv.lstColonnes[ixMode].choices = ['ND non déposés']
        self.ctrlOlv.InitObjectListView()
        self.Refresh()

    def TransposeDonnees(self,lstDonnees):
        # ajustement des choix possibles selon le contenu du règlement
        ixmod = self.ctrlOlv.lstCodesColonnes.index('mode')
        ixnat = self.ctrlOlv.lstCodesColonnes.index('nature')
        ixdat = self.ctrlOlv.lstCodesColonnes.index('date')
        for donnees in lstDonnees:
            # choix du 'mode règlement'
            ok = False
            for mode,dicMod in self.dicModesRegl.items():
                for mot in dicMod['lstMots']:
                    if mot in donnees[ixmod].lower():
                        donnees[ixmod] = mode
                        ok = True
                        break
                if ok: break
            # forcer ne pas créer pour la reprise d'un dépot avec la prestation déjà créée avant
            donnees[ixnat] = 'Ne pas créer'
            # date remise en format français
            donnees[ixdat] = xformat.DateSqlToDatetime(donnees[ixdat])
        return

    def OnSsDepot(self,event):
        # cas d'une saisie différée, la grille est modifiée
        if event:
            value = event.EventObject.GetValue()
            self.pnlParams.btnDepot.Enable(not(value))
            self.pnlParams.lblRef.Enable(not(value))
        else:
            value = False
        self.withDepot = not value
        self.InitOlv(withDiffere=value)

    def OnRaz(self,event):
        # effacement des lignes sur l'écran
        self.pnlParams.ctrlRef.SetValue('')
        self.ctrlOlv.lstDonnees = []
        self.ctrlOlv.MAJ()
        self.pnlPied.SetItemsInfos(INFO_OLV, wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)))
        self.pnlOlv.Refresh()

    def OnGetDepot(self,event):
        # lancement de la recherche d'un dépot
        self.ctrlOlv.cellEditMode = self.ctrlOlv.CELLEDIT_NONE
        dicDepot = nur.GetDepot(self.db)
        IDdepot = None
        self.ctrlOlv.cellEditMode = self.ctrlOlv.CELLEDIT_DOUBLECLICK        # gestion du retour du choix dépot
        if 'numero' in dicDepot.keys():
            IDdepot = dicDepot['numero']
        self.pnlParams.ctrlSsDepot.Enable(True)
        if isinstance(IDdepot,int):
            lstDonnees = [rec[:-2] for rec in  nur.GetReglements(self.db,IDdepot)]
            lstEnCompta = [rec[:-2] for rec in  nur.GetReglements(self.db,IDdepot) if (rec[-2] or rec[-1])]
            # présence de lignes déjà transférées compta
            if len(lstEnCompta) >0:
                self.ctrlOlv.cellEditMode = self.ctrlOlv.CELLEDIT_NONE
                self.pnlPied.SetItemsInfos("NON MODIFIABLE: règlement ou prestation transféré en compta ",
                                           wx.ArtProvider.GetBitmap(wx.ART_ERROR, wx.ART_OTHER, (16, 16)))

            if len(lstDonnees)>0:
                # transposition mode de règlement
                self.TransposeDonnees(lstDonnees)
                # marque dépot non différé car déjà déposé
                self.pnlParams.ctrlSsDepot.Enable(False)
                # set date du dépot
                if xformat.DateSqlToWxdate(dicDepot['date']):
                    self.pnlParams.ctrlDate.SetValue(xformat.DateSqlToWxdate(dicDepot['date']))
                # set IDdepot en référence
                self.pnlParams.ctrlRef.SetValue(str(IDdepot))
                # set le nom de la banque
                self.pnlParams.ctrlBanque.SetSelection(self.pnlParams.ctrlBanque.FindString(dicDepot['banque']))
                # place les règlements du dépôt dans la grille
                self.ctrlOlv.lstDonnees = lstDonnees
                self.InitOlv(withDiffere=False)
                # les écritures reprises sont censées être valides
                for item in self.ctrlOlv.modelObjects[:-1]:
                    item.valide = True
                self.ctrlOlv._FormatAllRows()
                # stockage pour test de saisie
                self.depotOrigine = self.ctrlOlv.innerList
                self.IDdepot = IDdepot
                self.withDepot = True
            else:
                wx.MessageBox("Aucune écriture:\n\nle dépôt %s est vide ou pb d'accès"%IDdepot)
                self.IDdepot = None

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
    dlg = Dialog()
    dlg.ShowModal()
    app.MainLoop()
