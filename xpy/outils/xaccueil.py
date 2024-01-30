#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import wx
import wx.html as html
from xpy.outils import ximport

COULEUR_FOND = wx.Colour(176,153,203)


def GetVersion(topwindows):
    chemin = topwindows.dictAppli['REP_SOURCES']
    fichier = ximport.GetFichierCsv(chemin + '/Versions.txt')
    version = None
    if fichier and len(fichier) > 0:
        version = fichier[0][0]
    return version

class Button(wx.Button):
    # Enrichissement du wx.Button par l'image, nom, toolTip et Bind
    def __init__(self, parent,**kwds):
        # image en bitmap ou ID de artProvider sont possibles
        ID = kwds.pop('ID',None)
        label = kwds.pop('label',None)
        code = kwds.pop('code',None)
        image = kwds.pop('image',None)
        infobulle = kwds.pop('infobulle',None)
        action = kwds.pop('action',None)
        size = kwds.pop('size',(80,80))
        sizeFont = kwds.pop('sizeFont',12)
        sizeBmp = kwds.pop('sizeBmp',(16,16))

        if not ID : ID = wx.ID_ANY

        # récupère le label
        if not label : label = ""
        if "\n" in label:
            sizeFont = int(sizeFont*0.75)
        else:
            lstMots = label.split(" ")
            label = ""
            for mot in lstMots:
                if label == "":
                    label += mot
                else:
                    label += "\n%s"%mot

        wx.Button.__init__(self,parent,ID,label,size=size,style=wx.BU_BOTTOM)
        font = wx.Font(sizeFont, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL,False)
        self.SetFont(font)
        self.SetBackgroundColour(COULEUR_FOND)

        # ajout de l'image. Le code de wx.ART_xxxx est de type bytes et peut être mis en lieu de l'image
        if  isinstance(image,bytes):
            # image ArtProvider
            if sizeBmp:
                self.SetBitmap(wx.ArtProvider.GetBitmap(image,wx.ART_BUTTON,wx.Size(sizeBmp)))
            else:
                self.SetBitmap(wx.ArtProvider.GetBitmap(image,wx.ART_BUTTON))
        elif isinstance(image,wx.Bitmap):
            # image déjà en format wx
            self.SetBitmap(image)
        elif isinstance(image,str):
            # image en bitmap pointée par son adresse
            self.SetBitmap(wx.Bitmap(image))
        self.SetBitmapPosition(wx.TOP)
        # ajustement de la taille si non précisée
        if not size :
            self.SetInitialSize()

        # Compléments d'actions
        self.SetToolTip(infobulle)
        self.code = code

        # implémente les fonctions bind transmises, soit par le pointeur soit par eval du texte
        if action:
            if isinstance(action, str):
                fonction = lambda evt, code=code: eval(action)
            else:
                fonction = action
            self.Bind(wx.EVT_BUTTON, fonction)

class CTRL_btnAction(wx.Panel):
    # Bouton personnalisé
    def __init__(self, parent,**kwds):
        # image en bitmap ou ID de artProvider sont possibles
        ID = kwds.pop('ID',None)
        label = kwds.pop('label',None)
        code = kwds.pop('code',None)
        image = kwds.pop('image',None)
        infobulle = kwds.pop('infobulle',None)
        action = kwds.pop('action',None)
        size = kwds.pop('size',None)
        sizeFont = kwds.pop('sizeFont',14)
        sizeBmp = kwds.pop('sizeFont',14)
        if not ID : ID = wx.ID_ANY
        # récupère le label
        if not label : label = ""
        if "\n" in label: sizeFont = int(sizeFont*0.75)

        wx.Button.__init__(self,parent,ID,label,wx.BU_EXACTFIT)
        font = wx.Font(sizeFont, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL,False)
        self.SetFont(font)


        # ajout de l'image. Le code de wx.ART_xxxx est de type bytes et peut être mis en lieu de l'image
        if  isinstance(image,bytes):
            # image ArtProvider
            if sizeBmp:
                self.SetBitmap(wx.ArtProvider.GetBitmap(image,wx.ART_BUTTON,wx.Size(sizeBmp)))
            else:
                self.SetBitmap(wx.ArtProvider.GetBitmap(image,wx.ART_BUTTON))
        elif isinstance(image,wx.Bitmap):
            # image déjà en format wx
            self.SetBitmap(image)
        elif isinstance(image,str):
            # image en bitmap pointée par son adresse
            self.SetBitmap(wx.Bitmap(image))

        # ajustement de la taille si non précisée
        if not size :
            self.SetInitialSize()

        # Compléments d'actions
        self.SetToolTip(infobulle)
        self.code = code

        # implémente les fonctions bind transmises, soit par le pointeur soit par eval du texte
        if action:
            if isinstance(action, str):
                fonction = lambda evt, code=code: eval(action)
            else:
                fonction = action
            self.Bind(wx.EVT_BUTTON, fonction)

