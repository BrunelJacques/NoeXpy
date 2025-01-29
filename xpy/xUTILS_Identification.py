#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------
# Application :    NoeXPY, outils d'identification avec mot de passe
# Auteur:          Ivan LUCAS, Jacques BRUNEL
# Licence:         Licence GNU GPL
#--------------------------------------------------------------------------

import xpy.outils.xchoixListe as xchoixliste
import xpy.outils.xshelve as xu_shelve
import xpy.xGestionConfig as xGestionConfig
import xpy.xUTILS_SaisieParams as xusp
import wx
import xpy.xUTILS_DB as xdb

# ---------- Gestion des utilisateurs

def VerificationDroits(dictUtilisateur=None, categorie="", action="", IDactivite=""):
    """ Vérifie si un utilisateur peut accéder à une action """
    if ((dictUtilisateur == None) or ("droits" in dictUtilisateur)) == False:
        return True

    dictDroits = dictUtilisateur["droits"]
    key = (categorie, action)

    if (dictDroits != None) and (key in dictDroits):
        etat = dictDroits[key]
        # Autorisation
        if etat.startswith("autorisation"):
            return True
        # Interdiction
        if etat.startswith("interdiction"):
            return False
        # Restriction
        if etat.startswith("restriction"):
            code = etat.replace("restriction_", "")
            mode, listeID = code.split(":")
            listeID = [int(x) for x in listeID.split(";")]

            if mode == "groupes":
                if len(listeID) == 1: condition = "IDtype_groupe_activite=%d" % listeID[0]
                if len(listeID) > 1: condition = "IDtype_groupe_activite IN %s" % str(
                    tuple(listeID))
                DB = xdb.DB()
                req = """SELECT IDgroupe_activite, activites 
                FROM groupes_activites
                WHERE %s;""" % condition
                DB.ExecuterReq(req)
                lstDonnees = DB.ResultatReq()
                listeActivites = []
                for IDgroupe_activite, IDactivite_temp in lstDonnees:
                    listeActivites.append(IDactivite_temp)
                DB.Close()

            if mode == "activites":
                listeActivites = listeID

            if IDactivite in listeActivites:
                return True
            else:
                return False

    return True

def VerificationDroitsUtilisateurActuel(categorie="", action="", IDactivite="",
                                        afficheMessage=True):
    try:
        topWindow = wx.GetApp().GetTopWindow()
        nomWindow = topWindow.GetName()
        dictUtilisateur = topWindow.dictUser
    except:
        dictUtilisateur = None
    if not dictUtilisateur:
        try:
            import xpy.outils.xshelve as xucfg
            cfg = xucfg.ParamUser()
            dictUtilisateur = cfg.GetDict(groupe='USER')
        except:
            pass
    if dictUtilisateur:
        # Si la frame 'General' est chargée, on y récupère le dict de config
        resultat = VerificationDroits(dictUtilisateur, categorie, action, IDactivite)
        if resultat == False and afficheMessage == True:
            wx.MessageBox(
                "'%s'\n\nVotre profil utilisateur  ne permet pas d'accéder à la fonctionnalité demandée!\n'%s' - '%s'"
                % (dictUtilisateur['nom'], categorie, action), style=wx.ICON_AUTH_NEEDED)
        return resultat
    return True

def GetIDutilisateur(afficheMessage=True):
    try:
        topWindow = wx.GetApp().GetTopWindow()
        dictUtilisateur = topWindow.dictUser
    except:
        dictUtilisateur = None
    if not dictUtilisateur:
        try:
            import xpy.outils.xshelve as xucfg
            cfg = xucfg.ParamUser()
            dictUtilisateur = cfg.GetDict(groupe='USER')
        except:
            pass
    if 'IDutilisateur' in dictUtilisateur.keys():
        # Si la frame 'General' est chargée, on y récupère le dict de config
        return dictUtilisateur['IDutilisateur']
    else:
        if afficheMessage == True:
            wx.MessageBox("Vous n'êtes pas identifiés\n\nrepassez par l'entrée",
                          style=wx.ICON_AUTH_NEEDED)
    return None

def GetDictUtilisateur(afficheMessage=True):
    try:
        topWindow = wx.GetApp().GetTopWindow()
        dictUtilisateur = topWindow.dictUser
    except:
        dictUtilisateur = None
    if not dictUtilisateur:
        # try :
        import xpy.outils.xshelve as xucfg
        cfg = xucfg.ParamUser()
        # userdomain, username ,config, mpUserDB, seudo, utilisateur, nom,prenom, IDutilisateur, droits,profil
        dictUtilisateur = cfg.GetDict(groupe='IDENT', close=False)
        user = cfg.GetDict(groupe='USER')
        dictUtilisateur.update(user)
        # except:
        pass
    if dictUtilisateur:
        # Si la frame 'General' est chargée, on y récupère le dict de config
        if not 'userdomain' in dictUtilisateur.keys():
            import socket
            dictUtilisateur['userdomain'] = socket.gethostname()
            dictUtilisateur['config'] = '_'
        return dictUtilisateur
    else:
        if afficheMessage == True:
            wx.MessageBox("Vous n'êtes pas identifiés\n\nrepassez par l'entrée",
                          style=wx.ICON_AUTH_NEEDED)
    return None

