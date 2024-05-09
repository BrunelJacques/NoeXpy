#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------
# Application :    Gestion GITHUB install ou mise à jour d'application
# Auteur:          Jacques BRUNEL
# Licence:         Licence GNU GPL
#--------------------------------------------------------------------------

import os, sys

try:
    mess = "lancement gitPython"
    messRaise = "Installer git par commande windows 'pip install gitpython'\n"
    SEP = "\\"
    if "linux" in sys.platform:
        messRaise = "Installer git sous linux: 'sudo apt install git'"
        SEP = "/"
    import git

    mess = "lancement wxPython"
    messRaise = "Installer wxPython par commande 'pip install wxPython'"
    if "linux" in sys.platform:
        messRaise = ("Installer wxPython sous Linux:\n" +
                    "pip3 install -U -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-22.04 wxPython")
    import wx
except Exception as err:
    raise Exception("Echec %s: %s\n%s" % (mess, err, messRaise))

def PullGithub(appli_path, stash_changes=False, reset_hard=False):
    mess = "Lancement Update\n"
    err = None
    try:
        # Ouvrir le dépôt Git
        repo = git.Repo(appli_path)

        # Stasher les changements locaux si nécessaire
        if stash_changes:
            repo.git.stash("save", "--include-untracked")
            mess += "Changements stashed."

        # Réinitialiser les changements locaux si nécessaire
        if reset_hard:
            repo.git.reset("--hard", "HEAD")
            mess += "Changements locaux réinitialisés.\n"

        # Effectuer git pull depuis la branche actuelle
        origin = repo.remote(name='origin')
        origin.pull()
        mess = "\nMise à jour réussie."

    except git.exc.GitCommandError as e:
        mess += f"\nErreur lors de la mise à jour : {e}"
        err = True
    return err, mess

def CloneGithub(repo_url, appli_path):
    err = None
    try:
        # Cloner le dépôt GitHub dans le chemin spécifié
        repo = git.Repo.clone_from(repo_url, appli_path)
        mess = "Clonage réussi."

    except git.exc.GitCommandError as e:
        mess = f"Erreur lors du clonage : {e}"
        err = True
    return err, mess

