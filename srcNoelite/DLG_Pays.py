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
import xpy.outils.xbandeau      as xbd
import srcNoelite.OL_Pays   as OL_Pays

class CTRL_Bouton_image(wx.Button):
    def __init__(self, parent, id=wx.ID_APPLY, texte="", cheminImage=None):
        wx.Button.__init__(self, parent, id=id, label=texte)
        if cheminImage:
            self.SetBitmap(wx.Bitmap(cheminImage))
        self.SetFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.SetInitialSize()

class Dialog(wx.Dialog):
    def __init__(self, parent,modeImportation=False):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        self.saisie_pays = ""
        intro = "Vous pouvez ici saisir, modifier ou supprimer des pays utilisés dans les adresses"
        titre = "Gestion des pays postaux"
        self.ctrl_bandeau = xbd.Bandeau(self, titre=titre, texte=intro, hauteur=15, nomImage="xpy/Images/32x32/Secteur.png")
        self.ctrlOlv = OL_Pays.ListView(self, id=-1, style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
        self.ctrlOlv.MAJ()
        self.ctrl_recherche = OL_Pays.CTRL_Outils(self, listview=self.ctrlOlv)
        
        self.bouton_ajouter = wx.BitmapButton(self, -1, wx.Bitmap("xpy/Images/16x16/Ajouter.png", wx.BITMAP_TYPE_ANY))
        self.bouton_modifier = wx.BitmapButton(self, -1, wx.Bitmap("xpy/Images/16x16/Modifier.png", wx.BITMAP_TYPE_ANY))
        self.bouton_supprimer = wx.BitmapButton(self, -1, wx.Bitmap("xpy/Images/16x16/Supprimer.png", wx.BITMAP_TYPE_ANY))
        self.bouton_importer = CTRL_Bouton_image(self, texte="Choisir le pays", cheminImage="xpy/Images/32x32/Fleche_bas.png")
        self.bouton_fermer = CTRL_Bouton_image(self, id=wx.ID_CANCEL, texte="Fermer", cheminImage="xpy/Images/32x32/Annuler.png")

        if modeImportation == False:
            self.bouton_importer.Show(False)
            self.bouton_fermer = CTRL_Bouton_image(self, id=wx.ID_CANCEL, texte="Fermer", cheminImage="xpy/Images/32x32/Valider.png")

        self.__set_properties()
        self.__do_layout()
        
        self.Bind(wx.EVT_BUTTON, self.Ajouter, self.bouton_ajouter)
        self.Bind(wx.EVT_BUTTON, self.Modifier, self.bouton_modifier)
        self.Bind(wx.EVT_BUTTON, self.Supprimer, self.bouton_supprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonChoisir, self.bouton_importer)

    def __set_properties(self):
        self.SetTitle("DLG_Secteurs")
        self.bouton_ajouter.SetToolTip("Cliquez ici pour ajouter un secteur géographique")
        self.bouton_modifier.SetToolTip("Cliquez ici pour modifier le secteur géographique dans la liste")
        self.bouton_supprimer.SetToolTip("Cliquez ici pour supprimer le secteur géographique sélectionné dans la liste")
        self.bouton_fermer.SetToolTip("Cliquez ici pour abandonner")
        self.bouton_importer.SetToolTip("Cliquez ici pour importer le pays sélectionné dans la liste")
        self.SetMinSize((200, 500))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        grid_sizer_contenu = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_droit = wx.FlexGridSizer(rows=4, cols=1, vgap=5, hgap=5)
        grid_sizer_gauche = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)
        grid_sizer_gauche.Add(self.ctrlOlv, 0, wx.EXPAND, 0)
        grid_sizer_gauche.Add(self.ctrl_recherche, 0, wx.EXPAND, 0)
        grid_sizer_gauche.AddGrowableRow(0)
        grid_sizer_gauche.AddGrowableCol(0)
        grid_sizer_contenu.Add(grid_sizer_gauche, 1, wx.EXPAND, 0)
        grid_sizer_droit.Add(self.bouton_ajouter, 0, 0, 0)
        grid_sizer_droit.Add(self.bouton_modifier, 0, 0, 0)
        grid_sizer_droit.Add(self.bouton_supprimer, 0, 0, 0)
        grid_sizer_contenu.Add(grid_sizer_droit, 1, wx.EXPAND, 0)
        grid_sizer_contenu.AddGrowableRow(0)
        grid_sizer_contenu.AddGrowableCol(0)
        grid_sizer_base.Add(grid_sizer_contenu, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        grid_sizer_boutons.Add((20,20), 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_fermer, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_importer, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen()

    def Ajouter(self, event):
        self.ctrlOlv.Ajouter(None)
        
    def Modifier(self, event):
        self.ctrlOlv.Modifier(None)

    def Supprimer(self, event):
        self.ctrlOlv.Supprimer(None)

    def OnBoutonChoisir(self, event):
        selection= self.ctrlOlv.Selection()
        if len(selection) == 0:
            dlg = wx.MessageDialog(self, "Vous n'avez effectué aucune sélection dans la liste !",
                                   "Erreur de saisie", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        self.saisie_pays = selection[0].nom
        self.EndModal(wx.OK)


if __name__ == "__main__":
    app = wx.App(0)
    import os
    os.chdir("..")
    dialog_1 = Dialog(None)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()