class CTRL_Bouton_image(wx.Button):
    # La classe xGTE.Button reprend le concept de manière plus large
    def __init__(self, parent, id=wx.ID_APPLY, texte="", cheminImage=None):
        wx.Button.__init__(self, parent, id=id, label=texte)
        if cheminImage:
            self.SetBitmap(wx.Bitmap(cheminImage))
        self.SetFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.SetInitialSize()

# ---------- Gestion identification

def SqlLstUsers(db=None):
    # Récupère la liste des utilisateurs et de leurs droits
    """ suppose l'accès à une base de donnée qui contient les tables génériques 'utilisateurs' et 'droits'"""
    if not db :
        DB = xdb.DB()
    else: DB = db
    if DB.echec:
        return False
    # Droits
    req = """SELECT IDdroit, IDutilisateur, IDmodele, categorie, action, etat
    FROM droits;"""
    DB.ExecuterReq(req)
    lstDonnees = DB.ResultatReq()
    dictDroitsUtilisateurs = {}
    dictDroitsModeles = {}
    for IDdroit, IDutilisateur, IDmodele, categorie, action, etat in lstDonnees:
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
    lstDonnees = DB.ResultatReq()
    listeUtilisateurs = []

    for IDutilisateur, sexe, nom, prenom, mdp, profil, actif in lstDonnees:
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

def GetNomOrdi():
    import socket
    return socket.gethostname()[:16]

def AfficheUsers(parent):
    # affiche les utilisateur puis sollicite le mot de passe pour le valider
    lstUsers = SqlLstUsers()
    if lstUsers:
        lstAffiche = [[x['nom'],x['prenom'],x['profil']] for x in lstUsers]
        lstColonnes = ["Nom", "Prénom", "Profil"]
        dlgListe = xchoixliste.DialogAffiche(titre="Liste des utilisateurs",intro="pour consultation seulement",
                                        lstDonnees=lstAffiche,
                                        lstColonnes=lstColonnes )
        ret = dlgListe.ShowModal()
        dlgListe.Destroy()
        if ret == wx.OK:
            SaisieMotPasse(parent)
        return ret

def SaisieMotPasse(parent):
    # lance l'écran de saisie de mot de passe d'identification et affiche le résultat en bas d'écran
    dlgMp = Dialog(parent)
    dlgMp.ShowModal()
    dictUser = dlgMp.GetDictUtilisateur()
    etat = False
    if dictUser:
        parent.dictUser = dictUser
        etat = True
    try:
        parent.GestMenu(etat)
        parent.infoStatus = "!"
        parent.MakeStatusText()
    except: pass
    dlgMp.Destroy()

class CTRL_Bouton_image(wx.Button):
    def __init__(self, parent, id=wx.ID_APPLY, texte="", cheminImage=None):
        wx.Button.__init__(self, parent, id=id, label=texte)
        if cheminImage:
            self.SetBitmap(wx.Bitmap(cheminImage))
        self.SetFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.SetInitialSize()

class CTRL_mdp(wx.TextCtrl):
    def __init__(self, parent, listeUtilisateurs=[], size=(-1, -1)):
        wx.TextCtrl.__init__(self, parent, size=size, style=wx.TE_PROCESS_ENTER | wx.TE_PASSWORD)
        self.parent = parent
        self.listeUtilisateurs = listeUtilisateurs
        #self.SetDescriptiveText("Votre mot de passe")

        # Options
        #self.SetCancelBitmap(wx.Bitmap("xpy/Images/16x16/Interdit.png", wx.BITMAP_TYPE_PNG))
        #self.SetSearchBitmap(wx.Bitmap("xpy/Images/16x16/Cadenas.png", wx.BITMAP_TYPE_PNG))

        # Binds
        #self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnSearch)
        #self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel)
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
        # Recherche de l'utilisateur et envoi dans ParamUser de shelve
        for dictUtilisateur in self.listeUtilisateurs :
            if txtSearch == dictUtilisateur["mdp"] :
                # Enregistrement de l'utilisateur et de ses propriétés
                import os
                cfg = xu_shelve.ParamUser()
                self.choix = cfg.GetDict(groupe='USER',close = False)
                dictUtilisateur['utilisateur'] =  dictUtilisateur['prenom'] + " " + dictUtilisateur['nom']
                self.choix['utilisateur'] =  dictUtilisateur['utilisateur']
                self.choix['nom'] = dictUtilisateur['nom']
                self.choix['prenom'] = dictUtilisateur['prenom']
                self.choix['IDutilisateur'] =  dictUtilisateur['IDutilisateur']
                self.choix['droits'] = dictUtilisateur['droits']
                self.choix['profil'] = dictUtilisateur['profil']
                self.choix['username'] = os.environ['USERNAME']
                self.choix['userdomain'] = GetNomOrdi()
                cfg.SetDict(self.choix, groupe='USER')

                if hasattr(self.parent,'On_trouve'):
                    self.parent.On_trouve(dictUtilisateur)
                    self.SetValue("")
                    break
        self.Refresh()

