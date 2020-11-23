# !/usr/bin/env python
# -*- coding: utf-8 -*-

# Noestock.py : Lanceur d'une application Noethys version lite

import os
import wx
import xpy.xAppli as xAppli
import xpy.outils.xaccueil as xaccueil
import srcNoestock.menu as menu

# Variables incontournables pour xpy
dictAPPLI = {
            'NOM_APPLICATION'       : "Noestock",
            'REP_SOURCES'           : "srcNoestock",
            'REP_DATA'              : "srcNoelite/Data",
            'REP_TEMP'              : "srcNoelite/Temp",
            'NOM_FICHIER_LOG'       : "logsNoestock.log",
            'TYPE_CONFIG'           : 'db_prim',
            'CHOIX_CONFIGS': [('Centralisation',"Base au siège, cible pour les synchro et sauvegarde"),
                             ('Donnees', "Base de travail, peut être la centrale  en mode connecté")]
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
        self.MakeBureau(pnlTitre=xaccueil.Panel_Titre(self,texte="NOESTOCK\n\nGestion des stocks et prix journée",
                                                      pos=(20,30),couleurFond=self.couleur_fond),
                        pnlBtnActions=xaccueil.Panel_Buttons(self,self.ldButtons,couleurFond=self.couleur_fond))

        #self.SetForegroundColour(self.couleur_fond)

        # Activer le menu décrit dans  PATH_SOURCES/menu.py
        test = os.getcwd()
        self.MakeMenuBar()

        self.Show()
        etat = True
        for numMenu in range(1,2):
            self.menu.EnableTop(numMenu, etat)
        self.panelAccueil.EnableBoutons(etat)

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