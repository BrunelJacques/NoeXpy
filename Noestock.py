# !/usr/bin/env python
# -*- coding: utf-8 -*-

# Noestock.py : Lanceur d'une application Noethys version lite

import wx
import xpy.xAppli as xAppli
import xpy.xUTILS_DB as xdb
import srcNoestock.menu as menu
from xpy.outils import xaccueil,xformat

# Variables incontournables pour xpy
dictAPPLI = {
            'NOM_APPLICATION'       : "Noestock",
            'REP_SOURCES'           : "srcNoestock",
            'REP_DATA'              : "C:/ProgramData/Noelite",
            'REP_TEMP'              : "C:/Temp",
            'NOM_FICHIER_LOG'       : "logsNoestock.log",
            'TYPE_CONFIG'           : 'db_reseau',
            'CHOIX_CONFIGS': [('Centralisation',"Base au siège, cible pour les synchro et sauvegarde"),
                             ('Donnees', "Base de travail, peut être la centrale  en mode connecté")],
            'LST_TABLES': ['utilisateurs','droits','cpta_analytiques',
                           'stArticles','stEffectifs','stMouvements','stInventaires']
            }
            # LST_TABLES Tables du schema à contrôler et à créer si inexistantes

class StFrame(xAppli.MainFrame):
    def __init__(self, *args, **kw):
        kw['size'] = (750,520)
        super().__init__( *args, **kw)

        # Intialise et Teste la présence de fichiers dans le répertoire sources
        #dictionnaire propre à l'appli
        self.dictAppli = dictAPPLI
        self.db = None

        self.xInit()
        self.menuClass = menu.MENU(self)
        self.dictMenu = menu.MENU.ParamMenu(self)
        self.ldButtons = menu.MENU.ParamBureau(self)
        if hasattr(menu.MENU,"CouleurFondBureau"):
            self.couleur_fond = menu.MENU.CouleurFondBureau(self)

        for dicBtn in self.ldButtons:
            if 'image' in dicBtn.keys() :
                    dicBtn['image'] = (str(self.pathXpy) + "/" + str(dicBtn["image"])).replace("\\","/")

        # Crée 'topPanel' et 'topContenu' destroyables
        self.MakeBureau(pnlTitre=xaccueil.Panel_Titre(self,texte="NOESTOCK\n\nGestion des stocks et prix journée",
                                                      image="xpy/Images/Noestock.png",
                                                      pos=(20,30),couleurFond=self.couleur_fond),
                        pnlBtnActions=xaccueil.Panel_Buttons(self,self.ldButtons,couleurFond=self.couleur_fond))

        self.MakeMenuBar()
        self.Show()
        self.ConnectBase(False)
        self.GestMenu(self.etat)

    def ConnectBase(self, etat= False):
        if self.db: return
        # test de connexion par défaut
        DB = xdb.DB(mute=True)
        self.echec = DB.echec
        self.etat = False
        if DB.echec == 0:
            self.etat = True
            self.db = DB
        return

    def GestMenu(self, etat):
        if not self.etat:
            mess = "Veuillez gérer les accès aux bases de données dans le menu Outils,\npuis testez l'accès !!"
            wx.MessageBox(mess,"Accès données impossible")
            self.infoStatus = "lancé sans accès à Noethys!"
        self.MakeStatusText()

        # grise les boutons si pas d'accès à la base
        self.panelAccueil.EnableBoutons(etat)
        for numMenu in range(1,4):
            self.menu.EnableTop(numMenu, etat)

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
        myframe = StFrame(None)
        self.SetTopWindow(myframe)
        return True

if __name__ == "__main__":
    # Lancement de l'application
    app = MyApp(redirect=False)
    app.MainLoop()