# --------------------------- DLG de saisie de mot de passe ----------------------------

class Dialog(wx.Dialog):
    # Affiche l'écran de saisie du mot de passe
    def __init__(self, parent, id=-1,title="xUTILS_Identification",confirm=True):
        wx.Dialog.__init__(self, parent, id, title, name="DLG_mdp",style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.parent = parent
        self.confirm = confirm
        self.echec = False
        self.dictUtilisateur = None
        self.listeUtilisateurs = []
        # reprise de la dernière connection
        DB = xdb.DB()
        self.dictAppli = DB.dictAppli
        self.grpConfigs = DB.grpConfigs
        # la dernière connection n'est pas valable, on la recrée en appelant un écran de connection
        if DB.echec:
            dlg = xGestionConfig.DLG_choixConfig(self)
            ret = dlg.ShowModal()
            if ret == wx.OK:
                DB = xdb.DB()
                self.dictAppli = DB.dictAppli
                self.grpConfigs = DB.grpConfigs
                if DB.echec:
                    self.echec = True
            else: self.echec = True
        # l'identification n'a de sens qu'en réseau
        if not DB.isNetwork:
            self.echec = True
            mess = "Identification impossible!\n\nIl faut se connecter à une base de donnée réseau pour s'identifier"
            wx.MessageBox(mess)
        if not self.echec:
            self.listeUtilisateurs = SqlLstUsers(db=DB)
        self.dictUtilisateur = None
        DB.Close()
        lstIDconfigs,lstConfigs,lstConfigsKO = xGestionConfig.GetLstConfigs(self.grpConfigs)
        try:
            lastConfig = self.grpConfigs['choixConfigs'][self.dictAppli['NOM_APPLICATION']]['lastConfig']
        except Exception:
            lastConfig = lstConfigs[0]

        # composition de l'écran
        self.staticbox = wx.StaticBox(self, -1, "Authentification")
        self.txtIntro = wx.StaticText(self, -1, "Vous serez identifié par votre seul mot de passe.\n"+
                                      "Choisissez une base de donnée du réseau !")
        self.txtConfigs = wx.StaticText(self, -1, "Base d'authentification:")
        self.comboConfigs = xusp.PNL_ctrl(self,
                                          **{'genre': 'combo', 'name': "configs",
                                                   'values': lstIDconfigs,
                                                   'help': "Choisissez la base de donnée qui servira à vous authentifier",
                                                   'size': (250, 30),
                                                    }
                                          )
        self.comboConfigs.SetValue(lastConfig)
        self.txtMdp = wx.StaticText(self, -1, "Votre mot de passe:")
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
        self.comboConfigs.Bind(wx.EVT_COMBOBOX, self.On_comboConfig)

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

    def On_comboConfig(self,event):
        config = event.EventObject.GetValue()
        DB = xdb.DB(config=config)
        if not DB.echec:
            self.listeUtilisateurs = SqlLstUsers(db=DB)
        DB.Close()

    # Fermeture de la fenêtre sur utilisateur trouvé
    def On_trouve(self, dictUtilisateur={}):
        # le contrôle a déja envoyé le dic utilisateur dans ParamUser via shelve
        self.dictUtilisateur = dictUtilisateur
        if self.confirm:
            wx.MessageBox("Utilisateur %s\n\nAvec droits: %s"%(dictUtilisateur["utilisateur"],
                                                           dictUtilisateur["profil"]))
        # Fermeture de la fenêtre
        self.EndModal(wx.OK)

    def GetDictUtilisateur(self):
        return self.dictUtilisateur
    
# ----------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    app = wx.App(0)
    import os
    os.chdir("..")
    ret = AfficheUsers(None)
    dlg = Dialog(None)
    app.SetTopWindow(dlg)
    ret = dlg.ShowModal()
    if ret == wx.OK:
        print(dlg.GetDictUtilisateur()['nom'])

    app.MainLoop()
