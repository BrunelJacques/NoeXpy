#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------
# Application :    Projet xpy, gérer des boutons par des paramètres
# Auteur:           Jacques BRUNEL
# Licence:         Licence GNU GPL
# ------------------------------------------------------------------------

import wx
from xpy.outils import xformat

def GetAddManyBtns(pnl,lstBtns,**kwds):
    # Trois possibles: déjàBouton avec parent pnl, listeParams, dicParams.  Tous produisent une liste pour Sizer.AddMany
    marge = kwds.pop('marge',5)
    lstWxBtns = []
    
    for itemBtn in lstBtns:
        bouton = None
        # gestion par série :(code, ID, image ou texte, texteToolTip), image ou texte mais pas les deux!
        try:
            if isinstance(itemBtn,(Bouton,wx.Button)):
                bouton = itemBtn
            # gestion de l'ancien format par tuples, le label pouvait être remplacé par une image
            elif isinstance(itemBtn, (tuple, list)):
                (name, ID, label, tooltip) = itemBtn
                if isinstance(name,(Bouton,wx.Button)):
                    # cas d'une redondance de l'appel
                    bouton = name
                else:
                    # tuple de params
                    if isinstance(label,wx.Bitmap):
                        image=label
                        label=' '
                    else: image=None
                    dicBtn = {'name':name,'ID':ID, 'label':label, 'help':tooltip,'image':image}
                    bouton= Bouton(pnl,**dicBtn)
            elif isinstance(itemBtn,dict):
                bouton= Bouton(pnl,**itemBtn)
        except Exception as err:
            bouton = wx.Button(pnl, wx.ID_ANY, 'Erreur\nparam!')
            print("Construction bouton: ",err)
        if bouton:
            lstWxBtns.append((bouton, 0, wx.ALL, marge))
    return lstWxBtns

def BTN_action(parent,**kwds):
    kw = {  'size' : (24,24),
            'image': "xpy/Images/16x16/Mecanisme.png",}
    kw.update(kwds)
    return Bouton(parent,**kw)

def BTN_tester(parent,**kwds):
    # valeurs par défaut modifiables par kwds
    kw = {  'image': wx.ART_FIND,
            'help': "Cliquez ici pour tester vos choix",
            'label': "Tester",
            'onBtn': 'OnTester',}
    kw.update(kwds)
    return Bouton(parent,**kw)

def BTN_esc(parent,**kwds):
    # valeurs par défaut modifiables par kwds
    kw = {  'image': wx.ART_DELETE,
            'help': "Cliquez ici pour abandonner et fermer la fenêtre",
            'label': "Abandonner",
            'onBtn': 'OnEsc',}
    kw.update(kwds)
    return Bouton(parent,**kw)

def BTN_fermer(parent,**kwds):
    # valeurs par défaut modifiables par kwds
    kw = {  'image': 'xpy/Images/32x32/Valider.png',
            'help': "Cliquez ici pour enregistrer et fermer la fenêtre",
            'label': "Fermer",
            'onBtn': 'OnFermer',}
    kw.update(kwds)
    return Bouton(parent,**kw)

