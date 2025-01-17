#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Modif pour gérer les zéros devant
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, Jacques Brunel
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
import xpy.xUTILS_DB                   as xdb
import srcNoelite.UTILS_Adresses   as usa
import xpy.xUTILS_Identification as nuu
import srcNoelite.DLG_Pays          as DLG_Pays
from xpy.ObjectListView.ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils

class CTRL_Bouton_image(wx.Button):
    def __init__(self, parent, id=wx.ID_APPLY, texte="", cheminImage=None):
        wx.Button.__init__(self, parent, id=id, label=texte)
        if cheminImage:
            self.SetBitmap(wx.Bitmap(cheminImage))
        self.SetFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.SetInitialSize()

# -------------------------------------------------------------------------------------------------------------------------------------------

class DLG_Saisie(wx.Dialog):
    def __init__(self, parent, nom=None, cp=None, pays=None):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent

        self.label_nom = wx.StaticText(self, -1, u"Nom de la ville :")
        self.ctrl_nom = wx.TextCtrl(self, -1, "", size=(280, -1))
        if nom != None :
            self.ctrl_nom.SetValue(nom)

        self.label_cp = wx.StaticText(self, -1, u"Code postal :")
        self.ctrl_cp = wx.TextCtrl(self, -1, "", size=(80, -1))
        if cp !=None :
            self.ctrl_cp.SetValue(cp)

        self.label_pays = wx.StaticText(self, -1, u"Pays étranger :")
        self.ctrl_pays = wx.TextCtrl(self, -1, "", size=(80, -1))
        if pays !=None :
            self.ctrl_pays.SetValue(pays)

        self.btnPays = wx.Button(self, -1, "...", size=(20, 20))
        self.btnPays.SetToolTip("Gestion des pays")
        self.btnPays.Bind(wx.EVT_BUTTON, self.OnChoixPays)


        self.bouton_ok = CTRL_Bouton_image(self, texte=u"Ok", cheminImage="xpy/Images/32x32/Valider.png")
        self.bouton_annuler = CTRL_Bouton_image(self, id=wx.ID_CANCEL, texte=u"Annuler", cheminImage="xpy/Images/32x32/Annuler.png")

        if nom == None :
            self.SetTitle(u"Saisie d'une ville")
        else:
            self.SetTitle(u"Modification d'une ville")
        self.SetMinSize((350, -1))

        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        grid_sizer_contenu = wx.FlexGridSizer(rows=3, cols=2, vgap=10, hgap=10)
        grid_sizer_contenu.Add(self.label_nom, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_contenu.Add(self.ctrl_nom, 0, wx.EXPAND, 0)
        grid_sizer_contenu.Add(self.label_cp, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_contenu.Add(self.ctrl_cp, 0, 0, 0)
        grid_sizer_contenu.Add(self.label_pays, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_pays = wx.FlexGridSizer(rows=1, cols=2, vgap=0, hgap=0)
        grid_sizer_pays.Add(self.btnPays, 0, 0, 0)
        grid_sizer_pays.Add(self.ctrl_pays, 0, 0, 0)
        grid_sizer_contenu.Add(grid_sizer_pays, 0, 0, 0)
        grid_sizer_contenu.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_contenu, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(0)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)

    def GetNom(self):
        return self.ctrl_nom.GetValue().upper()

    def GetCp(self):
        return self.ctrl_cp.GetValue().upper()

    def GetPays(self):
        return self.ctrl_pays.GetValue().upper()

    def OnChoixPays(self,event):
        dlg = DLG_Pays.Dialog(self)
        if dlg.ShowModal() == wx.OK:
            pays = dlg.saisie_pays
            self.ctrl_pays.SetValue(pays)
        dlg.Destroy()
        event.Skip()

    def OnBoutonOk(self, event):
        nom = self.ctrl_nom.GetValue()
        cp = self.ctrl_cp.GetValue()
        pays = self.ctrl_pays.GetValue()
        if nom == "" :
            dlg = wx.MessageDialog(self, u"Vous n'avez saisi aucun nom de ville !", u"Erreur de saisie", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_nom.SetFocus()
            return
        if cp == "" :
            dlg = wx.MessageDialog(self, u"Vous n'avez saisi aucun code postal !", u"Erreur de saisie", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_cp.SetFocus()
            return
        if pays:
            if len(pays)>0:
                getPays = usa.GetOnePays(pays)
                self.ctrl_pays.SetValue(getPays)
                self.ctrl_pays.SetFocus()
        self.EndModal(wx.OK)

# -----------------------------------------------------------------------------------------------------------------------------------------

class Track(object):
    def __init__(self, donnees):
        self.IDville = donnees[0]
        self.nom = donnees[1]
        self.cp = donnees[2]
        self.pays = donnees[3]
        self.mode = donnees[4]


class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        # Récupération des paramètres perso
        self.selectionID = None
        self.selectionTrack = None
        self.criteres = ""
        self.itemSelected = False
        self.popupIndex = -1
        self.listeFiltres = []
        # Initialisation du listCtrl
        FastObjectListView.__init__(self, *args, **kwds)
        # Binds perso
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)

    def OnItemActivated(self,event):
        #self.Modifier(None)
        self.GetParent().OnBoutonChoisir(None)
                
    def InitModel(self,**kwd):
        self.donnees = self.GetTracks()

    def GetTracks(self):
        """ Récupération des données """
        # Critères
        listeID = None
        self.criteres = ""
        # Liste de filtres
        if len(self.listeFiltres) > 0 :
            listeID, criteres = self.GetListeFiltres(self.listeFiltres)
            if criteres != "" :
                if self.criteres == "" :
                    self.criteres = "WHERE " + criteres
                else:
                    self.criteres += " AND " + criteres
        
        # Importation des villes par défaut
        DB = xdb.DB(nomFichier="srcNoelite/Data/Geographie.dat")
        req = """SELECT IDville, nom, cp, NULL
        FROM villes %s
        ORDER BY nom; """ % self.criteres
        DB.ExecuterReq(req)
        lstDonnees = DB.ResultatReq()
        DB.Close()
        # Importation des corrections de villes et codes postaux
        DB = xdb.DB()
        req = """SELECT IDcorrection, mode, IDville, nom, cp, pays
        FROM corrections_villes; """ 
        DB.ExecuterReq(req)
        listeCorrections = DB.ResultatReq()
        DB.Close()
        
        # Ajout des corrections
        dictCorrections = {}
        for IDcorrection, mode, IDville, nom, cp, pays in listeCorrections :
            dictCorrections[IDville] = {"mode":mode, "nom":nom, "cp":cp, "pays":pays,  "IDcorrection":IDcorrection}
            if mode == "ajout" :
                lstDonnees.append((100000+IDcorrection, nom, cp, pays))

        listeListeView = []
        for IDville, nom, cp, pays in lstDonnees :
            mode = None
            if not pays: pays = ""
            if len(cp) < 5 and len(pays) == 0:
                cp = (u"00000" + cp)[-5:]
            # Filtre de sélection
            valide = True
            if listeID != None :
                if IDville not in listeID :
                    valide = False
            
            # Traitement des corrections
            if IDville in dictCorrections :
                mode = dictCorrections[IDville]["mode"]
                if mode == "modif" :
                    nom = dictCorrections[IDville]["nom"]
                    cp = dictCorrections[IDville]["cp"]
                    pays = dictCorrections[IDville]["pays"]
                    IDville = 100000 + dictCorrections[IDville]["IDcorrection"]
                if mode == "suppr" :
                    valide = False
            
            if IDville > 100000 and mode == None :
                mode = "ajout"
            
            # Création des tracks
            if valide == True :
                track = Track((IDville, nom, cp, pays, mode))
                listeListeView.append(track)
                if self.selectionID == IDville :
                    self.selectionTrack = track
        return listeListeView
      
    def InitObjectListView(self):            
        # Couleur en alternance des lignes
        self.oddRowsBackColor = "#F0FBED" 
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True
                
        liste_Colonnes = [
            ColumnDefn(u"", "left", 0, "IDville"),
            ColumnDefn(u"Nom de la ville", 'left', 250, "nom"),
            ColumnDefn("Code postal", "left", 120, "cp"),
            ColumnDefn("Pays étranger", "left", 120, "pays"),
            ]
        
        self.SetColumns(liste_Colonnes)
        self.SetEmptyListMsg(u"Aucune ville")
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT))
        self.SetSortColumn(self.columns[1])
        self.SetObjects(self.donnees)
       
    def MAJ(self, IDville=None):
        if IDville != None :
            self.selectionID = IDville
            self.selectionTrack = None
        else:
            self.selectionID = None
            self.selectionTrack = None
        self.InitModel()
        self.InitObjectListView()
        # Sélection d'un item
        if self.selectionTrack != None :
            self.SelectObject(self.selectionTrack, deselectOthers=True, ensureVisible=True)
        self.selectionID = None
        self.selectionTrack = None
    
    def Selection(self):
        return self.GetSelectedObjects()

    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """
        if len(self.Selection()) == 0:
            noSelection = True
        else:
            noSelection = False
                
        # Création du menu contextuel
        menuPop = wx.Menu()

        # Item Ajouter
        item = wx.MenuItem(menuPop, 10, u"Ajouter")
        bmp = wx.Bitmap("xpy/Images/16x16/Ajouter.png", wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Ajouter, id=10)

        # Item Modifier
        item = wx.MenuItem(menuPop, 20, u"Modifier")
        bmp = wx.Bitmap("xpy/Images/16x16/Modifier.png", wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Modifier, id=20)
        if noSelection == True : item.Enable(False)
        
        # Item Supprimer
        item = wx.MenuItem(menuPop, 30, u"Supprimer")
        bmp = wx.Bitmap("xpy/Images/16x16/Supprimer.png", wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Supprimer, id=30)
        if noSelection == True : item.Enable(False)

        # Item Choisir
        item = wx.MenuItem(menuPop, 40, u"Choisir")
        bmp = wx.Bitmap("xpy/Images/16x16/Ok.png", wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Choisir, id=40)
        if noSelection == True : item.Enable(False)

        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Ajouter(self, event):
        """ Ajouter une ville """
        if nuu.VerificationDroitsUtilisateurActuel("parametrage_villes", "creer") == False : return
        # Demande le nom et le code postal
        dlg = DLG_Saisie(self)
        if dlg.ShowModal() == wx.OK:
            nom = dlg.GetNom()
            cp = dlg.GetCp()
            pays = dlg.GetPays()
            DB = xdb.DB()
            ret = DB.ReqInsert("corrections_villes", lstDonnees=[("mode", "ajout"), ("nom", nom), ("cp", cp), ("pays", pays)],
                               mess="OL_Villes.Ajouter",)
            IDcorrection = DB.newID
            DB.Close()
            if ret == 'ok':
                self.MAJ(100000+IDcorrection)
        dlg.Destroy()

    def Modifier(self, event):
        if nuu.VerificationDroitsUtilisateurActuel("parametrage_villes", "modifier") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, u"Vous n'avez sélectionné aucune ville à modifier dans la liste !", u"Erreur de saisie", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        IDville = self.Selection()[0].IDville
        nom = self.Selection()[0].nom
        cp = self.Selection()[0].cp
        pays = self.Selection()[0].pays
        mode = self.Selection()[0].mode
        
        dlg = DLG_Saisie(self, nom, cp, pays)
        if dlg.ShowModal() == wx.OK:
            nom = dlg.GetNom()
            cp = dlg.GetCp()
            pays = dlg.GetPays()
            DB = xdb.DB()
            # Si c'est une ville par défaut prise dans geographie.dat
            if IDville < 100000 :
                ret = DB.ReqInsert("corrections_villes", lstDonnees=[("mode", "modif"), ("IDville", IDville),("nom", nom), ("cp", cp), ("pays", pays)],
                               mess="OL_Villes.Modif",)
                IDcorrection = DB.newID
                DB.Close()
                if ret == 'ok':
                    self.MAJ(100000+IDcorrection)
            else :
                # Si c'est un ajout dans correctif qu'on vient de modifier
                IDcorrection = IDville-100000
                DB.ReqMAJ("corrections_villes", [("nom", nom), ("cp", cp), ("pays", pays)], "IDcorrection", IDcorrection)
                self.MAJ(IDville)
            DB.Close()
        dlg.Destroy()

    def Supprimer(self, event):
        if nuu.VerificationDroitsUtilisateurActuel("parametrage_villes", "supprimer") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, u"Vous n'avez sélectionné aucune ville à supprimer dans la liste !", u"Erreur de saisie", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        IDville = self.Selection()[0].IDville
        nom = self.Selection()[0].nom
        cp = self.Selection()[0].cp
        pays = self.Selection()[0].pays
        mode = self.Selection()[0].mode
        
        dlg = wx.MessageDialog(self, "Souhaitez-vous vraiment supprimer la ville '%s (%s)' ?" % (nom, cp), u"Suppression", wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
        ret = dlg.ShowModal()
        if  ret == wx.ID_YES :
            DB = xdb.DB()
            # Si c'est une ville par défaut
            if IDville < 100000 :
                IDcorrection = DB.ReqInsert("corrections_villes", lstDonnees=[("mode", "suppr"), ("IDville", IDville)])
            else :
                # Si la ville est un ajout ou une modif
                IDcorrection = IDville-100000
                if mode == "ajout" :
                    ret = DB.ReqDEL("corrections_villes", "IDcorrection", IDcorrection, mess="OL_Villes.ListView.Supprimer")
                if mode == "modif" :
                    lstDonnees = [("mode", "suppr"), ("nom", None), ("cp", None), ("pays", None)]
                    DB.ReqMAJ("corrections_villes", lstDonnees, "IDcorrection", IDcorrection)
                    
            DB.Close()
            self.MAJ()
        dlg.Destroy()

    def Choisir(self,event):
        event.Skip()
        self.GetParent().OnBoutonChoisir(None)
# -------------------------------------------------------------------------------------------------------------------------------------------

class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.rechercheEnCours = False
        
        self.SetDescriptiveText(u"Rechercher une ville ou un code postal...")
        self.ShowSearchButton(True)
        
        self.listView = self.parent.ctrl_villes
        nbreColonnes = self.listView.GetColumnCount()
        self.listView.SetFilter(Filter.TextSearch(self.listView, self.listView.columns[1:nbreColonnes]))
        
        self.SetCancelBitmap(wx.Bitmap("xpy/Images/16x16/Interdit.png", wx.BITMAP_TYPE_PNG))
        self.SetSearchBitmap(wx.Bitmap("xpy/Images/16x16/Loupe.png", wx.BITMAP_TYPE_PNG))
        
        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnSearch)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnDoSearch)
        #self.Bind(wx.EVT_TEXT, self.OnDoSearch)

    def OnSearch(self, evt):
        self.Recherche()
            
    def OnCancel(self, evt):
        self.SetValue("")
        self.Recherche()

    def OnDoSearch(self, evt):
        if self.rechercheEnCours == False :
            wx.CallLater(1000, self.Recherche)
            self.rechercheEnCours = True
        
    def Recherche(self):
        txtSearch = self.GetValue()
        self.ShowCancelButton(len(txtSearch))
        self.listView.GetFilter().SetText(txtSearch)
        self.listView.RepopulateList()
        self.Refresh() 
        self.rechercheEnCours = False

# -------------------------------------------------------------------------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="test1")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.myOlv = ListView(panel, id=-1, name="OL_test", style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
        self.myOlv.MAJ() 
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.myOlv, 1, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()

if __name__ == '__main__':
    app = wx.App(0)
    import os
    os.chdir("..")
    frame_1 = MyFrame(None, -1, "OL TEST")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
