#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Matthania
# Auteur:          Jacques Brunel, 12/2020
# Licence:         Licence GNU GPL
# Permet une saisie de mail et téléphones pour  Noethys
#------------------------------------------------------------------------

import wx
import xpy.xGestion_TableauEditor   as xgte
import xpy.xUTILS_SaisieParams      as xusp
import xpy.xUTILS_DB                as xdb
import srcNoelite.UTILS_Adresses as nua
from xpy.outils     import xbandeau,xboutons,xformat

# DICOLV paramètre les options de l'OLV
def GetDicOlvInd():
    # appel des données à afficher
    lstChamps = ["individus.IDindividu","individus.nom","individus.prenom","individus.date_naiss",
                 "individus.tel_domicile","individus.tel_mobile","individus.travail_tel",
                 "individus.mail","individus.travail_mail","individus.refus_pub","individus.refus_mel"]

    lstNomsColonnes = ["IDind","nom","prénom","né le",
                 "tel domicile","tel mobile","tel travail",
                 "mail1","mail2","noPub","noMel"]

    lstTypes = ["INTEGER","VARCHAR(32)","VARCHAR(32)","DATE",
                "VARCHAR(10)","VARCHAR(10)","VARCHAR(10)","VARCHAR(32)","VARCHAR(32)","BOOL","BOOL"]

    lstLargeurColonnes = [0,-1,-1,80,90,90,90,170,120,50,60]

    lstCodesColonnes = [xformat.SupprimeAccents(x) for x in lstNomsColonnes]
    lstValDefColonnes = xformat.ValeursDefaut(lstNomsColonnes, lstTypes)

    # matrice OLV
    lstColonnes = xformat.DefColonnes(lstNomsColonnes, lstCodesColonnes, lstValDefColonnes, lstLargeurColonnes)

    # personnalise les colonnes : fixe les éditables, pose minwidth
    for col in lstColonnes[3:]:
        col.isEditable=True
    for col in lstColonnes[:3]:
        col.isEditable=False
    for col in lstColonnes:
        if col.width == -1: col.minimumWidth=60

    dicOlv =    {
                'lstColonnes': lstColonnes,
                'lstChamps': lstChamps,
                'checkColonne': False,
                'getBtnActions': None,
                'sortColumnIndex': 2,
                'sortAscending': True,
                'style': wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES,
                'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
                'recherche': False,
                'autoAddRow': False,
                'editMode': True,
    }
    return dicOlv

def GetDicOlvFam():
    # appel des données à afficher
    lstChamps = ["individus.IDindividu","individus.nom","individus.prenom","familles.adresse_individu",
                 "rattachements.titulaire","rattachements.IDcategorie","individus.date_naiss",
                 "individus.tel_domicile","individus.tel_mobile", "individus.mail",
                "individus.travail_mail","individus.refus_pub","individus.refus_mel","individus.travail_tel"]

    lstNomsColonnes = ["IDind","nom","prénom","catégorie","né le",
                 "tel domicile","tel mobile",
                 "mail1","mail2","noPub","noMel","tel travail"]

    lstTypes = ["INTEGER","VARCHAR(32)","VARCHAR(32)","VARCHAR(7)","DATE",
                "VARCHAR(10)","VARCHAR(10)","VARCHAR(32)","VARCHAR(32)","BOOL","BOOL","VARCHAR(10)"]

    lstLargeurColonnes = [0,-1,-1,50,80,90,90,170,120,50,50,90]

    lstCodesColonnes = [xformat.SupprimeAccents(x) for x in lstNomsColonnes]
    lstValDefColonnes = xformat.ValeursDefaut(lstNomsColonnes, lstTypes)

    # matrice OLV
    lstColonnes = xformat.DefColonnes(lstNomsColonnes, lstCodesColonnes, lstValDefColonnes, lstLargeurColonnes)

    # personnalise les colonnes : fixe les éditables, pose minwidth
    for col in lstColonnes[4:]:
        col.isEditable=True
    for col in lstColonnes[:4]:
        col.isEditable=False
    for col in lstColonnes:
        if col.width == -1: col.minimumWidth=60

    dicOlv =    {
                'lstColonnes': lstColonnes,
                'lstChamps': lstChamps,
                'checkColonne': False,
                'getBtnActions': None,
                'sortColumnIndex': 2,
                'sortAscending': True,
                'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
                'recherche': False,
                'autoAddRow': False,
                'editMode': True,
    }
    return dicOlv

