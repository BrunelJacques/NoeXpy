# !/usr/bin/env python
# -*- coding: utf-8 -*-

# Noelite.py : Lanceur d'une application Noethys version lite

import os
import wx
import xpy.xAppli as xAppli
import xpy.xUTILS_Identification as ncident
import xpy.outils.xaccueil as xaccueil
import srcNoelite.menu as menu

# Variables incontournables pour xpy
dictAPPLI = {
            'NOM_APPLICATION'       : "Noelite",
            'REP_SOURCES'           : "srcNoelite",
            'REP_DATA'              : "C:/ProgramData/Noelite",
            'REP_TEMP'              : "C:/Temp",
            'NOM_FICHIER_LOG'       : "logsNoelite.log",
            'TYPE_CONFIG'         : 'db_reseau',
}

class MyFrame(xAppli.MainFrame):
    def __init__(self, *args, **kw):
        kw['size'] = (800,600)
        super().__init__( *args, **kw)

        #dictionnaire propre à l'appli
        self.dictAppli = dictAPPLI
        self.menuClass = menu.MENU(self)
        self.dictMenu = menu.MENU.ParamMenu(self)
        self.ldButtons = menu.MENU.ParamBureau(self)
        if hasattr(menu.MENU,"CouleurFondBureau"):
            self.couleur_fond = menu.MENU.CouleurFondBureau(self)

        # Intialise et Teste la présence de fichiers dans le répertoire sources
        self.xInit()
        for dicBtn in self.ldButtons:
            if 'image' in dicBtn.keys() :
                    dicBtn['image'] = (str(self.pathXpy) + "/" + str(dicBtn["image"])).replace("\\","/")

        # Crée 'topPanel' et 'topContenu' destroyables
        self.MakeBureau(pnlTitre=xaccueil.Panel_Titre(self,texte="NOELITE\n\nCompléments Noethys",
                                                      pos=(20,30),couleurFond=self.couleur_fond),
                        pnlBtnActions=xaccueil.Panel_Buttons(self,self.ldButtons,couleurFond=self.couleur_fond))

        #self.SetForegroundColour(self.couleur_fond)

        # Activer le menu décrit dans  PATH_SOURCES/menu.py
        test = os.getcwd()
        self.MakeMenuBar()
        self.Show()
        dlg = ncident.Dialog(self,confirm=False)
        etat = False
        if not dlg.echec:
            dlg.ShowModal()
            self.dictUser = dlg.GetDictUtilisateur()
            if self.dictUser:
                etat = True
        dlg.Destroy()
        for numMenu in range(1,2):
            self.menu.EnableTop(numMenu, etat)
        self.panelAccueil.EnableBoutons(etat)
        if not etat:
            self.infoStatus="lancé sans accès à Noethys!"
        self.MakeStatusText()

class MyApp(wx.App):
    def OnInit(self):
        xAppli.CrashReport(dictAPPLI)
        # Création de la frame principale
        myframe = MyFrame(None)
        self.SetTopWindow(myframe)
        return True

if __name__ == "__main__":
    # Lancement de l'application
    app = MyApp(redirect=False)
    app.MainLoop()