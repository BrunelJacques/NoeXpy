#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import sys
import wx
import xpy.xGestionDB as xdb
import xpy.outils.xchoixListe as xchoixliste
import xpy.xUTILS_Shelve as xu_shelve
import xpy.xGestionConfig as xGestionConfig
import xpy.xUTILS_SaisieParams as xusp

def GetUserLocal():
    # vient de Noethys, non encore utilisée
    argStart = sys.argv
    # lancement avec des arguments, le premier est l'user
    if len(argStart)>1:
        user = argStart[1]
    # récup l'user systeme
    else:
        import os
        os.environ['USERNAME']
    return [{"IDutilisateur": "local", "nom": user, "prenom": "en Local", "sexe": "M", "mdp": "local",
                        "profil": "", "actif": True, "droits": {}},]


def GetListeUsers():
    """ Récupère la liste des utilisateurs et de leurs droits """
    DB = xdb.DB()
    if DB.echec:
        return False
    # Droits
    req = """SELECT IDdroit, IDutilisateur, IDmodele, categorie, action, etat
    FROM droits;"""
    DB.ExecuterReq(req)
    listeDonnees = DB.ResultatReq()
    dictDroitsUtilisateurs = {}
    dictDroitsModeles = {}
    for IDdroit, IDutilisateur, IDmodele, categorie, action, etat in listeDonnees:
        key = (categorie, action)
        if IDutilisateur != None:
            if not IDutilisateur in dictDroitsUtilisateurs:
                dictDroitsUtilisateurs[IDutilisateur] = {}
            dictDroitsUtilisateurs[IDutilisateur][key] = etat
        if IDmodele != None:
            if not IDmodele in dictDroitsModeles:
                dictDroitsModeles[IDmodele] = {}
            dictDroitsModeles[IDmodele][key] = etat

    # Utilisateurs
    req = """SELECT IDutilisateur, sexe, nom, prenom, mdp, profil, actif
    FROM utilisateurs
    WHERE actif=1;"""
    DB.ExecuterReq(req)
    listeDonnees = DB.ResultatReq()
    listeUtilisateurs = []

    for IDutilisateur, sexe, nom, prenom, mdp, profil, actif in listeDonnees:
        droits = None
        if profil.startswith("administrateur"):
            droits = None
        if profil.startswith("modele"):
            IDmodele = int(profil.split(":")[1])
            if IDmodele in dictDroitsModeles:
                droits = dictDroitsModeles[IDmodele]
        if profil.startswith("perso"):
            if IDutilisateur in dictDroitsUtilisateurs:
                droits = dictDroitsUtilisateurs[IDutilisateur]

        dictTemp = {"IDutilisateur": IDutilisateur, "nom": nom, "prenom": prenom, "sexe": sexe, "mdp": mdp,
                    "profil": profil, "actif": actif, "droits": droits}
        listeUtilisateurs.append(dictTemp)

    DB.Close()
    return listeUtilisateurs

class AfficheUsers():
    def __init__(self):
        lstUsers = GetListeUsers()
        if lstUsers:
            lstAffiche = [[x['nom'],x['prenom'],x['profil']] for x in lstUsers]
            lstColonnes = ["Nom", "Prénom", "Profil"]
            dlg = xchoixliste.DialogAffiche(titre="Liste des utilisateurs",intro="pour consultation seulement",
                                            lstDonnees=lstAffiche,
                                            lstColonnes=lstColonnes )
            dlg.ShowModal()
            dlg.Destroy()

class CTRL_Bouton_image(wx.Button):
    def __init__(self, parent, id=wx.ID_APPLY, texte="", cheminImage=None):
        wx.Button.__init__(self, parent, id=id, label=texte)
        if cheminImage:
            self.SetBitmap(wx.Bitmap(cheminImage))
        self.SetFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.SetInitialSize()

class CTRL_mdp(wx.SearchCtrl):
    def __init__(self, parent, listeUtilisateurs=[], size=(-1, -1)):
        wx.SearchCtrl.__init__(self, parent, size=size, style=wx.TE_PROCESS_ENTER | wx.TE_PASSWORD)
        self.parent = parent
        self.listeUtilisateurs = listeUtilisateurs
        self.SetDescriptiveText("Votre mot de passe")

        # Options

        self.SetCancelBitmap(wx.Bitmap("xpy/Images/16x16/Interdit.png", wx.BITMAP_TYPE_PNG))
        self.SetSearchBitmap(wx.Bitmap("xpy/Images/16x16/Cadenas.png", wx.BITMAP_TYPE_PNG))
        # Binds
        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnSearch)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnDoSearch)
        self.Bind(wx.EVT_TEXT, self.OnDoSearch)

    def OnSearch(self, event):
        self.Recherche()
        event.Skip() 
            
    def OnCancel(self, event):
        self.SetValue("")
        self.Recherche()
        event.Skip() 

    def OnDoSearch(self, event):
        self.Recherche()
        event.Skip() 

    def Recherche(self):
        txtSearch = self.GetValue()
        # Recherche de l'utilisateur
        for dictUtilisateur in self.listeUtilisateurs :
            if txtSearch == dictUtilisateur["mdp"] :
                # Enregistrement du pseudo et mot de passe
                cfg = xu_shelve.ParamUser()
                self.choix = cfg.GetDict(groupe='USER',close = False)
                dictUtilisateur['utilisateur'] =  dictUtilisateur['prenom'] + " " + dictUtilisateur['nom']
                self.choix['utilisateur'] =  dictUtilisateur['utilisateur']
                self.choix['nom'] = dictUtilisateur['nom']
                self.choix['prenom'] = dictUtilisateur['prenom']
                self.choix['IDutilisateur'] =  dictUtilisateur['IDutilisateur']
                self.choix['droits'] = dictUtilisateur['droits']
                self.choix['profil'] = dictUtilisateur['profil']
                cfg.SetDict(self.choix, groupe='USER')

                if hasattr(self.parent,'ChargeUtilisateur'):
                    self.parent.ChargeUtilisateur(dictUtilisateur)
                    self.SetValue("")
                    break
        self.Refresh()

