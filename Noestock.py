# !/usr/bin/env python
# -*- coding: utf-8 -*-

# Noestock.py : Lanceur d'une application Noethys version lite

import os
import wx
import xpy.xAppli as xAppli
import xpy.xUTILS_DB as xdb
import xpy.xGestionConfig as xGestionConfig
import xpy.outils.xaccueil as xaccueil
import srcNoestock.menu as menu

# Variables incontournables pour xpy
dictAPPLI = {
            'NOM_APPLICATION'       : "Noestock",
            'REP_SOURCES'           : "srcNoestock",
            'REP_DATA'              : "C:/ProgramData/Noelite",
            'REP_TEMP'              : "C:/Temp",
            'NOM_FICHIER_LOG'       : "logsNoestock.log",
            'TYPE_CONFIG'           : 'db_reseau',
            'CHOIX_CONFIGS': [('Centralisation',"Base au siège, cible pour les synchro et sauvegarde"),
                             ('Donnees', "Base de travail, peut être la centrale  en mode connecté")]
            }

class MyFrame(xAppli.MainFrame):
    def __init__(self, *args, **kw):
        kw['size'] = (750,520)
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
        #test = os.getcwd()
        self.MakeMenuBar()
        self.Show()

        self.ConnectBase(False)

    def ConnectBase(self, etat= False):
        # test de connexion par défaut
        DB = xdb.DB()
        self.echec = DB.echec
        if DB.echec == 0:
            etat = True
        self.GestMenu(etat)
        if not etat:
            self.infoStatus = "lancé sans accès à Noethys!"
        self.MakeStatusText()
        return

    def GestMenu(self, etat):
        # grise les boutons si pas d'accès à la base
        self.panelAccueil.EnableBoutons(etat)

        # grise ou dégrise les options du menu selon l'identification
        if self.dictUser :
            etat = True
        else: etat = False
        for numMenu in range(2,4):
            self.menu.EnableTop(numMenu, etat)


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