# !/usr/bin/env python
# -*- coding: utf-8 -*-

#------------------------------------------------------------------------
# Application :    Projet XPY, atelier de développement
# Auteurs:          Jacques BRUNEL,
# Copyright:       (c) 2019-04     Cerfrance Provence, Matthania
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
import os
import sys
import xpy.outils.xUTILS_RapportBugs
import xpy.outils.xshelve
import xpy.outils.xshelve    as xucfg
from  xpy.outils import xaccueil


def CrashReport(dictAppli):
    # Crash report
    fichierLog = dictAppli['NOM_FICHIER_LOG']
    appli = dictAppli['NOM_APPLICATION']
    if 'VERSION_APPLICATION' in dictAppli.keys():
        version = dictAppli['VERSION_APPLICATION']
    else: version = appli
    xpy.outils.xUTILS_RapportBugs.Activer_rapport_erreurs(version=version, appli = appli)
    print('CrashReport ok')

    # Supprime le journal.log si supérieur à 10 Mo
    if os.path.isfile(fichierLog):
        taille = os.path.getsize(fichierLog)
        if taille > 5000000:
            os.remove(fichierLog)

class MainFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super().__init__(*args, name='general', style=wx.DEFAULT_FRAME_STYLE, **kw)
        # Vérifie le path xpy
        self.pathXpy = os.path.dirname(os.path.abspath(__file__))
        if not self.pathXpy in sys.path:
            sys.path = [self.pathXpy] + sys.path
        # le dictionnaire config contiendra  toutes les configurations de l'utilisateur,
        #       enregistrées dans des fichiers  soit dans profilUser ou dans Data selon xUTILS_Shelve
        self.config = None
        self.dictMenu = None
        self.lstBtnBureau = None
        self.couleur_fond = wx.Colour(0,240,240)
        self.dictUser = None

    def xInit(self):
        print("Lancement %s"%self.dictAppli['NOM_APPLICATION'])
        print(self.pathXpy)
        os.chdir(self.pathXpy)
        os.chdir('..')
        pathCourant = os.getcwd()
        self.pathData = pathCourant +"\\%s"%self.dictAppli['REP_DATA']
        if "c:" in self.dictAppli['REP_DATA'].lower():
            self.pathData = self.dictAppli['REP_DATA']

        self.pathTemp = pathCourant + "\\%s" % self.dictAppli['REP_TEMP']
        if "c:" in self.dictAppli['REP_TEMP'].lower():
            self.pathTemp = self.dictAppli['REP_TEMP']
        self.pathSrcAppli = pathCourant +"\\%s"%self.dictAppli['REP_SOURCES']
        # teste la présence de sources
        lstFiles = os.listdir(self.pathSrcAppli)
        self.CentreOnScreen()
        # vérif de la présence de modules dans le répertoire visé
        nbModules = 0
        for nom in lstFiles:
            if nom[-3:] == '.py':
                nbModules += 1
        if not nbModules > 0:
            wx.MessageBox("Aucun module présent dans %s"%self.pathSrcAppli, 'Lancement impossible', wx.OK | wx.ICON_STOP)
            return None
        # des modules sont présents on continue
        else:
            # Ajoute le path des modules spécifiques pour les imports
            if not self.pathSrcAppli in sys.path:
                sys.path = [self.pathSrcAppli] + sys.path
            # Vérifie l'existence des répertoires Data et Temp et les crées
            for rep in (self.pathData, self.pathTemp):
                xucfg.CreePath(rep)
            for rep in ('pathData', 'pathTemp','pathSrcAppli','pathXpy'):
                self.dictAppli[rep] = eval('self.'+rep)

            # Crée un message initial de bas de fenêtre status bar
            self.CreateStatusBar()
            self.MakeStatusText()
            return wx.OK

    def MakeStatusText(self):
        cfgU = xucfg.ParamUser()
        self.config = cfgU.SetDict(self.dictAppli, groupe='APPLI')

        # appel de la configuration base de données dans paramFile
        cfgF = xucfg.ParamFile()
        grpCONFIGS = cfgF.GetDict(dictDemande=None, groupe='CONFIGS')
        nomAppli = self.dictAppli['NOM_APPLICATION']
        nomConfig = ''
        if 'choixConfigs' in grpCONFIGS:
            if nomAppli and nomAppli in grpCONFIGS['choixConfigs'].keys():
                if 'lastConfig' in grpCONFIGS['choixConfigs'][nomAppli].keys():
                    nomConfig = grpCONFIGS['choixConfigs'][nomAppli]['lastConfig']
        messBD = "données: '%s'" % (nomConfig)
        self.nomVersion = "%s %s" % (self.dictAppli['NOM_APPLICATION'], xaccueil.GetVersion(self))
        self.messageStatus = "%s |  %s" % (self.nomVersion, messBD)

        if hasattr(self,'dictUser') and self.dictUser:
            self.messageStatus += ",  Utilisateur: %s" % (self.dictUser['utilisateur'])
        if hasattr(self,'infoStatus'):
            self.messageStatus += " | %s" % (self.infoStatus)

        self.SetStatusText(self.messageStatus)

    def MakeHello(self,message):
        # affichage d'un écran simple rappelant un message
        self.topPanel = wx.Panel(self)
        self.topContenu = wx.StaticText(self.topPanel, label=message, pos=(25, 25))
        font = self.topContenu.GetFont()
        font.PointSize += 5
        font = font.Bold()
        self.topContenu.SetFont(font)

    def MakeBureau(self,pnlTitre=None,pnlBtnActions=None):
        # Construction du bureau composé d'un titre et d'un aligment de boutons d'actions du menu choisies
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.panelAccueil = xaccueil.Panel_Accueil(self,pnlTitre=pnlTitre,pnlBtnActions=pnlBtnActions)
        sizer.Add(self.panelAccueil, 0, wx.EXPAND, 0)
        self.SetSizerAndFit(sizer)

    def MakeMenuBar(self):
        # Construction de la barre de menu à partir du fichier menu.py présent dans les sources de l'appli
        if not self.dictMenu:
            self.dictMenu = {}
            try:
                import menu
                self.menuClass = menu.MENU(self)
                self.dictMenu = menu.MENU.ParamMenu(self)
            except:
                wx.MessageBox("Echec de l'ouverture de l'objet : 'MENU.ParamMenu'\ndans %s"%self.pathSrcAppli+"\menu.py", 'Lancement impossible', wx.OK | wx.ICON_STOP)

        # Création du menu dernière branche
        def CreationItem(menuParent, item):

            # Lance l'action dans l'appli ou dans xAppli par défaut
            def OnAction(event):
                id = event.GetId()
                if id in self.dictMenuActions:
                    if self.dictMenuActions[id] in dir(self.menuClass):
                        action='self.menuClass.'+self.dictMenuActions[id]+'(self)'
                    else:
                        mess1 = 'Fonction \'%s\' non présente dans le fichier menu.py de l\'appli'%self.dictMenuActions[id]
                        if self.dictMenuActions[id] in dir(self):
                            action = 'self.' + self.dictMenuActions[id] + '(self)'
                        else:
                            wx.MessageBox(mess1,'Non Programmé', wx.OK | wx.ICON_STOP)
                eval(action)

            id = wx.NewId()
            if 'genre' in item.keys():
                genre = item['genre']
            else :
                genre = wx.ITEM_NORMAL
            itemMenu = wx.MenuItem(parentMenu=menuParent, id = id, text = item['label'], helpString=item['infobulle'], kind = genre)
            if 'actif' in item.keys() :
                itemMenu.Enable(item['actif'])
            if 'image' in item.keys():
                ptImage = (str(self.pathXpy) + "/" + str(item['image'])).replace('\\','/')
                itemMenu.SetBitmap(wx.Bitmap(ptImage, wx.BITMAP_TYPE_PNG))
            ctrl = menuParent.Append(itemMenu)
            self.Bind(wx.EVT_MENU, OnAction, id=id)

            self.dictInfosMenu[item['code']] = {'id' : id, 'ctrl' : ctrl}
            self.dictMenuActions[id] = item['action']

        # Déroulé des branches du menu
        def CreationMenu(menuParent, item, sousmenu=False):
            menu = wx.Menu()
            id = wx.NewId()
            for sousitem in item['items']:
                if sousitem == '-':
                    menu.AppendSeparator()
                elif 'items' in sousitem.keys():
                    CreationMenu(menu, sousitem, sousmenu=True)
                else:
                    CreationItem(menu, sousitem)
            if sousmenu == True:
                ctrl = menuParent.AppendSubMenu( menu, item['label'])
            else:
                ctrl = menuParent.Append(menu, item['label'])
            self.dictInfosMenu[item['code']] = {'id': id, 'ctrl': ctrl}

        # Racine du menu
        self.menu = wx.MenuBar()
        self.dictInfosMenu = {}
        self.dictMenuActions = {}

        # Pour chaque colonne
        for colonne in self.dictMenu:
            CreationMenu(self.menu, colonne)

        # Give the menu bar to the frame
        self.SetMenuBar(self.menu)

    def Final(self, videRepertoiresTemp=True):
        """ Fin de l'application
        # Mémorise l'action dans l'historique
        if self.userConfig["nomFichier"] != "":
            try:
                UTILS_Historique.InsertActions([{
                    "IDcategorie": 1,
                    "action": _(u"Fermeture du fichier"),
                }, ])
            except:
                pass

        # Mémorisation du paramètre de la taille d'écran
        if self.IsMaximized() == True:
            taille_fenetre = (0, 0)
        else:
            taille_fenetre = tuple(self.GetSize())
        self.userConfig["taille_fenetre"] = taille_fenetre

        # Mémorisation des perspectives
        self.SauvegardePerspectiveActive()
        self.userConfig["perspectives"] = self.perspectives
        self.userConfig["perspective_active"] = self.perspective_active

        if hasattr(self, "ctrl_remplissage"):
            self.userConfig["perspective_ctrl_effectifs"] = self.ctrl_remplissage.SavePerspective()
            self.userConfig["page_ctrl_effectifs"] = self.ctrl_remplissage.GetPageActive()

            # Sauvegarde du fichier de configuration
        self.SaveFichierConfig(nomFichier=self.nomFichierConfig)

        # Vidage des répertoires Temp
        if videRepertoiresTemp == True:
            FonctionsPerso.VideRepertoireTemp()
            FonctionsPerso.VideRepertoireUpdates()

        # Arrête le timer Autodeconnect
        if self.autodeconnect_timer.IsRunning():
            self.autodeconnect_timer.Stop()

        # Affiche les connexions restées ouvertes
        GestionDB.AfficheConnexionOuvertes()
        """
        return True

    def xQuitter(self, event):
        """Close the frame, terminating the application."""
        if self.Final() == False :
            return
        self.Close(True)

    def xInfos(self, event):
        """Display an About Dialog"""
        wx.MessageBox("xAppli : Prochainement une action d'information sera générée par défaut", 'Projet en attente',
                      wx.OK|wx.ICON_INFORMATION)

    def xAide(self, event):
        """Display an About Dialog"""
        wx.MessageBox("xAppli : Prochainement une action d'aide sera générée par défaut", 'Projet en attente',
                      wx.OK|wx.ICON_INFORMATION)

    def SaisieConfig(self):
        import xpy.xGestionConfig as gc
        cfg = gc.DLG_implantation(self )
        ret = cfg.ShowModal()
        if ret == wx.ID_OK:
            self.MakeStatusText()
        return ret

#************************   Pour Test    *******************************
if __name__ == "__main__":
    # Lancement de l'application
    app = wx.App()
    frm = MainFrame(None, title='xPY morceaux choisis')
    frm.dictAppli = {
        'NOM_APPLICATION': "xAppli",
        'REP_SOURCES': "srcMyAppli",
        'REP_DATA': "srcMyAppli/Data",
        'REP_TEMP': "srcMyAppli/Temp",
        'NOM_FICHIER_LOG':"testLOG",
        'TYPE_CONFIG': 'db_reseau',
        }
    CrashReport(frm.dictAppli)
    frm.xInit()

    frm.Show()
    #frm.MakeHello("OK test")
    frm.SaisieConfig()
    app.MainLoop()

