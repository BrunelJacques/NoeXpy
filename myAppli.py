# !/usr/bin/env python
# -*- coding: utf-8 -*-

# myXappli.py : Exemple de lanceur d'une application standard

import wx
import xpy.xAppli as xAppli

# Variables incontournables pour xpy
dictAPPLI = {
            'NOM_APPLICATION'       : "myAppli",
            'REP_SOURCES'           : "srcMyAppli",
            'REP_DATA'              : "srcMyAppli/Data",
            'REP_TEMP'              : "srcMyAppli/Temp",
            'NOM_FICHIER_LOG'       : "logsMyAppli.log",
            'TYPE_CONFIG'         : 'db_prim',
}

class MyFrame(xAppli.MainFrame):
    def __init__(self, *args, **kw):
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
        #self.ConnexionReseau()
        #self.ConnexionLocal()
        #self.SuiviActivite()

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