class PNL_corps(xgte.PNL_corps):
    #panel olv avec habillage optionnel pour des boutons actions (à droite) des infos (bas gauche) et boutons sorties
    def __init__(self, parent, dicOlv,*args, **kwds):
        xgte.PNL_corps.__init__(self,parent,dicOlv,*args,**kwds)
        self.flagSkipEdit = False
        self.oldRow = None

    def OnEditFinishing(self,code=None,value=None,parent=None):
        # flagSkipEdit permet d'occulter les évènements redondants. True durant la durée du traitement
        if self.flagSkipEdit : return
        self.flagSkipEdit = True

        (row, col) = self.ctrlOlv.cellBeingEdited
        track = self.ctrlOlv.GetObjectAt(row)

        # si pas de saisie on passe
        if (not value) or track.oldValue == value:
            self.flagSkipEdit = False
            return

        # Traitement des spécificités selon les zones
        if self.parent.mode == 'familles':
            if code == 'nopub':
                self.parent.pnlPied.famNoPub.Set3StateValue(wx.CHK_UNDETERMINED)
                self.parent.pnlPied.famNoPub.Refresh()

            if code == 'nomel':
                self.parent.pnlPied.famNoMel.Set3StateValue(wx.CHK_UNDETERMINED)
                self.parent.pnlPied.famNoMel.Refresh()

        if code == 'mail1' or code == 'mail2':
            if len(value)>0:
                if not '@' in value or not '.' in value:
                    wx.MessageBox("Une adresse mail doit comporter '@' et '.'")

        self.flagSkipEdit = False

class PNL_pied(wx.Panel):
    #personnalisation du pied avec boutons sorties(droite)
    def __init__(self, parent, **kwds):
        self.parent = parent
        wx.Panel.__init__(self, parent,  **kwds)
        self.lstBtns = [xboutons.BTN_esc(self),
                        xboutons.BTN_fermer(self,label='Valider')]
        if self.parent.mode == 'familles':
            self.famNoPub = wx.CheckBox(self,wx.ID_ANY,label="No Pub pour famille",style=wx.CHK_3STATE)
            self.famNoPub.Bind(wx.EVT_CHECKBOX,parent.ONfamNoPub)
            self.famNoPub.SetToolTip("En cliquant vous aller appliquer l'action à l'ensemble des membres de la famille")
            self.famNoMel = wx.CheckBox(self,label="No Mails pour famille",style=wx.CHK_3STATE)
            self.famNoMel.Bind(wx.EVT_CHECKBOX,parent.ONfamNoMel)
            self.famNoMel.SetToolTip("En cliquant vous aller appliquer l'action à l'ensemble des membres de la famille")

        self.Sizer()

    def Sizer(self):
        self.itemsBtns = xboutons.GetAddManyBtns(self,self.lstBtns)
        #composition de l'écran selon les composants
        sizerpied = wx.FlexGridSizer(rows=1, cols=5, vgap=0, hgap=0)
        sizerpied.Add((10,10),1,wx.ALL|wx.EXPAND,5)
        if self.parent.mode == 'familles':
            sizerpied.Add(self.famNoPub,0,wx.ALL|wx.EXPAND,5)
            sizerpied.Add(self.famNoMel,0,wx.ALL|wx.EXPAND,5)
        if self.lstBtns:
            sizerpied.AddMany(self.itemsBtns)
        sizerpied.AddGrowableCol(0)
        self.SetSizer(sizerpied)

    def CreateItemsInfos(self,lstInfos):
        # images ou texte sont retenus
        self.infosImage = None
        self.infosTexte = None
        lstItems = [(7,7)]
        if not lstInfos: lstInfos = []
        for item in lstInfos:
            if isinstance(item,wx.Bitmap):
                self.infosImage = wx.StaticBitmap(self, wx.ID_ANY, item)
                lstItems.append((self.infosImage,0,wx.ALIGN_LEFT|wx.TOP,10))
            elif isinstance(item,str):
                self.infosTexte = wx.StaticText(self,wx.ID_ANY,item)
                lstItems.append((self.infosTexte,10,wx.ALIGN_LEFT|wx.ALL|wx.EXPAND,5))
            lstItems.append((7,7))
        return lstItems

    def SetItemsInfos(self,text=None,image=None,):
        # après create  permet de modifier l'info du pied pour dernière image et dernier texte
        if image:
            self.infosImage.SetBitmap(image)
        if text:
            self.infosTexte.SetLabelText(text)

    def OnBoutonOK(self,event):
        self.parent.OnFermer(None)

