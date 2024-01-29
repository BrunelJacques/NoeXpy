# !/usr/bin/env python
# -*- coding: utf-8 -*-

# myXappli.py : Exemple de lanceur d'une application standard

import wx
import xpy.xAppli as xAppli
import xpy.outils.xchemins as xchemins

# Variables incontournables pour xpy
dictAPPLI = {
            'NOM_APPLICATION'       : "myAppli",
            'REP_SOURCES'           : "srcMyAppli",
            'REP_DATA': xchemins.GetRepData("MyAppli"),
            'REP_TEMP': xchemins.GetRepTemp(),
            'NOM_FICHIER_LOG': xchemins.GetRepData("MyAppli/logs"),
            'TYPE_CONFIG'         : 'db_reseau',
}

class MyFrame(xAppli.MainFrame):
    def __init__(self, *args, **kw):
        kw['size'] = (750, 520)
        super().__init__( *args, **kw)

        #dictionnaire propre à l'appli
        self.dictAppli = dictAPPLI

        # Intialise et Teste la présence de fichiers dans le répertoire sources
        self.xInit()
        # Crée 'topPanel' et 'topContenu' destroyables
        self.MakeHello("TopPanel de " + self.dictAppli['NOM_APPLICATION'])
        # Activer le menu décrit dans  PATH_SOURCES/menu.py
        self.MakeMenuBar()
        self.Show()
        ret = self.SaisieConfig()
        self.GestMenu(True)

    def GestMenu(self, etat):
        # grise les boutons si pas d'accès à la base
        if hasattr(self,"panelAccueil"):
            self.panelAccueil.EnableBoutons(etat)
        try:
            for numMenu in range(1,4):
                self.menu.EnableTop(numMenu, etat)

            # grise ou dégrise les options du menu selon l'identification
            if self.dictUser :
                etat = True
            else: etat = False
            for numMenu in range(2,4):
                self.menu.EnableTop(numMenu, etat)
        except: pass


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