class DLG(wx.Dialog):
    def __init__(self,lanceur=""):
        super().__init__(None, title="Installateur depuis GITHUB",
                         pos=(400, 200),
                         style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.initialPath = os.getcwd()
        self.lblPull = "   Release de l'existant"
        self.lblClone = "   Nouvelle installation"
        self.lstApplis = ['NoeXpy','Noethys-Matthania']
        self.lstFichierTest = ['Noestock.py','noethys%sNoethys.py'%SEP]
        self.lanceur = lanceur
        self.initChoixAppli = ""
        if lanceur.lower() in ['noestock', 'noelite','noexpy']:
            self.initChoixAppli = 'NoeXpy'
        elif lanceur.lower() in ['noethys-matthania','noethys']:
            self.initChoixAppli = 'Noethys-Matthania'
        self.warning = False
        self.Controls()
        self.Proprietes()
        self.InitSizer()

    def Controls(self):
        self.staticboxAppli = wx.StaticBox(self, label=" Choix de l'application ")
        self.staticboxDir = wx.StaticBox(self, label=" Répertoire de l'application (parcourir avec BROWSE)")
        choices = []
        for x in self.lstApplis:
            if x not in choices:
                choices.append(x)
        self.cmbAppli = wx.ComboBox(self, value=self.initChoixAppli, choices=choices)
        self.radPull = wx.RadioButton(self, label=self.lblPull, style=wx.RB_GROUP)
        self.radClone = wx.RadioButton(self, label=self.lblClone)


        self.dirPicker = wx.DirPickerCtrl(self,
                                          message="Choisir le répertoire d'installation:",
                                          path=self.initialPath,
                                          style=wx.DIRP_USE_TEXTCTRL,
                                          name="dirPicker")
        self.checkForce = wx.CheckBox(self, label="Forcer l'opération sans contrôle")
        self.btnOk = wx.Button(self, label="Action")

    def Proprietes(self):
        self.Bind(wx.EVT_COMBOBOX, self.Validation, self.cmbAppli)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadio, self.radClone)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadio, self.radPull)
        self.Bind(wx.EVT_DIRPICKER_CHANGED, self.OnDirPicker, self.dirPicker)
        self.Bind(wx.EVT_BUTTON, self.on_ok, self.btnOk)
        self.radClone.SetToolTip(
            "Pour une nouvelle installation, l'emplacement doit être vide")
        self.radPull.SetToolTip("Pour une mise à jour, être dans l'emplacement")
        self.cmbAppli.SetToolTip("Choix de l'application à installer")
        self.dirPicker.SetToolTip(
            "Il s'agit du répertoire où l'application doit être installée")
        self.checkForce.SetToolTip(
            "Cette option permet d'ignorer les modifications locales, écrase l'existant")
        self.SetMinSize((350, 270))
        self.SetSize(450, 300)

    def InitSizer(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizerAppli = wx.StaticBoxSizer(self.staticboxAppli)
        sizerAppli.Add(self.cmbAppli, 0, wx.ALL, 5)
        sizerAppli.Add((10, 10), 1, wx.EXPAND, 0)
        sizerRadio = wx.BoxSizer(wx.VERTICAL)
        sizerRadio.Add(self.radPull, 1, wx.TOP, 5)
        sizerRadio.Add(self.radClone, 1, wx.BOTTOM | wx.EXPAND, 5)
        sizerAppli.Add(sizerRadio, 15, wx.EXPAND, 0)
        sizer.Add(sizerAppli, 1, wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, 10)
        sizerDir = wx.StaticBoxSizer(self.staticboxDir, orient=wx.VERTICAL)
        sizerDir.Add(self.dirPicker, 1, wx.EXPAND | wx.ALL, 5)
        sizerDir.Add(self.checkForce, 0, wx.LEFT, 15)
        sizer.Add(sizerDir, 1, wx.EXPAND | wx.ALL, 10)
        sizer.Add(self.btnOk, 0, wx.RIGHT | wx.BOTTOM | wx.ALIGN_RIGHT, 20)
        self.SetSizer(sizer)
        self.Show()

    def Validation(self,event=None):
        self.warning = False
        # vérif choix appli, certains tests ne bloquent pas: self.checkForce.GetValue()
        libAppli = self.cmbAppli.GetValue()
        if len(libAppli) < 3:
            wx.MessageBox("Choisissez une application dans la liste\n\nouvrez la liste",
                          "Nom de l'appli court!")
            self.cmbAppli.SetFocus()
            self.warning = True
            return self.checkForce.GetValue()

        # vérif de l'emplacement selon action souhaitée
        dir = self.dirPicker.GetPath()
        lstDir = dir.split(SEP)
        if lstDir[0] == "":
            # absence de dir
            wx.MessageBox("Déterminez une localisation pour l'appli\n\nutilisez Browse",
                          "Pas de répertoire")
            self.dirPicker.SetFocus()
            return False
        isPull = self.radPull.GetValue()
        from pathlib import Path

        # vérif télescopage de fichiers
        if isPull:
            # une mise à jour est demandée
            file = "requirements.txt"
            if libAppli in self.lstApplis:
                file = self.lstFichierTest[self.lstApplis.index(libAppli)]
            chemin_fichier = dir + SEP + file
            if not Path(chemin_fichier).is_file():
                # absence de fichier requirements = mauvais positionnement
                mess = "Pb de positionnement pour une mise à jour, \n\n"
                mess += f"'{SEP}{file}' est normalement présent à la racine de l'appli"
                mess += f" '{libAppli}'"
                wx.MessageBox(mess,"Echec test de présence fichier")
                self.dirPicker.SetFocus()
                self.warning = True
                return self.checkForce.GetValue()
        else:
            # nouvelle installation
            chemin_appli = dir + SEP + libAppli
            exists = os.path.exists(chemin_appli)
            if exists and len(os.listdir(chemin_appli)) > 0:
                # répertoire non vide
                mess = f"Le répertoire '{chemin_appli}' n'est pas vide\n\n"
                mess += "une installation crée le repertoire ou se fait dans un vide"
                wx.MessageBox(mess,"Echec car présence fichiers")
                self.dirPicker.SetFocus()
                self.warning = True
                return self.checkForce.GetValue()

        # vérif de non imbrication d'applis
        if not isPull:
            # test nom d'une appli à installer déjà le path
            for appli in self.lstApplis:
                if appli in dir:
                    mess = f"Le répertoire '{dir}' contient déjà une appli\n\n"
                    mess += f"l'appli '{libAppli}' ne peut s'installer dans '{appli}'"
                    mess += "\nvoyez pour une mise à jour ou installer ailleurs."
                    wx.MessageBox(mess,"Risque d'imbrication d'applications")
                    self.dirPicker.SetFocus()
                    self.warning = True
                    return self.checkForce.GetValue()

        # l'ensemble de tests est ok
        return True

    def Execution(self):
        # confirmation du lancement
        dir = self.dirPicker.GetPath()
        appli = self.cmbAppli.GetValue()
        isPull = self.radPull.GetValue()
        style = wx.YES_NO | wx.ICON_INFORMATION
        force = ""
        if self.warning:
            style = wx.YES_NO | wx.ICON_WARNING
            force = "\navec tentative d'écrasement de l'éxistant"
        action = "Nous allons procéder à une installation de"
        if isPull: action = "Nous allons mettre à jour "
        ret = wx.MessageBox(f"{action} '{appli}'\n\nsur: {dir} {force}",
                            "Confirmez", style)
        if ret != wx.YES:
            return None

        # lance l'action
        if isPull:
            # MAJ par pull
            stash = self.checkForce
            reset = self.checkForce
            err, mess = PullGithub(dir, stash_changes=stash, reset_hard=reset)
        else:
            # Install par clone
            url = f"https://github.com/BrunelJacques/{appli}"
            err, mess = CloneGithub(url, dir)
        if err:
            style = wx.ICON_ERROR
        else:
            style = wx.ICON_INFORMATION
        return  wx.MessageBox(mess, "Rapport de l'action", style=style)

    def AjustePath(self):
        appli = self.cmbAppli.GetValue()
        dir = self.dirPicker.GetPath()
        # enlève un éventuel séparateur final
        if dir[-1] == SEP:
            dir = dir[:-1]
        lastDir = dir.split(SEP)[-1]
        # ajuste dir si lastDir est n'est pas contenu avec le nom de l'appli
        if not lastDir.lower()[:6] in appli.lower():
            dir += SEP+appli
        self.dirPicker.SetPath(dir)

    def OnDirPicker(self, event):
        self.AjustePath()
        self.Validation()

    def OnRadio(self, event):
        self.AjustePath()
        self.Validation()

    def on_ok(self, event):
        self.AjustePath()
        if not self.Validation():
            return
        ret = self.Execution()
        if ret == wx.OK:
             self.Close()

# Lancement
if __name__ == "__main__":
    os.chdir("..")
    app = wx.App(False)
    #repo = git.Repo(os.getcwd())
    repo = git.Repo("D:\\temp\\zztest\\NoeXpy")
    ret = repo.git.status()

    dlg = DLG("Noexpy")
    app.MainLoop()

    """
    repo_url = "https://github.com/BrunelJacques/NoeXpy"# URL du dépôt GitHub
    appli_path = "D:\\temp\\Noexpy_Test\\"
    # CloneGithub(repo_url, appli_path)
    # PullGithub(appli_path, stash_changes=True, reset_hard=False)
    """
