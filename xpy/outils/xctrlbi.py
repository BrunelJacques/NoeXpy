#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
# ------------------------------------------------------------------------
# Application :     Noethys, gestion multi-activités
# Site internet :   www.noethys.com
# Auteur :          Ivan LUCAS
# Copyright :       (c) 2010-15 Ivan LUCAS
# Licence :         Licence GNU GPL
# Fichier :         xctrlbi (X Control Bouton Image)
# ------------------------------------------------------------------------

import wx
import time

import PIL.Image as Image
import PIL.ImageOps as ImageOps

def PILtoWx(image):
    """Convert a PIL image to wx image format"""
    largeur, hauteur = image.size
    imagewx = wx.Image(largeur, hauteur)
    imagewx.SetData(image.tobytes('raw', 'RGB'))
    imagewx.SetAlpha(image.convert("RGBA").tobytes()[3::4])
    return imagewx

class CTRL(wx.Button):
    def __init__(self, parent, id=-1, texte="", cheminImage=None, tailleImage=(20, 20), margesImage=(4, 0, 0, 0),
                 positionImage=wx.LEFT, margesTexte=(0, 1)):
        wx.Button.__init__(self, parent, id=id, label=texte)
        self.parent = parent
        self.texte = texte
        self.cheminImage = cheminImage
        self.tailleImage = tailleImage
        self.margesImage = margesImage
        self.positionImage = positionImage
        self.margesTexte = margesTexte
        self.MAJ()

    def MAJ(self):
        # Redimensionne et ajoute des marges autour de l'image
        if self.cheminImage not in ("", None):
            img = Image.open(self.cheminImage)
            img = img.resize(self.tailleImage, Image.ANTIALIAS)
            img = ImageOps.expand(img, border=self.margesImage)
            img = PILtoWx(img)
            bmp = img.ConvertToBitmap()
        else:
            bmp = wx.NullBitmap

        # MAJ du bouton
        self.SetBitmap(bmp, self.positionImage)
        if self.cheminImage not in ("", None):
            self.SetBitmapMargins(self.margesTexte)
        self.SetFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.SetInitialSize()

    def SetImage(self, cheminImage=""):
        self.SetBitmap(wx.NullBitmap)
        self.cheminImage = cheminImage
        self.MAJ()

    def SetTexte(self, texte=""):
        self.texte = texte
        self.SetLabel(texte)
        self.MAJ()

    def SetImageEtTexte(self, cheminImage="", texte=""):
        self.SetBitmap(wx.NullBitmap)
        self.cheminImage = cheminImage
        self.texte = texte
        self.SetLabel(texte)
        self.MAJ()

    # -------------------------------------------- DLG de test -----------------------------------------------------

class Dialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1,
                           style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX)#| wx.THICK_FRAME)
        self.parent = parent
        t1 = time.time()

        self.label_test = wx.StaticText(self, wx.ID_ANY, "Test :")
        self.ctrl_test = wx.TextCtrl(self, wx.ID_ANY, "", style=wx.TE_MULTILINE)

        self.bouton_aide1 = CTRL(self, texte="Transmettre\npar Email", tailleImage=(32, 32), margesImage=(4, 4, 0, 0),
                                 margesTexte=(0, 1), cheminImage="xpy/Images/32x32/Emails_exp.png")
        self.bouton_aide2 = wx.BitmapButton(self, wx.ID_ANY,
                                            wx.Bitmap("xpy/Images/32x32/Aide.png", wx.BITMAP_TYPE_ANY))
        self.bouton_ok1 = CTRL(self, texte="Ok", cheminImage="xpy/Images/32x32/Valider.png")
        self.bouton_ok2 = wx.BitmapButton(self, wx.ID_ANY,
                                          wx.Bitmap("xpy/Images/32x32/Valider.png", wx.BITMAP_TYPE_ANY))
        self.bouton_annuler1 = CTRL(self, texte="Annuler", cheminImage="xpy/Images/32x32/Annuler.png")
        self.bouton_annuler2 = wx.BitmapButton(self, wx.ID_ANY,
                                               wx.Bitmap("xpy/Images/32x32/Annuler.png", wx.BITMAP_TYPE_ANY))

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonTest, self.bouton_aide1)

    def __set_properties(self):
        self.SetTitle("Saisie d'une traduction")
        self.SetMinSize((670, 400))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(3, 1, 10, 10)

        grid_sizer_haut = wx.FlexGridSizer(4, 2, 10, 10)
        grid_sizer_haut.Add(self.label_test, 0, wx.ALIGN_RIGHT, 0)
        grid_sizer_haut.Add(self.ctrl_test, 0, wx.EXPAND, 0)
        grid_sizer_haut.AddGrowableRow(0)
        grid_sizer_haut.AddGrowableRow(1)
        grid_sizer_haut.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_haut, 1, wx.ALL | wx.EXPAND, 10)

        grid_sizer_boutons = wx.FlexGridSizer(1, 8, 10, 10)
        grid_sizer_boutons.Add(self.bouton_aide1, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_aide2, 0, 0, 0)
        grid_sizer_boutons.Add((5, 5), 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_ok1, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_ok2, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler1, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler2, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(2)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.AddGrowableRow(0)
        self.Layout()
        self.CenterOnScreen()

    def OnBoutonTest(self, event):
        self.bouton_aide1.SetImage("xpy/Images/32x32/Annuler.png")
        self.bouton_aide1.SetTexte("Couco")

if __name__ == "__main__":
    app = wx.App(0)
    import os
    os.chdir("..")
    os.chdir("..")
    dialog_1 = Dialog(None)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()