class DlgAdrMelTel(xusp.DLG_vide):
    # minimum fonctionnel dans dialog tout est dans les pnl
    def __init__(self,ID,mode='familles',titre="",**kwds):
        minSize = (400, 200)
        kw = {'size':(1200,400),'pos':(55,180)}
        super().__init__(None,**kw)
        self.mode = mode
        self.IDref = ID
        if not ID: raise("pas d'ID %s reçu!"%mode)
        self.famNoPub, self.famNoMel = False,False

        intro = "Vous pouvez saisir dans la liste sans pouvoir ajouter ni retrancher une ligne, "
        intro += "le changement de nom ou de catérorie se fait dans NOETHYS."
        self.bandeau = xbandeau.Bandeau(self, titre=titre, texte=intro,  hauteur=15, nomImage="xpy/Images/32x32/Matth.png")

        # appel des paramètes de l'OLV et chargement des données initiales, corrigées dans self.lstDonnees
        if mode == 'familles':
            self.dicOlv = GetDicOlvFam()
            self.dicOlv['lstDonnees'] = self.GetCoordonnees()
        else:
            self.dicOlv = GetDicOlvInd()
            self.dicOlv['lstDonnees'] = self.GetCoordIndividu()

        # pnl et pnlPied sont reconnus par le Size de DLG_vide
        self.pnl = PNL_corps(self, self.dicOlv,  **kwds )
        self.ctrl = self.pnl.ctrlOlv

        self.pnlPied = PNL_pied(self)
        self.SetMinSize(minSize)

        if self.mode == 'familles':
            self.SetCheckFamNo()
        self.Sizer()

    def GetCoordonnees(self):
        # appel des coordonnées de la famille
        lstCoordonnees = []
        DB = xdb.DB()
        req = """SELECT %s
                FROM (familles 
                INNER JOIN rattachements ON familles.IDfamille = rattachements.IDfamille) 
                INNER JOIN individus ON rattachements.IDindividu = individus.IDindividu
                WHERE (familles.IDfamille = %d)
                ;"""%(",".join(self.dicOlv['lstChamps']),self.IDref)
        ret = DB.ExecuterReq(req,mess="aUTILS_Adresses_saisie.GetDBfamille")
        if ret == "ok":
            recordset = DB.ResultatReq()
            for IDindividu,nom,prenom,corresp,titulaire,IDcategorie,date_naiss,tel_domcile,tel_mobile,\
                travail_tel,mail,travail_mail,refus_pub,refus_mail in recordset:
                categorie = ""
                if corresp == IDindividu:   categorie += "* "
                if titulaire == 1:          categorie += "Titul."
                elif IDcategorie == 1:      categorie += "repr."
                if IDcategorie == 3:        categorie += "contact"
                coordonnee = [IDindividu,nom,prenom,categorie,date_naiss,tel_domcile,tel_mobile,
                              travail_tel,mail,travail_mail,refus_pub,refus_mail]
                lstCoordonnees.append(coordonnee)

        # appel des noPub, noMel famille
        req = """SELECT refus_pub, refus_mel
                FROM familles 
                WHERE (familles.IDfamille = %d)
                ;"""%(self.IDref)
        ret = DB.ExecuterReq(req,mess="aUTILS_Adresses_saisie.GetDBfamille")
        if ret == "ok":
            recordset = DB.ResultatReq()
            for noPub, noMel in recordset:
                if not noPub: noPub = False
                if not noMel: noMel = False
                self.famNoPub = noPub
                self.famNoMel = noMel
        DB.Close()
        return lstCoordonnees

    def GetCoordIndividu(self):
        # appel des coordonnées de la famille de l'individu
        lstCoordonnees = []
        DB = xdb.DB()
        req = """SELECT %s
                FROM individus
                WHERE IDindividu = %d
                ;"""%(",".join(self.dicOlv['lstChamps']),self.IDref)
        ret = DB.ExecuterReq(req,mess="aUTILS_Adresses_saisie.GetDBIndividu")
        if ret == "ok":
            recordset = DB.ResultatReq()
            for IDindividu,nom,prenom,date_naiss,tel_domcile,tel_mobile,\
                travail_tel,mail,travail_mail,refus_pub,refus_mail in recordset:
                coordonnee = [IDindividu,nom,prenom,date_naiss,tel_domcile,tel_mobile,
                              travail_tel,mail,travail_mail,refus_pub,refus_mail]
                lstCoordonnees.append(coordonnee)
        DB.Close()
        return lstCoordonnees

    def SetCheckFamNo(self):
        self.pnlPied.famNoPub.SetValue(self.famNoPub)
        self.pnlPied.famNoMel.SetValue(self.famNoMel)

    def ONfamNoMel(self,evt):
        value =  evt.EventObject.GetValue()
        ix = self.ctrl.lstCodesColonnes.index('nomel')
        for ligne in self.ctrl.lstDonnees:
            ligne[ix] = value
        self.ctrl.MAJ()

    def ONfamNoPub(self,evt):
        value =  evt.EventObject.GetValue()
        ix = self.ctrl.lstCodesColonnes.index('nopub')
        for ligne in self.ctrl.lstDonnees:
            ligne[ix] = value
        self.ctrl.MAJ()

    def GetRetourInd(self):
        return (self.nele,self.teldomicile,self.telmobile,self.mail1)

    def ValideSaisie(self,*arg,**kwds):
        if len(self.ctrl.lstDonnees) == 0: return
        lstChamps = ["date_naiss","tel_domicile", "tel_mobile", "travail_tel",
                    "mail", "travail_mail", "refus_pub", "refus_mel"]
        lstCodes = ["nele","teldomicile","telmobile","teltravail","mail1","mail2","nopub","nomel"]
        lstIdx = [self.ctrl.lstCodesColonnes.index(x) for x in lstCodes]
        DB = xdb.DB()
        for ligne in self.ctrl.lstDonnees:
            IDindividu = ligne[0]
            donnees = []
            for ix in lstIdx:
                donnees.append(ligne[ix])
            DB.ReqMAJ('individus',nomChampID='IDindividu',ID=IDindividu,lstChamps=lstChamps,
                      lstValues=donnees,mess="MAJ DLG_AdrMel")
        if self.mode == 'familles':
            donnees = [self.famNoPub,self.famNoMel]
            DB.ReqMAJ('familles',nomChampID='IDfamille',ID=self.IDref,lstChamps=['refus_pub','refus_mel'],
                      lstValues=donnees,mess="MAJ DLG_AdrMel refus")
        ligne = self.ctrl.lstDonnees[0]
        self.nele = ligne[self.ctrl.lstCodesColonnes.index('nele')]
        self.teldomicile = ligne[self.ctrl.lstCodesColonnes.index('teldomicile')]
        self.telmobile = ligne[self.ctrl.lstCodesColonnes.index('telmobile')]
        self.mail1 = ligne[self.ctrl.lstCodesColonnes.index('mail1')]
        DB.Close()
        return wx.OK

if __name__ == "__main__":
    app = wx.App(0)
    import os
    os.chdir("..")
    dlg = wx.Frame(None)
    dlg.ID = 709
    dlg2 = DlgAdrMelTel(dlg.ID, mode='familles',titre="Coordonnées de %d"%dlg.ID)
    dlg2.ShowModal()
    app.MainLoop()
