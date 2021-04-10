#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, Jacques Brunel
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
import xpy.outils.xbandeau      as xbd
import srcNoelite.OL_Villes     as olv

class CTRL_Bouton_image(wx.Button):
    def __init__(self, parent, id=-1, texte="", cheminImage=None):
        wx.Button.__init__(self, parent, id=id, label=texte)
        if cheminImage:
            self.SetBitmap(wx.Bitmap(cheminImage))
        self.SetFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.SetInitialSize()

class Dialog(wx.Dialog):
    def __init__(self, parent, modeImportation=False):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.panel_saisie = wx.Panel(self, -1)
        self.SetTitle("DLG_Villes")
        titre = u"Gestion villes et codes postaux"
        if modeImportation == True :
            intro = u"Vous pouvez ici rechercher une ville ou un code postal grâce à la barre de recherche. Cliquez sur 'Choisir' pour importer la ville saisie ou sélectionnée."
        else:
            intro =u"Vous pouvez ici rechercher une ville ou un code postal. La barre de recherche vous permet d'effectuer une recherche sur une partie du nom ou du code postal."
        self.ctrl_bandeau = xbd.Bandeau(self, titre=titre, texte=intro, hauteur=15, nomImage="xpy/Images/32x32/Carte.png")
        self.ctrl_villes = olv.ListView(self, id=-1, style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
        self.ctrl_villes.MAJ()

        self.ctrl_barreRecherche = olv.CTRL_Outils(self, listview=self.ctrl_villes)

        self.staticbox_saisie_staticbox = wx.StaticBox(self.panel_saisie, -1, u"Forcer une ville dans l'Adresse sans sauvegarde en modèle")
        self.label_cp = wx.StaticText(self.panel_saisie, -1, "Code postal :")
        self.ctrl_cp = wx.TextCtrl(self.panel_saisie, -1, "")
        self.label_ville = wx.StaticText(self.panel_saisie, -1, "Ville :")
        self.ctrl_ville = wx.TextCtrl(self.panel_saisie, -1, "")
        self.label_pays = wx.StaticText(self.panel_saisie, -1, "Pays :")
        self.ctrl_pays = wx.TextCtrl(self.panel_saisie, -1, "")

        self.bouton_ajouter = wx.BitmapButton(self, -1, wx.Bitmap("xpy/Images/16x16/Ajouter.png", wx.BITMAP_TYPE_ANY))
        self.bouton_modifier = wx.BitmapButton(self, -1, wx.Bitmap("xpy/Images/16x16/Modifier.png", wx.BITMAP_TYPE_ANY))
        self.bouton_supprimer = wx.BitmapButton(self, -1, wx.Bitmap("xpy/Images/16x16/Supprimer.png", wx.BITMAP_TYPE_ANY))

        self.bouton_importer = CTRL_Bouton_image(self, texte=u"Choisir la ville", cheminImage="xpy/Images/32x32/Fleche_bas.png")
        self.bouton_annuler = CTRL_Bouton_image(self, texte=u"Fermer", cheminImage="xpy/Images/32x32/Annuler.png")
        
        if modeImportation == False :
            self.panel_saisie.Show(False)
            self.bouton_importer.Show(False)
            
        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.Ajouter, self.bouton_ajouter)
        self.Bind(wx.EVT_BUTTON, self.Modifier, self.bouton_modifier)
        self.Bind(wx.EVT_BUTTON, self.Supprimer, self.bouton_supprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonChoisir, self.bouton_importer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)

    def __set_properties(self):
        self.ctrl_cp.SetMinSize((60, -1))
        self.ctrl_cp.SetToolTip(u"Saisissez ici un code postal")
        self.ctrl_ville.SetToolTip(u"Saisissez ici le nom d'une ville")
        self.ctrl_pays.SetToolTip(u"Saisissez ici le nom du pays")
        self.bouton_ajouter.SetToolTip(u"Cliquez ici pour ajouter une ville")
        self.bouton_modifier.SetToolTip(u"Cliquez ici pour modifier la ville sélectionnée dans la liste")
        self.bouton_supprimer.SetToolTip(u"Cliquez ici pour supprimer la ville sélectionnée dans la liste")
        self.bouton_importer.SetToolTip(u"Cliquez ici pour importer la ville saisie manuellement ou sélectionnée dans la liste")
        self.bouton_annuler.SetToolTip(u"Cliquez ici pour abandonner")
        self.SetMinSize((480, 600))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)
        
        grid_sizer_saisie = wx.GridSizer(rows=1, cols=1, vgap=0, hgap=0)
        staticbox_saisie = wx.StaticBoxSizer(self.staticbox_saisie_staticbox, wx.VERTICAL)
        
        grid_sizer_recherche = wx.FlexGridSizer(rows=2, cols=2, vgap=5, hgap=5)
        grid_sizer_recherche.Add(self.ctrl_villes, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, 0)
        
        grid_sizer_droit = wx.FlexGridSizer(rows=5, cols=1, vgap=5, hgap=5)
        grid_sizer_droit.Add(self.bouton_ajouter, 0, 0, 0)
        grid_sizer_droit.Add(self.bouton_modifier, 0, 0, 0)
        grid_sizer_droit.Add(self.bouton_supprimer, 0, 0, 0)
        grid_sizer_recherche.Add(grid_sizer_droit, 1, wx.EXPAND, 0)
        
        
        grid_sizer_recherche.Add(self.ctrl_barreRecherche, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 0)
        grid_sizer_recherche.AddGrowableRow(0)
        grid_sizer_recherche.AddGrowableCol(0)
        
        grid_sizer_base.Add(grid_sizer_recherche, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        
        grid_sizer_saisie_2 = wx.FlexGridSizer(rows=1, cols=6, vgap=5, hgap=5)
        grid_sizer_saisie_2.Add(self.label_cp, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_saisie_2.Add(self.ctrl_cp, 0, 0, 0)
        grid_sizer_saisie_2.Add(self.label_ville, 0, wx.LEFT|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
        grid_sizer_saisie_2.Add(self.ctrl_ville, 0, wx.EXPAND, 0)
        grid_sizer_saisie_2.Add(self.label_pays, 0, wx.LEFT|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
        grid_sizer_saisie_2.Add(self.ctrl_pays, 0, wx.EXPAND, 0)
        grid_sizer_saisie_2.AddGrowableRow(0)
        grid_sizer_saisie_2.AddGrowableCol(3)
        staticbox_saisie.Add(grid_sizer_saisie_2, 1, wx.ALL|wx.EXPAND, 5)
        
        grid_sizer_saisie.Add(staticbox_saisie, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        
        self.panel_saisie.SetSizer(grid_sizer_saisie)
        grid_sizer_base.Add(self.panel_saisie, 1, wx.EXPAND, 0)
        
        # Boutons
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=3, vgap=10, hgap=10)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_importer, 0, 0, 0)
        grid_sizer_boutons.AddGrowableRow(0)
        grid_sizer_boutons.AddGrowableCol(0)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.ALL|wx.EXPAND, 10)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CentreOnScreen()

    def Ajouter(self, event):
        self.ctrl_villes.Ajouter(None)
        
    def Modifier(self, event):
        self.ctrl_villes.Modifier(None)

    def Supprimer(self, event):
        self.ctrl_villes.Supprimer(None)

    def GetVille(self):
        saisie_cp = self.ctrl_cp.GetValue().upper()
        saisie_ville = self.ctrl_ville.GetValue().upper()
        saisie_pays = self.ctrl_pays.GetValue().upper()
        if saisie_ville != "" and saisie_cp != "" :
            return saisie_cp, saisie_ville, saisie_pays
        return self.ctrl_villes.Selection()[0].cp, self.ctrl_villes.Selection()[0].nom,\
               self.ctrl_villes.Selection()[0].pays

    def OnBoutonChoisir(self, event):
        selectionListe = self.ctrl_villes.Selection()
        if not event:
            # renvoyé par le double clic dans l'OLV, priorité à la selection
            self.EndModal(wx.OK)
        saisie_cp = self.ctrl_cp.GetValue()
        saisie_ville = self.ctrl_ville.GetValue()
        if saisie_ville == "" and saisie_cp == "" and len(selectionListe) == 0 :
            dlg = wx.MessageDialog(self, u"Vous n'avez effectué aucune saisie manuelle ou sélection dans la liste !", u"Erreur de saisie", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        if saisie_ville != "" and saisie_cp == "":
            dlg = wx.MessageDialog(self, u"Vous avez saisi le nom d'une ville sans saisir le code postal !", u"Erreur de saisie", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        if saisie_ville == "" and saisie_cp != "":
            dlg = wx.MessageDialog(self, u"Vous avez saisi le code postal sans saisir le nom de la ville !", u"Erreur de saisie", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        self.EndModal(wx.OK)

    def OnBoutonAnnuler(self, event): 
        self.EndModal(wx.ID_CANCEL)   


if __name__ == "__main__":
    app = wx.App(0)
    import os
    os.chdir("..")
    dialog_1 = Dialog(None, modeImportation=True)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()
