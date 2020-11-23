#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------
# Application :    xpy, outils pythons

# Auteur:           Jacques BRUNEL
# Licence:         Licence GNU GPL
# ------------------------------------------------------------------------

import wx
import wx.lib.agw.hyperlink as hl
from wx.lib.mixins.listctrl import CheckListCtrlMixin
import six
from xpy.outils import xos

from xpy.outils import xctrlbi


class DLG_selection(wx.Dialog):
    def __init__(self, parent,lstColonnes=[],lstValeurs=[],title="Elément à choisir",minsize=(800, 460),check=False):
        wx.Dialog.__init__(self, parent, -1, title=title,size=minsize,style=wx.RESIZE_BORDER)
        self.parent = parent
        self.check = check
        self.minsize = minsize
        # Adapte taille Police pour Linux
        if xos.islinux():
            from xpy.outils import xlinux
            xlinux.AdaptePolice(self)

        self.lstColonnes = lstColonnes
        self.lstValeurs = lstValeurs

        self.label_intro = wx.StaticText(self, -1, title)

        # ListCtrl
        if check:
            self.listCtrl = CheckListCtrl(self, self.lstColonnes, self.lstValeurs)
        else:
            self.listCtrl = ListCtrl(self, self.lstColonnes, self.lstValeurs)

        if check:
            # Hyperlinks
            self.hyperlink_select = self.Build_Hyperlink_select()
            self.label_separation = wx.StaticText(self, -1, u"|")
            self.hyperlink_deselect = self.Build_Hyperlink_deselect()

        self.bouton_ok = xctrlbi.CTRL(self, texte="Ok", cheminImage="xpy/Images/32x32/Valider.png")
        self.bouton_annuler = xctrlbi.CTRL(self, id=wx.ID_CANCEL, texte="Annuler",
                                                     cheminImage="xpy/Images/32x32/Annuler.png")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)

    def __set_properties(self):
        self.bouton_ok.SetToolTip(wx.ToolTip("Cliquez ici pour valider"))
        self.bouton_annuler.SetToolTip(wx.ToolTip("Cliquez ici pour annuler la saisie"))

    def __do_layout(self):
        sizer_base = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_base = wx.FlexGridSizer(rows=7, cols=1, vgap=0, hgap=0)
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        grid_sizer_base.Add(self.label_intro, 1, wx.LEFT | wx.TOP | wx.RIGHT | wx.EXPAND, 10)
        grid_sizer_base.Add(self.listCtrl, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)

        if self.check:
            grid_sizer_commandes = wx.FlexGridSizer(rows=1, cols=4, vgap=2, hgap=2)
            grid_sizer_commandes.Add((20, 20), 0, wx.EXPAND, 0)
            grid_sizer_commandes.Add(self.hyperlink_select, 1, wx.EXPAND, 10)
            grid_sizer_commandes.Add(self.label_separation, 1, wx.EXPAND, 10)
            grid_sizer_commandes.Add(self.hyperlink_deselect, 1, wx.EXPAND, 10)
            grid_sizer_commandes.AddGrowableCol(0)
            grid_sizer_base.Add(grid_sizer_commandes, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.ALIGN_RIGHT, 10)

        grid_sizer_base.Add((10, 10), 1, wx.EXPAND | wx.ALL, 0)

        grid_sizer_boutons.Add((20, 20), 1, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, wx.RIGHT, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0,wx.RIGHT, 0)
        grid_sizer_boutons.AddGrowableCol(0)

        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        self.SetSizer(grid_sizer_base)
        sizer_base.Add(self, 1, wx.EXPAND, 0)
        self.Layout()
        self.CentreOnScreen()

    def Build_Hyperlink_select(self):
        """ Construit un hyperlien """
        self.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL, False))
        hyper = hl.HyperLinkCtrl(self, -1, "Tout sélectionner", URL="")
        hyper.Bind(hl.EVT_HYPERLINK_LEFT, self.OnLeftLink_select)
        hyper.AutoBrowse(False)
        hyper.SetColours("BLACK", "BLACK", "BLUE")
        hyper.EnableRollover(True)
        hyper.SetUnderlines(False, False, True)
        hyper.SetBold(False)
        hyper.SetToolTip(wx.ToolTip("Tout sélectionner"))
        hyper.UpdateLink()
        hyper.DoPopup(False)
        return hyper

    def OnLeftLink_select(self, event):
        """ Sélectionner tout """
        self.listCtrl.MAJListeCtrl(action="select")

    def Build_Hyperlink_deselect(self):
        """ Construit un hyperlien """
        self.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL, False))
        hyper = hl.HyperLinkCtrl(self, -1, "Tout dé-sélectionner", URL="")
        hyper.Bind(hl.EVT_HYPERLINK_LEFT, self.OnLeftLink_deselect)
        hyper.AutoBrowse(False)
        hyper.SetColours("BLACK", "BLACK", "BLUE")
        hyper.EnableRollover(True)
        hyper.SetUnderlines(False, False, True)
        hyper.SetBold(False)
        hyper.SetToolTip(wx.ToolTip("Tout dé-sélectionner"))
        hyper.UpdateLink()
        hyper.DoPopup(False)
        return hyper

    def OnLeftLink_deselect(self, event):
        """ dé-Sélectionner tout """
        self.listCtrl.MAJListeCtrl(action="deselect")

    def OnBoutonOk(self, event):
        """ Validation des données saisies """
        selections = self.GetSelections()

        # Validation de la sélection
        if selections == -1:
            dlg = wx.MessageDialog(self, "Vous n'avez fait aucune sélection", "Erreur de saisie",
                                   wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return

        # Ferme la boîte de dialogue
        self.EndModal(wx.ID_OK)

    def GetSelections(self):
        if self.check:
            return self.listCtrl.ListeItemsCoches()
        else:
            return self.listCtrl.GetFirstSelected()

# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class ListCtrl(wx.ListCtrl):
    def __init__(self, parent, lstColonnes, lstValeurs):
        wx.ListCtrl.__init__(self, parent, -1, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES)
        #ListCtrlAutoWidthMixin.__init__(self)
        self.parent = parent
        self.lstColonnes = lstColonnes
        self.lstValeurs = lstValeurs

        self.Remplissage()
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)

    def Remplissage(self, select=None, action=None):
        # Création des colonnes
        index = 0
        for labelCol, alignement, largeur, code in self.lstColonnes:
            self.InsertColumn(index, labelCol)
            index += 1

        # Remplissage avec les valeurs
        self.remplissage = True
        ID = 0
        for valeurs in self.lstValeurs:
            ID += 1
            if 'phoenix' in wx.PlatformInfo:
                index = self.InsertItem(six.MAXSIZE, str(ID))
            else:
                index = self.InsertStringItem(six.MAXSIZE, str(ID))
            x = 0
            for valeur in valeurs:
                if 'phoenix' in wx.PlatformInfo:
                    self.SetItem(index, x, str(valeur))
                else:
                    self.SetStringItem(index, x, valeur)
                x += 1
            self.SetItemData(index, ID)

        # ajustement des largeurs après remplissage
        index = 0
        for labelCol, alignement, largeur, code in self.lstColonnes:
            if largeur >= 0:
                self.SetColumnWidth(index, largeur)
            else:
                self.SetColumnWidth(index,wx.LIST_AUTOSIZE_USEHEADER)
            index += 1

        self.remplissage = False

    def MAJListeCtrl(self, select=None, action=None):
        self.ClearAll()
        self.Remplissage(select, action)

    def OnItemActivated(self, evt):
        self.ToggleItem(evt.m_itemIndex)

