#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -------------------------------------------------------------
# Application :    NoeLITE, gestion des adresses des individus
# Auteur:           Jacques BRUNEL
# Licence:         Licence GNU GPL
# -------------------------------------------------------------

NOM_MODULE = "DLG_Adresses_gestion"
ACTION = "Gestion\nadresse"
ACTION2 = "Tél. /\nmails"
TITRE = "Choisissez une ligne !"
INTRO = "Double clic pour lancer la gestion de l'adresse"
MINSIZE = (1200,650)
WCODE = 150
WLIBELLE = 100
LIMITSQL =100

import wx
import datetime
import xpy.xGestion_TableauRecherche     as xgtr
import xpy.xUTILS_DB           as xdb
import srcNoelite.UTILS_Utilisateurs  as nuu
import srcNoelite.DLG_Adresses_saisie   as nsa
import srcNoelite.UTILS_Adresses        as nua
import srcNoelite.DLG_AdrMelTel_saisie  as nsc
from xpy.outils import xformat, xbandeau, xboutons

def dicOlvIndividus():
    # appel des données à afficher
    lstChamps = ["0","IDindividu", "nom", "prenom","date_naiss", "adresse_auto",
                "rue_resid", "cp_resid", "ville_resid","tel_domicile", "tel_mobile", "mail"]
    lstNomsColonnes = ["null","Individu", "Nom", "Prenom","Naissance","chez",
                        "rue", "cp", "ville","tel domicile", "tel mobile", "mail"]
    lstTypes = ["INTEGER","INTEGER","VARCHAR(100)","VARCHAR(100)","DATE","INTEGER",
                "VARCHAR(100)","VARCHAR(8)","VARCHAR(100)","VARCHAR(11)","VARCHAR(11)","VARCHAR(40)"]
    lstCodesColonnes = [xformat.SupprimeAccents(x) for x in lstNomsColonnes]
    lstValDefColonnes = xformat.ValeursDefaut(lstNomsColonnes, lstTypes)
    lstLargeurColonnes = xformat.LargeursDefaut(lstNomsColonnes, lstTypes)
    # composition des données du tableau à partir du recordset
    # matrice OLV
    lstColonnes = xformat.DefColonnes(lstNomsColonnes, lstCodesColonnes, lstValDefColonnes, lstLargeurColonnes)
    dicOlv =    {
                'lstColonnes': lstColonnes,
                'lstChamps': lstChamps,
                'checkColonne': False,
                'sortColumnIndex': 2,
                'style': wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES,
                'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
                'dictColFooter': {"nom": {"mode": "nombre", "alignement": wx.ALIGN_CENTER},}
                }
    return dicOlv

def dicOlvFamilles():
    # appel des données à afficher
    lstChamps = ["0","familles.IDfamille","individus.IDindividu","familles.adresse_intitule","individus.nom",
                 "individus.prenom","individus.adresse_auto","individus.rue_resid","individus.cp_resid","individus.ville_resid"]

    lstNomsColonnes = ["0","famille","individu","intitule famille","nom corresp.",
                        "prenomcorresp.","chez","rue","cp","ville"]

    lstTypes = ["INTEGER","INTEGER","INTEGER","VARCHAR(100)","VARCHAR(100)",
                "VARCHAR(100)","INTEGER","VARCHAR(100)","VARCHAR(11)","VARCHAR(80)"]
    lstCodesColonnes = [xformat.SupprimeAccents(x) for x in lstNomsColonnes]
    lstValDefColonnes = xformat.ValeursDefaut(lstNomsColonnes, lstTypes)
    lstLargeurColonnes = xformat.LargeursDefaut(lstNomsColonnes, lstTypes)

    # matrice OLV
    lstColonnes = xformat.DefColonnes(lstNomsColonnes, lstCodesColonnes, lstValDefColonnes, lstLargeurColonnes)
    dicOlv =    {
                'lstColonnes': lstColonnes,
                'lstChamps': lstChamps,
                'checkColonne': False,
                'sortColumnIndex': 4,
                'style': wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES|wx.LC_REPORT,
                'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
                'dictColFooter': {"nom": {"mode": "nombre", "alignement": wx.ALIGN_CENTER},}
                }
    return dicOlv

