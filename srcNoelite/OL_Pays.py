#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import wx
import xpy.xUTILS_DB                   as xdb
import srcNoelite.UTILS_Utilisateurs    as nuu
from xpy.outils.ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils



class Track(object):
    def __init__(self, donnees):
        self.IDsecteur = donnees[0]
        self.nom = donnees[1]
        self.nbreTitulaires = donnees[2]
    
    
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
        event.Skip()
        self.GetParent().OnBoutonChoisir(None)

    def InitModel(self,**kwd):
        self.donnees = self.GetTracks()

    def GetTracks(self):
        """ Récupération des données """
        listeID = None
        db = xdb.DB()
        req = """SELECT secteurs.IDsecteur, secteurs.nom, Count(individus.IDindividu) AS nbreTitulaires
        FROM secteurs
        LEFT JOIN individus ON secteurs.IDsecteur = individus.IDsecteur
        GROUP BY secteurs.IDsecteur;"""
        db.ExecuterReq(req)
        lstDonnees = db.ResultatReq()
        db.Close()

        listeListeView = []
        for item in lstDonnees :
            valide = True
            if listeID != None :
                if item[0] not in listeID :
                    valide = False
            if valide == True :
                track = Track(item)
                listeListeView.append(track)
                if self.selectionID == item[0] :
                    self.selectionTrack = track
        return listeListeView
            
    def InitObjectListView(self):            
        # Couleur en alternance des lignes
        self.oddRowsBackColor = "#F0FBED" 
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True
                    
        liste_Colonnes = [
            ColumnDefn("ID", "left", 0, "IDsecteur"),
            ColumnDefn("Nom", "left", 200, "nom"),
            ColumnDefn("Nbre titulaires", "left", 100, "nbreTitulaires"),
            ]
        
        self.SetColumns(liste_Colonnes)
        self.SetEmptyListMsg("Aucun secteur géographique")
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT))
        self.SetSortColumn(self.columns[1])
        self.SetObjects(self.donnees)
       
    def MAJ(self, ID=None):
        if ID != None :
            self.selectionID = ID
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
            ID = self.Selection()[0].IDsecteur
                
        # Création du menu contextuel
        menuPop = wx.Menu()

        # Item Modifier
        item = wx.MenuItem(menuPop, 10, "Ajouter")
        bmp = wx.Bitmap("xpy/Images/16x16/Ajouter.png", wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Ajouter, id=10)
        
        menuPop.AppendSeparator()

        # Item Ajouter
        item = wx.MenuItem(menuPop, 20, "Modifier")
        bmp = wx.Bitmap("xpy/Images/16x16/Modifier.png", wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Modifier, id=20)
        if noSelection == True : item.Enable(False)
        
        # Item Supprimer
        item = wx.MenuItem(menuPop, 30, "Supprimer")
        bmp = wx.Bitmap("xpy/Images/16x16/Supprimer.png", wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Supprimer, id=30)
        if noSelection == True : item.Enable(False)
                
        menuPop.AppendSeparator()
    
        # Item Apercu avant impression
        item = wx.MenuItem(menuPop, 40, "Aperçu avant impression")
        bmp = wx.Bitmap("xpy/Images/16x16/Apercu.png", wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Apercu, id=40)
        
        # Item Imprimer
        item = wx.MenuItem(menuPop, 50, "Imprimer")
        bmp = wx.Bitmap("xpy/Images/16x16/Imprimante.png", wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Imprimer, id=50)
        
       # Item Choisir
        item = wx.MenuItem(menuPop, 60, "Choisir")
        bmp = wx.Bitmap("xpy/Images/16x16/Ok.png", wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Choisir, id=60)
        if noSelection == True : item.Enable(False)

        self.PopupMenu(menuPop)
        menuPop.Destroy()


    def Apercu(self, event):
        import xpy.outils.ObjectListView.Printer as xprt
        prt = xprt.ObjectListViewPrinter(self, titre="Liste des pays postaux", format="A", orientation=wx.PORTRAIT)
        prt.Preview()

    def Imprimer(self, event):
        import xpy.outils.ObjectListView.Printer as xprt
        prt = xprt.ObjectListViewPrinter(self, titre="Liste des pays postaux", format="A", orientation=wx.PORTRAIT)
        prt.Print()

    def Ajouter(self, event):
        if nuu.VerificationDroitsUtilisateurActuel("parametrage_secteurs", "creer") == False : return
        dlg = wx.TextEntryDialog(self, "Saisissez le nom du nouveau secteur géographique :", "Saisie d'un nouveau secteur", u"")
        if dlg.ShowModal() == wx.ID_OK:
            nom = dlg.GetValue()
            if nom == "":
                dlg = wx.MessageDialog(self, "Le nom que vous avez saisi n'est pas valide.", "Erreur de saisie", wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                return
            else:
                DB = xdb.DB()
                IDsecteur = DB.ReqInsert("secteurs", lstDonnees=[ ("nom", nom ), ])
                DB.Close()
                self.MAJ(IDsecteur)
        dlg.Destroy()

    def Modifier(self, event):
        if nuu.VerificationDroitsUtilisateurActuel("parametrage_secteurs", "modifier") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, "Vous n'avez sélectionné aucun secteur à modifier dans la liste", "Erreur de saisie", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        IDsecteur = self.Selection()[0].IDsecteur
        nom = self.Selection()[0].nom
        dlg = wx.TextEntryDialog(self, "Modifiez le nom du secteur géographique :", "Modification d'un secteur", nom)
        if dlg.ShowModal() == wx.ID_OK:
            nom = dlg.GetValue()
            if nom == "":
                dlg = wx.MessageDialog(self, "Le nom que vous avez saisi n'est pas valide.", "Erreur de saisie", wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                return
            else:
                DB = xdb.DB()
                lstDonnees = [ ("nom", nom ), ]
                DB.ReqMAJ("secteurs", lstDonnees, "IDsecteur", IDsecteur)
                DB.Close()
                self.MAJ(IDsecteur)
        dlg.Destroy()

    def Supprimer(self, event):
        if nuu.VerificationDroitsUtilisateurActuel("parametrage_secteurs", "supprimer") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, "Vous n'avez sélectionné aucun secteur à supprimer dans la liste", "Erreur de saisie", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        if self.Selection()[0].nbreTitulaires > 0 :
            dlg = wx.MessageDialog(self, "Il est impossible de supprimer un secteur déjà assigné à un ou plusieurs individus !", "Suppression impossible", wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        dlg = wx.MessageDialog(self, "Souhaitez-vous vraiment supprimer ce secteur ?", "Suppression", wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
        if dlg.ShowModal() == wx.ID_YES :
            IDsecteur = self.Selection()[0].IDsecteur
            DB = xdb.DB()
            DB.ReqDEL("secteurs", "IDsecteur", IDsecteur)
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
        
        self.SetDescriptiveText("Rechercher un secteur géographique...")
        self.ShowSearchButton(True)
        
        self.listView = self.parent.ctrl_listview
        nbreColonnes = self.listView.GetColumnCount()
        self.listView.SetFilter(Filter.TextSearch(self.listView, self.listView.columns[0:nbreColonnes]))
        
        self.SetCancelBitmap(wx.Bitmap("xpy/Images/16x16/Interdit.png", wx.BITMAP_TYPE_PNG))
        self.SetSearchBitmap(wx.Bitmap("xpy/Images/16x16/Loupe.png", wx.BITMAP_TYPE_PNG))
        
        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnSearch)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnDoSearch)
        self.Bind(wx.EVT_TEXT, self.OnDoSearch)

    def OnSearch(self, evt):
        self.Recherche()
            
    def OnCancel(self, evt):
        self.SetValue("")
        self.Recherche()

    def OnDoSearch(self, evt):
        self.Recherche()
        
    def Recherche(self):
        txtSearch = self.GetValue()
        self.ShowCancelButton(len(txtSearch))
        self.listView.GetFilter().SetText(txtSearch)
        self.listView.RepopulateList()
        self.Refresh() 


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