class Bouton(wx.Button):
    # Enrichissement du wx.Button par l'image, nom, help et Bind, via un dictionnaire
    def __init__(self,parent,**kwds):
        # image en bitmap ou ID de artProvider sont possibles
        ID =        kwds.pop('ID',wx.ID_ANY)
        # récupère un éventuel id en minuscule
        ID =        kwds.pop('id',ID)
        label =     kwds.pop('label','')
        name =      kwds.pop('name',None)
        help =      kwds.pop('help',None)
        onBtn =     kwds.pop('onBtn',None)
        image =     kwds.pop('image',None)
        sizeBmp =   kwds.pop('sizeBmp',None)
        sizeFont =  kwds.pop('sizeFont',None)
        # cas des boutons avec label
        if image and len(label) > 2:
            defsize = (110,35)
        # cas des '...' sans image ou image seule
        elif len(label) <= 3 :
            defsize = (24,24)
        else: defsize = (70,24)
        size =      kwds.pop('size',defsize)

        # ajout de l'image. Le code de wx.ART_xxxx est de type bytes et peut être mis en lieu de l'image
        if isinstance(image,bytes):
            # images ArtProvider pas encore en Bitmap
            if not sizeBmp:
                if size:
                    sizeBmp = (size[1] - 10, size[1] - 10)
                else:
                    sizeBmp = (16, 16)
            imageBmp = wx.ArtProvider.GetBitmap(image,wx.ART_BUTTON,wx.Size(sizeBmp))
        elif isinstance(image,wx.Bitmap):
            # image déjà en format Bitmap
            if sizeBmp:
                imageBmp = xformat.ResizeBmp(image,sizeBmp)
            else:
                imageBmp = image

        elif isinstance(image,str):
            # image en bitmap pointée par son adresse
            imageBmp = xformat.GetImage(image,sizeBmp)
        else: imageBmp = None

        # Ajustements de la taille
        if size and isinstance(size,tuple):
            if not sizeFont:
                lgBmp = 0
                lignes = label.split('\n')
                if imageBmp:
                    lgBmp = (imageBmp.GetSize()[0] * 2) - 25
                    hiBmp = (imageBmp.GetSize()[1] * 2) - 25
                    if size[0] < lgBmp:
                        size = (lgBmp,size[1])
                    if size[1] < hiBmp:
                        size = (size[0],hiBmp)

                #mise en proportion de la hauteur
                sizeFont = (size[1]) * 0.4 / (len(lignes) * 0.5 + 0.5)
                # Teste si le label est trop long
                nblettres = max([ len(x) for x in lignes])
                lglabel = (nblettres * sizeFont * 1.0) + lgBmp
                if lglabel > 1:
                    prorata = min(1,size[0] / lglabel)
                else: prorata = 1
                sizeFont = int(sizeFont * prorata)
        elif sizeFont:
            lg = 5
            ht = sizeFont * 2
            if label:
                lg += min(80,int(len(label) * 5.5))
            if imageBmp:
                lg += imageBmp.GetSize()[0]+5
                ht = max(16,imageBmp.GetSize()[1])+5
            size = (lg,ht)

        # fixe le nom interne du controle
        if not name:
            name = 'btn'
            if len(label)>0:
                name += str(label.capitalize())

        #----Construction----------------------------------------------------------------------------------
        kwds['name'] = name
        if size : kwds['size'] = size
        super().__init__(parent,ID,label,**kwds)
        if sizeFont:
            font = wx.Font(sizeFont, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD,False)
            self.SetFont(font)
        self.SetForegroundColour((0,0,100))

        # ajout de l'image
        if imageBmp: self.SetBitmap(imageBmp)

        # ajustement de la taille si non précisée
        if not size and not sizeFont :
           self.SetInitialSize()

        # Compléments d'actions
        if help: self.SetToolTip(help)
        self.name = name

        # implémente les fonctions bind transmises, soit par le pointeur soit par eval du texte
        fonction = None
        if onBtn == None:
            # composition d'un bind par défaut
            if ID in (wx.ID_CANCEL, wx.ID_EXIT):
                onBtn = "OnEsc"
            elif (ID in (wx.ID_OK, wx.OK)) or ('OK' in name):
                onBtn = "OnFermer"

        if isinstance(onBtn, str):
            try:
                fonction = eval("parent.%s"%onBtn)
            except Exception:
                fonction = eval("parent.parent.%s"%onBtn)
        else:
            fonction = onBtn
        self.Bind(wx.EVT_BUTTON, fonction)

        if help: self.SetToolTip(help)

#************************   Pour Test ou modèle  *********************************

class xFrame(wx.Frame):
    # reçoit les controles à gérer sous la forme d'un ensemble de paramètres
    def __init__(self, *args):
        self.parent = None
        wx.Frame.__init__(self,*args,size=(800,300))
        #topPnl = wx.Panel(self)
        lstParamsBtns = self.GetLstParamsBtns()
        lstBtns = GetAddManyBtns(self,lstParamsBtns)
        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_1.Add((10,10),1,0,0)
        sizer_1.AddMany(lstBtns)
        self.SetSizer(sizer_1)
        self.CentreOnScreen()

    def OnAction1(self,event):
        wx.MessageBox("Action1")

    def OnAction2(self,event):
        wx.MessageBox("Action2")

    def OnFermer(self,event):
        self.Close()

    # description des diverses possibilités boutons en pied d'écran et de leurs actions
    def GetLstParamsBtns(self):
            return  [ BTN_fermer(self,image="../Images/32x32/Annuler.png"),
                    ('BtnPrec2',-1, "Ecran\nprécédent", "Retour à l'écran précédent next"),
                    ('BtnOK', -1, wx.Bitmap("../Images/32x32/Configuration.png", wx.BITMAP_TYPE_ANY),"Cliquez ici pour fermer la fenêtre"),

                    {'name': 'btnImp', 'label': "Importer\nfichier",
                        'help': "Cliquez ici pour lancer l'importation du fichier de km consommés",
                        'size': (120, 50), 'image': wx.ART_UNDO,'onBtn':self.OnAction1,'sizeBmp':(60,40)},
                    {'name': 'btnExp', 'label': "Exporter\nfichier",
                        'help': "Cliquez ici pour lancer l'exportation du fichier selon les paramètres que vous avez défini",
                        'size': (120, 35), 'image': wx.ART_REDO,'onBtn':self.OnAction2},
                    {'name':'btnOK','ID':wx.ID_ANY,'label':"Img Resizée",'help':"Cliquez ici pour fermer la fenêtre",
                        'size':(150,60),'image':"../Images/80x80/Famille.png",'onBtn':self.OnFermer,'sizeBmp':(50,50)}
                    ]
        

if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = xFrame(None)
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