def ComposeLstDonnees(record,lstChamps,lstColonnes):
    # retourne les données pour colonnes, les champs doivent correspondre aux premières colonnes
    lstdonnees=[]
    nbcol = min(len(lstChamps),len(lstColonnes))
    for ix in range(nbcol):
        if type(lstColonnes[ix].valueSetter) in (wx.DateTime, datetime.date, datetime.datetime):
            if type(lstColonnes[ix].valueSetter) == wx.DateTime:
                lstdonnees.append(xformat.DateSqlToWxdate(record[ix]))
            else:
                lstdonnees.append(xformat.DateSqlToDatetime(record[ix]))
        else:
            lstdonnees.append(record[ix])
    return lstdonnees

class Pnl_tableau(xgtr.PNL_tableau):
    def __init__(self,parent,dicOlv):

        dicOlv['menuPersonnel'] = True
        dicOlv['autoSizer'] = False
        xgtr.PNL_tableau.__init__(self,parent,dicOlv)
        # Boutons
        bmpcoords = wx.Bitmap("xpy/Images/32x32/Mobile.png")
        helpcoords = "Ouvre une nouvelle fenêtre pour gérer l'adresse"
        bouton_coords = xboutons.Bouton(self,label=ACTION2,image=bmpcoords,help=helpcoords,onBtn=self.OnCoord)

        bmpok = wx.Bitmap("xpy/Images/32x32/Boite.png")
        helpok = "Ouvre une nouvelle fenêtre pour gérer l'adresse"
        bouton_ok = xboutons.Bouton(self,label=ACTION,image=bmpok,help=helpok,onBtn=self.OnDblClick)

        bmpabort = wx.Bitmap("xpy/Images/32x32/Quitter.png")
        bouton_fermer = wx.Button(self, id = wx.ID_CANCEL,label=(u"Quitter"))
        bouton_fermer.SetBitmap(bmpabort)
        bouton_fermer.SetToolTip(u"Cliquez ici pour fermer")
        #self.bouton_fermer = bouton_fermer
        self.lstBtns = [bouton_coords,bouton_ok,bouton_fermer]

        # Binds
        self.Bind(wx.EVT_BUTTON, self.OnDblClicFermer, bouton_fermer)
        #self.ctrlOlv.Bind(wx.EVT_LIST_ITEM_ACTIVATED,self.OnDblClic)
        self.ProprietesOlv()
        self.Sizer()

    def GetMenuPersonnel(self):
        menuPop = wx.Menu()
        # On met un separateur
        menuPop.AppendSeparator()
        item = wx.MenuItem(menuPop, 13, "Téléphones/Mails")
        item.SetBitmap(wx.Bitmap("xpy/Images/16x16/Mobile.png", wx.BITMAP_TYPE_PNG))
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.OnCoord, id=13)
        item = wx.MenuItem(menuPop, 17, "Gérer l'adresse")
        item.SetBitmap(wx.Bitmap("xpy/Images/16x16/Boite.png", wx.BITMAP_TYPE_PNG))
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.OnDblClick, id=17)
        return menuPop

    def OnCoord(self,event):
        self.choix = self.ctrlOlv.GetSelectedObject()
        if self.choix == None:
            dlg = wx.MessageDialog(self, (u"Pas de sélection faite !\nIl faut choisir ou cliquer sur annuler"), (u"Accord Impossible"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
        else:
            if nuu.VerificationDroitsUtilisateurActuel("individus_coordonnees", "modifier") == False: return
            if self.parent.mode == 'familles':
                ID = self.choix.famille
                nom = "famille"
                prenom = self.choix.intitulefamille
            else:
                ID = self.choix.individu
                nom = self.choix.nom
                prenom = self.choix.prenom
            dlg2 = nsc.DlgAdrMelTel(ID,mode=self.parent.mode, titre=u"Adresse de %d - %s %s"%(ID,nom,prenom))
            ret = dlg2.ShowModal()
            if ret == wx.OK and self.parent.mode == 'individus':
                nele,teldomicile, telmobile, mail = dlg2.GetRetourInd()
                self.choix.naissance = nele
                self.choix.teldomicile= teldomicile
                self.choix.telmobile = telmobile
                self.choix.mail = mail
                self.ctrlOlv.SelectObject(self.choix)
            dlg2.Destroy()

    def OnDblClick(self,event):
        self.choix = self.ctrlOlv.GetSelectedObject()
        if self.choix == None:
            dlg = wx.MessageDialog(self, (u"Pas de sélection faite !\nIl faut choisir ou cliquer sur annuler"), (u"Accord Impossible"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
        else:
            if nuu.VerificationDroitsUtilisateurActuel("individus_coordonnees", "modifier") == False: return
            if self.parent.mode == 'familles':
                ID = self.choix.famille
                nom = "famille"
                prenom = self.choix.intitulefamille
            else:
                ID = self.choix.individu
                nom = self.choix.nom
                prenom = self.choix.prenom
            dlg2 = nsa.DlgAdresses_saisie(ID,mode=self.parent.mode, titre=u"Adresse de %d - %s %s"%(ID,nom,prenom))
            ret = dlg2.ShowModal()
            if ret == wx.OK:
                lstAdresse = dlg2.lstAdresse
                rue, cp, ville = nua.LstAdresseToChamps(lstAdresse)
                self.choix.rue = rue
                self.choix.ville = ville
                self.choix.cp = cp
                self.ctrlOlv.SelectObject(self.choix)
            dlg2.Destroy()

    def OnDblClicFermer(self, event):
        self.parent.EndModal(wx.ID_CANCEL)

class Dialog(wx.Dialog):
    def __init__(self, mode='individus', titre=TITRE, intro=INTRO):
        self.limitSql = LIMITSQL
        self.db = xdb.DB()
        wx.Dialog.__init__(self, None, -1,pos=(50,80),style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        if nuu.VerificationDroitsUtilisateurActuel("individus_fiche", "consulter") == False:
            if self.IsModal():
                self.EndModal(wx.ID_CANCEL)
            else: self.Destroy()
        self.mode = mode
        self.SetTitle(NOM_MODULE)
        self.choix= None

        # Bandeau
        self.ctrl_bandeau = xbandeau.Bandeau(self, titre=titre, texte=intro,  hauteur=18, nomImage="xpy/Images/32x32/Matth.png")

        # composition des objets
        if self.mode == 'familles':
            dicOlv = dicOlvFamilles()
            self.getDonnees = self.GetFamilles
        else:
            dicOlv = dicOlvIndividus()
            self.\
                getDonnees = self.GetIndividus

        dicOlv['getDonnees'] = self.getDonnees
        pnlOlv = Pnl_tableau(self, dicOlv)
        self.ctrlOlv = pnlOlv.ctrlOlv
        self.olv = pnlOlv

        # Initialisations
        self.__set_properties()
        self.Sizer()

    def __set_properties(self):
        self.SetMinSize(MINSIZE)

    def Sizer(self):
        gridsizer_base = wx.FlexGridSizer(rows=6, cols=1, vgap=0, hgap=0)
        gridsizer_base.Add(self.ctrl_bandeau, 1, wx.EXPAND, 0)

        sizerolv = wx.BoxSizer(wx.VERTICAL)
        sizerolv.Add(self.olv, 10, wx.EXPAND, 10)
        gridsizer_base.Add(sizerolv, 10, wx.EXPAND, 10)
        gridsizer_base.Add(wx.StaticLine(self), 0, wx.TOP| wx.EXPAND, 3)

        self.SetSizer(gridsizer_base)
        gridsizer_base.Fit(self)
        gridsizer_base.AddGrowableRow(1)
        gridsizer_base.AddGrowableCol(0)
        self.Layout()
        self.SetSizer(gridsizer_base)

    def GetIndividus(self,db,**kwd):
        # appel des données à afficher
        filtreTxt = kwd.pop('filtreTxt','')
        lstChamps = kwd['dicOlv']['lstChamps']
        lstColonnes = kwd['dicOlv']['lstColonnes']
        nbreFiltres = kwd.pop('nbreFiltres',0)

        # en présence d'autres filtres: tout charger pour filtrer en mémoire par predicate.
        # cf self.listeFiltresColonnes  à gérer avec champs au lieu de codes colonnes
        limit = ''
        if self.limitSql and (nbreFiltres == 0 ):
            limit = "LIMIT %d"%self.limitSql

        whereFiltre = ''
        if filtreTxt and len(filtreTxt) >0:
            whereFiltre = xformat.ComposeWhereFiltre(filtreTxt,lstChamps, lstColonnes = lstColonnes)

        del db.cursor
        db.cursor = db.connexion.cursor(buffered=False)

        req = """FLUSH  TABLES individus;"""
        retour = db.ExecuterReq(req, mess='%s.GetIndividus' % NOM_MODULE)

        req = """
                SELECT %s
                FROM individus
                %s
                ORDER BY %s DESC
                %s; """ % (",".join(lstChamps),whereFiltre,lstChamps[1],limit)
        retour = db.ExecuterReq(req, mess='%s.GetIndividus' % NOM_MODULE)
        if retour == "ok":
            recordset = db.ResultatReq()
            if len(recordset) == 0:
                retour = "aucun enregistrement disponible"
        else:
            wx.MessageBox("Erreur : %s" % retour)
            return 'ko'
        # composition des données du tableau à partir du recordset
        lstDonnees = []
        for record in recordset:
            ligne = ComposeLstDonnees(record, lstChamps,lstColonnes)
            lstDonnees.append(ligne)
        return lstDonnees

    def GetFamilles(self,db,**kwd):
        # appel des données à afficher
        filtreTxt = kwd.pop('filtreTxt','')
        lstChamps = kwd['dicOlv']['lstChamps']
        lstColonnes = kwd['dicOlv']['lstColonnes']
        nbreFiltres = kwd.pop('nbreFiltres',0)

        # en présence d'autres filtres: tout charger pour filtrer en mémoire par predicate.
        # cf self.listeFiltresColonnes  à gérer avec champs au lieu de codes colonnes
        limit = ''
        if self.limitSql and (nbreFiltres == 0 ):
            limit = "LIMIT %d"%self.limitSql

        whereFiltre = ''
        if filtreTxt and len(filtreTxt) >0:
                whereFiltre = xformat.ComposeWhereFiltre(filtreTxt,lstChamps, lstColonnes = lstColonnes,lien='WHERE')

        req = """FLUSH TABLES individus;"""
        retour = db.ExecuterReq(req, mess='%s.GetIndividus' % NOM_MODULE)
        req = """   SELECT %s
                    FROM familles 
                    INNER JOIN individus ON familles.adresse_individu = individus.IDindividu
                    %s
                    ORDER BY %s DESC
                    %s;
                    """ % (",".join(lstChamps),whereFiltre,lstChamps[1],limit)
        retour = db.ExecuterReq(req, mess='%s.GetIndividus' % NOM_MODULE)
        if retour == "ok":
            recordset = db.ResultatReq()
            if len(recordset) == 0:
                retour = "aucun enregistrement disponible"
        else:
            wx.MessageBox("Erreur : %s" % retour)
            return 'ko'
        # composition des données du tableau à partir du recordset
        lstDonnees = []
        for record in recordset:
            ligne = ComposeLstDonnees(record, lstChamps, lstColonnes)
            lstDonnees.append(ligne)
        return lstDonnees

    def GetChoix(self):
        self.choix = self.ctrlOlv.GetSelectedObject()
        return self.choix

#-------------------------------------------------

if __name__ == '__main__':
    app = wx.App(0)
    import os
    os.chdir("..")
    dlg = Dialog(mode='individus')
    dlg.ShowModal()
    app.MainLoop()
