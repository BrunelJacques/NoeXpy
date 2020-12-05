#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-13 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
import os
import sys
import platform
import traceback
import datetime
import wx.lib.dialogs

def Activer_rapport_erreurs(version="", appli=""):
    def my_excepthook(exctype, value, tb):
        dateDuJour = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        systeme = u"%s %s %s %s" % (sys.platform, platform.system(), platform.release(), platform.machine())
        infos = u"## %s | %s | %s ##" % (dateDuJour, version, systeme)
        bug = ''.join(traceback.format_exception(exctype, value, tb))
        
        # Affichage dans le journal
        print(bug)
        
        # Affichage dans une DLG
        try :
            texte = u"%s\n%s" % (infos, bug)
            dlg = DLG_Rapport(None, texte, appli)
            dlg.ShowModal() 
            dlg.Destroy()
        except :
            pass
            
    sys.excepthook = my_excepthook

# ----------------------- BOITE DE DIALOGUE ---------------------------------

class DLG_Rapport(wx.Dialog):
    def __init__(self, parent, texte="", appli = ""):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.SetTitle((u"Rapport d'erreurs %s"%appli))
        self.parent = parent
        self.ctrl_image = wx.StaticBitmap(self, wx.ID_ANY, wx.Bitmap(u"xpy/Images/48x48/Erreur.png", wx.BITMAP_TYPE_ANY))
        self.label_ligne_1 = wx.StaticText(self, wx.ID_ANY, (u"L'application %s a rencontré un problème !"%appli))
        self.label_ligne_2 = wx.StaticText(self, wx.ID_ANY, (u"Le rapport d'erreur ci-dessous est déja 'copié', vous pouvez le 'coller' dans un mail.\nMerci de bien vouloir le communiquer à l'administrateur informatique pour résoudre le bug."))
        self.ctrl_rapport = wx.TextCtrl(self, wx.ID_ANY, texte, style=wx.TE_MULTILINE | wx.TE_READONLY)
        #self.bouton_fermer = wx.BitmapButton(self, -1, wx.Bitmap('xpy/Images/48x48/Quitter.png'))
        self.bouton_fermer = wx.Button(self, -1, "Fermer")
        font = wx.Font(14, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD,False)
        self.bouton_fermer.SetFont(font)
        self.bouton_fermer.SetForegroundColour((0,0,100))
        self.bouton_fermer.SetBitmap( wx.Bitmap('xpy/Images/32x32/Quitter.png'))
        self.bouton_fermer.SetInitialSize()

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonFermer, self.bouton_fermer)
        
        # Envoi dans le presse-papiers
        clipdata = wx.TextDataObject()
        clipdata.SetText(texte)
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(clipdata)
        wx.TheClipboard.Close()
        self.bouton_fermer.SetFocus()

    def __set_properties(self):
        self.label_ligne_1.SetFont(wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.ctrl_rapport.SetToolTip(("Ce rapport d'erreur a été copié dans le presse-papiers"))
        self.bouton_fermer.SetToolTip(("Cliquez ici pour fermer"))
        self.SetMinSize((600, 700))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(3, 1, 10, 10)
        grid_sizer_bas = wx.FlexGridSizer(1, 5, 10, 10)
        grid_sizer_haut = wx.FlexGridSizer(2, 2, 10, 10)
        grid_sizer_droit = wx.FlexGridSizer(2, 1, 10, 10)
        grid_sizer_haut.Add(self.ctrl_image, 0, wx.ALL, 10)
        grid_sizer_droit.Add(self.label_ligne_1, 0, 0, 0)
        grid_sizer_droit.Add(self.label_ligne_2, 0, 0, 0)
        #grid_sizer_droit.AddGrowableRow(2)
        #grid_sizer_droit.AddGrowableCol(0)
        grid_sizer_haut.Add(grid_sizer_droit, 0, wx.RIGHT | wx.TOP , 10)
        grid_sizer_haut.AddGrowableRow(0)
        grid_sizer_haut.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_haut, 0, wx.TOP, 0)
        grid_sizer_base.Add(self.ctrl_rapport, 1, wx.EXPAND, 0)
        grid_sizer_bas.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_bas.Add(self.bouton_fermer, 0, 0, 0)
        grid_sizer_bas.AddGrowableCol(0)
        grid_sizer_base.Add(grid_sizer_bas, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen() 

    def OnBoutonFermer(self, event):  
        self.EndModal(wx.ID_CANCEL)

#************************   Pour Test    *******************************
if __name__ == u"__main__":
    app = wx.App(0)
    os.chdir("..")
    Activer_rapport_erreurs(version='1.0')
    1/0
    app.MainLoop()