class CheckListCtrl(wx.ListCtrl, CheckListCtrlMixin):
    def __init__(self, parent, lstColonnes, lstValeurs):
        wx.ListCtrl.__init__(self, parent, -1, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES)
        CheckListCtrlMixin.__init__(self)
        self.parent = parent
        self.lstColonnes = lstColonnes
        self.lstValeurs = lstValeurs

        self.Remplissage()
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)

    def Remplissage(self, select=None, action=None):

        # Création des colonnes
        index = 0
        for labelCol, alignement, largeur, code in self.lstColonnes:
            self.InsertColumn(index, labelCol)
            if index == 0 and largeur == 0: largeur = 50
            self.SetColumnWidth(index, largeur)
            index += 1

        # Remplissage avec les valeurs
        self.remplissage = True
        for valeurs in self.lstValeurs:
            if valeurs[0] == "":
                ID = 0
            else:
                ID = int(valeurs[0])
            if 'phoenix' in wx.PlatformInfo:
                index = self.InsertItem(six.MAXSIZE, str(ID))
            else:
                index = self.InsertStringItem(six.MAXSIZE, str(ID))
            x = 1
            for valeur in valeurs[1:]:
                if 'phoenix' in wx.PlatformInfo:
                    self.SetItem(index, x, valeur)
                else:
                    self.SetStringItem(index, x, valeur)
                x += 1

            self.SetItemData(index, ID)

            # Check
            if action == None or action == "select":
                self.CheckItem(index)

        self.remplissage = False

    def MAJListeCtrl(self, select=None, action=None):
        self.ClearAll()
        self.Remplissage(select, action)

    def OnItemActivated(self, evt):
        self.ToggleItem(evt.m_itemIndex)

    def ListeItemsCoches(self):
        """ Récupère la liste des IDdeplacements cochés """
        listeIDcoches = []
        nbreItems = self.GetItemCount()
        for index in range(0, nbreItems):
            ID = int(self.GetItem(index, 0).GetText())
            # Vérifie si l'item est coché
            if self.IsChecked(index):
                listeIDcoches.append(ID)
        return listeIDcoches


if __name__ == "__main__":
    app = wx.App(0)
    import os
    os.chdir("..")
    os.chdir("..")

    # wx.InitAllImageHandlers()
    liste_labelsColonnes = [(u"COL1", "left", 50, "col1"), (u"COL2", "left", -1, "col2"), ]
    lstValeurs = [(1, "ligne1-col2"), (2, " colone deuxième avec une grande longueur de texte pour essai "), ]
    frm = DLG_selection(None, liste_labelsColonnes, lstValeurs,check=False,minsize=(400,300))
    frm.ShowModal()
    app.MainLoop()