class CTRL_html(html.HtmlWindow):
    def __init__(self, parent):
        html.HtmlWindow.__init__(self, parent, -1, style=wx.html.HW_NO_SELECTION | wx.html.HW_SCROLLBAR_NEVER )
        self.parent = parent
        if "gtk2" in wx.PlatformInfo:
            self.SetStandardFonts()
        self.SetBorders(0)
        self.SetMinSize((368, 30))
        self.SetTexte()
    
    def SetTexte(self, texte="test"):
        try :
            self.SetPage("""<BODY'><FONT SIZE=20>%s</FONT></BODY>""" % texte)
            self.SetBackgroundColour(wx.Colour(196,173,223))
        except :
            pass

class Panel_Titre(wx.Panel):
    def __init__(self, parent, pos=(0,0),image="xpy/Images/Globe.ico",posImage=(20, 10),
                 texte="monAppli..."*5,posLabel=(160, 40),tailleFont=16,couleurFond=None):
        self.parent = parent
        size = parent.GetSize()

        size[1] = 145
        wx.Panel.__init__(self, parent, name="panel_titre", id=-1, size=size, pos=pos, style=wx.TAB_TRAVERSAL)

        # imageBmp = xformat.GetImage("xpy/Images/Noestock.png",(80,80))
        self.image_titre = wx.StaticBitmap(self, -1, wx.Bitmap(image, wx.BITMAP_TYPE_ANY), pos=posImage)
        if not couleurFond: couleurFond = COULEUR_FOND
        self.SetForegroundColour(couleurFond)
        self.label = wx.StaticText(self, -1, texte, pos=posLabel,style=wx.ST_ELLIPSIZE_END)
        self.label.SetFont(wx.Font(tailleFont, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.version = GetVersion(self.parent)
        if self.version:
            self.ctrlVersion = wx.StaticText(self, -1, self.version)
            self.ctrlVersion.SetFont(wx.Font(int(tailleFont/2), wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.__do_layout()

    def __do_layout(self):
        grid_sizer = wx.FlexGridSizer(rows=1, cols=2, vgap=10, hgap=20)
        grid_sizer.Add(self.image_titre, 0, wx.ALL, 20)
        sizer_right = wx.FlexGridSizer(rows=5, cols=1, vgap=0, hgap=20)
        sizer_right.Add(self.label, 0, wx.TOP, 20)
        if self.version:
            sizer_right.Add(self.ctrlVersion, 1, wx.TOP|wx.EXPAND, 10)
        grid_sizer.Add(sizer_right)
        grid_sizer.AddGrowableCol(1)
        self.SetSizerAndFit(grid_sizer)

class Panel_Buttons(wx.Panel):
    def __init__(self, parent,lstButtons=[],sizeFont=12,sizeBmp=80,couleurFond=None,
                 sizeBtn=(140,140)):
        size = parent.GetSize()
        size[1] -= 145
        wx.Panel.__init__(self, parent, name="panel_boutons", id=-1, size=size, style=wx.TAB_TRAVERSAL)

        self.parent = parent
        self.lstCtrlBtns = []
        self.couleurFond = couleurFond
        if not couleurFond: self.couleurFond = COULEUR_FOND
        for dicBtn in lstButtons:
            if not isinstance(dicBtn,dict): continue
            dicBtn['size'] = sizeBtn
            dicBtn['sizeFont'] = sizeFont
            dicBtn['sizeBmp'] = sizeBmp
            self.lstCtrlBtns.append(Button(self,**dicBtn))
        (lg,ht) = self.GetSize()
        self.nbBtnOnRow = int((lg -40)/ (sizeBtn[0]+30))
        if self.nbBtnOnRow == 0:
            self.nbBtnOnRow = 1

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.SetBackgroundColour(self.couleurFond)

    def __do_layout(self):
        grid_sizer = wx.FlexGridSizer(rows=5, cols=self.nbBtnOnRow, vgap=30, hgap=30)
        for ctrlBtn in self.lstCtrlBtns:
            grid_sizer.Add(ctrlBtn, 1, wx.ALL, 10)
        self.SetSizer(grid_sizer)


class Panel_Accueil(wx.Panel):
    def __init__(self, parent,pnlTitre=None,pnlBtnActions=None):
        wx.Panel.__init__(self, parent, name="panel_accueil", id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.pnlBtnActions = None
        self.pnlTitre = pnlTitre
        self.pnlBtnActions = pnlBtnActions
        self.Sizer()
        self.EnableBoutons(False)

    def Sizer(self):
        box_sizer = wx.BoxSizer(wx.VERTICAL)
        if self.pnlTitre:
            box_sizer.Add(self.pnlTitre, 0, wx.EXPAND, 0)
        if self.pnlBtnActions:
            box_sizer.Add(self.pnlBtnActions, 1, wx.EXPAND, 0)
        self.parent.SetSizerAndFit(box_sizer)

    def EnableBoutons(self,etat=False):
        if self.pnlBtnActions:
            for button in self.pnlBtnActions.lstCtrlBtns:
                button.Enable(etat)

# -------------------------- pour tests -------------------------------------------------------------------------------
class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args,name="frame_top",size=(800,400) )
        self.dictAppli = kwds.pop('dictAppli',{})
        self.size = (800,400)
        lstButtons = [
            {"code": "modifAdresses", "label": ("&Modification d'adresses Individus"),
             "infobulle": (u"Gestion de l'adresses de rattachement des personnes (soit la leur soit celle de leur hébergeur"),
             "image": "xpy/Images/80x80/Adresse.png",
             "action": self.OnAction, "genre": wx.ITEM_NORMAL},
            {"code": "modifAdressesF", "label": ("&Modification d'adresses Familles"),
             "infobulle": (u"Gestion des adresses des familles, mais pas de tous les individus de la famille"),
             "image": "xpy/Images/80x80/Adresse-famille.jpg",
             "action": self.OnAction, "genre": wx.ITEM_NORMAL},
            "-",
            {"code": "gestionReglements", "label": ("&Gestion des règlements"),
             "infobulle": (u"Gestion de bordereau de règlements : remise de chèques, arrivée de virements, de dons..."),
             "image": "xpy/Images/80x80/Euro.png",
             "action": self.OnAction, "genre": wx.ITEM_NORMAL},
        ]
        pnlTitre= Panel_Titre(self, texte="Mon appli ...\n\n%s"%("mais encore! "*3,), pos=(20, 30))
        pnlBtnActions = Panel_Buttons(self, lstButtons)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel = Panel_Accueil(self,pnlTitre=pnlTitre,pnlBtnActions=pnlBtnActions)
        self.panel.SetMinSize(self.size)
        sizer.Add(self.panel, 1, wx.EXPAND, 0)
        #self.SetSizer(sizer)

    def OnAction(self,event):
        wx.MessageBox("Voici mon action !!")

if __name__ == '__main__':
    app = wx.App(0)
    import os
    os.chdir("..")
    os.chdir("..")
    dictAppli ={
            'NOM_APPLICATION'       : "testappli",
            'REP_DATA'              : "srcNoelite/Data",
            'REP_SOURCES'              : "srcNoelite",
            'TYPE_CONFIG'           : 'db_reseau',
            'CHOIX_CONFIGS': [('Donnees', "Base de travail, peut être la centrale  en mode connecté"),]
            }
    frame_1 = MyFrame(None, -1, "TEST",dictAppli=dictAppli)
    app.SetTopWindow(frame_1)

    frame_1.Show()
    app.MainLoop()