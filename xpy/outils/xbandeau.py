#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
# -----------------------------------------------------------

import wx
import wx.html as html
from xpy.outils import xformat
class MyHtml(html.HtmlWindow):
    def __init__(self, parent, texte="", hauteur=25, fontsize = -1):
        html.HtmlWindow.__init__(self, parent, -1,
                                 style=wx.html.HW_NO_SELECTION | wx.html.HW_SCROLLBAR_NEVER | wx.NO_FULL_REPAINT_ON_RESIZE)
        if "gtk2" in wx.PlatformInfo:
            self.SetStandardFonts()
        self.SetBorders(0)
        self.SetMinSize((-1, hauteur))
        self.SetPage("<FONT SIZE=%d>%s</FONT>""" %(fontsize ,texte))

class Bandeau(wx.Panel):
    def __init__(self, parent, titre="", texte="", hauteur=15, nomImage=None,sizeImage=None,bgColor = None):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.hauteur = hauteur
        self.ctrlImage = (2,2)
        if nomImage != None:
            self.ctrlImage = wx.StaticBitmap(self, -1, xformat.GetImage(nomImage,sizeImage))
        self.ctrlTitre = wx.StaticText(self, -1, titre)
        self.ctrlIntro = wx.StaticText(self, -1, texte)
        #self.ctrlIntro = MyHtml(self, texte, hauteurHtml+20,-1)
        self.ligne = wx.StaticLine(self, -1)

        self.__set_properties()
        if bgColor:
            self.SetBackgroundColour(wx.Colour(bgColor))
        self.__do_layout()

    def __set_properties(self):
        self.SetBackgroundColour(wx.Colour(220, 230, 240))
        self.ctrlTitre.SetFont(wx.Font(int(self.hauteur*0.6), wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.ctrlIntro.SetFont(wx.Font(int(self.hauteur*0.5), wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        #Font(pixelSize, family, style, weight, underline=False, faceName="", encoding=FONTENCODING_DEFAULT)

    def __do_layout(self):
        grid_sizer_vertical = wx.FlexGridSizer(rows=2, cols=1, vgap=4, hgap=4)
        grid_sizer_horizontal = wx.FlexGridSizer(rows=1, cols=2, vgap=0, hgap=0)
        grid_sizer_texte = wx.FlexGridSizer(rows=2, cols=1, vgap=4, hgap=4)
        grid_sizer_horizontal.Add(self.ctrlImage, 0, wx.ALL, 10)
        grid_sizer_texte.Add(self.ctrlTitre, 0, wx.TOP, 7)
        grid_sizer_texte.Add(self.ctrlIntro, 0, wx.RIGHT | wx.EXPAND, 5)
        grid_sizer_texte.AddGrowableRow(1)
        grid_sizer_texte.AddGrowableCol(0)
        grid_sizer_horizontal.Add(grid_sizer_texte, 1, wx.EXPAND, 0)
        grid_sizer_horizontal.AddGrowableRow(0)
        grid_sizer_horizontal.AddGrowableCol(1)
        grid_sizer_vertical.Add(grid_sizer_horizontal, 1, wx.EXPAND, 0)
        grid_sizer_vertical.Add(self.ligne, 0, wx.EXPAND, 0)
        self.SetSizer(grid_sizer_vertical)
        grid_sizer_vertical.Fit(self)
        grid_sizer_vertical.AddGrowableRow(0)
        grid_sizer_vertical.AddGrowableCol(0)


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL | wx.EXPAND)
        self.SetSizer(sizer_1)
        self.ctrl = Bandeau(panel, "COUCOU", "coincoin<BR />...et la suite", nomImage="xpy/Images/32x32/Python.png")
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl, 1, wx.ALL | wx.EXPAND, 0)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.CentreOnScreen()


if __name__ == '__main__':
    app = wx.App(0)
    import os
    os.chdir("..")
    os.chdir("..")
    frame_1 = MyFrame(None, -1, "TEST", size=(800, 200))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