# --------------------------- DLG de saisie de mot de passe ----------------------------

class Dialog(wx.Dialog):
    # Affiche la liste des utilisateur
    def __init__(self, parent, id=-1, title="xUTILS_Identification"):
        wx.Dialog.__init__(self, parent, id, title, name="DLG_mdp",style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.parent = parent
        self.echec = False
        self.dictUtilisateur = None
        self.listeUtilisateurs = []
        DB = xdb.DB()
        self.dictAppli = DB.dictAppli
        self.grpConfigs = DB.grpConfigs
        if DB.echec:
            dlg = xGestionConfig.DLG_implantation(self)
            ret = dlg.ShowModal()
            if ret == wx.ID_OK:
                DB = xdb.DB()
                self.dictAppli = DB.dictAppli
                self.grpConfigs = DB.grpConfigs
                if DB.echec:
                    self.echec = True
            else: self.echec = True
        # l'identification n'a de sens qu'en réseau
        if not DB.isNetwork:
            self.echec = True
        DB.Close()
        if not self.echec:
            self.listeUtilisateurs = GetListeUsers()
        self.dictUtilisateur = None
        lstIDconfigs,lstConfigs,lstConfigsKO = xGestionConfig.GetLstConfigs(self.grpConfigs)

        # composition de l'écran
        self.staticbox = wx.StaticBox(self, -1, "Authentification")
        self.txtIntro = wx.StaticText(self, -1, "Vous serez identifié par votre seul mot de passe.\n"+
                                      "Choisissez une base de donnée du réseau !")
        self.txtConfigs = wx.StaticText(self, -1, "Base d'authentification:")
        self.comboConfigs = xusp.PNL_ctrl(self,
                                          **{'genre': 'combo', 'name': "configs",
                                                   'values': lstIDconfigs,
                                                   'help': "Choisissez la base de donnée qui servira à vous authentifier",
                                                   'size': (250, 60)}
                                          )
        self.txtMdp = wx.StaticText(self, -1, "Utilisateur:")
        self.ctrlMdp = CTRL_mdp(self, listeUtilisateurs=self.listeUtilisateurs)

        self.bouton_annuler = CTRL_Bouton_image(self, id=wx.ID_CANCEL, texte="Annuler",
                                                cheminImage="xpy/Images/32x32/Annuler.png")

        self.__set_properties()
        self.__do_layout()
        self.ctrlMdp.SetFocus()
        
    def __set_properties(self):
        self.txtConfigs.SetForegroundColour((100,100,100))
        self.txtIntro.SetForegroundColour(wx.BLUE)
        self.bouton_annuler.SetToolTip("Cliquez ici pour abandonner")

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=0, hgap=0)

        grid_sizer_base.Add(self.txtIntro, 0, wx.ALL| wx.EXPAND, 10)
        # Staticbox
        staticbox = wx.StaticBoxSizer(self.staticbox, wx.HORIZONTAL)
        grid_sizer_contenu = wx.FlexGridSizer(rows=4, cols=1, vgap=2, hgap=2)
        grid_sizer_contenu.Add(self.txtConfigs, 0, wx.TOP, 10)
        grid_sizer_contenu.Add(self.comboConfigs,  1, wx.LEFT|wx.ALIGN_LEFT|wx.EXPAND, 20)
        grid_sizer_contenu.Add(self.txtMdp,  0, wx.TOP, 20 )
        grid_sizer_contenu.Add(self.ctrlMdp, 1, wx.LEFT|wx.ALIGN_LEFT|wx.EXPAND, 30)
        grid_sizer_contenu.AddGrowableCol(0)
        staticbox.Add(grid_sizer_contenu, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(staticbox, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        
        # Boutons
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=3, vgap=10, hgap=10)
        grid_sizer_boutons.Add((20, 20), 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(0)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.ALL|wx.EXPAND, 10)
        
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.Fit(self)
        self.Layout()
        self.CentreOnScreen()

    def ChargeUtilisateur(self, dictUtilisateur={}):
        self.dictUtilisateur = dictUtilisateur
        # Fermeture de la fenêtre
        self.EndModal(wx.ID_OK)

    def GetDictUtilisateur(self):
        return self.dictUtilisateur
    
# ----------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    app = wx.App(0)
    import os
    os.chdir("..")
    #ret = AfficheUsers()
    dlg = Dialog(None)
    app.SetTopWindow(dlg)
    ret = dlg.ShowModal()
    if ret == wx.ID_OK:
        print(dlg.GetDictUtilisateur()['nom'])

    app.MainLoop()
