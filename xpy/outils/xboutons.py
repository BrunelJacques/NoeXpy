#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------
# Application :    Projet xpy, gérer des boutons par des paramètres
# Auteur:           Jacques BRUNEL
# Licence:         Licence GNU GPL
# ------------------------------------------------------------------------

import wx

def GetAddManyBtns(pnl,ldParamsBtns,**kwds):
    # décompactage des paramètres, prouduit une liste pour Sizer.AddMany
    marge = kwds.pop('marge',5)
    lstWxBtns = []
    
    for dicParam in ldParamsBtns:
        # gestion par série :(code, ID, image ou texte, texteToolTip), image ou texte mais pas les deux!
        try:
            # gestgion de l'ancien format par tuples, le label pouvait être remplacé par une image
            if isinstance(dicParam, (tuple, list)):
                (name, ID, label, tooltip) = dicParam
                if isinstance(label,wx.Bitmap):
                    image=label
                    label=''
                else: image=None
                dicParam = {'name':name,'ID':ID, 'label':label, 'help':tooltip,'image':image}
            bouton= Bouton(pnl,**dicParam)
        except Exception as err:
            bouton = wx.Button(pnl, wx.ID_ANY, 'Erreur\nparam!')
            print("Construction bouton: ",err)
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
            'label': "Abandon",
            'onBtn': 'OnBtnEsc',}
    kw.update(kwds)
    return Bouton(parent,**kw)

def BTN_fermer(parent,**kwds):
    # valeurs par défaut modifiables par kwds
    kw = {  'image': 'xpy/Images/32x32/Valider.png',
            'help': "Cliquez ici pour enregistrer et fermer la fenêtre",
            'label': "Fermer",
            'sizeFont':14,
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
        image =     kwds.pop('image',None)
        help =      kwds.pop('help',None)
        onBtn =     kwds.pop('onBtn',None)
        size =      kwds.pop('size',(110,35))
        sizeBmp =   kwds.pop('sizeBmp',None)
        sizeFont =  kwds.pop('sizeFont',None)

        # ajout de l'image. Le code de wx.ART_xxxx est de type bytes et peut être mis en lieu de l'image
        if isinstance(image,bytes):
            # images ArtProvider pas encore en Bitmap
            if not sizeBmp:
                if size:
                    sizeBmp = (size[1] - 10, size[1] - 10)
                else: sizeBmp = (16,16)
            imageBmp = wx.ArtProvider.GetBitmap(image,wx.ART_BUTTON,wx.Size(sizeBmp))
        elif isinstance(image,wx.Bitmap):
            # image déjà en format Bitmap
            imageBmp = image
        elif isinstance(image,str):
            # image en bitmap pointée par son adresse
            imageBmp = wx.Bitmap(image)
        else: imageBmp = None

        # Ajustements de la taille
        if size and isinstance(size,tuple):
            if not sizeFont:
                lgBmp = 0
                lignes = label.split('\n')
                if imageBmp:
                    lgBmp = (imageBmp.GetSize()[0] * 2) - 30
                #mise en proportion de la hauteur
                sizeFont = (size[1]) * 0.4 / (len(lignes) * 0.5 + 0.5)
                # Teste si le label est trop long
                nblettres = max([ len(x) for x in lignes])
                lglabel = (nblettres * sizeFont * 1.0) + lgBmp
                prorata = min(1,size[0] / lglabel)
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
        kwds['size'] = size
        super().__init__(parent,ID,label,**kwds)

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
        if onBtn:
            if isinstance(onBtn, str):
                fonction = eval("parent.%s"%onBtn)
            else:
                fonction = onBtn
            self.Bind(wx.EVT_BUTTON, fonction)

        if help: self.SetToolTip(help)

#************************   Pour Test ou modèle  *********************************

class xFrame(wx.Frame):
    # reçoit les controles à gérer sous la forme d'un ensemble de paramètres
    def __init__(self, *args):
        self.parent = None
        wx.Frame.__init__(self,*args,size=(800,80))
        #topPnl = wx.Panel(self)
        lstParamsBtns = self.GetLstParamsBtns()
        lstBtns = GetAddManyBtns(self,lstParamsBtns)
        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_1.Add((10,10),1,0,0)
        sizer_1.AddMany(lstBtns)
        for param in lstParamsBtns:
            btn = Bouton(self,**param)
            sizer_1.Add(btn,0,wx.ALL,5)
        self.SetSizer(sizer_1)
        self.CentreOnScreen()

    def OnAction1(self,event):
        wx.MessageBox("Action1")

    def OnAction2(self,event):
        wx.MessageBox("Action2")

    def OnFermer(self,event):
        self.Close()

    # description des boutons en pied d'écran et de leurs actions
    def GetLstParamsBtns(self):
            return  [
                        {'name': 'btnImp', 'label': "Importer\nfichier",
                            'help': "Cliquez ici pour lancer l'importation du fichier de km consommés",
                            'size': (120, 35), 'image': wx.ART_UNDO,'onBtn':self.OnAction1},
                        {'name': 'btnExp', 'label': "Exporter\nfichier",
                            'help': "Cliquez ici pour lancer l'exportation du fichier selon les paramètres que vous avez défini",
                            'size': (120, 35), 'image': wx.ART_REDO,'onBtn':self.OnAction2},
                        {'name':'btnOK','ID':wx.ID_ANY,'label':"Quitter",'help':"Cliquez ici pour fermer la fenêtre",
                            'size':(120,35),'image':"../Images/32x32/Quitter.png",'onBtn':self.OnFermer}
                    ]
        

if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = xFrame(None)
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
